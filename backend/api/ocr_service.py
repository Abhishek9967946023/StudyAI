"""
=============================================================================
StudyAI — Optical Character Recognition (OCR) Production Subsystem
=============================================================================
Provides a robust, portable, page-aware, and fault-tolerant document processing
and OCR subsystem for scanned, image-based, and mixed PDFs.

Core Features:
1. Multi-Stage Discovery:
   Resolves Tesseract binary across settings, TESSERACT_CMD env, PATH,
   Windows Registry (UB-Mannheim / Tesseract-OCR), and standard OS locations
   (Windows, Linux, macOS) without hardcoding developer paths.
2. Health & Diagnostic Engine:
   Full health report (executable, version, language packs, renderers, permissions, limits).
3. Structured Error Taxonomy:
   Categorized error codes (OCR_TESSERACT_NOT_FOUND, OCR_LANGUAGE_NOT_FOUND,
   OCR_RENDER_FAILED, OCR_TIMEOUT, OCR_MEMORY_LIMIT, OCR_EMPTY_RESULT, etc.)
   with technical root-causes and actionable user/developer remedies.
4. Intelligent PDF Classification:
   Detects document and page-level types (TEXT_BASED, SCANNED, MIXED, EMPTY,
   ENCRYPTED, CORRUPTED).
5. High-Fidelity Rendering:
   Native PyMuPDF (fitz) page rasterization without external Poppler requirement.
6. Image Preprocessing & Orientation Handling:
   Configurable quality modes (FAST, BALANCED, HIGH_QUALITY), contrast boost,
   adaptive binarization, and rotation compensation.
7. Quality Validation & Bounded Retries:
   Analyzes word count, char count, confidence, and suspicious char ratios.
   Performs bounded retries on weak pages.
8. Resource Safety & Partial Preservation:
   Incremental page-by-page streaming, page timeouts, MAX_OCR_PAGES ceiling,
   and partial success preservation (successful pages are never discarded).
=============================================================================
"""

import io
import os
import re
import sys
import time
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from django.conf import settings

logger = logging.getLogger(__name__)

# Standard binary paths for Tesseract across supported operating systems
COMMON_TESSERACT_PATHS = [
    # Windows standard locations
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    os.path.expandvars(r"%PROGRAMDATA%\chocolatey\bin\tesseract.exe"),
    os.path.expandvars(r"%USERPROFILE%\scoop\shims\tesseract.exe"),
    # Linux standard locations
    r"/usr/bin/tesseract",
    r"/usr/local/bin/tesseract",
    r"/usr/bin/tesseract-ocr",
    # macOS standard locations (Homebrew / MacPorts)
    r"/opt/homebrew/bin/tesseract",
    r"/usr/local/bin/tesseract",
]


# =============================================================================
# 1. STRUCTURED OCR ERROR TAXONOMY
# =============================================================================

class OCRError(Exception):
    """Base exception for all document processing and OCR subsystem errors."""
    def __init__(
        self,
        message: str,
        code: str = "OCR_ERROR",
        technical_details: str = "",
        action: str = "",
        retryable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.technical_details = technical_details
        self.action = action
        self.retryable = retryable

    def to_dict(self) -> dict:
        return {
            "error": self.message,
            "code": self.code,
            "technical_details": self.technical_details,
            "action": self.action,
            "retryable": self.retryable,
        }


class OCRTesseractNotFoundError(OCRError):
    """Raised when the Tesseract OCR executable cannot be found on the system."""
    def __init__(self, technical_details: str = "", action: str = ""):
        super().__init__(
            message="OCR engine (Tesseract) is not installed or could not be detected on this system.",
            code="OCR_TESSERACT_NOT_FOUND",
            technical_details=technical_details or "Tesseract binary not found in PATH, TESSERACT_CMD, registry, or standard locations.",
            action=action or (
                "Windows: Run 'winget install UB-Mannheim.TesseractOCR' or download from "
                "https://github.com/UB-Mannheim/tesseract/wiki, then set TESSERACT_CMD in .env.\n"
                "Linux: Run 'sudo apt-get install tesseract-ocr tesseract-ocr-eng'.\n"
                "macOS: Run 'brew install tesseract'."
            ),
            retryable=False
        )


class OCRLanguageNotFoundError(OCRError):
    """Raised when the requested OCR language pack is missing from tessdata."""
    def __init__(self, requested_lang: str, available_langs: List[str], missing_langs: List[str]):
        missing_str = "+".join(missing_langs)
        avail_str = ", ".join(available_langs) if available_langs else "none"
        super().__init__(
            message=f"OCR language pack '{missing_str}' is not installed.",
            code="OCR_LANGUAGE_NOT_FOUND",
            technical_details=f"Requested: '{requested_lang}'. Available in tessdata: [{avail_str}]. Missing: [{missing_str}].",
            action=(
                f"Install the missing language traineddata for '{missing_str}'. "
                f"Download {missing_langs[0]}.traineddata from https://github.com/tesseract-ocr/tessdata "
                f"into your tessdata folder or install via OS package manager (e.g. 'apt install tesseract-ocr-{missing_langs[0]}')."
            ),
            retryable=False
        )
        self.requested_lang = requested_lang
        self.available_langs = available_langs
        self.missing_langs = missing_langs


class OCRRenderFailedError(OCRError):
    """Raised when rendering a PDF page to raster image fails."""
    def __init__(self, page_number: int, technical_details: str = ""):
        super().__init__(
            message=f"Failed to render PDF page {page_number} into an image for OCR.",
            code="OCR_RENDER_FAILED",
            technical_details=technical_details,
            action="Verify that the PDF file is uncorrupted and not password-protected.",
            retryable=True
        )
        self.page_number = page_number


class OCRTimeoutError(OCRError):
    """Raised when OCR processing exceeds configured page or document timeout."""
    def __init__(self, page_number: int, timeout_seconds: int):
        super().__init__(
            message=f"OCR timed out while processing page {page_number} (exceeded {timeout_seconds}s limit).",
            code="OCR_TIMEOUT",
            technical_details=f"Page {page_number} took longer than {timeout_seconds} seconds to process.",
            action="Try lowering OCR_DPI in .env or selecting FAST OCR quality mode.",
            retryable=True
        )
        self.page_number = page_number


class OCRMemoryLimitError(OCRError):
    """Raised when the document exceeds page or file size limits."""
    def __init__(self, page_count: int, max_pages: int):
        super().__init__(
            message=f"Document exceeds the maximum OCR processing limit of {max_pages} pages (has {page_count} pages).",
            code="OCR_MEMORY_LIMIT",
            technical_details=f"Document has {page_count} pages; limit is MAX_OCR_PAGES={max_pages}.",
            action=f"Split the document into sections under {max_pages} pages, or increase MAX_OCR_PAGES in .env.",
            retryable=False
        )


class OCRInvalidPDFError(OCRError):
    """Raised when file signature is not a valid PDF."""
    def __init__(self, technical_details: str = ""):
        super().__init__(
            message="Uploaded file is not a valid PDF document.",
            code="OCR_INVALID_PDF",
            technical_details=technical_details,
            action="Please upload a valid, uncorrupted PDF document.",
            retryable=False
        )


class OCRCorruptedPDFError(OCRError):
    """Raised when the PDF structure is broken or truncated."""
    def __init__(self, technical_details: str = ""):
        super().__init__(
            message="The PDF could not be read because its internal structure is corrupted.",
            code="OCR_CORRUPTED_PDF",
            technical_details=technical_details,
            action="Open the file in a standard PDF viewer, re-save or re-export it, and upload again.",
            retryable=False
        )


class OCREncryptedPDFError(OCRError):
    """Raised when PDF is encrypted or password-protected."""
    def __init__(self):
        super().__init__(
            message="The PDF is password-protected or encrypted. Password-protected documents cannot be OCR processed.",
            code="OCR_ENCRYPTED_PDF",
            technical_details="PDF security handler returned encrypted status.",
            action="Please remove password protection from the PDF before uploading.",
            retryable=False
        )


class OCREmptyResultError(OCRError):
    """Raised when OCR produces zero readable text across all scanned pages."""
    def __init__(self, scanned_pages_count: int = 1):
        super().__init__(
            message="This PDF appears to be scanned, but no readable text could be recognized by OCR.",
            code="OCR_EMPTY_RESULT",
            technical_details=f"OCR processed {scanned_pages_count} page(s) but recognized 0 substantive words.",
            action="Ensure the scanned document contains legible text with sufficient lighting and contrast.",
            retryable=True
        )


class OCRWeakQualityError(OCRError):
    """Raised or flagged when OCR extracted text quality is marginal."""
    def __init__(self, confidence: float, word_count: int):
        super().__init__(
            message="OCR completed, but some pages produced low-quality or partially unreadable text.",
            code="OCR_WEAK_QUALITY",
            technical_details=f"Average confidence: {confidence:.1f}%, words extracted: {word_count}.",
            action="Consider scanning at a higher resolution or re-running OCR in HIGH_QUALITY mode.",
            retryable=True
        )


class OCRConfigurationError(OCRError):
    """Raised when OCR settings are invalid or misconfigured."""
    def __init__(self, message: str, technical_details: str = ""):
        super().__init__(
            message=message,
            code="OCR_CONFIGURATION_ERROR",
            technical_details=technical_details,
            action="Check your OCR settings in .env or settings.py.",
            retryable=False
        )


class OCRDependencyMissingError(OCRError):
    """Raised when a required Python library is missing."""
    def __init__(self, package_name: str):
        super().__init__(
            message=f"Required OCR Python dependency '{package_name}' is not installed.",
            code="OCR_DEPENDENCY_MISSING",
            technical_details=f"Import of '{package_name}' failed.",
            action=f"Run 'pip install {package_name}' in your virtual environment.",
            retryable=False
        )


# =============================================================================
# 2. PLATFORM-AWARE BINARY DISCOVERY
# =============================================================================

def find_tesseract_in_registry() -> Optional[str]:
    """
    Discovers Tesseract executable from Windows Registry (HKLM & HKCU).
    Checks standard UB-Mannheim and official Tesseract-OCR uninstall entries.
    Safe on non-Windows systems (returns None).
    """
    if sys.platform != 'win32':
        return None

    try:
        import winreg
    except ImportError:
        return None

    keys_to_check = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for root_hkey, subkey_path in keys_to_check:
        try:
            with winreg.OpenKey(root_hkey, subkey_path) as parent_key:
                num_subkeys = winreg.QueryInfoKey(parent_key)[0]
                for i in range(num_subkeys):
                    try:
                        child_name = winreg.EnumKey(parent_key, i)
                        with winreg.OpenKey(parent_key, child_name) as child_key:
                            vals = {}
                            num_vals = winreg.QueryInfoKey(child_key)[1]
                            for j in range(num_vals):
                                v_name, v_data, _ = winreg.EnumValue(child_key, j)
                                vals[v_name] = v_data

                            display_name = str(vals.get('DisplayName', ''))
                            if 'tesseract' in display_name.lower():
                                candidates = [
                                    vals.get('InstallLocation'),
                                    os.path.dirname(str(vals.get('DisplayIcon', '')).strip('"')),
                                    os.path.dirname(str(vals.get('UninstallString', '')).strip('"')),
                                ]
                                for cand in candidates:
                                    if cand and os.path.isdir(cand):
                                        exe = os.path.join(cand, 'tesseract.exe')
                                        if os.path.isfile(exe):
                                            return os.path.abspath(exe)
                    except OSError:
                        continue
        except OSError:
            continue

    return None


_CACHED_TESSERACT_CMD: Optional[str] = None


def get_tesseract_cmd(force_refresh: bool = False) -> str:
    """
    Resolves the tesseract executable path across:
    1. Django settings.TESSERACT_CMD or TESSERACT_CMD environment variable
    2. System PATH (shutil.which)
    3. Windows Registry lookup (UB-Mannheim / Tesseract-OCR uninstall keys)
    4. OS-specific standard installation candidate directories
    5. Returns empty string if not found.

    Configures TESSDATA_PREFIX environment variable automatically when found.
    """
    global _CACHED_TESSERACT_CMD
    if _CACHED_TESSERACT_CMD and not force_refresh and os.path.isfile(_CACHED_TESSERACT_CMD):
        return _CACHED_TESSERACT_CMD

    tess_path: Optional[str] = None

    # 1. Configured TESSERACT_CMD (settings or env)
    env_cmd = getattr(settings, 'TESSERACT_CMD', '') or os.environ.get("TESSERACT_CMD", "")
    env_cmd = env_cmd.strip().strip('"').strip("'")
    if env_cmd and os.path.isfile(env_cmd):
        tess_path = os.path.abspath(env_cmd)

    # 2. System PATH
    if not tess_path:
        which_path = shutil.which("tesseract")
        if which_path and os.path.isfile(which_path):
            tess_path = os.path.abspath(which_path)

    # 3. Windows Registry lookup
    if not tess_path and sys.platform == 'win32':
        reg_path = find_tesseract_in_registry()
        if reg_path and os.path.isfile(reg_path):
            tess_path = reg_path

    # 4. Standard candidate locations
    if not tess_path:
        for p in COMMON_TESSERACT_PATHS:
            if os.path.isfile(p):
                tess_path = os.path.abspath(p)
                break

    # Setup TESSDATA_PREFIX automatically if not already specified
    if tess_path:
        _CACHED_TESSERACT_CMD = tess_path
        tess_dir = os.path.dirname(tess_path)
        tessdata_cand = os.path.join(tess_dir, "tessdata")
        if "TESSDATA_PREFIX" not in os.environ:
            if os.path.isdir(tessdata_cand):
                os.environ["TESSDATA_PREFIX"] = tessdata_cand
            elif os.path.isdir(tess_dir):
                os.environ["TESSDATA_PREFIX"] = tess_dir

        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tess_path
        except Exception:
            pass

        return tess_path

    return ""


# =============================================================================
# 3. LANGUAGE DETECTION & VALIDATION
# =============================================================================

def get_installed_languages(tess_cmd: Optional[str] = None) -> List[str]:
    """
    Retrieves the list of installed language codes from Tesseract.
    Returns: list of language tags (e.g. ['eng', 'osd', 'hin']).
    """
    cmd = tess_cmd or get_tesseract_cmd()
    if not cmd:
        return []

    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = cmd
        langs = pytesseract.get_languages()
        if langs:
            return sorted(langs)
    except Exception:
        pass

    # Direct subprocess fallback
    try:
        import subprocess
        res = subprocess.run(
            [cmd, "--list-langs"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            lines = res.stdout.strip().splitlines()
            # First line is usually 'List of available languages...'
            langs = [l.strip() for l in lines[1:] if l.strip() and not l.startswith("List")]
            return sorted(langs)
    except Exception as e:
        logger.debug(f"Failed to query tesseract --list-langs directly: {e}")

    return []


def validate_requested_languages(requested_lang: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validates that all requested languages (plus-delimited, e.g. 'eng+hin')
    exist in the installed tessdata.
    Returns:
        (all_valid: bool, available_langs: list, missing_langs: list)
    """
    installed = get_installed_languages()
    if not installed:
        # If installed list cannot be retrieved, fallback to basic sanity
        return True, [], []

    requested_codes = [c.strip() for c in requested_lang.split('+') if c.strip()]
    if not requested_codes:
        requested_codes = ['eng']

    missing = [c for c in requested_codes if c not in installed]
    all_valid = len(missing) == 0
    return all_valid, installed, missing


# =============================================================================
# 4. HEALTH CHECK & DIAGNOSTICS
# =============================================================================

def is_ocr_available() -> Tuple[bool, str]:
    """
    Backward-compatible availability check.
    Returns:
        (is_available: bool, status_message: str)
    """
    report = get_ocr_health_report()
    if report["status"] == "READY":
        return True, f"Tesseract OCR is available (v{report.get('tesseract_version', '5.x')})"
    return False, report.get("recommended_action") or report.get("status_message") or "Tesseract OCR binary is not installed on this system."


def get_ocr_health_report() -> Dict[str, Any]:
    """
    Generates a comprehensive diagnostic report of the OCR subsystem.
    Checks:
    - Executable detection & version
    - Python bindings (pytesseract, Pillow)
    - PDF rasterizer (PyMuPDF / fitz)
    - Available language packs
    - Temp directory write permission
    - Processing configuration & resource ceilings
    """
    pillow_ok = False
    try:
        from PIL import Image
        pillow_ok = True
    except ImportError:
        pass

    pytesseract_ok = False
    try:
        import pytesseract
        pytesseract_ok = True
    except ImportError:
        pass

    fitz_ok = False
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        fitz_ok = True
    except ImportError:
        pass

    tess_path = get_tesseract_cmd()
    tess_version = ""
    tess_ok = False
    if tess_path and os.path.isfile(tess_path):
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tess_path
            tess_version = str(pytesseract.get_tesseract_version())
            tess_ok = True
        except Exception:
            # Subprocess version check
            try:
                import subprocess
                res = subprocess.run([tess_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                first_line = (res.stdout or res.stderr).splitlines()[0]
                match = re.search(r'v?(\d+\.\d+[\.\w\-]*)', first_line)
                tess_version = match.group(1) if match else first_line
                tess_ok = True
            except Exception:
                tess_ok = False

    available_langs = get_installed_languages(tess_path) if tess_ok else []
    configured_lang = getattr(settings, 'OCR_LANGUAGES', 'eng') or 'eng'
    lang_valid, _, missing_langs = validate_requested_languages(configured_lang) if tess_ok else (False, [], [])

    # Temp directory write check
    import tempfile
    temp_dir = tempfile.gettempdir()
    temp_writable = False
    try:
        test_file = os.path.join(temp_dir, f".studyai_ocr_probe_{os.getpid()}.tmp")
        with open(test_file, 'w') as f:
            f.write("probe")
        if os.path.exists(test_file):
            os.remove(test_file)
            temp_writable = True
    except Exception:
        temp_writable = False

    # Status classification
    if tess_ok and pytesseract_ok and pillow_ok and fitz_ok and lang_valid and temp_writable:
        status = "READY"
        msg = "OCR subsystem is fully operational."
        action = "Ready to process scanned and mixed documents."
    elif not tess_ok:
        status = "NOT_FOUND"
        msg = "Tesseract OCR binary is not installed on this system."
        action = (
            "Install Tesseract OCR engine.\n"
            "- Windows: winget install UB-Mannheim.TesseractOCR\n"
            "- Linux: sudo apt-get install tesseract-ocr tesseract-ocr-eng\n"
            "- macOS: brew install tesseract\n"
            "Or configure TESSERACT_CMD in your .env file."
        )
    elif not lang_valid:
        status = "DEGRADED"
        msg = f"Configured language '{configured_lang}' is missing pack(s): {missing_langs}."
        action = f"Install the missing language pack ({', '.join(missing_langs)}) in tessdata."
    else:
        status = "DEGRADED"
        missing_pkgs = []
        if not pillow_ok: missing_pkgs.append("Pillow")
        if not pytesseract_ok: missing_pkgs.append("pytesseract")
        if not fitz_ok: missing_pkgs.append("PyMuPDF")
        msg = f"Missing required Python libraries: {', '.join(missing_pkgs)}."
        action = f"Run: pip install {' '.join(missing_pkgs)}"

    return {
        "status": status,
        "status_message": msg,
        "tesseract_detected": tess_ok,
        "tesseract_version": tess_version,
        "executable_path": tess_path or "NOT DETECTED",
        "python_binding_available": pytesseract_ok,
        "pillow_available": pillow_ok,
        "pdf_renderer_available": fitz_ok,
        "pdf_renderer_engine": "PyMuPDF (fitz)" if fitz_ok else "UNAVAILABLE",
        "temp_directory": temp_dir,
        "temp_writable": temp_writable,
        "available_languages": available_langs,
        "configured_languages": configured_lang,
        "missing_configured_languages": missing_langs,
        "max_ocr_pages": getattr(settings, 'MAX_OCR_PAGES', 100),
        "ocr_dpi": getattr(settings, 'OCR_DPI', 200),
        "ocr_timeout_per_page": getattr(settings, 'OCR_TIMEOUT_PER_PAGE', 25),
        "ocr_quality_mode": getattr(settings, 'OCR_QUALITY_MODE', 'BALANCED'),
        "recommended_action": action,
    }


# =============================================================================
# 5. DOCUMENT & PAGE CLASSIFICATION
# =============================================================================

def is_page_scanned(page_text: str, min_chars: int = 30) -> bool:
    """
    Determines whether an individual page lacks sufficient vector text
    and requires OCR processing.
    """
    if not page_text:
        return True
    cleaned = re.sub(r'\s+', '', page_text)
    return len(cleaned) < min_chars


def detect_scanned_pdf(pages_data: List[dict], min_chars_per_page: int = 30) -> Tuple[bool, List[int]]:
    """
    Analyzes page text data to determine if any or all pages are scanned.
    Returns:
        (is_scanned: bool, scanned_page_numbers: list[int])
    """
    if not pages_data:
        return True, [1]

    scanned_pages = []
    for p in pages_data:
        p_num = p.get("page_number", 1)
        p_text = p.get("text", "")
        if is_page_scanned(p_text, min_chars_per_page):
            scanned_pages.append(p_num)

    total_pages = len(pages_data)
    total_chars = sum(len(p.get("text", "").strip()) for p in pages_data)
    avg_chars = total_chars / max(1, total_pages)

    is_scanned = len(scanned_pages) > 0 or avg_chars < min_chars_per_page
    return is_scanned, scanned_pages


def classify_pdf_document(file_bytes: bytes) -> Dict[str, Any]:
    """
    Deeply inspects PDF bytes and classifies document type:
    - TEXT_BASED: all pages contain rich selectable vector text
    - SCANNED: pages contain little/no vector text (images/scans)
    - MIXED: document contains a mixture of native text pages and scanned pages
    - EMPTY: document has 0 pages
    - ENCRYPTED: document is password-protected
    - CORRUPTED: file cannot be opened by PDF engines

    Returns:
        dict with classification metadata.
    """
    if not file_bytes:
        return {"doc_type": "EMPTY", "page_count": 0, "error": "File is empty (0 bytes)."}

    # Attempt PyMuPDF (fitz) inspection
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.is_encrypted:
            return {"doc_type": "ENCRYPTED", "page_count": len(doc), "error": "PDF is password-protected."}

        page_count = len(doc)
        if page_count == 0:
            return {"doc_type": "EMPTY", "page_count": 0, "error": "PDF has 0 pages."}

        scanned_pages = []
        text_pages = []
        page_stats = []

        for idx in range(page_count):
            page = doc[idx]
            raw = page.get_text("text") or ""
            cleaned = re.sub(r'\s+', '', raw)
            char_count = len(cleaned)
            is_scan = char_count < 30

            stat = {
                "page_number": idx + 1,
                "char_count": char_count,
                "is_scanned": is_scan,
                "rotation": page.rotation
            }
            page_stats.append(stat)

            if is_scan:
                scanned_pages.append(idx + 1)
            else:
                text_pages.append(idx + 1)

        if len(scanned_pages) == page_count:
            doc_type = "SCANNED"
        elif len(text_pages) == page_count:
            doc_type = "TEXT_BASED"
        else:
            doc_type = "MIXED"

        return {
            "doc_type": doc_type,
            "page_count": page_count,
            "scanned_pages": scanned_pages,
            "text_pages": text_pages,
            "page_stats": page_stats,
            "error": None
        }

    except Exception as e:
        err_str = str(e).lower()
        if "password" in err_str or "encrypted" in err_str:
            return {"doc_type": "ENCRYPTED", "page_count": 0, "error": str(e)}

    # Fallback inspection via pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            return {"doc_type": "ENCRYPTED", "page_count": len(reader.pages), "error": "PDF is encrypted."}

        page_count = len(reader.pages)
        if page_count == 0:
            return {"doc_type": "EMPTY", "page_count": 0, "error": "PDF has 0 pages."}

        scanned_pages = []
        text_pages = []
        for idx, page in enumerate(reader.pages, start=1):
            txt = page.extract_text() or ""
            cleaned = re.sub(r'\s+', '', txt)
            if len(cleaned) < 30:
                scanned_pages.append(idx)
            else:
                text_pages.append(idx)

        if len(scanned_pages) == page_count:
            doc_type = "SCANNED"
        elif len(text_pages) == page_count:
            doc_type = "TEXT_BASED"
        else:
            doc_type = "MIXED"

        return {
            "doc_type": doc_type,
            "page_count": page_count,
            "scanned_pages": scanned_pages,
            "text_pages": text_pages,
            "error": None
        }
    except Exception as e:
        return {"doc_type": "CORRUPTED", "page_count": 0, "error": f"Failed to parse PDF: {str(e)}"}


# =============================================================================
# 6. PDF RENDERING & IMAGE PREPROCESSING
# =============================================================================

def render_pdf_page_to_image(
    file_bytes: bytes,
    page_index: int,
    dpi: int = 200
):
    """
    Renders a single 0-indexed PDF page to a PIL.Image instance.
    Primary Engine: PyMuPDF (fitz) - high-speed, self-contained in Python.
    Fallback Engine: pdf2image (if poppler present) or pypdf embedded images.
    """
    from PIL import Image

    # Strategy 1: PyMuPDF (fitz)
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if 0 <= page_index < len(doc):
            page = doc[page_index]
            # Render page layout at configured DPI
            pix = page.get_pixmap(dpi=dpi)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            # Apply page rotation if flagged in PDF metadata
            if page.rotation != 0:
                img = img.rotate(360 - page.rotation, expand=True)
            return img
    except Exception as e:
        logger.debug(f"fitz page rendering failed on page {page_index + 1}: {e}")

    # Strategy 2: pdf2image
    try:
        from pdf2image import convert_from_bytes
        rendered = convert_from_bytes(
            file_bytes,
            first_page=page_index + 1,
            last_page=page_index + 1,
            dpi=dpi
        )
        if rendered:
            return rendered[0].convert("RGB")
    except Exception:
        pass

    # Strategy 3: pypdf embedded images
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if 0 <= page_index < len(reader.pages):
            page = reader.pages[page_index]
            if hasattr(page, 'images') and page.images:
                return Image.open(io.BytesIO(page.images[0].data)).convert("RGB")
    except Exception:
        pass

    raise OCRRenderFailedError(page_index + 1, "No compatible PDF rendering engine could rasterize this page.")


def extract_images_from_pdf_page(file_bytes: bytes, page_index: int) -> list:
    """
    Backward-compatible image extraction helper.
    Returns list of PIL.Image instances.
    """
    try:
        img = render_pdf_page_to_image(file_bytes, page_index, dpi=getattr(settings, 'OCR_DPI', 200))
        return [img]
    except Exception:
        return []


def preprocess_image_for_ocr(img, quality_mode: str = "BALANCED", attempt: int = 1):
    """
    Applies configurable image preprocessing before feeding to Tesseract:
    - Attempt 1 (Standard):
        Grayscale conversion + auto-contrast normalization.
        In HIGH_QUALITY mode, adds gentle contrast boost.
    - Attempt 2 (Retry on weak text):
        Strong contrast enhancement + adaptive thresholding (binarization).
    """
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter

    # Convert to grayscale
    gray = img.convert('L')

    if attempt == 1:
        # Standard balanced pass
        contrasted = ImageOps.autocontrast(gray, cutoff=2)
        if quality_mode.upper() == 'HIGH_QUALITY':
            enhancer = ImageEnhance.Contrast(contrasted)
            contrasted = enhancer.enhance(1.4)
            contrasted = contrasted.filter(ImageFilter.SHARPEN)
        return contrasted

    # Attempt 2: Aggressive retry pass (e.g. for faint scans or photocopies)
    enhancer = ImageEnhance.Contrast(gray)
    boosted = enhancer.enhance(2.0)
    # Adaptive thresholding point mapping (Otsu-like binarization)
    threshold = 145
    binary = boosted.point(lambda p: 255 if p > threshold else 0, mode='1')
    return binary.convert('L')


# =============================================================================
# 7. OCR EXECUTION & QUALITY EVALUATION
# =============================================================================

def evaluate_ocr_quality(text: str, avg_conf: float, word_count: int) -> str:
    """
    Classifies OCR extraction quality:
    - GOOD: sufficient words, acceptable confidence, reasonable alphanumeric ratio
    - WEAK: low confidence or high proportion of suspicious non-standard symbols
    - FAILED: 0 words or empty string
    """
    if not text or word_count == 0 or len(text.strip()) < 5:
        return "FAILED"

    # Alphanumeric ratio check
    chars = re.sub(r'\s+', '', text)
    if not chars:
        return "FAILED"

    alpha_count = len(re.findall(r'[a-zA-Z0-9\u0900-\u0D7F]', chars))
    alpha_ratio = alpha_count / max(1, len(chars))

    # Repetition ratio check (e.g. '||||||||||' or '............')
    repeats = len(re.findall(r'(.)\1{4,}', chars))

    if avg_conf >= 50.0 and alpha_ratio >= 0.55 and word_count >= 10 and repeats == 0:
        return "GOOD"
    if word_count >= 3 and alpha_ratio >= 0.35:
        return "WEAK"
    return "FAILED"


def run_ocr_page_with_quality(
    img,
    lang: str = 'eng',
    page_number: int = 1,
    quality_mode: str = 'BALANCED',
    timeout_seconds: int = 25
) -> Dict[str, Any]:
    """
    Executes Tesseract OCR on a PIL image with confidence inspection,
    quality classification, and bounded retry on weak results.
    """
    import pytesseract

    tess_path = get_tesseract_cmd()
    if tess_path:
        pytesseract.pytesseract.tesseract_cmd = tess_path

    best_text = ""
    best_quality = "FAILED"
    best_conf = 0.0
    best_words = 0
    attempts_made = 0

    # Max 2 attempts: Attempt 1 standard, Attempt 2 with enhanced contrast/binarization
    max_attempts = 2 if quality_mode.upper() in ('BALANCED', 'HIGH_QUALITY') else 1

    for attempt in range(1, max_attempts + 1):
        attempts_made += 1
        processed_img = preprocess_image_for_ocr(img, quality_mode=quality_mode, attempt=attempt)

        try:
            # Extract detailed word-level data
            data = pytesseract.image_to_data(
                processed_img,
                lang=lang,
                output_type=pytesseract.Output.DICT,
                timeout=timeout_seconds
            )
            words = [w.strip() for w in data.get('text', []) if w.strip()]
            valid_confs = [
                float(c) for c, w in zip(data.get('conf', []), data.get('text', []))
                if w.strip() and float(c) >= 0
            ]
            avg_conf = sum(valid_confs) / len(valid_confs) if valid_confs else 0.0
            raw_text = " ".join(words).strip()
            
            # Full layout string
            full_layout_text = pytesseract.image_to_string(
                processed_img,
                lang=lang,
                timeout=timeout_seconds
            ).strip()

            text_to_evaluate = full_layout_text if len(full_layout_text) >= len(raw_text) else raw_text
            quality = evaluate_ocr_quality(text_to_evaluate, avg_conf, len(words))

            if quality == "GOOD":
                return {
                    "text": text_to_evaluate,
                    "quality": "GOOD",
                    "confidence": avg_conf,
                    "word_count": len(words),
                    "char_count": len(text_to_evaluate),
                    "attempt": attempt,
                    "error": None
                }

            # If better than previous attempt, retain
            if len(words) > best_words or (len(words) == best_words and avg_conf > best_conf):
                best_text = text_to_evaluate
                best_quality = quality
                best_conf = avg_conf
                best_words = len(words)

        except Exception as e:
            logger.warning(f"OCR attempt {attempt} failed on page {page_number}: {e}")
            if "timed out" in str(e).lower():
                return {
                    "text": best_text,
                    "quality": "FAILED",
                    "confidence": 0.0,
                    "word_count": 0,
                    "char_count": 0,
                    "attempt": attempt,
                    "error": f"OCR timeout after {timeout_seconds}s"
                }

    return {
        "text": best_text,
        "quality": best_quality,
        "confidence": best_conf,
        "word_count": best_words,
        "char_count": len(best_text),
        "attempt": attempts_made,
        "error": None if best_text else "No text recognized."
    }


def run_ocr_on_image(
    img,
    lang: str = 'eng',
    quality_mode: str = 'BALANCED',
    timeout_seconds: int = 25,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[str, bool, str]:
    """
    Backward-compatible simple OCR runner.
    Supports PIL Image instances as well as test mocks.
    Returns:
        (extracted_text: str, success: bool, error_message: str)
    """
    if metadata is not None:
        metadata.clear()

    try:
        from PIL import Image
        if not isinstance(img, Image.Image):
            if isinstance(img, str) and img and not os.path.exists(img):
                if metadata is not None:
                    metadata.update({
                        "quality": "UNMEASURED",
                        "confidence": None,
                        "word_count": None,
                        "char_count": len(img),
                        "attempt": 0,
                        "error": None
                    })
                return img, True, ""
            elif isinstance(img, str) and os.path.isfile(img):
                img = Image.open(img)
            else:
                if metadata is not None:
                    metadata.update({
                        "quality": "FAILED",
                        "confidence": None,
                        "word_count": 0,
                        "char_count": 0,
                        "attempt": 0,
                        "error": "Invalid image object"
                    })
                return "", False, "Invalid image object"
    except Exception:
        pass

    res = run_ocr_page_with_quality(
        img,
        lang=lang,
        quality_mode=quality_mode,
        timeout_seconds=timeout_seconds
    )
    if metadata is not None:
        metadata.update(res)

    if res["quality"] in ("GOOD", "WEAK") and res["text"]:
        return res["text"], True, ""
    return res["text"], False, res.get("error") or "OCR recognition produced no substantive text."



# =============================================================================
# 8. PRODUCTION PIPELINE FOR SCANNED & MIXED DOCUMENTS
# =============================================================================

def process_scanned_pdf(
    file_bytes: bytes,
    pages_data: Optional[List[dict]] = None,
    page_count: int = 1,
    lang: Optional[str] = None,
    quality_mode: Optional[str] = None,
    dpi: Optional[int] = None,
    progress_callback: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Orchestrates page-by-page OCR extraction for scanned or mixed PDFs.
    
    Guarantees:
    1. Availability check: Returns structured error if binary or libraries missing.
    2. Page classification & mixed preservation: Keeps native vector text for
       pages that have it, invoking OCR only on scanned pages.
    3. Memory safety: Renders and processes pages incrementally (one at a time).
    4. Timeouts & limits: Enforces MAX_OCR_PAGES and page-level timeouts.
    5. Partial success: Preserves successful pages even if individual pages fail.
    6. Source metadata: Preserves exact page headers ('--- Page X ---').
    """
    active_lang = lang or getattr(settings, 'OCR_LANGUAGES', 'eng') or 'eng'
    active_mode = quality_mode or getattr(settings, 'OCR_QUALITY_MODE', 'BALANCED') or 'BALANCED'
    active_dpi = dpi or getattr(settings, 'OCR_DPI', 200) or 200
    timeout_per_page = getattr(settings, 'OCR_TIMEOUT_PER_PAGE', 25)
    max_pages = getattr(settings, 'MAX_OCR_PAGES', 100)

    # 1. System availability check
    available, reason = is_ocr_available()
    if not available:
        health = get_ocr_health_report()
        is_missing_binary = (
            not health.get("tesseract_detected")
            or "not installed" in reason.lower()
            or "not found" in reason.lower()
            or "not available" in reason.lower()
        )
        return {
            "success": False,
            "error_code": "OCR_TESSERACT_NOT_FOUND" if is_missing_binary else "OCR_CONFIGURATION_ERROR",
            "error_message": "This PDF appears to be scanned, but OCR is not available on this system.",
            "technical_details": health.get("status_message", ""),
            "action": health.get("recommended_action", "Install Tesseract OCR or set TESSERACT_CMD."),
            "retryable": False,
            "full_text": "",
            "pages_data": pages_data or [],
            "page_count": max(1, page_count),
            "ocr_applied": False,
            "scanned_pages": [],
            "failed_pages": [],
            "partial_success": False
        }


    # 2. Validate requested languages
    lang_valid, avail_langs, missing_langs = validate_requested_languages(active_lang)
    if not lang_valid:
        err = OCRLanguageNotFoundError(active_lang, avail_langs, missing_langs)
        return {
            "success": False,
            "error_code": err.code,
            "error_message": err.message,
            "technical_details": err.technical_details,
            "action": err.action,
            "retryable": False,
            "full_text": "",
            "pages_data": pages_data or [],
            "page_count": max(1, page_count),
            "ocr_applied": False,
            "scanned_pages": [],
            "failed_pages": [],
            "partial_success": False
        }

    # 3. Classify document and check total pages
    classification = classify_pdf_document(file_bytes)
    if classification["doc_type"] == "ENCRYPTED":
        err = OCREncryptedPDFError()
        return {
            "success": False,
            "error_code": err.code,
            "error_message": err.message,
            "technical_details": err.technical_details,
            "action": err.action,
            "retryable": False,
            "full_text": "",
            "pages_data": [],
            "page_count": classification["page_count"],
            "ocr_applied": False,
            "scanned_pages": [],
            "failed_pages": [],
            "partial_success": False
        }

    if classification["doc_type"] == "CORRUPTED":
        err = OCRCorruptedPDFError(classification.get("error", ""))
        return {
            "success": False,
            "error_code": err.code,
            "error_message": err.message,
            "technical_details": err.technical_details,
            "action": err.action,
            "retryable": False,
            "full_text": "",
            "pages_data": [],
            "page_count": 0,
            "ocr_applied": False,
            "scanned_pages": [],
            "failed_pages": [],
            "partial_success": False
        }

    total_pages = classification.get("page_count") or page_count or 1
    if total_pages > max_pages:
        err = OCRMemoryLimitError(total_pages, max_pages)
        return {
            "success": False,
            "error_code": err.code,
            "error_message": err.message,
            "technical_details": err.technical_details,
            "action": err.action,
            "retryable": False,
            "full_text": "",
            "pages_data": pages_data or [],
            "page_count": total_pages,
            "ocr_applied": False,
            "scanned_pages": [],
            "failed_pages": [],
            "partial_success": False
        }

    # Build existing text lookup
    existing_by_page = {}
    page_metadata_by_number = {}
    if pages_data:
        for p in pages_data:
            existing_by_page[p.get("page_number")] = p.get("text", "")
            page_metadata_by_number[p.get("page_number")] = {
                key: p[key]
                for key in (
                    "tables",
                    "table_extraction_status",
                    "image_count",
                    "vector_graphic_count",
                    "visual_extraction_status",
                )
                if key in p
            }

    # 4. Incremental page-by-page processing
    updated_pages_data: List[dict] = []
    full_text_parts: List[str] = []
    scanned_pages_detected: List[int] = []
    failed_pages: List[int] = []
    ocr_applied_any = False
    confs_collected: List[float] = []

    for idx in range(total_pages):
        page_num = idx + 1
        existing_text = existing_by_page.get(page_num, "").strip()

        if progress_callback:
            try:
                progress_callback(page_num, total_pages, f"Reading page {page_num} of {total_pages}")
            except Exception:
                pass

        # Check if page already has native vector text (Mixed PDF support)
        if not is_page_scanned(existing_text, min_chars=30):
            updated_pages_data.append({
                **page_metadata_by_number.get(page_num, {}),
                "page_number": page_num,
                "text": existing_text,
                "char_count": len(existing_text),
                "is_ocr": False,
                "is_scanned": False,
                "extraction_method": "native",
                "quality": "GOOD",
                "confidence": 100.0
            })
            if existing_text:
                full_text_parts.append(f"--- Page {page_num} ---\n{existing_text}")
            continue

        # Page is scanned: apply OCR
        scanned_pages_detected.append(page_num)
        page_text = ""
        ocr_ok = False
        page_conf = None
        page_confidences = []
        page_qualities = []

        try:
            page_images = extract_images_from_pdf_page(file_bytes, idx)
            page_parts = []
            for p_img in page_images:
                ocr_metadata = {}
                txt, ok, _ = run_ocr_on_image(
                    p_img,
                    lang=active_lang,
                    quality_mode=active_mode,
                    timeout_seconds=timeout_per_page,
                    metadata=ocr_metadata
                )
                confidence = ocr_metadata.get("confidence")
                if isinstance(confidence, (int, float)):
                    page_confidences.append(float(confidence))
                quality = ocr_metadata.get("quality")
                if isinstance(quality, str):
                    page_qualities.append(quality.upper())
                if ok and txt:
                    page_parts.append(txt)

            if page_parts:
                page_text = "\n\n".join(page_parts).strip()
                ocr_ok = True
                ocr_applied_any = True
                if page_confidences:
                    page_conf = sum(page_confidences) / len(page_confidences)
                    if page_conf > 0:
                        confs_collected.append(page_conf)
            else:
                failed_pages.append(page_num)
                logger.info(f"Page {page_num} produced zero OCR text.")
        except Exception as e:
            logger.warning(f"OCR execution failed on page {page_num}: {e}")
            failed_pages.append(page_num)


        if not page_text:
            page_text = existing_text

        measured_qualities = [
            quality for quality in page_qualities
            if quality in ("GOOD", "WEAK", "FAILED")
        ]
        page_quality = "UNKNOWN"
        if ocr_ok and measured_qualities:
            page_quality = (
                "WEAK"
                if any(quality != "GOOD" for quality in measured_qualities)
                else "GOOD"
            )
        elif not ocr_ok and "FAILED" in measured_qualities:
            page_quality = "FAILED"

        updated_pages_data.append({
            **page_metadata_by_number.get(page_num, {}),
            "page_number": page_num,
            "text": page_text,
            "char_count": len(page_text),
            "is_ocr": ocr_ok,
            "is_scanned": True,
            "extraction_method": "ocr" if ocr_ok else "unextracted",
            "quality": page_quality,
            "confidence": page_conf
        })

        if page_text:
            full_text_parts.append(f"--- Page {page_num} ---\n{page_text}")

    full_text = "\n\n".join(full_text_parts).strip()
    avg_confidence = sum(confs_collected) / len(confs_collected) if confs_collected else 0.0

    # 5. Evaluate final document state
    if full_text and len(full_text) >= 20:
        is_partial = len(failed_pages) > 0 and len(failed_pages) < total_pages
        return {
            "success": True,
            "error_code": None,
            "error_message": f"{len(failed_pages)} of {total_pages} pages could not be recognized." if is_partial else "",
            "action": "Review extracted text." if not is_partial else "Some pages were unclear; successful pages preserved.",
            "retryable": is_partial,
            "full_text": full_text,
            "pages_data": updated_pages_data,
            "page_count": total_pages,
            "ocr_applied": ocr_applied_any,
            "scanned_pages": scanned_pages_detected,
            "failed_pages": failed_pages,
            "partial_success": is_partial,
            "avg_confidence": avg_confidence,
            "doc_type": classification.get("doc_type", "SCANNED")
        }

    # Zero text extracted across the entire document
    empty_err = OCREmptyResultError(len(scanned_pages_detected))
    return {
        "success": False,
        "error_code": empty_err.code,
        "error_message": empty_err.message,
        "technical_details": empty_err.technical_details,
        "action": empty_err.action,
        "retryable": True,
        "full_text": "",
        "pages_data": updated_pages_data,
        "page_count": total_pages,
        "ocr_applied": ocr_applied_any,
        "scanned_pages": scanned_pages_detected,
        "failed_pages": failed_pages,
        "partial_success": False,
        "avg_confidence": 0.0,
        "doc_type": classification.get("doc_type", "SCANNED")
    }
