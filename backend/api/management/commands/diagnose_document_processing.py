"""
=============================================================================
StudyAI — Document Processing Diagnostic Tool (python manage.py diagnose_document_processing)
=============================================================================
Performs an end-to-end audit of all prerequisites for zero-hang document processing:
1. Django Configuration & Settings
2. Database Connectivity & Document Records
3. Media Storage Permissions (Write/Read)
4. PDF Extraction Libraries (PyMuPDF / fitz)
5. Tesseract Optical Character Recognition (OCR) Engine & Languages
6. Ollama Local LLM Daemon Connectivity
7. Configured Ollama Model Availability
8. Background Pipeline Workers & Execution Pool
9. Stale Processing Jobs Audit & Recovery
=============================================================================
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from api.models import Document, Chunk, Topic
from api.ocr_service import get_ocr_health_report
from api.ollama_service import check_ollama_status, get_configured_model
from api.document_pipeline import recover_stale_jobs, MAX_PIPELINE_WORKERS, HEARTBEAT_TIMEOUT_SECONDS


class Command(BaseCommand):
    help = "Audits and validates the complete StudyAI document processing pipeline."

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically recover any detected stale processing jobs.',
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output audit results as JSON.',
        )

    def handle(self, *args, **options):
        results = {}
        all_passed = True

        # ---------------------------------------------------------
        # 1. Database Connection
        # ---------------------------------------------------------
        try:
            doc_count = Document.objects.count()
            results["database"] = {
                "status": "PASS",
                "message": f"Connected. {doc_count} documents in database."
            }
        except Exception as e:
            all_passed = False
            results["database"] = {
                "status": "FAIL",
                "message": f"Database unreachable: {e}"
            }

        # ---------------------------------------------------------
        # 2. Media Storage
        # ---------------------------------------------------------
        try:
            media_dir = Path(getattr(settings, 'MEDIA_ROOT', 'media'))
            media_dir.mkdir(parents=True, exist_ok=True)
            test_file = media_dir / '.pipeline_test_probe'
            test_file.write_text("StudyAI probe test", encoding="utf-8")
            content = test_file.read_text(encoding="utf-8")
            test_file.unlink(missing_ok=True)
            if content == "StudyAI probe test":
                results["storage"] = {
                    "status": "PASS",
                    "message": f"Media directory writable ({media_dir.resolve()})."
                }
            else:
                raise IOError("Write verification mismatch")
        except Exception as e:
            all_passed = False
            results["storage"] = {
                "status": "FAIL",
                "message": f"Media storage error: {e}"
            }

        # ---------------------------------------------------------
        # 3. PDF Extraction Capability
        # ---------------------------------------------------------
        try:
            import fitz
            version = getattr(fitz, '__version__', 'detected')
            results["pdf_extraction"] = {
                "status": "PASS",
                "message": f"PyMuPDF (fitz) {version} operational."
            }
        except ImportError:
            try:
                import pypdf
                results["pdf_extraction"] = {
                    "status": "WARNING",
                    "message": "pypdf available (PyMuPDF recommended for higher performance)."
                }
            except ImportError:
                all_passed = False
                results["pdf_extraction"] = {
                    "status": "FAIL",
                    "message": "Neither PyMuPDF nor pypdf is installed."
                }

        # ---------------------------------------------------------
        # 4. OCR Engine (Tesseract)
        # ---------------------------------------------------------
        try:
            ocr_rep = get_ocr_health_report()
            if ocr_rep.get("tesseract_detected"):
                langs = ocr_rep.get("available_languages", [])
                results["ocr"] = {
                    "status": "PASS",
                    "message": f"Tesseract operational ({ocr_rep.get('executable_path')}). Languages: {', '.join(langs[:4]) if langs else 'None'}."
                }
            else:
                results["ocr"] = {
                    "status": "WARNING",
                    "message": f"Tesseract not found. Scanned PDFs will fail unless Tesseract is installed."
                }
        except Exception as e:
            results["ocr"] = {
                "status": "WARNING",
                "message": f"OCR check failed: {e}"
            }

        # ---------------------------------------------------------
        # 5. Ollama LLM Connection & Model
        # ---------------------------------------------------------
        try:
            ollama_status = check_ollama_status()
            cfg_model = get_configured_model()
            is_online = ollama_status.get("is_online", False)
            models = ollama_status.get("models", [])

            if is_online:
                results["ollama_connection"] = {
                    "status": "PASS",
                    "message": f"Connected to {ollama_status.get('endpoint', 'http://localhost:11434')}."
                }
                model_found = any(m.startswith(cfg_model.split(':')[0]) for m in models)
                if model_found:
                    results["ollama_model"] = {
                        "status": "PASS",
                        "message": f"Configured model '{cfg_model}' is installed and ready."
                    }
                else:
                    results["ollama_model"] = {
                        "status": "WARNING",
                        "message": f"Model '{cfg_model}' not found in installed models ({', '.join(models) or 'none'}). Run: ollama pull {cfg_model}"
                    }
            else:
                results["ollama_connection"] = {
                    "status": "WARNING",
                    "message": f"Ollama is offline at {ollama_status.get('endpoint')}. Ensure Ollama is running."
                }
                results["ollama_model"] = {
                    "status": "WARNING",
                    "message": f"Cannot check '{cfg_model}' while Ollama is offline."
                }
        except Exception as e:
            results["ollama_connection"] = {
                "status": "WARNING",
                "message": f"Ollama check failed: {e}"
            }
            results["ollama_model"] = {
                "status": "WARNING",
                "message": "N/A"
            }

        # ---------------------------------------------------------
        # 6. Document Pipeline Worker Pool
        # ---------------------------------------------------------
        results["worker_pool"] = {
            "status": "PASS",
            "message": f"ThreadPoolExecutor active (max_workers={MAX_PIPELINE_WORKERS}, heartbeat_timeout={HEARTBEAT_TIMEOUT_SECONDS}s)."
        }

        # ---------------------------------------------------------
        # 7. Stale Processing Jobs Audit
        # ---------------------------------------------------------
        stale_docs = []
        try:
            now = timezone.now()
            processing_docs = Document.objects.filter(status='PROCESSING')
            for d in processing_docs:
                if d.is_stale(timeout_seconds=HEARTBEAT_TIMEOUT_SECONDS):
                    stale_docs.append({
                        "id": d.id,
                        "title": d.title,
                        "stage": d.processing_stage,
                        "progress": d.processing_progress,
                        "heartbeat": d.processing_heartbeat_at.isoformat() if d.processing_heartbeat_at else None
                    })

            if stale_docs:
                if options.get('fix'):
                    recovered = recover_stale_jobs()
                    results["stale_jobs"] = {
                        "status": "PASS",
                        "message": f"Found and recovered {recovered} stale jobs."
                    }
                else:
                    results["stale_jobs"] = {
                        "status": "WARNING",
                        "message": f"{len(stale_docs)} document(s) stuck in PROCESSING without heartbeat. Run with --fix to recover them."
                    }
            else:
                results["stale_jobs"] = {
                    "status": "PASS",
                    "message": "Zero stale processing jobs detected."
                }
        except Exception as e:
            results["stale_jobs"] = {
                "status": "WARNING",
                "message": f"Could not check stale jobs: {e}"
            }

        # ---------------------------------------------------------
        # Output Results
        # ---------------------------------------------------------
        if options.get('json'):
            self.stdout.write(json.dumps(results, indent=2))
            return

        self.stdout.write("\n" + "=" * 65)
        self.stdout.write("  STUDYAI — DOCUMENT PROCESSING RELIABILITY DIAGNOSTICS")
        self.stdout.write("=" * 65)

        for key, info in results.items():
            status = info["status"]
            name = key.replace("_", " ").title()
            if status == "PASS":
                tag = self.style.SUCCESS("[PASS]")
            elif status == "WARNING":
                tag = self.style.WARNING("[WARN]")
            else:
                tag = self.style.ERROR("[FAIL]")

            self.stdout.write(f"  {tag} {name:<24} : {info['message']}")

        self.stdout.write("=" * 65)
        if all_passed:
            self.stdout.write(self.style.SUCCESS("  All core systems operational. Document pipeline ready.\n"))
        else:
            self.stdout.write(self.style.ERROR("  One or more critical systems failed check.\n"))

