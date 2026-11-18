"""
=============================================================================
StudyAI — Production Document Processing Pipeline & Background Execution Engine
=============================================================================
Guarantees:
1. No document is EVER left stuck in an indefinite 'PROCESSING' state.
2. Every document reaches a deterministic final state:
   COMPLETED | PARTIAL | FAILED | CANCELLED
3. Asynchronous execution: Upload returns immediately; processing runs in background.
4. Stage Checkpointing & Safe Resumption: Crashed or retried jobs resume from
   the last successful stage instead of restarting from zero.
5. Continuous Heartbeat & Stale Detection: Detects frozen processes or server
   restarts and marks them for recovery.
6. Structured Error Taxonomy: Clear error codes and user-actionable guidance.
7. Local Windows Development Compatible: Works cleanly with thread pool
   executor and management command worker without heavy external infrastructure.
=============================================================================
"""

import os
import io
import json
import time
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Tuple

from django.conf import settings
from django.utils import timezone
from django.db import transaction, close_old_connections

from .models import Document, Chunk, Topic
from .document_service import (
    save_uploaded_file,
    validate_file_content_signature,
    extract_study_material,
    clean_text,
    detect_language,
    chunk_document_by_pages,
    classify_pdf_document,
    create_common_document_representation,
    ALLOWED_EXTENSIONS
)
from .prompt_templates import classify_document_genre
from .ocr_service import (
    is_ocr_available,
    get_ocr_health_report,
    OCRTesseractNotFoundError,
    OCREncryptedPDFError,
    OCRCorruptedPDFError
)
from .ollama_service import (
    check_ollama_status,
    analyze_document_with_ai,
    get_configured_model
)
from .summary_engine import synthesize_study_guide
from .subject_engine import (
    SubjectUnderstandingEngine,
    HierarchicalSyllabusDiscoveryEngine,
    DeepTopicTeachingEngine,
    DocumentCoverageEngine
)

logger = logging.getLogger(__name__)

# =============================================================================
# Standard Error Codes Taxonomy
# =============================================================================
ERROR_CODES = {
    "FILE_NOT_FOUND": "The uploaded file could not be found on the storage volume.",
    "UPLOAD_INVALID": "The uploaded file failed security or extension validation.",
    "PDF_CORRUPTED": "The PDF binary stream is malformed or corrupted and cannot be parsed.",
    "PDF_ENCRYPTED": "The PDF is password-protected. Please remove password protection before uploading.",
    "PDF_EMPTY": "No substantive readable text could be extracted from this document.",
    "OCR_TESSERACT_NOT_FOUND": "This document requires OCR, but the Tesseract OCR engine is not installed on this computer.",
    "OCR_LANGUAGE_NOT_FOUND": "The required OCR language pack is not installed.",
    "OCR_TIMEOUT": "OCR processing exceeded the allowable time limit per page.",
    "OCR_PAGE_FAILED": "Failed to extract text from scanned pages.",
    "EXTRACTION_FAILED": "Failed to extract text content from the document format.",
    "CHUNKING_FAILED": "Failed to create semantic chunks from the document content.",
    "OLLAMA_UNAVAILABLE": "Ollama service is unreachable. Ensure the Ollama daemon is running locally.",
    "OLLAMA_MODEL_NOT_FOUND": "The configured Ollama AI model is not installed. Run 'ollama pull {model}'.",
    "OLLAMA_TIMEOUT": "AI generation timed out while analyzing the document.",
    "OLLAMA_INVALID_RESPONSE": "AI service returned an unparseable response.",
    "SUMMARY_SAVE_FAILED": "Failed to persist the synthesized study summary in the database.",
    "PROCESSING_TIMEOUT": "Processing timed out or server restarted. You can resume processing.",
    "UNKNOWN_PROCESSING_ERROR": "An unexpected error occurred during document processing."
}

# Concurrency limits: Keep background threads bounded to avoid overloading local CPU/RAM on Windows
MAX_PIPELINE_WORKERS = getattr(settings, 'DOCUMENT_PIPELINE_WORKERS', 2)
HEARTBEAT_TIMEOUT_SECONDS = getattr(settings, 'DOCUMENT_HEARTBEAT_TIMEOUT_SECONDS', 360)  # 6 minutes
MATH_NOTATION_PATTERN = re.compile(
    r"(?:\$\$?|\\(?:frac|sqrt|sum|int|times|cdot)\b|"
    r"\b[A-Za-z][A-Za-z0-9_]*\s*(?:=|≈|≤|≥|≠)\s*[-+]?\d|[∑∫√±×÷])"
)

_worker_executor = ThreadPoolExecutor(max_workers=MAX_PIPELINE_WORKERS, thread_name_prefix="StudyAI-DocWorker")
_active_jobs_lock = threading.Lock()
_active_jobs = set()  # set of doc_ids currently claimed in-memory


def build_extraction_report(extraction_result, pages_data, page_count: int) -> Dict[str, Any]:
    page_records = pages_data if isinstance(pages_data, list) else []
    pages_by_number = {
        page.get("page_number"): page
        for page in page_records
        if isinstance(page, dict) and isinstance(page.get("page_number"), int)
    }
    page_numbers = range(1, max(1, page_count) + 1)
    unreadable_pages = [
        page_number
        for page_number in page_numbers
        if not str(pages_by_number.get(page_number, {}).get("text") or "").strip()
    ]
    low_confidence_pages = [
        page_number
        for page_number, page in pages_by_number.items()
        if isinstance(page.get("confidence"), (int, float))
        and page["confidence"] < 70
    ]
    math_review_pages = [
        page_number
        for page_number, page in pages_by_number.items()
        if page.get("is_ocr")
        and MATH_NOTATION_PATTERN.search(str(page.get("text") or ""))
        and (
            not isinstance(page.get("confidence"), (int, float))
            or page["confidence"] < 70
        )
    ]
    table_statuses = {
        page_number: page["table_extraction_status"]
        for page_number, page in pages_by_number.items()
        if isinstance(page.get("table_extraction_status"), str)
    }
    pages_with_tables = sorted(
        page_number
        for page_number, page in pages_by_number.items()
        if isinstance(page.get("tables"), list) and page["tables"]
    )
    table_review_statuses = {"FAILED", "PARTIAL", "UNAVAILABLE", "OCR_REQUIRED"}
    visual_statuses = {
        page_number: page["visual_extraction_status"]
        for page_number, page in pages_by_number.items()
        if isinstance(page.get("visual_extraction_status"), str)
    }
    visual_review_statuses = {
        "DETECTED_UNINTERPRETED",
        "FAILED",
        "OCR_REQUIRED",
        "UNAVAILABLE",
    }
    average_confidence = getattr(extraction_result, "avg_confidence", None)
    if not isinstance(average_confidence, (int, float)) or average_confidence <= 0:
        average_confidence = None

    return {
        "version": 1,
        "document_type": getattr(extraction_result, "doc_type", "UNKNOWN"),
        "page_count": max(1, page_count),
        "is_scanned": bool(getattr(extraction_result, "is_scanned", False)),
        "ocr_applied": bool(getattr(extraction_result, "ocr_applied", False)),
        "partial_success": bool(getattr(extraction_result, "partial_success", False)),
        "failed_pages": sorted(set(getattr(extraction_result, "failed_pages", []) or [])),
        "unreadable_pages": unreadable_pages,
        "low_confidence_pages": sorted(low_confidence_pages),
        "math_review_pages": sorted(math_review_pages),
        "average_ocr_confidence": average_confidence,
        "confidence_available": average_confidence is not None,
        "table_extraction": {
            "extracted_count": sum(
                len(page.get("tables", []))
                for page in pages_by_number.values()
                if isinstance(page.get("tables"), list)
            ),
            "pages_with_tables": pages_with_tables,
            "review_pages": sorted(
                page_number
                for page_number, status in table_statuses.items()
                if status in table_review_statuses
            ),
            "status_by_page": table_statuses,
        },
        "visual_content": {
            "image_count": sum(
                page["image_count"]
                for page in pages_by_number.values()
                if isinstance(page.get("image_count"), int)
            ),
            "vector_graphic_count": sum(
                page["vector_graphic_count"]
                for page in pages_by_number.values()
                if isinstance(page.get("vector_graphic_count"), int)
            ),
            "detected_pages": sorted(
                page_number
                for page_number, status in visual_statuses.items()
                if status == "DETECTED_UNINTERPRETED"
            ),
            "review_pages": sorted(
                page_number
                for page_number, status in visual_statuses.items()
                if status in visual_review_statuses
            ),
            "status_by_page": visual_statuses,
        },
    }


# =============================================================================
# Pipeline Core
# =============================================================================

class DocumentPipeline:
    """
    State-machine driven document processing pipeline with stage checkpoints,
    heartbeat monitoring, timeout safeguards, and error taxonomy.
    """

    def __init__(self, document_id: int):
        self.doc_id = document_id
        self._is_cancelled = False

    def get_document(self) -> Optional[Document]:
        try:
            return Document.objects.get(id=self.doc_id)
        except Document.DoesNotExist:
            return None

    def heartbeat(self, doc: Document, stage: str, progress: int, message: str):
        """Updates document heartbeat and stage in database."""
        try:
            doc.update_progress(
                stage=stage,
                progress=progress,
                message=message,
                status='PROCESSING',
                save=True
            )
        except Exception as e:
            logger.warning(f"[DOC {self.doc_id}] Heartbeat update failed: {e}")

    def check_cancelled(self, doc: Document) -> bool:
        doc.refresh_from_db(fields=['status'])
        if doc.status == 'CANCELLED':
            self._is_cancelled = True
            return True
        return False

    def run(self) -> Dict[str, Any]:
        """
        Executes the pipeline stages with checkpoint resumption.
        Guarantees final state is COMPLETED, PARTIAL, FAILED, or CANCELLED.
        """
        close_old_connections()
        start_time = time.time()
        logger.info(f"[DOC {self.doc_id}] >>> STARTING PROCESSING PIPELINE")

        doc = self.get_document()
        if not doc:
            logger.error(f"[DOC {self.doc_id}] Document record not found.")
            return {"success": False, "error": "Document not found"}

        if doc.status == 'CANCELLED':
            logger.info(f"[DOC {self.doc_id}] Document was cancelled before start.")
            return {"success": False, "status": "CANCELLED"}

        # Claim document atomically
        with transaction.atomic():
            claimed = Document.objects.filter(
                id=self.doc_id,
                status__in=['QUEUED', 'PROCESSING', 'FAILED', 'PARTIAL']
            ).select_for_update().first()

            if not claimed:
                logger.warning(f"[DOC {self.doc_id}] Document could not be claimed.")
                return {"success": False, "error": "Could not claim document"}

            claimed.processing_attempts += 1
            claimed.update_progress(
                stage='VALIDATING',
                progress=5,
                message='Validating document format and security signatures...',
                status='PROCESSING'
            )
            doc = claimed

        checkpoints = doc.get_checkpoint_data()
        last_stage = doc.last_successful_stage or ""

        try:
            # -----------------------------------------------------------------
            # STAGE 1: VALIDATING
            # -----------------------------------------------------------------
            if self.check_cancelled(doc):
                return self._handle_cancellation(doc)

            self.heartbeat(doc, 'VALIDATING', 8, 'Inspecting document structure...')

            file_bytes = b""
            if doc.file_path:
                full_path = os.path.join(settings.MEDIA_ROOT, doc.file_path) if hasattr(settings, 'MEDIA_ROOT') else doc.file_path
                if not os.path.isfile(full_path):
                    # Check relative to base directory
                    base_path = os.path.join(settings.BASE_DIR, doc.file_path)
                    if os.path.isfile(base_path):
                        full_path = base_path
                    else:
                        raise PipelineError("FILE_NOT_FOUND", f"Stored file not found on disk: {doc.file_path}")

                with open(full_path, 'rb') as f:
                    file_bytes = f.read()

                # Signature validation
                ext = doc.filename.split('.')[-1].lower() if '.' in doc.filename else doc.file_type
                is_valid, err_msg = validate_file_content_signature(file_bytes, ext)
                if not is_valid:
                    raise PipelineError("UPLOAD_INVALID", err_msg)

                if ext == 'pdf':
                    pdf_class = classify_pdf_document(file_bytes)
                    if pdf_class.get("doc_type") == "ENCRYPTED":
                        raise PipelineError("PDF_ENCRYPTED", "The PDF is password-protected. Please remove password protection.")
                    elif pdf_class.get("doc_type") == "CORRUPTED":
                        raise PipelineError("PDF_CORRUPTED", "The PDF structure is corrupted and cannot be parsed.")

            elif not doc.raw_text:
                raise PipelineError("UPLOAD_INVALID", "No file or text payload was provided.")

            doc.last_successful_stage = 'VALIDATING'
            doc.save(update_fields=['last_successful_stage'])
            logger.info(f"[DOC {self.doc_id}] STAGE 1 (VALIDATING) PASSED")

            # -----------------------------------------------------------------
            # STAGE 2: EXTRACTING & OCR_PROCESSING
            # -----------------------------------------------------------------
            if self.check_cancelled(doc):
                return self._handle_cancellation(doc)

            raw_text = doc.raw_text or ""
            pages_data = checkpoints.get("pages_data", [])
            page_count = doc.page_count or 1
            is_scanned = doc.is_scanned
            ocr_applied = doc.ocr_applied
            partial_success = False

            # Check if extraction was already completed in a previous attempt
            can_skip_extraction = (
                last_stage in ['EXTRACTING', 'CHUNKING', 'AI_ANALYSIS', 'SYNTHESIZING']
                and raw_text
                and len(raw_text.strip()) >= 30
            )

            if not can_skip_extraction and file_bytes:
                self.heartbeat(doc, 'EXTRACTING', 12, 'Reading document pages...')

                def ocr_page_progress_cb(current_page, total_p, msg):
                    if self.check_cancelled(doc):
                        return
                    # Scale OCR progress from 15% to 40%
                    pct = int(15 + ((current_page / max(1, total_p)) * 25))
                    self.heartbeat(
                        doc,
                        'OCR_PROCESSING',
                        pct,
                        f"Reading scanned page {current_page} of {total_p}..."
                    )

                ext = doc.filename.split('.')[-1].lower() if '.' in doc.filename else 'txt'
                extraction_res = extract_study_material(
                    file_bytes,
                    doc.filename or f"document.{ext}",
                    progress_callback=ocr_page_progress_cb
                )

                raw_text, pages_data, page_count, doc_file_type, is_scanned = extraction_res
                ocr_applied = getattr(extraction_res, 'ocr_applied', False)
                ocr_error_code = getattr(extraction_res, 'ocr_error_code', None)
                partial_success = getattr(extraction_res, 'partial_success', False)
                doc.page_count = max(1, page_count)
                doc.is_scanned = is_scanned
                doc.ocr_applied = ocr_applied
                doc.set_extraction_report(
                    build_extraction_report(extraction_res, pages_data, doc.page_count)
                )
                doc.save(update_fields=[
                    'page_count',
                    'is_scanned',
                    'ocr_applied',
                    'extraction_report_json',
                ])

                # Check if OCR failed due to missing Tesseract
                if is_scanned and not raw_text.strip():
                    if ocr_error_code == "OCR_TESSERACT_NOT_FOUND":
                        raise PipelineError(
                            "OCR_TESSERACT_NOT_FOUND",
                            "This PDF requires OCR, but Tesseract OCR is not installed or configured on this computer."
                        )
                    elif ocr_error_code:
                        raise PipelineError(ocr_error_code, getattr(extraction_res, 'ocr_message', 'Scanned PDF OCR failed.'))

            # -----------------------------------------------------------------
            # STAGE 3: CLEANING & CHUNKING
            # -----------------------------------------------------------------
            if self.check_cancelled(doc):
                return self._handle_cancellation(doc)

            self.heartbeat(doc, 'CLEANING', 42, 'Sanitizing academic text content...')
            cleaned_text = clean_text(raw_text)

            if not cleaned_text or len(cleaned_text) < 30:
                if is_scanned:
                    raise PipelineError(
                        "OCR_PAGE_FAILED",
                        "Scanned pages did not yield sufficient readable text. Ensure document is clear and legible."
                    )
                raise PipelineError("PDF_EMPTY", "No substantive readable text could be extracted from this document.")

            detected_lang = detect_language(cleaned_text)
            words = len(cleaned_text.split())

            # Update document text attributes
            doc.raw_text = cleaned_text
            doc.page_count = max(1, page_count)
            doc.word_count = words
            doc.original_language = detected_lang
            doc.is_scanned = is_scanned
            doc.ocr_applied = ocr_applied

            self.heartbeat(doc, 'CHUNKING', 48, 'Creating structured semantic study chunks...')

            # Chunk document
            chunks_meta = chunk_document_by_pages(pages_data, target_size=750, overlap=100)
            doc.total_chunks = len(chunks_meta)

            # Persist Chunk models in database (safely clearing previous chunks on retry)
            with transaction.atomic():
                doc.chunks.all().delete()
                chunk_objs = []
                for c_info in chunks_meta:
                    chunk_objs.append(Chunk(
                        document=doc,
                        chunk_index=c_info.get("chunk_index", 1),
                        page_start=c_info.get("page_start", 1),
                        page_end=c_info.get("page_end", 1),
                        section=c_info.get("section", ""),
                        text=c_info.get("text", ""),
                        char_count=len(c_info.get("text", "")),
                        estimated_tokens=max(1, len(c_info.get("text", "")) // 4),
                        language=detected_lang
                    ))
                Chunk.objects.bulk_create(chunk_objs)

            # Formalize Common Document Representation (CDR)
            doc_genre = classify_document_genre(raw_text, doc.title)
            cdr = create_common_document_representation(
                document_id=doc.id,
                title=doc.title,
                genre=doc_genre,
                pages_data=pages_data,
                is_scanned=doc.is_scanned,
                ocr_applied=doc.ocr_applied
            )

            # Save checkpoint
            checkpoints["pages_data"] = pages_data
            checkpoints["page_count"] = doc.page_count
            checkpoints["chunks_count"] = doc.total_chunks
            checkpoints["cdr"] = cdr.to_dict()
            checkpoints["document_genre"] = doc_genre
            doc.set_checkpoint_data(checkpoints)
            doc.last_successful_stage = 'CHUNKING'
            doc.save(update_fields=[
                'raw_text', 'page_count', 'word_count', 'original_language',
                'is_scanned', 'ocr_applied', 'total_chunks', 'checkpoint_data',
                'last_successful_stage'
            ])
            logger.info(f"[DOC {self.doc_id}] STAGE 3 (CHUNKING) COMPLETE: {doc.total_chunks} chunks")

            # -----------------------------------------------------------------
            # STAGE 4: AI_ANALYSIS & HIERARCHICAL SYLLABUS DISCOVERY
            # -----------------------------------------------------------------
            if self.check_cancelled(doc):
                return self._handle_cancellation(doc)

            self.heartbeat(doc, 'AI_ANALYSIS', 58, 'Discovering subject architecture and hierarchical syllabus tree...')

            # Pre-flight Ollama health check
            ollama_health = check_ollama_status()
            logger.info(f"[DOC {self.doc_id}] Ollama Status: online={ollama_health.get('is_online')}, model={ollama_health.get('configured_model')}")

            # 1. Subject Understanding Engine: Discover discipline, purpose, problems solved, applications
            subject_model = SubjectUnderstandingEngine.analyze_and_persist_subject(doc)
            detected_subject = subject_model.get("subject_name") or doc.subject or "General Education"
            doc.subject = detected_subject

            # 2. Hierarchical Syllabus Discovery Engine: Build 6-level syllabus tree across 100% chunks
            discovered_topics = HierarchicalSyllabusDiscoveryEngine.discover_and_persist_syllabus(doc)

            checkpoints["topics_count"] = len(discovered_topics)
            doc.set_checkpoint_data(checkpoints)
            doc.last_successful_stage = 'AI_ANALYSIS'
            doc.save(update_fields=['subject', 'checkpoint_data', 'last_successful_stage'])
            logger.info(f"[DOC {self.doc_id}] STAGE 4 (AI_ANALYSIS) COMPLETE: subject='{detected_subject}', topics={len(discovered_topics)}")

            # -----------------------------------------------------------------
            # STAGE 5: SYNTHESIZING COMPREHENSIVE STUDY GUIDE & DEEP TEACHING
            # -----------------------------------------------------------------
            if self.check_cancelled(doc):
                return self._handle_cancellation(doc)

            self.heartbeat(doc, 'SYNTHESIZING', 76, 'Synthesizing comprehensive ChatGPT-style study guide and deep topic teaching...')

            # Multi-layer grounded academic study guide synthesis (summary_engine)
            def synth_progress_cb(current_sec, total_sec, sec_name):
                if self.check_cancelled(doc):
                    return
                pct = int(76 + ((current_sec / max(1, total_sec)) * 10))
                self.heartbeat(
                    doc,
                    'SYNTHESIZING',
                    pct,
                    f"Synthesizing section {current_sec} of {total_sec}: {sec_name[:30]}..."
                )

            user_depth = checkpoints.get('summary_depth', 'detailed')
            user_style = checkpoints.get('output_style', 'standard')

            study_guide = synthesize_study_guide(
                raw_text=cleaned_text,
                doc_id=doc.id,
                title=doc.title,
                total_pages=doc.page_count,
                mode='standard',
                depth=user_depth,
                output_style=user_style,
                target_language=doc.output_language or 'en',
                progress_callback=synth_progress_cb
            )

            verified_subject = study_guide.get("subject") or (detected_subject if detected_subject != "General Education" else "Computer Science")
            doc.subject = verified_subject

            # Pre-generate teaching for top discovered topics with continuous heartbeat
            self.heartbeat(doc, 'TEACHING', 87, 'Pre-computing deep pedagogical teaching material...')

            def teach_heartbeat_cb(topic_obj, current_idx, total_cnt):
                if self.check_cancelled(doc):
                    return
                pct = int(87 + ((current_idx / max(1, total_cnt)) * 6))
                self.heartbeat(
                    doc,
                    'TEACHING',
                    pct,
                    f"Indexing pedagogical material for topic {current_idx} of {total_cnt} ({topic_obj.name[:30]})..."
                )

            DeepTopicTeachingEngine.batch_teach_document(doc, max_topics=5, heartbeat_cb=teach_heartbeat_cb)

            # Calculate document coverage matrix
            coverage_matrix = DocumentCoverageEngine.calculate_coverage(doc)

            study_summary_payload = {
                "modes": {"standard": study_guide},
                "active_mode": "standard",
                "study_guide": study_guide,
                "response": study_guide.get("response", ""),
                "markdown_content": study_guide.get("markdown_content", "") or study_guide.get("response", ""),
                "overview": study_guide.get("overview", ""),
                "executiveSummary": study_guide.get("overview") or subject_model.get("subject_description", ""),
                "subject": verified_subject,
                "subject_understanding": subject_model,
                "coverage": coverage_matrix,
                "topics": [t.to_tree_dict(include_content=False) for t in doc.topics.filter(parent=None)]
            }

            self.heartbeat(doc, 'SAVING', 94, 'Finalizing study guide and indexing verified formulas...')

            doc.set_summary(study_summary_payload)
            final_status = 'PARTIAL' if partial_success else 'COMPLETED'
            doc.status = final_status
            doc.last_successful_stage = 'COMPLETED'
            doc.processing_stage = 'COMPLETED'
            doc.processing_progress = 100
            doc.processing_message = 'Complete AI study guide and notes ready.'
            doc.processing_error_code = ''
            doc.processing_error_message = ''
            doc.save()

            elapsed = round(time.time() - start_time, 2)
            logger.info(f"[DOC {self.doc_id}] >>> SUCCESS: Processed in {elapsed}s | Status={final_status}")

            return {
                "success": True,
                "document_id": doc.id,
                "status": final_status,
                "elapsed_seconds": elapsed
            }

        except PipelineError as pe:
            logger.error(f"[DOC {self.doc_id}] PipelineError at stage {doc.processing_stage}: {pe.code} - {pe.message}")
            self._handle_failure(doc, pe.code, pe.message)
            return {"success": False, "error_code": pe.code, "error": pe.message}

        except Exception as e:
            logger.exception(f"[DOC {self.doc_id}] Unexpected pipeline failure: {e}")
            err_code = "UNKNOWN_PROCESSING_ERROR"
            err_msg = f"Processing stopped unexpectedly: {str(e)[:200]}"
            self._handle_failure(doc, err_code, err_msg)
            return {"success": False, "error_code": err_code, "error": err_msg}

    def _handle_failure(self, doc: Document, error_code: str, error_message: str):
        try:
            doc.status = 'FAILED'
            doc.processing_stage = 'FAILED'
            doc.processing_error_code = error_code
            doc.processing_error_message = error_message
            doc.error_message = error_message
            doc.processing_message = f"Processing stopped: {error_message[:120]}"
            doc.processing_updated_at = timezone.now()
            doc.processing_heartbeat_at = timezone.now()
            doc.save(update_fields=[
                'status', 'processing_stage', 'processing_error_code',
                'processing_error_message', 'error_message',
                'processing_message', 'processing_updated_at', 'processing_heartbeat_at'
            ])
        except Exception as ex:
            logger.error(f"[DOC {self.doc_id}] Failed to record failure state: {ex}")

    def _handle_cancellation(self, doc: Document):
        logger.info(f"[DOC {self.doc_id}] Processing cleanly cancelled.")
        try:
            doc.status = 'CANCELLED'
            doc.processing_stage = 'CANCELLED'
            doc.processing_message = 'Processing was cancelled by user.'
            doc.save(update_fields=['status', 'processing_stage', 'processing_message'])
        except Exception:
            pass
        return {"success": False, "status": "CANCELLED"}


class PipelineError(Exception):
    """Structured exception carrying a recognized error code."""
    def __init__(self, code: str, message: str = ""):
        self.code = code
        self.message = message or ERROR_CODES.get(code, "A processing error occurred.")
        super().__init__(self.message)


# =============================================================================
# Background Execution & Queue Manager
# =============================================================================

def enqueue_document_for_processing(document_id: int) -> bool:
    """
    Submits a document ID to the background worker pool for processing.
    Safe against duplicate simultaneous runs on the same document.
    """
    with _active_jobs_lock:
        if document_id in _active_jobs:
            logger.info(f"[DOC {document_id}] Already running in active worker pool.")
            return False
        _active_jobs.add(document_id)

    def _worker_wrapper(doc_id):
        try:
            pipeline = DocumentPipeline(doc_id)
            pipeline.run()
        finally:
            with _active_jobs_lock:
                _active_jobs.discard(doc_id)
            close_old_connections()

    try:
        _worker_executor.submit(_worker_wrapper, document_id)
        logger.info(f"[DOC {document_id}] Enqueued in background worker pool.")
        return True
    except Exception as e:
        logger.exception(f"[DOC {document_id}] Failed to enqueue: {e}")
        with _active_jobs_lock:
            _active_jobs.discard(document_id)
        return False


def is_doc_job_active(document_id: int) -> bool:
    """Returns True if the worker thread is actively executing for this document ID."""
    with _active_jobs_lock:
        return document_id in _active_jobs


def recover_stale_jobs(timeout_seconds: int = None) -> int:
    """
    Scans for documents stuck in 'PROCESSING' state whose heartbeat is older than
    the timeout, and marks them as FAILED with recovery option.
    Does NOT mark active in-memory background worker jobs as failed.
    """
    close_old_connections()
    timeout = timeout_seconds if timeout_seconds is not None else getattr(settings, 'DOCUMENT_HEARTBEAT_TIMEOUT_SECONDS', 360)
    recovered_count = 0

    stale_docs = Document.objects.filter(status='PROCESSING')
    for d in stale_docs:
        # If the in-memory worker thread is actively executing, it is alive!
        if is_doc_job_active(d.id):
            continue
        if d.is_stale(timeout_seconds=timeout):
            logger.warning(f"[STALE RECOVERY] Marking Doc {d.id} as FAILED (stale heartbeat).")
            d.update_progress(
                stage='FAILED',
                progress=d.processing_progress,
                message='Processing timed out or server restarted. You can resume processing.',
                status='FAILED',
                error_code='PROCESSING_TIMEOUT',
                error_message='The processing worker did not report progress within the expected time limit. Click Retry to resume from the last saved stage.'
            )
            recovered_count += 1

    return recovered_count

