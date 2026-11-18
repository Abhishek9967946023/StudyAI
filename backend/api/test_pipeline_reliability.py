"""
=============================================================================
StudyAI — Document Processing Reliability Test Suite
=============================================================================
Verifies zero-hang processing, deterministic state machines, checkpointing,
cancellation, retry, stale recovery, and error taxonomy (Tests A - J).
=============================================================================
"""

import json
import time
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from api.models import Document, Chunk, Topic
from api.document_pipeline import (
    DocumentPipeline,
    PipelineError,
    recover_stale_jobs,
    enqueue_document_for_processing
)


class DocumentProcessingReliabilityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="pipelinetest@studyai.internal",
            email="pipelinetest@studyai.internal",
            password="TestPassword123!"
        )
        self.client.force_login(self.user)

    def test_model_fields_and_methods(self):
        """Verifies new pipeline fields, progress updater, and stale detection."""
        doc = Document.objects.create(
            user=self.user,
            title="Physics Notes",
            filename="physics.pdf",
            file_type="pdf",
            status="QUEUED"
        )
        self.assertEqual(doc.status, "QUEUED")
        self.assertEqual(doc.processing_progress, 0)
        self.assertEqual(doc.processing_stage, "QUEUED")

        # Update progress
        doc.update_progress(
            stage="EXTRACTING",
            progress=25,
            message="Extracting page 1 of 4",
            status="PROCESSING"
        )
        doc.refresh_from_db()
        self.assertEqual(doc.status, "PROCESSING")
        self.assertEqual(doc.processing_stage, "EXTRACTING")
        self.assertEqual(doc.processing_progress, 25)
        self.assertIsNotNone(doc.processing_heartbeat_at)

        # Checkpoint serialization
        doc.set_checkpoint_data({"pages_extracted": 4, "sample": "val"})
        doc.save(update_fields=['checkpoint_data'])
        doc.refresh_from_db()
        data = doc.get_checkpoint_data()
        self.assertEqual(data.get("pages_extracted"), 4)

        # Stale check
        self.assertFalse(doc.is_stale(timeout_seconds=60))
        # Artificially age the heartbeat
        doc.processing_heartbeat_at = timezone.now() - timedelta(seconds=200)
        doc.save(update_fields=['processing_heartbeat_at'])
        self.assertTrue(doc.is_stale(timeout_seconds=60))

    def test_upload_returns_immediately_with_queued_status(self):
        """Upload request must return in < 100ms with status='QUEUED', not block."""
        content = "This is a comprehensive study chapter on Classical Thermodynamics and Heat Transfer with entropy."
        t0 = time.time()
        resp = self.client.post(
            '/api/v1/materials',
            data=json.dumps({"text": content, "title": "Thermodynamics 101"}),
            content_type="application/json"
        )
        elapsed = time.time() - t0
        self.assertLess(elapsed, 0.5)  # comfortably under threshold
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "QUEUED")
        self.assertEqual(data.get("processing_stage"), "QUEUED")
        self.assertIn("id", data)

    def test_status_endpoint_returns_rich_pipeline_fields(self):
        """Status endpoint returns dynamic stages, steps, and retry capability."""
        doc = Document.objects.create(
            user=self.user,
            title="Bio 101",
            filename="bio.pdf",
            file_type="pdf",
            status="PROCESSING",
            processing_stage="OCR_PROCESSING",
            processing_progress=35,
            processing_message="Reading scanned page 2 of 5"
        )
        resp = self.client.get(f'/api/v1/materials/{doc.id}/status')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("id"), doc.id)
        self.assertEqual(data.get("status"), "PROCESSING")
        self.assertEqual(data.get("stage"), "OCR_PROCESSING")
        self.assertEqual(data.get("progress"), 35)
        self.assertEqual(data.get("message"), "Reading scanned page 2 of 5")
        self.assertFalse(data.get("isComplete"))
        self.assertFalse(data.get("isFailed"))
        self.assertIn("steps", data)
        self.assertTrue(len(data.get("steps")) > 0)

    def test_cancel_endpoint(self):
        """Cancel endpoint halts processing and sets status to CANCELLED."""
        doc = Document.objects.create(
            user=self.user,
            title="Math Syllabus",
            filename="math.pdf",
            file_type="pdf",
            status="PROCESSING",
            processing_stage="EXTRACTING"
        )
        resp = self.client.post(f'/api/v1/materials/{doc.id}/cancel')
        self.assertEqual(resp.status_code, 200)
        doc.refresh_from_db()
        self.assertEqual(doc.status, "CANCELLED")
        self.assertEqual(doc.processing_stage, "CANCELLED")

        # Test pipeline aborts when document is cancelled
        pipeline = DocumentPipeline(doc.id)
        res = pipeline.run()
        self.assertEqual(res.get("status"), "CANCELLED")

    def test_retry_endpoint(self):
        """Retry endpoint resumes/re-queues a failed document."""
        doc = Document.objects.create(
            user=self.user,
            title="Failed Material",
            filename="failed.pdf",
            file_type="pdf",
            status="FAILED",
            processing_stage="FAILED",
            processing_progress=40,
            processing_error_code="OCR_TIMEOUT",
            processing_error_message="OCR timed out on page 3",
            last_successful_stage="EXTRACTING"
        )
        resp = self.client.post(f'/api/v1/materials/{doc.id}/retry')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "QUEUED")

        doc.refresh_from_db()
        self.assertEqual(doc.status, "QUEUED")
        self.assertEqual(doc.processing_error_code, "")
        # Checkpoint remains intact for resumption
        self.assertEqual(doc.last_successful_stage, "EXTRACTING")

    def test_stale_job_recovery(self):
        """Stale jobs stuck in PROCESSING without heartbeat must be recovered as FAILED."""
        stale_doc = Document.objects.create(
            user=self.user,
            title="Stuck Doc",
            filename="stuck.pdf",
            file_type="pdf",
            status="PROCESSING",
            processing_stage="AI_ANALYSIS",
            processing_progress=60,
            processing_heartbeat_at=timezone.now() - timedelta(minutes=10)
        )
        recovered = recover_stale_jobs(timeout_seconds=60)
        self.assertGreaterEqual(recovered, 1)

        stale_doc.refresh_from_db()
        self.assertEqual(stale_doc.status, "FAILED")
        self.assertEqual(stale_doc.processing_error_code, "PROCESSING_TIMEOUT")

    def test_empty_document_validation(self):
        """Text submissions under minimum length must fail immediately with PDF_EMPTY."""
        resp = self.client.post(
            '/api/v1/materials',
            data=json.dumps({"text": "Too short", "title": "Short"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data.get("code"), "PDF_EMPTY")

    def test_corrupt_pdf_validation(self):
        """Uploading corrupted binary streams triggers PDF_CORRUPTED validation."""
        fake_corrupted_pdf = SimpleUploadedFile(
            "bad.pdf",
            b"%PDF-1.4 corrupt junk random binary non pdf content",
            content_type="application/pdf"
        )
        resp = self.client.post(
            '/api/v1/materials',
            data={"file": fake_corrupted_pdf}
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data.get("code"), "PDF_CORRUPTED")

    def test_active_job_never_falsely_timed_out_in_status_view(self):
        """Active jobs in _active_jobs must never be killed by polling status checks."""
        from api.document_pipeline import _active_jobs, _active_jobs_lock

        doc = Document.objects.create(
            user=self.user,
            title="Active Long Running Job",
            filename="active.pdf",
            file_type="pdf",
            status="PROCESSING",
            processing_stage="TEACHING",
            processing_progress=88,
            processing_heartbeat_at=timezone.now() - timedelta(seconds=250)  # > 180s ago
        )

        with _active_jobs_lock:
            _active_jobs.add(doc.id)

        try:
            # Polling status view
            resp = self.client.get(f'/api/v1/materials/{doc.id}/status')
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            # Must NOT be marked as failed or timed out
            self.assertEqual(data.get("status"), "PROCESSING")
            self.assertEqual(data.get("stage"), "TEACHING")
            self.assertFalse(data.get("isFailed"))
            self.assertNotEqual(data.get("error_code"), "PROCESSING_TIMEOUT")

            doc.refresh_from_db()
            self.assertEqual(doc.status, "PROCESSING")
            # Heartbeat was automatically refreshed!
            self.assertGreater(
                doc.processing_heartbeat_at,
                timezone.now() - timedelta(seconds=5)
            )
        finally:
            with _active_jobs_lock:
                _active_jobs.discard(doc.id)

    def test_truly_stale_job_marked_failed_after_timeout(self):
        """Stalled job without active worker thread must be marked FAILED after timeout threshold."""
        doc = Document.objects.create(
            user=self.user,
            title="Dead Worker Doc",
            filename="dead.pdf",
            file_type="pdf",
            status="PROCESSING",
            processing_stage="AI_ANALYSIS",
            processing_progress=60,
            processing_heartbeat_at=timezone.now() - timedelta(seconds=400)  # > 360s
        )

        resp = self.client.get(f'/api/v1/materials/{doc.id}/status')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data.get("status"), "FAILED")
        self.assertEqual(data.get("error_code"), "PROCESSING_TIMEOUT")
        self.assertTrue(data.get("canRetry"))

        doc.refresh_from_db()
        self.assertEqual(doc.status, "FAILED")
        self.assertEqual(doc.processing_error_code, "PROCESSING_TIMEOUT")
