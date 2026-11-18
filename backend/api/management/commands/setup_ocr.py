"""
=============================================================================
StudyAI — OCR Setup & Configuration Helper (python manage.py setup_ocr)
=============================================================================
Inspects the current operating system and environment, and prints exact,
safe, step-by-step instructions for installing and configuring Tesseract OCR
and language packs without silently modifying system software.
=============================================================================
"""

import sys
from django.core.management.base import BaseCommand
from api.ocr_service import get_ocr_health_report, get_tesseract_cmd


class Command(BaseCommand):
    help = "Displays platform-specific installation and configuration instructions for Tesseract OCR."

    def handle(self, *args, **options):
        report = get_ocr_health_report()
        tess_path = get_tesseract_cmd()

        self.stdout.write("\n" + "=" * 65)
        self.stdout.write("  STUDYAI — OCR INSTALLATION & SETUP GUIDE")
        self.stdout.write("=" * 65)

        if report.get("status") == "READY":
            self.stdout.write(self.style.SUCCESS(
                f"\n[OK] Tesseract OCR is already detected and operational at:\n  {tess_path}"
            ))
            self.stdout.write(f"Version: {report.get('tesseract_version')}")
            self.stdout.write(f"Available Languages: {', '.join(report.get('available_languages', []))}")
            self.stdout.write("\nNo further system setup required for OCR processing.")
            self.stdout.write("=" * 65 + "\n")
            return

        current_platform = sys.platform
        self.stdout.write(f"\nDetected Host Platform: {current_platform.upper()}")

        if current_platform == 'win32':
            self.stdout.write("\n--- WINDOWS SETUP INSTRUCTIONS ---")
            self.stdout.write("Option 1 (Fastest via Windows Package Manager / winget):")
            self.stdout.write("  Run in PowerShell or Command Prompt:")
            self.stdout.write(self.style.SUCCESS("    winget install UB-Mannheim.TesseractOCR"))
            self.stdout.write("\nOption 2 (Official Windows Installer):")
            self.stdout.write("  1. Download the 64-bit installer from:")
            self.stdout.write("     https://github.com/UB-Mannheim/tesseract/wiki")
            self.stdout.write("  2. Run the installer (default: C:\\Program Files\\Tesseract-OCR)")
            self.stdout.write("  3. Check the box 'Additional script data' or 'Additional language data' if you need Hindi/other languages.")
            self.stdout.write("\nOption 3 (Custom Installation Directory):")
            self.stdout.write("  If you install to a non-standard location (e.g. D:\\Tools\\Tesseract), add it to your .env file:")
            self.stdout.write(self.style.SUCCESS("    TESSERACT_CMD=D:\\Tools\\Tesseract\\tesseract.exe"))

        elif current_platform.startswith('linux'):
            self.stdout.write("\n--- LINUX (DEBIAN / UBUNTU) SETUP INSTRUCTIONS ---")
            self.stdout.write("  1. Update package index and install Tesseract + language data:")
            self.stdout.write(self.style.SUCCESS("    sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng"))
            self.stdout.write("  2. For Indian vernaculars (Hindi, Kannada, Tamil, Telugu):")
            self.stdout.write(self.style.SUCCESS("    sudo apt-get install -y tesseract-ocr-hin tesseract-ocr-kan tesseract-ocr-tam tesseract-ocr-tel"))
            self.stdout.write("\n--- LINUX (RHEL / FEDORA / CENTOS) ---")
            self.stdout.write(self.style.SUCCESS("    sudo dnf install -y tesseract tesseract-langpack-eng"))

        elif current_platform == 'darwin':
            self.stdout.write("\n--- MACOS SETUP INSTRUCTIONS ---")
            self.stdout.write("  Run with Homebrew:")
            self.stdout.write(self.style.SUCCESS("    brew install tesseract"))
            self.stdout.write("  For multilingual support (e.g. Hindi, Spanish):")
            self.stdout.write(self.style.SUCCESS("    brew install tesseract-lang"))

        self.stdout.write("\n--- DOCKER REPRODUCIBILITY ---")
        self.stdout.write("  Dockerfile.backend already includes system dependencies:")
        self.stdout.write("    RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng ...")

        self.stdout.write("\n--- VERIFICATION ---")
        self.stdout.write("  After installing, verify your setup by running:")
        self.stdout.write(self.style.SUCCESS("    python manage.py check_ocr"))
        self.stdout.write("=" * 65 + "\n")
