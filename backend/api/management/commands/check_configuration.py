"""
=============================================================================
StudyAI — Environment & Diagnostics Configuration Checker
=============================================================================
Usage:
    python manage.py check_configuration
=============================================================================
"""

import sys
import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from api.ollama_service import check_ollama_status, get_ollama_base_url, get_configured_model
from api.ocr_service import is_ocr_available, get_tesseract_cmd


class Command(BaseCommand):
    help = "Validates StudyAI environment configuration, dependencies, database, storage, and AI services."

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("  StudyAI — Comprehensive Configuration & Environment Diagnostic")
        self.stdout.write("=" * 70)

        issues = []
        warnings = []

        # 1. Python Version Check
        py_ver = sys.version_info
        py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
        if py_ver.major == 3 and py_ver.minor in (10, 11, 12):
            self.stdout.write(self.style.SUCCESS(f"  [OK] Python Version: {py_ver_str} (Supported stable release)"))
        elif py_ver.major == 3 and py_ver.minor >= 13:
            warnings.append(f"Python {py_ver_str} is higher than recommended (3.10-3.12). Some C-extensions may exhibit instability.")
            self.stdout.write(self.style.WARNING(f"  [WARN] Python Version: {py_ver_str} (Recommended: 3.10 - 3.12)"))
        else:
            issues.append(f"Python {py_ver_str} is unsupported. Python 3.10+ is required.")
            self.stdout.write(self.style.ERROR(f"  [FAIL] Python Version: {py_ver_str} (Unsupported)"))

        # 2. Django Settings & Security
        debug_mode = getattr(settings, 'DEBUG', False)
        secret_key = getattr(settings, 'SECRET_KEY', '')
        if debug_mode:
            self.stdout.write(self.style.WARNING("  [INFO] Environment: DEVELOPMENT (DEBUG=True)"))
        else:
            self.stdout.write(self.style.SUCCESS("  [OK] Environment: PRODUCTION (DEBUG=False)"))
            if len(secret_key) < 32:
                issues.append("DJANGO_SECRET_KEY is too short for production (< 32 characters).")

        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        self.stdout.write(f"  [OK] ALLOWED_HOSTS: {', '.join(allowed_hosts) if allowed_hosts else 'None'}")

        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        self.stdout.write(f"  [OK] CORS_ALLOWED_ORIGINS ({len(cors_origins)} origins configured)")

        # 3. Database Connectivity Check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_engine = settings.DATABASES['default']['ENGINE'].split('.')[-1]
            db_name = settings.DATABASES['default'].get('NAME', '')
            self.stdout.write(self.style.SUCCESS(f"  [OK] Database ({db_engine}): Connected successfully"))
        except Exception as e:
            issues.append(f"Database connection failed: {str(e)}")
            self.stdout.write(self.style.ERROR(f"  [FAIL] Database: Connection failed ({str(e)})"))

        # 4. Storage & Media Root Check
        try:
            media_root = Path(settings.MEDIA_ROOT).resolve()
            media_root.mkdir(parents=True, exist_ok=True)
            test_probe = media_root / '.config_probe'
            test_probe.write_text("ok", encoding="utf-8")
            test_probe.unlink(missing_ok=True)
            self.stdout.write(self.style.SUCCESS(f"  [OK] Media Storage: Writable ({media_root})"))
        except Exception as e:
            issues.append(f"Media storage directory not writable: {str(e)}")
            self.stdout.write(self.style.ERROR(f"  [FAIL] Media Storage: Not writable ({str(e)})"))

        # 5. Ollama & AI Service Check
        ollama_url = get_ollama_base_url()
        configured_model = get_configured_model()
        ollama_status = check_ollama_status()

        if ollama_status.get('is_online'):
            models = ollama_status.get('models', [])
            if ollama_status.get('model_available'):
                self.stdout.write(self.style.SUCCESS(
                    f"  [OK] Ollama AI: Online at {ollama_url} with '{configured_model}' ready ({len(models)} model(s) available)"
                ))
            else:
                warnings.append(f"Ollama is running at {ollama_url}, but model '{configured_model}' is not pulled.")
                self.stdout.write(self.style.WARNING(
                    f"  [WARN] Ollama AI: Online at {ollama_url}, but model '{configured_model}' is missing. (Run 'ollama pull {configured_model}')"
                ))
        else:
            warnings.append(f"Ollama daemon not reachable at {ollama_url}. Deterministic fallback engine will be used.")
            self.stdout.write(self.style.WARNING(
                f"  [WARN] Ollama AI: Unavailable at {ollama_url} (Deterministic fallback engine will handle requests)"
            ))

        # 6. OCR Dependencies Check
        ocr_ok, ocr_msg = is_ocr_available()
        tess_bin = get_tesseract_cmd()
        if ocr_ok:
            self.stdout.write(self.style.SUCCESS(f"  [OK] OCR Engine: Available ({tess_bin})"))
        else:
            warnings.append(f"OCR is unavailable: {ocr_msg}. Standard PDFs and Word documents will process normally; scanned PDFs will be flagged.")
            self.stdout.write(self.style.WARNING(f"  [INFO] OCR Engine: {ocr_msg} (Optional for scanned PDFs)"))

        # 7. Email & Authentication Check
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        if 'console' in email_backend:
            self.stdout.write(self.style.SUCCESS("  [OK] Email Delivery: Console Backend (OTP codes print to server terminal)"))
        else:
            email_user = getattr(settings, 'EMAIL_HOST_USER', '')
            if email_user:
                self.stdout.write(self.style.SUCCESS(f"  [OK] Email Delivery: SMTP configured with user {email_user[:3]}***"))
            else:
                warnings.append("SMTP email backend configured without EMAIL_HOST_USER. Email sending may fail.")
                self.stdout.write(self.style.WARNING("  [WARN] Email Delivery: SMTP selected but EMAIL_HOST_USER is unset"))

        # Summary & Recommendations
        self.stdout.write("-" * 70)
        if issues:
            self.stdout.write(self.style.ERROR(f"  Configuration Check: FAILED with {len(issues)} critical issue(s):"))
            for iss in issues:
                self.stdout.write(self.style.ERROR(f"    - {iss}"))
        else:
            self.stdout.write(self.style.SUCCESS("  Configuration Check: ALL CRITICAL SERVICES HEALTHY"))

        if warnings:
            self.stdout.write(self.style.WARNING(f"\n  Notices & Recommendations ({len(warnings)}):"))
            for w in warnings:
                self.stdout.write(self.style.WARNING(f"    - {w}"))

        self.stdout.write("=" * 70 + "\n")
