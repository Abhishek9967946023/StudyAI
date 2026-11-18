"""
=============================================================================
StudyAI — OCR Health Check Management Command (python manage.py check_ocr)
=============================================================================
Comprehensive diagnostic tool that inspects the OCR subsystem:
- Tesseract binary detection, version, and executable path
- Language pack inspection (traineddata in tessdata)
- Python bindings (pytesseract, Pillow)
- PDF rasterizer (PyMuPDF / fitz)
- Temp storage write permissions
- Processing limits & configuration
=============================================================================
"""

import sys
import json
from django.core.management.base import BaseCommand
from api.ocr_service import get_ocr_health_report


class Command(BaseCommand):
    help = "Inspects and diagnoses the StudyAI Optical Character Recognition (OCR) subsystem."

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output raw JSON diagnostic payload.',
        )

    def handle(self, *args, **options):
        report = get_ocr_health_report()

        if options.get('json'):
            self.stdout.write(json.dumps(report, indent=2))
            if report.get('status') == 'NOT_FOUND':
                sys.exit(1)
            return

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  STUDYAI — OCR SUBSYSTEM DIAGNOSTIC REPORT")
        self.stdout.write("=" * 60)

        # Status Badge
        status = report.get("status", "UNKNOWN")
        if status == "READY":
            status_line = self.style.SUCCESS(f"Status: {status} (Fully Operational)")
        elif status == "DEGRADED":
            status_line = self.style.WARNING(f"Status: {status} (Partially Available)")
        else:
            status_line = self.style.ERROR(f"Status: {status} (Unavailable)")
        self.stdout.write(f"Overall OCR Status      : {status_line}")

        # Tesseract Binary
        tess_ok = report.get("tesseract_detected", False)
        tess_str = self.style.SUCCESS("AVAILABLE") if tess_ok else self.style.ERROR("NOT FOUND")
        self.stdout.write(f"Tesseract Binary        : {tess_str}")
        self.stdout.write(f"Executable Path         : {report.get('executable_path', 'None')}")
        self.stdout.write(f"Tesseract Version       : {report.get('tesseract_version', 'N/A') or 'N/A'}")

        # Languages
        langs = report.get("available_languages", [])
        langs_str = ", ".join(langs) if langs else self.style.WARNING("None detected")
        self.stdout.write(f"Available Languages     : {langs_str}")
        self.stdout.write(f"Configured Languages    : {report.get('configured_languages', 'eng')}")
        missing_langs = report.get("missing_configured_languages", [])
        if missing_langs:
            self.stdout.write(self.style.ERROR(f"Missing Requested Langs : {', '.join(missing_langs)}"))

        # Python Bindings & Libraries
        py_tess = self.style.SUCCESS("AVAILABLE") if report.get("python_binding_available") else self.style.ERROR("MISSING")
        pil_ok = self.style.SUCCESS("AVAILABLE") if report.get("pillow_available") else self.style.ERROR("MISSING")
        fitz_ok = self.style.SUCCESS("AVAILABLE (fitz)") if report.get("pdf_renderer_available") else self.style.ERROR("MISSING")
        self.stdout.write(f"Python Binding (pytess) : {py_tess}")
        self.stdout.write(f"Image Library (Pillow)  : {pil_ok}")
        self.stdout.write(f"PDF Renderer (PyMuPDF)  : {fitz_ok}")

        # Storage & Limits
        temp_dir = report.get("temp_directory", "N/A")
        temp_ok = self.style.SUCCESS("WRITABLE") if report.get("temp_writable") else self.style.ERROR("READ-ONLY")
        self.stdout.write(f"Temp Directory Status   : {temp_ok} ({temp_dir})")
        self.stdout.write(f"Rasterization DPI       : {report.get('ocr_dpi', 200)}")
        self.stdout.write(f"Quality Mode            : {report.get('ocr_quality_mode', 'BALANCED')}")
        self.stdout.write(f"Page Timeout Limit      : {report.get('ocr_timeout_per_page', 25)}s")
        self.stdout.write(f"Max Pages Per Document  : {report.get('max_ocr_pages', 100)}")

        self.stdout.write("-" * 60)
        self.stdout.write(f"Diagnostic Summary      : {report.get('status_message', '')}")
        if status != "READY":
            self.stdout.write("\n" + self.style.WARNING("RECOMMENDED ACTION:"))
            self.stdout.write(report.get("recommended_action", "Check installation."))
        self.stdout.write("=" * 60 + "\n")

        if status == "NOT_FOUND":
            sys.exit(1)
