"""
=============================================================================
StudyAI — Document Processing, Extraction & Semantic Chunking Engine
=============================================================================
Supports:
- PDF (via pypdf with page-level boundary preservation)
- DOCX (native pure-Python zipfile + XML parser)
- TXT / MD / Raw pasted text
- Scanned PDF detection
- Unicode & Multilingual detection (Hindi, Kannada, Tamil, Telugu, European, etc.)
- Sliding-window semantic chunking with page attribution
=============================================================================
"""

import os
import re
import io
import logging
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
from pathlib import Path
from django.conf import settings
from .models import Document, Chunk

# Allowed upload extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'txt', 'md', 'png', 'jpg', 'jpeg', 'webp'}
MAX_UPLOAD_SIZE_BYTES = getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', 25 * 1024 * 1024)
logger = logging.getLogger(__name__)


@dataclass
class NormalizedDocumentUnit:
    """
    Standardized internal document representation unit per page/slide.
    Tracks exact page boundaries, text, headings, formulas, and extraction status.
    """
    document_id: Optional[int]
    page_number: int
    text: str
    char_count: int
    headings: list[str] = field(default_factory=list)
    equations: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    source_location: str = ""
    is_ocr: bool = False
    ocr_confidence: float = 1.0
    extraction_status: str = "SUCCESS"  # SUCCESS, EMPTY, OCR_RECOVERED, FAILED


@dataclass
class CommonDocumentRepresentation:
    """
    Formal Common Document Representation (CDR) schema.
    Unifies all extraction formats (PDF, DOCX, PPTX, Image, TXT) into a consistent,
    grounded internal knowledge representation.
    """
    document_id: Optional[int]
    title: str
    genre: str
    page_count: int
    units: list[NormalizedDocumentUnit] = field(default_factory=list)
    total_characters: int = 0
    total_words: int = 0
    total_tables: int = 0
    total_equations: int = 0
    total_visuals: int = 0
    is_scanned: bool = False
    ocr_applied: bool = False

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "genre": self.genre,
            "page_count": self.page_count,
            "total_characters": self.total_characters,
            "total_words": self.total_words,
            "total_tables": self.total_tables,
            "total_equations": self.total_equations,
            "total_visuals": self.total_visuals,
            "is_scanned": self.is_scanned,
            "ocr_applied": self.ocr_applied,
            "pages": [
                {
                    "page_number": u.page_number,
                    "char_count": u.char_count,
                    "headings": u.headings,
                    "equations": u.equations,
                    "tables": u.tables,
                    "is_ocr": u.is_ocr,
                    "ocr_confidence": u.ocr_confidence,
                    "extraction_status": u.extraction_status,
                    "text": u.text
                }
                for u in self.units
            ]
        }


def create_common_document_representation(
    document_id: Optional[int],
    title: str,
    genre: str,
    pages_data: list[dict],
    is_scanned: bool = False,
    ocr_applied: bool = False
) -> CommonDocumentRepresentation:
    """
    Constructs a formalized Common Document Representation (CDR) instance
    from page-level extraction records and metadata.
    """
    units = []
    tot_chars = 0
    tot_words = 0
    tot_tables = 0
    tot_eqs = 0
    tot_visuals = 0

    for p in pages_data or []:
        p_num = p.get("page_number", 1)
        p_text = p.get("text", "")
        p_tables = p.get("tables", [])
        p_eqs = p.get("equations", [])
        p_headings = p.get("headings", [])
        char_c = len(p_text)
        word_c = len(p_text.split())
        tot_chars += char_c
        tot_words += word_c
        tot_tables += len(p_tables)
        tot_eqs += len(p_eqs)
        if p.get("image_count") or p.get("vector_graphic_count"):
            tot_visuals += (p.get("image_count") or 0) + (p.get("vector_graphic_count") or 0)

        unit = NormalizedDocumentUnit(
            document_id=document_id,
            page_number=p_num,
            text=p_text,
            char_count=char_c,
            headings=p_headings,
            equations=p_eqs,
            tables=p_tables,
            source_location=f"Page {p_num}",
            is_ocr=p.get("is_ocr", False),
            ocr_confidence=p.get("ocr_confidence", 1.0),
            extraction_status=p.get("extraction_status", "SUCCESS")
        )
        units.append(unit)

    return CommonDocumentRepresentation(
        document_id=document_id,
        title=title,
        genre=genre,
        page_count=max(1, len(units)),
        units=units,
        total_characters=tot_chars,
        total_words=tot_words,
        total_tables=tot_tables,
        total_equations=tot_eqs,
        total_visuals=tot_visuals,
        is_scanned=is_scanned,
        ocr_applied=ocr_applied
    )


def validate_file_content_signature(file_bytes: bytes, declared_ext: str) -> tuple[bool, str]:
    """
    Validates file content against declared extension using magic byte header inspection:
    - PDF: starts with '%PDF-'
    - DOCX: valid ZIP container starting with 'PK\\x03\\x04' containing '[Content_Types].xml'
    - PPTX: valid ZIP container starting with 'PK\\x03\\x04' containing 'ppt/presentation.xml'
    - TXT / MD: valid UTF-8/ASCII without embedded null bytes or binary control characters
    """
    if not file_bytes:
        return False, "Uploaded file is empty (0 bytes)."

    ext = declared_ext.lower().strip('.')

    if ext == 'pdf':
        if not file_bytes.startswith(b'%PDF-'):
            return False, "Invalid PDF header signature. File does not appear to be a genuine PDF."
        return True, ""

    elif ext == 'docx':
        if not file_bytes.startswith(b'PK\x03\x04'):
            return False, "Invalid DOCX package signature. File does not appear to be a genuine Microsoft Word document."
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as zf:
                names = zf.namelist()
                if '[Content_Types].xml' not in names and 'word/document.xml' not in names:
                    return False, "Corrupt or malformed DOCX package: missing required OpenXML descriptors."
                # Zip bomb / decompression ratio defense
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                if total_uncompressed > 100 * 1024 * 1024:
                    return False, "Decompression limit exceeded: potential decompression bomb detected."
        except Exception as e:
            return False, f"Malformed Word document: {str(e)}"
        return True, ""

    elif ext == 'pptx':
        if not file_bytes.startswith(b'PK\x03\x04'):
            return False, "Invalid PPTX package signature. File does not appear to be a genuine PowerPoint presentation."
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as zf:
                names = zf.namelist()
                if '[Content_Types].xml' not in names and not any(n.startswith('ppt/') for n in names):
                    return False, "Corrupt or malformed PPTX package: missing required presentation descriptors."
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                if total_uncompressed > 100 * 1024 * 1024:
                    return False, "Decompression limit exceeded: potential decompression bomb detected."
        except Exception as e:
            return False, f"Malformed PowerPoint presentation: {str(e)}"
        return True, ""

    elif ext in ('txt', 'md'):
        if b'\x00' in file_bytes[:8192]:
            return False, "Binary data or null bytes detected in text file."
        try:
            file_bytes[:102400].decode('utf-8')
        except UnicodeDecodeError:
            try:
                file_bytes[:102400].decode('latin-1')
            except Exception:
                return False, "Text document contains undecodable or unsupported character encoding."
        return True, ""

    elif ext in ('png', 'jpg', 'jpeg', 'webp'):
        if ext == 'png' and not file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return False, "Invalid PNG image signature."
        elif ext in ('jpg', 'jpeg') and not file_bytes.startswith(b'\xff\xd8\xff'):
            return False, "Invalid JPEG image signature."
        elif ext == 'webp' and not (file_bytes.startswith(b'RIFF') and file_bytes[8:12] == b'WEBP'):
            return False, "Invalid WebP image signature."
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
            img.verify()
        except Exception as e:
            return False, f"Malformed or corrupted image file: {str(e)}"
        return True, ""

    return False, f"Unsupported file extension '.{ext}'."


def sanitize_filename(filename: str) -> str:
    """Removes path traversal symbols and unsafe characters."""
    filename = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    clean = clean.lstrip('. ')
    if not clean or clean in ('.', '..'):
        import uuid
        return f"document_{uuid.uuid4().hex[:8]}.txt"
    return clean


def detect_language(text: str) -> str:
    """
    Detects document language using Unicode script inspection and character frequency.
    Supports Indian vernaculars, European languages, and default English.
    """
    if not text:
        return 'en'

    sample = text[:15000]

    devanagari_count = len(re.findall(r'[\u0900-\u097F]', sample))
    kannada_count = len(re.findall(r'[\u0C80-\u0CFF]', sample))
    tamil_count = len(re.findall(r'[\u0B80-\u0BFF]', sample))
    telugu_count = len(re.findall(r'[\u0C00-\u0C7F]', sample))

    counts = [
        ('hi', devanagari_count),
        ('kn', kannada_count),
        ('ta', tamil_count),
        ('te', telugu_count),
    ]
    counts.sort(key=lambda x: x[1], reverse=True)

    if counts[0][1] >= 10:
        return counts[0][0]

    # European language frequency scoring with English priority safeguards
    lower_sample = ' ' + sample.lower() + ' '
    en_stopwords = [' the ', ' and ', ' is ', ' of ', ' to ', ' in ', ' that ', ' with ', ' for ', ' as ', ' by ', ' on ', ' are ', ' this ']
    en_score = sum(1 for w in en_stopwords if w in lower_sample)

    euro_scores = {
        'de': sum(1 for w in [' und ', ' der ', ' die ', ' das ', ' nicht ', ' ist ', ' von '] if w in lower_sample),
        'es': sum(1 for w in [' y ', ' el ', ' del ', ' para ', ' en ', ' los ', ' las ', ' es ', ' con '] if w in lower_sample),
        'fr': sum(1 for w in [' et ', ' du ', ' des ', ' pour ', ' dans ', ' les ', ' est ', ' avec ', ' une '] if w in lower_sample),
    }
    best_euro = max(euro_scores.items(), key=lambda x: x[1])
    if best_euro[1] >= 2 and best_euro[1] > en_score:
        return best_euro[0]

    return 'en'



def destack_vertical_text(text: str) -> str:
    """
    Repairs vertical character stacking produced by narrow margins, vertical text, or OCR artifacts
    (e.g., 'T\\nh\\ne\\n \\nr\\ne\\nv\\ne\\nr\\ns\\na\\nl' -> 'The reversal').
    Detects sequences of >= 3 lines that are 1 character (or empty) and merges them horizontally.
    Also strips duplicate scanning headers and repeated phrases.
    """
    if not text:
        return ""
    lines = text.split('\n')
    out_lines = []
    i = 0
    n = len(lines)
    while i < n:
        curr = lines[i].strip()
        if len(curr) == 1:
            run_items = []
            j = i
            while j < n:
                item = lines[j].strip()
                if len(item) == 1:
                    run_items.append(item)
                    j += 1
                elif item == "":
                    if j + 1 < n and len(lines[j + 1].strip()) == 1:
                        run_items.append(" ")
                        j += 1
                    else:
                        break
                else:
                    break

            real_chars = [c for c in run_items if c != " "]
            if len(real_chars) >= 3:
                stitched = "".join(run_items).strip()
                stitched = re.sub(r'[ \t]+', ' ', stitched)
                out_lines.append(stitched)
                i = j
                continue
        out_lines.append(lines[i])
        i += 1

    # Remove consecutive duplicate lines created by overlapping page scans
    deduped_lines = []
    for line in out_lines:
        line_clean = line.strip()
        if line_clean and deduped_lines and deduped_lines[-1].strip() == line_clean:
            continue
        deduped_lines.append(line)

    return '\n'.join(deduped_lines)


def normalize_academic_math_and_ocr(text: str) -> str:
    """
    Normalizes common OCR and mathematical distortions in academic materials:
    - Repairs broken subscript and sequence representations: 'a;a2--+d@' -> 'a_1 a_2 \\dots a_n'
    - Repairs formula variable asterisks: '*h*(*a*)=01*andh*(*b*)=10' -> 'h(a) = 01 and h(b) = 10'
    - Normalizes mathematical operators: arrows, superscripts, Greek symbols, unions, intersections
    - Replaces OCR corrupted replacement characters with appropriate mathematical symbols
    - Faithfully preserves automata notation, regular expressions, and complexity expressions
    """
    if not text:
        return ""

    # Repair OCR asterisk variable wraps like *h*(*a*)=01*andh*(*b*)=10
    text = re.sub(r'\*([a-zA-Z])\*\(\*([a-zA-Z0-9])\*\)', r'\1(\2)', text)
    text = re.sub(r'\*and([a-zA-Z])\*', r' and \1', text)
    text = re.sub(r'\*([a-zA-Z])\*', r'\1', text)
    text = re.sub(r'([0-9a-zA-Z])\*and\s*([a-zA-Z])', r'\1 and \2', text)
    text = re.sub(r'and([a-zA-Z])\(', r'and \1(', text)

    # Scanned textbook reversal & Kleene star corruptions
    text = re.sub(r'w\s*=\s*a[1j;]a2[−\-\+]+d?n\b', r'w = a_1 a_2 \\dots a_n', text)
    text = re.sub(r'a[1j;]a2[−\-\+]+d?[@n]', r'a_1 a_2 \\dots a_n', text)
    text = re.sub(r'Andn-1\s*[−\-\+]+a[,.]?', r'a_n a_{n-1} \\dots a_1', text)
    text = re.sub(r'w\^R\s*=\s*a_?n\s*a_?\{?n-1\}?[−\-\+]+a_?1', r'w^R = a_n a_{n-1} \\dots a_1', text)
    text = re.sub(r'aja2[−\-\+]+[a-z0-9]+', r'a_1 a_2 \\dots a_n', text)
    text = re.sub(r'aja2', r'a_1 a_2', text)
    text = re.sub(r'--\+d@', r'\\dots a_n', text)
    text = re.sub(r'---\s*a,\.?', r'\\dots a_1', text)
    text = re.sub(r'\bet\s*=\s*6\b', r'\\epsilon^R = \\epsilon', text)
    text = re.sub(r'\b0010"\s*is\s*0100\b', r'0010^R \\text{ is } 0100', text)

    # Fix Kleene star expansion corruption: L* = Lu L' UL? -> L^* = L^0 \cup L^1 \cup L^2 \dots = \bigcup_{i \ge 0} L^i
    text = re.sub(r'L\*\s*=\s*L[u°\ufffd\?]?\s*u\s*L\'\s*U\s*L\?', r'L^* = L^0 \\cup L^1 \\cup L^2 \\dots = \\bigcup_{i \\ge 0} L^i', text)
    text = re.sub(r'L\*\s*=\s*L[u°\ufffd\?]?\s*u\s*L\'\s*UL\?', r'L^* = L^0 \\cup L^1 \\cup L^2 \\dots = \\bigcup_{i \\ge 0} L^i', text)

    # Regular expressions building identities (Theorem 3.4 / inductive definition)
    text = re.sub(r'L\([BE]\+[FE]\)\s*=\s*L\([BE]\)\s*[U∪]\s*L\([FE]\)', r'L(E + F) = L(E) \\cup L(F)', text)
    text = re.sub(r'L\([BE][FE]\)\s*=\s*L\([BE]\)\s*[\.·]?\s*L\([FE]\)', r'L(EF) = L(E)L(F)', text)
    text = re.sub(r'L\([BE]\*\)\s*=\s*\(L\([BE]\)\)[*\ufffd\']?', r'L(E^*) = (L(E))^*', text)
    text = re.sub(r'L\(\([BE]\)\)\s*=\s*L\([BE\ufffd]?\)', r'L((E)) = L(E)', text)
    text = re.sub(r'L\(e\+1\)\s*=\s*L\(e\)\s*UL\(1\)\s*=\s*\{e\}\s*U\s*\{1\}\s*=\s*\{a1\}', r'L(\\epsilon + 1) = L(\\epsilon) \\cup L(1) = {\\epsilon} \\cup {1} = {\\epsilon, 1}', text)

    # State Elimination path formula: Rp = REP + RD (RYD)* RS
    text = re.sub(r'Rp\s*=\s*REP\s*\+\s*RD\s*\(RYD\)\*\s*RS', r'R_{ij}^{(k)} = R_{ij}^{(k-1)} + R_{ik}^{(k-1)} (R_{kk}^{(k-1)})^* R_{kj}^{(k-1)}', text)

    # Homomorphisms
    text = re.sub(r'h\(a[1j]\)h\(a2\)[−\-]+h\(an\)', r'h(a_1)h(a_2) \\dots h(a_n)', text)
    text = re.sub(r'h\(a1\)\s*h\(a2\)[−\-]+h\(an\)', r'h(a_1)h(a_2) \\dots h(a_n)', text)
    text = re.sub(r'h\(w\)\s*=\s*h\(a1\)\s*h\(a2\)[−\-]+h\(an\)', r'h(w) = h(a_1)h(a_2) \\dots h(a_n)', text)

    # Reversal context fixes
    text = re.sub(r'\bWe use w\*\s+for the reversal of string w\b', 'We use w^R for the reversal of string w', text, flags=re.I)
    text = re.sub(r'\bThe reversal of a language L,\s*written\s+L\*', 'The reversal of a language L, written L^R', text, flags=re.I)
    text = re.sub(r'\bL\?\s*=\s*\{100', 'L^R = {100', text)

    # Union with 'U' between sets
    text = re.sub(r'(\bL\([A-Za-z0-9\+\*\s]+\))\s+U\s+(\bL\([A-Za-z0-9\+\*\s]+\))', r'\1 \\cup \2', text)
    text = re.sub(r'(\{[^\{\}]+\})\s+U\s+(\{[^\{\}]+\})', r'\1 \\cup \2', text)

    # Common OCR hyphenation and math symbol normalizations
    text = text.replace('->', '→').replace('<->', '↔').replace('<=', '≤').replace('>=', '≥')
    text = text.replace('∪', r'\cup').replace('∩', r'\cap').replace('⊆', r'\subseteq')
    text = text.replace('∈', r'\in').replace('∉', r'\notin').replace('∅', r'\emptyset')
    text = text.replace('ε', r'\epsilon')

    return text


def clean_text(raw_text: str) -> str:
    """Normalizes whitespace, fixes vertical character stacking, and removes control characters."""
    if not raw_text:
        return ""
    text = re.sub(r'\r\n|\r', '\n', raw_text)
    text = destack_vertical_text(text)
    text = normalize_academic_math_and_ocr(text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


from .ocr_service import (
    is_ocr_available,
    detect_scanned_pdf,
    classify_pdf_document,
    process_scanned_pdf,
    OCRError,
)


class PdfExtractionResult(tuple):
    """
    4-tuple (full_text, pages_data, page_count, is_scanned) with extra OCR metadata.
    Guarantees full backward compatibility for standard tuple unpacking:
    text, pages, count, is_scanned = extract_text_from_pdf(...)
    """
    def __new__(
        cls,
        full_text,
        pages_data,
        page_count,
        is_scanned,
        ocr_applied=False,
        ocr_message="",
        ocr_error_code=None,
        ocr_action="",
        doc_type="UNKNOWN",
        partial_success=False,
        failed_pages=None,
        avg_confidence=0.0,
        reconstruction_metrics=None
    ):
        obj = super().__new__(cls, (full_text, pages_data, page_count, is_scanned))
        obj.full_text = full_text
        obj.pages_data = pages_data
        obj.page_count = page_count
        obj.is_scanned = is_scanned
        obj.ocr_applied = ocr_applied
        obj.ocr_message = ocr_message
        obj.ocr_error_code = ocr_error_code
        obj.ocr_action = ocr_action
        obj.doc_type = doc_type
        obj.partial_success = partial_success
        obj.failed_pages = failed_pages or []
        obj.avg_confidence = avg_confidence
        obj.reconstruction_metrics = reconstruction_metrics or {}
        return obj


class StudyMaterialExtractionResult(tuple):
    """
    5-tuple (full_text, pages_data, page_count, file_type, is_scanned) with extra OCR metadata.
    Guarantees full backward compatibility for standard tuple unpacking:
    raw_text, pages_data, page_count, file_type, is_scanned = extract_study_material(...)
    """
    def __new__(
        cls,
        full_text,
        pages_data,
        page_count,
        file_type,
        is_scanned,
        ocr_applied=False,
        ocr_message="",
        ocr_error_code=None,
        ocr_action="",
        doc_type="UNKNOWN",
        partial_success=False,
        failed_pages=None,
        avg_confidence=0.0,
        reconstruction_metrics=None
    ):
        obj = super().__new__(cls, (full_text, pages_data, page_count, file_type, is_scanned))
        obj.full_text = full_text
        obj.pages_data = pages_data
        obj.page_count = page_count
        obj.file_type = file_type
        obj.is_scanned = is_scanned
        obj.ocr_applied = ocr_applied
        obj.ocr_message = ocr_message
        obj.ocr_error_code = ocr_error_code
        obj.ocr_action = ocr_action
        obj.doc_type = doc_type
        obj.partial_success = partial_success
        obj.failed_pages = failed_pages or []
        obj.avg_confidence = avg_confidence
        obj.reconstruction_metrics = reconstruction_metrics or {}
        return obj


def extract_text_from_pdf(file_bytes: bytes, progress_callback: Any = None) -> PdfExtractionResult:
    """
    Extracts text and page boundaries from PDF bytes using PyMuPDF (fitz) if available,
    falling back to pypdf. Detects scanned documents and coordinates page-by-page OCR.
    Preserves exact page numbers and handles mixed (text + scanned) documents.
    Returns: PdfExtractionResult (unpacks as full_text, pages_data, page_count, is_scanned)
    """
    pages_data = []
    full_text_parts = []
    page_count = 1

    # Pre-check for encryption or corruption
    classification = classify_pdf_document(file_bytes)
    if classification.get("doc_type") == "ENCRYPTED":
        return PdfExtractionResult(
            "",
            [],
            classification.get("page_count", 0),
            False,
            ocr_applied=False,
            ocr_message="The PDF is password-protected or encrypted. Password-protected documents cannot be OCR processed.",
            ocr_error_code="OCR_ENCRYPTED_PDF",
            ocr_action="Please remove password protection from the PDF before uploading.",
            doc_type="ENCRYPTED"
        )

    # Strategy 1: Attempt PyMuPDF (fitz) for high-fidelity native text extraction
    fitz_success = False
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        for idx in range(page_count):
            p = doc[idx]
            page_text = p.get_text("text") or ""
            tables, table_status = _extract_pdf_tables(p)
            image_count, vector_graphic_count, visual_status = _inspect_pdf_visual_content(p)
            combined_text = "\n\n".join(part for part in [page_text, "\n\n".join(tables)] if part)
            cleaned_page = clean_text(combined_text)
            pages_data.append({
                "page_number": idx + 1,
                "text": cleaned_page,
                "char_count": len(cleaned_page),
                "is_ocr": False,
                "tables": tables,
                "table_extraction_status": table_status,
                "image_count": image_count,
                "vector_graphic_count": vector_graphic_count,
                "visual_extraction_status": visual_status
            })
            if cleaned_page:
                full_text_parts.append(cleaned_page)
        fitz_success = True
    except Exception:
        fitz_success = False

    # Strategy 2: Fallback to pypdf if PyMuPDF not installed or failed
    if not fitz_success:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            page_count = len(reader.pages)
            pages_data = []
            full_text_parts = []

            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ''
                cleaned_page = clean_text(page_text)
                pages_data.append({
                    "page_number": idx,
                    "text": cleaned_page,
                    "char_count": len(cleaned_page),
                    "is_ocr": False,
                    "tables": [],
                    "table_extraction_status": "UNAVAILABLE",
                    "image_count": None,
                    "vector_graphic_count": None,
                    "visual_extraction_status": "UNAVAILABLE"
                })
                if cleaned_page:
                    full_text_parts.append(cleaned_page)
        except Exception:
            # Corrupted PDF: neither fitz nor pypdf could parse the binary stream.
            return PdfExtractionResult(
                "",
                [],
                0,
                False,
                ocr_applied=False,
                ocr_message="The PDF could not be read because its internal structure is corrupted.",
                ocr_error_code="OCR_CORRUPTED_PDF",
                ocr_action="Please re-save or re-export the PDF and upload again.",
                doc_type="CORRUPTED"
            )

    # Strategy 3: Check if PDF contains scanned / image-based pages
    is_scanned, scanned_page_numbers = detect_scanned_pdf(pages_data, min_chars_per_page=30)
    scanned_page_set = set(scanned_page_numbers)
    for page in pages_data:
        if (
            page.get("page_number") in scanned_page_set
            and page.get("table_extraction_status") in {"NOT_FOUND", "UNAVAILABLE"}
        ):
            page["table_extraction_status"] = "OCR_REQUIRED"
        if (
            page.get("page_number") in scanned_page_set
            and page.get("visual_extraction_status") in {"NOT_DETECTED", "UNAVAILABLE"}
        ):
            page["visual_extraction_status"] = "OCR_REQUIRED"
    ocr_applied = False
    ocr_message = ""
    ocr_error_code = None
    ocr_action = ""
    partial_success = False
    failed_pages = []
    avg_confidence = 0.0
    doc_type = classification.get("doc_type", "SCANNED" if is_scanned else "TEXT_BASED")

    if is_scanned:
        # Delegate to page-by-page OCR engine
        try:
            ocr_result = process_scanned_pdf(file_bytes, pages_data=pages_data, page_count=page_count, progress_callback=progress_callback)
        except Exception as ocr_err:
            ocr_result = {
                "success": False,
                "error_code": "OCR_RENDER_FAILED",
                "error_message": f"OCR processing failed: {str(ocr_err)}",
                "action": "Check document readability and server logs.",
                "full_text": "",
                "pages_data": pages_data,
                "page_count": page_count,
                "ocr_applied": False,
                "scanned_pages": scanned_page_numbers,
                "failed_pages": scanned_page_numbers,
                "partial_success": False,
                "avg_confidence": 0.0
            }

        ocr_error_code = ocr_result.get("error_code")
        ocr_action = ocr_result.get("action", "")
        partial_success = ocr_result.get("partial_success", False)
        failed_pages = ocr_result.get("failed_pages", [])
        avg_confidence = ocr_result.get("avg_confidence", 0.0)

        if ocr_result.get("success"):
            # OCR succeeded on scanned pages!
            full_text = ocr_result["full_text"]
            pages_data = ocr_result["pages_data"]
            page_count = ocr_result["page_count"]
            ocr_applied = ocr_result.get("ocr_applied", False)
            is_scanned = True
            ocr_message = ocr_result.get("error_message", "")
        else:
            # OCR unavailable, blank scan, or hard failure
            is_scanned = True
            ocr_applied = False
            ocr_message = ocr_result.get("error_message", "Failed to extract text via OCR.")
            full_text = "\n\n".join(full_text_parts)
    else:
        full_text = "\n\n".join(full_text_parts)

    # Phase 4A: Intelligent Line Segmentation & Paragraph Reconstruction
    rec_metrics = {}
    try:
        from .intelligent_reconstruction import IntelligentTextReconstructor
        full_text, pages_data, rec_metrics = IntelligentTextReconstructor.reconstruct_document(pages_data)
        if ocr_applied:
            full_text = "\n\n".join(f"--- Page {p.get('page_number', i+1)} ---\n{p.get('text', '')}" for i, p in enumerate(pages_data))
    except Exception as rec_err:
        logger.warning(f"Intelligent reconstruction warning: {rec_err}")

    return PdfExtractionResult(
        full_text,
        pages_data,
        max(1, page_count),
        is_scanned,
        ocr_applied=ocr_applied,
        ocr_message=ocr_message,
        ocr_error_code=ocr_error_code,
        ocr_action=ocr_action,
        doc_type=doc_type,
        partial_success=partial_success,
        failed_pages=failed_pages,
        avg_confidence=avg_confidence,
        reconstruction_metrics=rec_metrics
    )


def _extract_pdf_tables(page: Any) -> tuple[list[str], str]:
    find_tables = getattr(page, "find_tables", None)
    if not callable(find_tables):
        return [], "UNAVAILABLE"

    try:
        table_finder = find_tables()
        tables = getattr(table_finder, "tables", None)
    except Exception as exc:
        logger.warning("PDF table detection failed: %s", exc)
        return [], "FAILED"

    if tables is None:
        logger.warning("PDF table detection returned no table collection.")
        return [], "FAILED"
    if not tables:
        return [], "NOT_FOUND"

    rendered_tables = []
    extraction_failed = False
    for table_index, table in enumerate(tables, start=1):
        try:
            rendered_table = _render_table_as_markdown(table.extract(), table_index)
        except Exception as exc:
            logger.warning("PDF table %s extraction failed: %s", table_index, exc)
            extraction_failed = True
            continue

        if not rendered_table:
            extraction_failed = True
            continue

        rendered_tables.append(rendered_table)

    if rendered_tables:
        return rendered_tables, "PARTIAL" if extraction_failed else "EXTRACTED"
    return [], "FAILED" if extraction_failed else "NOT_FOUND"


def _inspect_pdf_visual_content(page: Any) -> tuple[Optional[int], Optional[int], str]:
    get_images = getattr(page, "get_images", None)
    get_drawings = getattr(page, "get_drawings", None)
    if not callable(get_images) or not callable(get_drawings):
        return None, None, "UNAVAILABLE"

    try:
        image_count = len(get_images(full=True))
        vector_graphic_count = len(get_drawings())
    except Exception as exc:
        logger.warning("PDF visual-content detection failed: %s", exc)
        return None, None, "FAILED"

    status = (
        "DETECTED_UNINTERPRETED"
        if image_count or vector_graphic_count
        else "NOT_DETECTED"
    )
    return image_count, vector_graphic_count, status


def _render_table_as_markdown(rows: Any, table_index: int) -> str:
    normalized_rows = []
    for row in rows or []:
        cells = [
            str(cell or "").replace("\r", " ").replace("\n", " ").replace("|", "\\|").strip()
            for cell in row
        ]
        if any(cells):
            normalized_rows.append(cells)
    if not normalized_rows:
        return ""

    column_count = max(len(row) for row in normalized_rows)
    normalized_rows = [
        row + [""] * (column_count - len(row))
        for row in normalized_rows
    ]
    markdown_rows = [
        "| " + " | ".join(row) + " |"
        for row in normalized_rows
    ]
    markdown_rows.insert(1, "| " + " | ".join(["---"] * column_count) + " |")
    return f"[Table {table_index}]\n" + "\n".join(markdown_rows)



def extract_text_from_docx(file_bytes: bytes) -> tuple[str, list[dict], int]:
    """
    Extracts text from DOCX using native Python zipfile and ElementTree.
    Guarantees zero compiled dependency issues on any OS.
    """
    paragraphs = []
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx_zip:
            # Zip bomb safeguard
            total_uncompressed = sum(info.file_size for info in docx_zip.infolist())
            if total_uncompressed > 50 * 1024 * 1024:
                raise ValueError("DOCX uncompressed content exceeds 50MB security ceiling.")
            xml_content = docx_zip.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

            body = tree.find('.//w:body', namespace)
            word_namespace = f"{{{namespace['w']}}}"
            if body is None:
                raise ValueError("DOCX document body is missing.")

            table_index = 0
            def extract_block(block):
                nonlocal table_index
                if block.tag == f"{word_namespace}p":
                    texts = [node.text for node in block.iterfind('.//w:t', namespace) if node.text]
                    if texts:
                        paragraphs.append(''.join(texts))
                elif block.tag == f"{word_namespace}tbl":
                    table_index += 1
                    rows = []
                    for row in block.findall('./w:tr', namespace):
                        cells = []
                        for cell in row.findall('./w:tc', namespace):
                            cell_text = ''.join(
                                node.text
                                for node in cell.iterfind('.//w:t', namespace)
                                if node.text
                            )
                            cells.append(cell_text)
                        rows.append(cells)
                    table_markdown = _render_table_as_markdown(rows, table_index)
                    if table_markdown:
                        paragraphs.append(table_markdown)
                else:
                    for child in block:
                        extract_block(child)

            for block in body:
                extract_block(block)
    except Exception:
        paragraphs.append(file_bytes.decode('utf-8', errors='ignore'))

    full_text = clean_text('\n\n'.join(paragraphs))
    est_pages = max(1, len(full_text) // 2500)
    pages_data = [{"page_number": 1, "text": full_text, "char_count": len(full_text), "is_ocr": False}]
    return full_text, pages_data, est_pages


def extract_text_from_pptx(file_bytes: bytes) -> tuple[str, list[dict], int]:
    """
    Extracts text, slide titles, bullet points, and tables from PPTX slides.
    Preserves slide numbers as page boundaries.
    Uses python-pptx when available, with a resilient native OpenXML fallback.
    """
    paragraphs = []
    pages_data = []

    # Attempt 1: python-pptx high-level parser
    try:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(file_bytes))
        slide_count = len(prs.slides)
        for idx, slide in enumerate(prs.slides, start=1):
            slide_lines = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        p_text = para.text.strip()
                        if p_text:
                            slide_lines.append(p_text)
                elif shape.has_table:
                    for row in shape.table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                        if row_text:
                            slide_lines.append(f"| {row_text} |")
            slide_text = clean_text("\n".join(slide_lines))
            pages_data.append({
                "page_number": idx,
                "text": slide_text,
                "char_count": len(slide_text),
                "is_ocr": False
            })
            if slide_text:
                paragraphs.append(slide_text)
        return "\n\n".join(paragraphs), pages_data, max(1, slide_count)
    except Exception as pptx_err:
        logger.info(f"python-pptx extraction failed or unavailable ({pptx_err}); falling back to native OpenXML.")

    # Attempt 2: Native pure-Python OpenXML parser (zero external compiled dependencies)
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as pptx_zip:
            slide_names = [n for n in pptx_zip.namelist() if re.match(r'^ppt/slides/slide\d+\.xml$', n)]
            slide_names.sort(key=lambda s: int(re.search(r'\d+', s).group(0)))
            if slide_names:
                for idx, sname in enumerate(slide_names, start=1):
                    xml_data = pptx_zip.read(sname)
                    tree = ET.fromstring(xml_data)
                    slide_lines = []
                    for p_node in tree.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}p'):
                        t_nodes = [t.text for t in p_node.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if t.text]
                        if t_nodes:
                            line = "".join(t_nodes).strip()
                            if line:
                                slide_lines.append(line)
                    slide_text = clean_text("\n".join(slide_lines))
                    pages_data.append({
                        "page_number": idx,
                        "text": slide_text,
                        "char_count": len(slide_text),
                        "is_ocr": False
                    })
                    if slide_text:
                        paragraphs.append(slide_text)
                return "\n\n".join(paragraphs), pages_data, max(1, len(slide_names))
    except Exception as xml_err:
        logger.warning(f"Native PPTX OpenXML extraction failed: {xml_err}")

    pages_data = [{"page_number": 1, "text": "", "char_count": 0, "is_ocr": False}]
    return "", pages_data, 1


def extract_text_from_image(file_bytes: bytes, filename: str) -> StudyMaterialExtractionResult:
    """
    Extracts text from standalone images (PNG, JPG, JPEG, WEBP) using OCR.
    Handles orientation, contrast enhancement, and evaluates extraction quality.
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else 'image'
    try:
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(file_bytes))
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        if img.mode != 'RGB':
            img = img.convert('RGB')
    except Exception as e:
        logger.error(f"Failed to open image file {filename}: {e}")
        return StudyMaterialExtractionResult(
            "",
            [{"page_number": 1, "text": "", "char_count": 0, "is_ocr": True, "tables": [], "visual_extraction_status": "FAILED"}],
            1,
            ext,
            True,
            ocr_applied=False,
            ocr_message=f"Corrupt or unreadable image file: {str(e)}",
            ocr_error_code="OCR_CORRUPTED_IMAGE",
            ocr_action="Please check that the image file is a valid PNG, JPG, or WEBP file.",
            doc_type="IMAGE"
        )

    from .ocr_service import is_ocr_available, run_ocr_page_with_quality
    ocr_ok, ocr_msg = is_ocr_available()
    if not ocr_ok:
        return StudyMaterialExtractionResult(
            "",
            [{"page_number": 1, "text": "", "char_count": 0, "is_ocr": True, "tables": [], "visual_extraction_status": "OCR_REQUIRED"}],
            1,
            ext,
            True,
            ocr_applied=False,
            ocr_message="OCR engine is not available on this server.",
            ocr_error_code="OCR_TESSERACT_NOT_FOUND",
            ocr_action=ocr_msg,
            doc_type="IMAGE"
        )

    configured_lang = getattr(settings, 'OCR_LANGUAGES', 'eng') or 'eng'
    quality_mode = getattr(settings, 'OCR_QUALITY_MODE', 'BALANCED')
    timeout_sec = getattr(settings, 'OCR_TIMEOUT_PER_PAGE', 25)

    ocr_res = run_ocr_page_with_quality(
        img,
        lang=configured_lang,
        page_number=1,
        quality_mode=quality_mode,
        timeout_seconds=timeout_sec
    )
    text = clean_text(ocr_res.get("text", ""))
    conf = float(ocr_res.get("confidence", 0.0))
    success = bool(text and len(text.strip()) >= 5)

    pages_data = [{
        "page_number": 1,
        "text": text,
        "char_count": len(text),
        "is_ocr": True,
        "ocr_confidence": conf,
        "tables": [],
        "table_extraction_status": "NOT_FOUND",
        "image_count": 1,
        "vector_graphic_count": 0,
        "visual_extraction_status": "OCR_COMPLETED" if success else "OCR_EMPTY"
    }]

    return StudyMaterialExtractionResult(
        text,
        pages_data,
        1,
        ext,
        True,
        ocr_applied=True,
        ocr_message="" if success else "No legible text could be recognized from this image.",
        ocr_error_code=None if success else "OCR_EMPTY_RESULT",
        ocr_action="" if success else "Ensure the image contains clear, sharp, high-contrast text.",
        doc_type="IMAGE",
        avg_confidence=conf
    )


def extract_study_material(file_bytes: bytes, filename: str, progress_callback: Any = None) -> StudyMaterialExtractionResult:
    """
    Orchestrates extraction based on file extension.
    Returns: StudyMaterialExtractionResult (unpacks as text, pages_data, page_count, file_type, is_scanned)
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else 'txt'

    if ext == 'pdf':
        pdf_res = extract_text_from_pdf(file_bytes, progress_callback=progress_callback)
        return StudyMaterialExtractionResult(
            pdf_res[0],
            pdf_res[1],
            pdf_res[2],
            'pdf',
            pdf_res[3],
            ocr_applied=pdf_res.ocr_applied,
            ocr_message=pdf_res.ocr_message,
            ocr_error_code=pdf_res.ocr_error_code,
            ocr_action=pdf_res.ocr_action,
            doc_type=pdf_res.doc_type,
            partial_success=pdf_res.partial_success,
            failed_pages=pdf_res.failed_pages,
            avg_confidence=pdf_res.avg_confidence
        )
    elif ext == 'docx':
        text, pages_data, page_count = extract_text_from_docx(file_bytes)
        try:
            from .intelligent_reconstruction import IntelligentTextReconstructor
            text, pages_data, rec_metrics = IntelligentTextReconstructor.reconstruct_document(pages_data)
        except Exception:
            rec_metrics = {}
        return StudyMaterialExtractionResult(text, pages_data, page_count, 'docx', False, False, "", reconstruction_metrics=rec_metrics)
    elif ext == 'pptx':
        text, pages_data, page_count = extract_text_from_pptx(file_bytes)
        try:
            from .intelligent_reconstruction import IntelligentTextReconstructor
            text, pages_data, rec_metrics = IntelligentTextReconstructor.reconstruct_document(pages_data)
        except Exception:
            rec_metrics = {}
        return StudyMaterialExtractionResult(text, pages_data, page_count, 'pptx', False, False, "", reconstruction_metrics=rec_metrics)
    elif ext in ('png', 'jpg', 'jpeg', 'webp'):
        return extract_text_from_image(file_bytes, filename)
    else:
        text = clean_text(file_bytes.decode('utf-8', errors='ignore'))
        page_count = max(1, len(text) // 2500)
        pages_data = [{"page_number": 1, "text": text, "char_count": len(text), "is_ocr": False}]
        try:
            from .intelligent_reconstruction import IntelligentTextReconstructor
            text, pages_data, rec_metrics = IntelligentTextReconstructor.reconstruct_document(pages_data)
        except Exception:
            rec_metrics = {}
        return StudyMaterialExtractionResult(text, pages_data, page_count, ext if ext in ['txt', 'md'] else 'txt', False, False, "", reconstruction_metrics=rec_metrics)


def chunk_document_by_pages(pages_data, target_size: int = 1500, overlap: int = 150, document_id: int = None, language: str = 'en', **kwargs) -> list[dict]:
    """
    Chunks text while preserving source page start, page end, language, and document ID references.
    Avoids splitting formulas ($$...$$) and definitions across chunk boundaries.
    Supports either list of page dicts or raw string input.
    """
    if 'max_chunk_chars' in kwargs:
        target_size = kwargs['max_chunk_chars']
    if 'overlap_chars' in kwargs:
        overlap = kwargs['overlap_chars']
    if isinstance(pages_data, str):
        pages_data = [{"page_number": 1, "text": pages_data, "char_count": len(pages_data), "is_ocr": False}]

    chunks = []
    chunk_index = 1

    current_text = ""
    current_page_start = 1
    current_page_end = 1
    current_section = ""

    for p in pages_data:
        p_num = p["page_number"]
        p_text = p["text"]
        if not p_text.strip():
            continue

        # Split into paragraphs and standalone math equations
        blocks = re.split(r'(\$\$.*?\$\$|\n{2,})', p_text, flags=re.S)

        for blk in blocks:
            b_clean = blk.strip()
            if not b_clean:
                continue

            # Detect section heading
            if len(b_clean) < 80 and re.match(r'^(Chapter|Section|\d+\.|\b[A-Z0-9\s]{4,}\b)', b_clean):
                current_section = b_clean

            # Keep equation blocks contiguous
            is_equation = b_clean.startswith('$$') and b_clean.endswith('$$')

            if len(current_text) + len(b_clean) > target_size and len(current_text) > 0 and not is_equation:
                chunks.append({
                    "document_id": document_id,
                    "chunk_id": chunk_index,
                    "chunk_index": chunk_index,
                    "order": chunk_index,
                    "page_start": current_page_start,
                    "page_end": current_page_end,
                    "section": current_section,
                    "language": language,
                    "text": current_text.strip(),
                    "char_count": len(current_text.strip()),
                    "estimated_tokens": (len(current_text.strip()) + 3) // 4,
                    "preview": current_text.strip()[:140] + "..."
                })
                chunk_index += 1

                # Carry overlap
                words = current_text.split()
                overlap_text = " ".join(words[-max(1, overlap // 6):])
                if overlap_text.count('$$') % 2 != 0:
                    overlap_text = ""
                current_text = (overlap_text + "\n\n" + b_clean).strip() if overlap_text else b_clean
                current_page_start = p_num
                current_page_end = p_num
            else:
                if not current_text:
                    current_page_start = p_num
                current_text = (current_text + "\n\n" + b_clean) if current_text else b_clean
                current_page_end = p_num

    if current_text.strip():
        chunks.append({
            "document_id": document_id,
            "chunk_id": chunk_index,
            "chunk_index": chunk_index,
            "order": chunk_index,
            "page_start": current_page_start,
            "page_end": current_page_end,
            "section": current_section,
            "language": language,
            "text": current_text.strip(),
            "char_count": len(current_text.strip()),
            "estimated_tokens": (len(current_text.strip()) + 3) // 4,
            "preview": current_text.strip()[:140] + "..."
        })

    return chunks


def save_uploaded_file(file_bytes: bytes, filename: str) -> str:
    """Saves file to media/documents storage safely with path traversal validation."""
    media_dir = Path(settings.MEDIA_ROOT).resolve() / 'documents'
    media_dir.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(filename)
    target_path = media_dir / safe_name

    # Path traversal safeguard
    resolved_target = target_path.resolve()
    if not (resolved_target == media_dir or media_dir in resolved_target.parents):
        raise ValueError("Path traversal attempt detected in filename.")

    # Avoid name collision
    counter = 1
    base_stem = target_path.stem
    base_ext = target_path.suffix
    while target_path.exists():
        target_path = media_dir / f"{base_stem}_{counter}{base_ext}"
        counter += 1

    with open(target_path, 'wb') as f:
        f.write(file_bytes)

    return str(target_path.relative_to(settings.BASE_DIR))
