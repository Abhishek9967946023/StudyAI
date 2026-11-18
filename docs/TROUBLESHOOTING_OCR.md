# StudyAI — Optical Character Recognition (OCR) Troubleshooting Guide

This guide provides targeted diagnoses, technical root causes, and verified fixes for any issue encountered when processing scanned, image-based, or mixed PDFs in StudyAI.

---

## Quick Diagnostic Command

Whenever you experience an OCR issue or set up a new machine, always run the dedicated diagnostic command first:

```bash
# Windows (PowerShell or Command Prompt)
.\backend\venv\Scripts\python.exe backend\manage.py check_ocr

# Linux / macOS
backend/venv/bin/python backend/manage.py check_ocr

# Machine-readable JSON output
python backend/manage.py check_ocr --json
```

To view operating-system-specific installation and configuration instructions without modifying system software:

```bash
python backend/manage.py setup_ocr
```

---

## 1. "Tesseract not found" / `OCR_TESSERACT_NOT_FOUND`

### Symptoms:
- Uploading a scanned PDF fails with HTTP 400 and error code `OCR_TESSERACT_NOT_FOUND`.
- `python manage.py check_ocr` reports `Tesseract: NOT FOUND`.

### Root Cause:
The Tesseract OCR binary executable is not present in system `PATH`, nor configured in `TESSERACT_CMD`, nor discoverable in standard OS install paths or Windows Registry.

### Solutions:
#### Windows:
1. **Via Windows Package Manager (`winget`)** (Recommended):
   ```powershell
   winget install UB-Mannheim.TesseractOCR
   ```
2. **Via Installer**:
   Download the installer from [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
3. **If installed in a custom directory** (e.g. `C:\Users\Username\Desktop\tessdata\tesseract.exe` or `D:\Tools\Tesseract\tesseract.exe`):
   Set the exact executable path in your `.env` file:
   ```env
   TESSERACT_CMD=C:\Users\Username\Desktop\tessdata\tesseract.exe
   ```

#### Linux (Debian / Ubuntu):
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
```

#### macOS (Homebrew):
```bash
brew install tesseract
```

---

## 2. "pytesseract installed but Tesseract missing"

### Root Cause:
`pytesseract` is merely a Python wrapper library. It does **not** bundle the compiled Tesseract C++ executable. Both the Python library and the system binary are required:
- Python library: `pytesseract` (managed via `pip` inside `venv`)
- System executable: `tesseract` / `tesseract.exe` (managed via OS package manager or installer)

### Fix:
Follow the OS installation steps in Section 1 above to install the system binary.

---

## 3. "Language not found" / `OCR_LANGUAGE_NOT_FOUND`

### Symptoms:
- Uploading non-English documents fails with `OCR language pack 'hin' is not installed`.
- Diagnostic output shows `Available Languages: eng, osd` while requested was `eng+hin`.

### Root Cause:
Tesseract requires trained language models (`<lang>.traineddata`) in its `tessdata` directory.

### Solutions:
1. **Ubuntu / Debian**:
   ```bash
   sudo apt-get install -y tesseract-ocr-hin tesseract-ocr-kan tesseract-ocr-tam tesseract-ocr-tel
   ```
2. **Windows**:
   Download the required `.traineddata` file (e.g. `hin.traineddata`) from the official [Tesseract tessdata repository](https://github.com/tesseract-ocr/tessdata) and copy it into your Tesseract `tessdata/` directory (e.g. `C:\Program Files\Tesseract-OCR\tessdata\`).
3. **Verify installed languages**:
   ```bash
   python backend/manage.py check_ocr
   ```

---

## 4. "OCR works on one computer but not another"

### Root Cause:
One computer has Tesseract in its system `PATH` or in standard directories, while the second computer either:
1. Does not have the system executable installed.
2. Installed Tesseract in a non-standard folder without setting `PATH` or `TESSERACT_CMD`.
3. Has missing language packs.

### Fix:
1. On the new computer, run:
   ```bash
   python backend/manage.py check_ocr
   ```
2. If `Tesseract: NOT FOUND`, install via `winget` or package manager, or set `TESSERACT_CMD` in `.env`.
3. Verify that `backend/studyai_backend/settings.py` loads `.env`.

---

## 5. "OCR works from terminal but not Django"

### Root Cause:
1. When running Django as a background service or under a different user account (e.g., `www-data` or a dedicated system user), the user's personal environment `PATH` might not be loaded.
2. Web servers often run with stripped environment variables.

### Fix:
Explicitly set `TESSERACT_CMD` in the `.env` file used by Django:
```env
TESSERACT_CMD=/usr/bin/tesseract
```
or on Windows:
```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

## 6. "Permission denied" / `OCR_PERMISSION_DENIED`

### Root Cause:
1. The temporary directory (e.g. `C:\Users\...\AppData\Local\Temp` or `/tmp`) does not have write permissions for the user running the Django process.
2. Uploaded media directory `backend/media/documents` lacks write permissions.

### Fix:
1. Check diagnostic report: `python backend/manage.py check_ocr` reports `Temp Directory Status`.
2. Ensure directory write permissions:
   - Linux: `chmod -R 775 backend/media /tmp`
   - Windows: Verify standard user temp permissions.

---

## 7. "PDF rendering failed" / `OCR_RENDER_FAILED`

### Root Cause:
1. The PDF is password-protected or encrypted.
2. The PDF has broken xref tables or syntax errors.
3. PyMuPDF (`fitz`) is missing and Poppler is not installed.

### Fix:
1. StudyAI uses PyMuPDF (`pymupdf`) for zero-dependency PDF rendering on Windows. Verify PyMuPDF is installed:
   ```bash
   pip install pymupdf
   ```
2. If the document is password-protected, remove encryption before uploading.

---

## 8. "OCR output is empty" / `OCR_EMPTY_RESULT`

### Root Cause:
1. The PDF consists of blank scanned pages (e.g., blank separator sheets).
2. The scan resolution is too low (< 100 DPI) or contrast is extremely washed out.

### Fix:
1. Ensure the scanned document has readable text.
2. Increase rendering resolution in `.env`:
   ```env
   OCR_DPI=250
   OCR_QUALITY_MODE=HIGH_QUALITY
   ```

---

## 9. "OCR output is garbage / gibberish" / `OCR_WEAK_QUALITY`

### Root Cause:
1. Page is rotated by 90°, 180°, or 270°.
2. Inappropriate thresholding destroying thin character strokes.
3. Document is in a different language than configured in `OCR_LANGUAGES`.

### Fix:
1. If the document is in Hindi or Spanish, configure:
   ```env
   OCR_LANGUAGES=eng+hin
   ```
2. Set quality mode to balanced or high quality in `.env`:
   ```env
   OCR_QUALITY_MODE=HIGH_QUALITY
   ```

---

## 10. "OCR is too slow" or "OCR times out" / `OCR_TIMEOUT`

### Root Cause:
1. `OCR_DPI` is set too high (e.g. 400 or 600 DPI), creating gigantic multi-megapixel images.
2. Document has 100+ pages and is being processed in a single synchronous burst.

### Fix:
1. Configure balanced DPI and page timeout in `.env`:
   ```env
   OCR_DPI=200
   OCR_TIMEOUT_PER_PAGE=20
   MAX_OCR_PAGES=50
   OCR_QUALITY_MODE=FAST
   ```
2. StudyAI processes pages incrementally and preserves partial results if individual pages exceed the timeout limit.

---

## 11. "Docker OCR doesn't work"

### Root Cause:
The Dockerfile only ran `pip install pytesseract` without installing the Linux system packages `tesseract-ocr` and `tesseract-ocr-eng`.

### Fix:
`Dockerfile.backend` in StudyAI includes the full system dependencies:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```
Verify inside the running container:
```bash
docker-compose exec backend python manage.py check_ocr
```

---

## 12. "Windows path with spaces problem"

### Root Cause:
Subprocess execution passing unquoted string shell commands when paths contain spaces (e.g. `C:\Program Files\Tesseract-OCR\tesseract.exe`).

### Fix:
StudyAI strictly avoids `shell=True` and passes executable arguments as structured Python lists `[tess_cmd, ...]` with `pathlib.Path` normalization.

---

## 13. "Scanned PDF detected incorrectly"

### Rules used by StudyAI:
1. If a page has $\ge 30$ non-whitespace native text characters: it is treated as a **native text page** and extracted directly.
2. If a page has $< 30$ native text characters: it is treated as a **scanned page** and routed to the OCR engine.
3. Documents with both native and scanned pages are treated as **MIXED** documents; native pages preserve perfect vector fidelity while scanned pages are OCR-processed.
