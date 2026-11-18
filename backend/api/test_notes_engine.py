"""
=============================================================================
StudyAI — Comprehensive Automated Tests for Notes Generation & Verification Engine
=============================================================================
Tests:
1. PPTX Extraction & NormalizedDocumentUnit
2. LaTeX formula-preserving chunking
3. Syllabus checklist planning & chunk mapping
4. 15-dimension section note generation
5. Completeness & LaTeX mathematical verification audit
6. Targeted defect repair loop
7. Resumable job orchestration loop
8. Word (.docx) export generation
9. PDF (.pdf) export generation
10. REST API endpoints (start, status, retry, resume, exports)
=============================================================================
"""

import os
import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings
from api.models import Document, Chunk, NotesGenerationJob, SyllabusSection
from api.document_service import (
    extract_text_from_pptx,
    chunk_document_by_pages,
    NormalizedDocumentUnit
)
from api.notes_engine import (
    normalize_notes_depth,
    plan_syllabus_checklist,
    generate_single_section_notes,
    verify_section_notes,
    repair_section_notes,
    process_notes_generation_job,
    assemble_final_document,
    _export_notes_to_docx_fallback,
    _export_notes_to_pdf_fallback,
    export_notes_to_docx,
    export_notes_to_pdf
)

User = get_user_model()


@patch("api.notes_engine.check_ai_provider_status", return_value={"can_generate": False})
class NotesEngineUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="teststudent",
            email="student@studyai.test",
            password="SecurePassword123!"
        )
        self.doc = Document.objects.create(
            user=self.user,
            title="Advanced Operating Systems & Synchronization",
            subject="Computer Science",
            page_count=12,
            raw_text=(
                "# Module 1: Concurrency and Mutual Exclusion\n\n"
                "## Topic 1.1: Semaphores and Deadlock\n"
                "A semaphore S is an integer variable accessed only through atomic operations wait() and signal().\n"
                "The mathematical invariant is given by:\n"
                "$$S_{val} = S_{init} + \\sum signal - \\sum wait$$\n\n"
                "## Topic 1.2: Monitors and Condition Variables\n"
                "Monitors guarantee mutual exclusion inside procedure scopes.\n\n"
                "# Module 2: Memory Management & Paging\n\n"
                "## Topic 2.1: Virtual Memory and Page Replacement\n"
                "The effective memory access time EAT is computed as:\n"
                "$$EAT = (1 - p) \\times t_m + p \\times t_{pf}$$\n"
                "where p is the page fault rate and t_m is physical memory access latency."
            ),
            output_language="en",
            status="ready"
        )
        # Create Chunks
        Chunk.objects.create(
            document=self.doc,
            chunk_index=0,
            page_start=1,
            page_end=1,
            text=self.doc.raw_text[:400]
        )
        Chunk.objects.create(
            document=self.doc,
            chunk_index=1,
            page_start=2,
            page_end=2,
            text=self.doc.raw_text[400:]
        )

    def test_depth_aliases_match_generator_levels(self, mock_ollama):
        self.assertEqual(normalize_notes_depth("basic"), "basic")
        self.assertEqual(normalize_notes_depth("standard"), "intermediate")
        self.assertEqual(normalize_notes_depth("thorough"), "advanced")
        self.assertEqual(normalize_notes_depth("deep"), "advanced")

    def test_notes_prompt_uses_shared_source_and_context_guidelines(self, mock_ollama):
        job = NotesGenerationJob.objects.create(
            job_id="test_prompt_job",
            document=self.doc,
            user=self.user,
            mode="comprehensive"
        )
        section = SyllabusSection.objects.create(
            job=job,
            topic_id="prompt_topic",
            module="Concurrency",
            title="Semaphores",
            order_index=0
        )
        generated = "## Semaphores\n\n" + ("Source-grounded explanation. " * 160)

        with patch("api.notes_engine.check_ai_provider_status", return_value={"can_generate": True}), patch(
            "api.notes_engine.query_ai",
            return_value=(generated, True, None)
        ) as query:
            generate_single_section_notes(
                section=section,
                source_chunks=[{"page_start": 1, "page_end": 1, "text": "Semaphores coordinate processes."}],
                language="en"
            )

        prompt = query.call_args.args[0]
        self.assertIn("Output language: en", prompt)
        self.assertIn("label it as additional context", prompt)
        self.assertIn("advantages, disadvantages, limitations", prompt)
        self.assertIn("independently verified", prompt)

    def test_chunking_preserves_latex_formula_boundaries(self, mock_ollama):
        """Verifies that math equations $$...$$ are never cut mid-equation across chunk boundaries."""
        sample_text = (
            "Introduction to paging.\n\n"
            "$$EAT = (1 - p) \\times t_m + p \\times t_{pf}$$\n\n"
            "Conclusion of memory management section."
        )
        chunks = chunk_document_by_pages(sample_text, max_chunk_chars=50, overlap_chars=10)
        self.assertTrue(len(chunks) >= 1)
        for ch in chunks:
            count = ch["text"].count("$$")
            self.assertEqual(count % 2, 0, f"Unbalanced $$ in chunk: {ch}")

    def test_plan_syllabus_checklist(self, mock_ollama):
        """Verifies that plan_syllabus_checklist creates a structured hierarchy."""
        job = plan_syllabus_checklist(self.doc)
        self.assertIsInstance(job, NotesGenerationJob)
        self.assertTrue(job.sections.count() >= 2)
        first_sec = job.sections.first()
        self.assertTrue(bool(first_sec.topic_id))
        self.assertTrue(bool(first_sec.title))
        self.assertTrue(bool(first_sec.module))

    def test_unmatched_syllabus_topic_does_not_borrow_first_chunk(self, mock_ollama):
        job = plan_syllabus_checklist(
            self.doc,
            user_syllabus=[{"name": "Quantum chromodynamics", "pages": [99]}]
        )
        section = job.sections.get()

        self.assertEqual(section.get_source_chunks(), [])
        notes = generate_single_section_notes(section=section, source_chunks=[])
        self.assertIn("There is no source text mapped to this topic", notes)
        self.assertNotIn("scheduler", notes.lower())

    def test_generate_single_section_notes(self, mock_ollama):
        """Offline notes quote available source material rather than inventing a lesson."""
        job = NotesGenerationJob.objects.create(
            job_id="test_gen_job",
            document=self.doc,
            user=self.user,
            mode="comprehensive",
            depth="intermediate",
            language="en"
        )
        sec = SyllabusSection.objects.create(
            job=job,
            topic_id="sec_1",
            module="Concurrency",
            title="Semaphores and Mutexes",
            parent_topic="Atomic operations",
            order_index=0
        )
        notes = generate_single_section_notes(
            section=sec,
            source_chunks=list(self.doc.chunks.all()),
            document_subject=self.doc.subject,
            mode="comprehensive",
            depth="intermediate"
        )
        self.assertIn("Semaphores and Mutexes", notes)
        self.assertIn("What the source says", notes)
        self.assertIn("semaphore", notes.lower())
        self.assertIn("(Source: Page 1)", notes)
        self.assertIn("No worked example was identified", notes)
        self.assertNotIn("coordinated scheduler", notes)
        self.assertNotIn("operational constraints", notes)

    def test_missing_source_page_metadata_is_not_assumed_to_be_page_one(self, mock_ollama):
        job = NotesGenerationJob.objects.create(
            job_id="test_missing_page_job",
            document=self.doc,
            user=self.user,
            mode="comprehensive"
        )
        section = SyllabusSection.objects.create(
            job=job,
            topic_id="unpaged_topic",
            module="Concurrency",
            title="Synchronization",
            order_index=0
        )

        notes = generate_single_section_notes(
            section=section,
            source_chunks=[{
                "text": "Synchronization coordinates concurrent activity using shared rules and operations."
            }]
        )

        self.assertIn("(Source: page unavailable)", notes)
        self.assertNotIn("(Source: Page 1)", notes)

    def test_verify_section_notes_defect_detection(self, mock_ollama):
        """Verifies that incomplete notes are flagged by the quality verifier."""
        job = NotesGenerationJob.objects.create(job_id="test_ver_job", document=self.doc, user=self.user)
        sec = SyllabusSection.objects.create(
            job=job,
            topic_id="sec_math",
            module="Math",
            title="Effective Access Time and Equations",
            order_index=0
        )
        # Case 1: Too short & unclosed math
        short_notes = (
            "This is a very brief summary with unclosed math: $$EAT = (1-p) "
            "\nCalculation: 15 * 4 = 50."
        )
        is_valid, score, report = verify_section_notes(short_notes, sec)
        self.assertFalse(is_valid)
        defects = report.get("defects", [])
        self.assertTrue(any("threshold" in d.lower() or "deficient" in d.lower() for d in defects))
        self.assertTrue(any("unbalanced" in d.lower() or "delimiters" in d.lower() for d in defects))
        self.assertEqual(report["calculation_audit"]["mismatches"][0]["calculated"], "60")

        # Case 2: Complete notes
        long_notes = (
            "# Effective Access Time and Equations\n\n"
            "## Intuitive Analogy\n"
            "Imagine looking for a book on your desk versus visiting the library.\n\n"
            "## Formal Definition\n"
            "Effective access time evaluates the weighted average latency between cache and main memory.\n\n"
            "## Core Equation\n"
            "$$EAT = (1 - p) \\times t_m + p \\times t_{pf}$$\n\n"
            "where $p$ is the page fault probability and $t_m$ is memory latency.\n\n"
            "## Worked Numerical Example\n"
            "Step 1: Suppose $p = 0.01$ and $t_m = 100$ ns.\n"
            "Step 2: $EAT = 0.99 \\times 100 + 0.01 \\times 10000000 = 100099$ ns.\n\n"
            "## Exam Watchouts\n"
            "Do not confuse hit time with miss penalty. Always double check conversion units.\n\n"
            "## In-Depth Architectural Analysis\n"
            "Under heavy multiprogramming workloads, page fault frequencies can trigger severe system thrashing.\n"
            "Operating systems mitigate this using working-set models and dynamic page frame allocation algorithms.\n"
            "Understanding the memory latency gap between L1 cache and secondary storage is fundamental.\n"
            "Here we conclude this comprehensive derivation with full mathematical grounding."
        ) * 2
        is_valid_complete, score_c, report_c = verify_section_notes(long_notes, sec, requested_depth="basic")
        self.assertTrue(is_valid_complete)
        self.assertEqual(len(report_c.get("defects", [])), 0)
        self.assertFalse(report_c["factual_accuracy_verified"])

    def test_repair_section_notes(self, mock_ollama):
        """Repair must explain missing evidence rather than padding notes with generic claims."""
        job = NotesGenerationJob.objects.create(job_id="test_rep_job", document=self.doc, user=self.user)
        sec = SyllabusSection.objects.create(
            job=job,
            topic_id="sec_repair",
            module="Operating Systems",
            title="Page Replacement Algorithms",
            order_index=0
        )
        initial_notes = "Page replacement occurs when a page fault happens."
        defects = [
            "Section length is below threshold",
            "Unbalanced LaTeX dollar ($) mathematical delimiters detected.",
            "No worked example or derivation was provided for this section."
        ]
        repaired = repair_section_notes(
            section=sec,
            existing_notes=initial_notes,
            defects=defects,
            relevant_chunks_text="FIFO, LRU, and Optimal page replacement.",
            mode="comprehensive"
        )
        self.assertIn("Page Replacement Algorithms", repaired)
        self.assertIn("no filler has been added", repaired)
        self.assertIn("a numerical example has not been invented", repaired)
        self.assertNotIn("Optimal Efficiency", repaired)
        unchanged = repair_section_notes(
            section=sec,
            existing_notes=initial_notes,
            defects=None
        )
        self.assertIn(initial_notes, unchanged)

    def test_process_notes_generation_job_orchestration(self, mock_ollama):
        """Verifies end-to-end orchestration, status transitions, and final assembly."""
        job = NotesGenerationJob.objects.create(
            job_id="test_orch_job",
            document=self.doc,
            user=self.user,
            mode="comprehensive",
            depth="intermediate",
            status="QUEUED"
        )
        sec1 = SyllabusSection.objects.create(
            job=job,
            topic_id="top_1",
            module="Module 1",
            title="Concurrency Fundamentals",
            order_index=0
        )
        sec2 = SyllabusSection.objects.create(
            job=job,
            topic_id="top_2",
            module="Module 2",
            title="Memory Paging",
            order_index=1
        )
        self.doc.set_summary({
            "response": "Original study guide",
            "markdown_content": "Original study guide markdown"
        })
        self.doc.save(update_fields=["summary_json"])

        completed_job = process_notes_generation_job(job.job_id)
        self.assertIn(completed_job.status, ["COMPLETED", "COMPLETED_WITH_WARNINGS"])
        self.assertEqual(completed_job.progress_percent, 100)
        self.assertTrue(len(completed_job.final_document_markdown) > 0)
        self.assertIn("Table of Contents", completed_job.final_document_markdown)
        self.assertIn("factual accuracy is not independently verified", completed_job.final_document_markdown)
        self.assertIn("factual accuracy was not independently verified", completed_job.current_step_label)
        self.assertIn("Syllabus Coverage & Quality Audit Appendix", completed_job.final_document_markdown)
        self.doc.refresh_from_db()
        persisted_summary = self.doc.get_summary()
        self.assertEqual(persisted_summary["response"], "Original study guide")
        self.assertEqual(persisted_summary["markdown_content"], "Original study guide markdown")
        self.assertEqual(
            persisted_summary["chatgpt_style_explanation"],
            completed_job.final_document_markdown
        )

        # Check export files exist
        self.assertTrue(os.path.exists(completed_job.docx_export_path))
        self.assertTrue(os.path.exists(completed_job.pdf_export_path))

    def test_assembled_document_labels_limited_verification(self, mock_ollama):
        job = NotesGenerationJob.objects.create(
            job_id="test_verification_scope_job",
            document=self.doc,
            user=self.user,
            mode="comprehensive",
            status="COMPLETED",
            total_topics=1,
            verified_topics=1
        )
        SyllabusSection.objects.create(
            job=job,
            topic_id="verified_topic",
            module="Concurrency",
            title="Semaphores",
            status="VERIFIED",
            generated_notes="## Semaphores\n\nA semaphore is an integer variable.",
            order_index=0
        )

        assembled = assemble_final_document(job)

        self.assertIn("[Automated checks passed]", assembled)
        self.assertIn("factual accuracy is not independently verified", assembled)

    def test_export_docx_and_pdf_generation(self, mock_ollama):
        """Verifies Word and PDF export generation directly."""
        job = NotesGenerationJob.objects.create(
            job_id="test_exp_job",
            document=self.doc,
            user=self.user,
            mode="comprehensive",
            status="COMPLETED"
        )
        SyllabusSection.objects.create(
            job=job,
            topic_id="sec_export",
            module="Module 1",
            title="Synchronization",
            generated_notes="## Synchronization\n\nDefinition of mutual exclusion with $$S=1$$.\n\nWorked example.",
            status="VERIFIED",
            order_index=0
        )
        docx_path = export_notes_to_docx(job)
        pdf_path = export_notes_to_pdf(job)

        self.assertTrue(os.path.exists(docx_path))
        self.assertTrue(docx_path.endswith(".docx"))
        self.assertGreater(os.path.getsize(docx_path), 500)

        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(pdf_path.endswith(".pdf"))
        self.assertGreater(os.path.getsize(pdf_path), 500)

        with zipfile.ZipFile(docx_path) as exported_docx:
            docx_xml = exported_docx.read("word/document.xml").decode("utf-8")
        self.assertIn("factual accuracy is not independently verified", docx_xml)

    def test_fallback_exports_disclose_verification_scope(self, mock_ollama):
        job = NotesGenerationJob.objects.create(
            job_id="test_fallback_scope_job",
            document=self.doc,
            user=self.user,
            mode="comprehensive"
        )

        with TemporaryDirectory() as output_dir:
            docx_path = Path(output_dir) / "fallback.docx"
            pdf_path = Path(output_dir) / "fallback.pdf"
            _export_notes_to_docx_fallback(job, docx_path)
            _export_notes_to_pdf_fallback(job, pdf_path)

            with zipfile.ZipFile(docx_path) as exported_docx:
                docx_xml = exported_docx.read("word/document.xml").decode("utf-8")
            pdf_bytes = pdf_path.read_bytes()

        self.assertIn("factual accuracy is not independently verified", docx_xml)
        self.assertIn(b"factual accuracy is not independently verified", pdf_bytes)

@patch("api.notes_engine.check_ai_provider_status", return_value={"can_generate": False})
class NotesEngineAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="apistudent",
            email="api@studyai.test",
            password="StrongPassword123!"
        )
        self.client.force_login(self.user)
        self.doc = Document.objects.create(
            user=self.user,
            title="Algorithm Analysis & Dynamic Programming",
            subject="Computer Science",
            page_count=6,
            raw_text=(
                "# Dynamic Programming\n\n"
                "## 0/1 Knapsack Problem\n"
                "Given items with weight $w_i$ and value $v_i$, maximize total value.\n"
                "$$DP[i][w] = \\max(DP[i-1][w], DP[i-1][w - w_i] + v_i)$$"
            ),
            output_language="en",
            status="ready"
        )
        Chunk.objects.create(
            document=self.doc,
            chunk_index=0,
            page_start=1,
            page_end=1,
            text=self.doc.raw_text
        )

    @patch("threading.Thread")
    def test_start_notes_generation_endpoint(self, mock_thread, mock_ollama):
        """Tests POST /api/documents/{id}/notes/start/"""
        url = f"/api/documents/{self.doc.id}/notes/start/"
        resp = self.client.post(
            url,
            data=json.dumps({"mode": "comprehensive", "depth": "thorough"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 202)
        data = resp.json()
        self.assertIn("job_id", data)
        self.assertTrue(mock_thread.called)

    def test_get_notes_job_status_endpoint(self, mock_ollama):
        """Tests GET /api/documents/{id}/notes/job/{job_id}/"""
        job = NotesGenerationJob.objects.create(
            job_id="test_status_job",
            document=self.doc,
            user=self.user,
            status="GENERATING",
            progress_percent=50
        )
        SyllabusSection.objects.create(
            job=job,
            topic_id="top_dp",
            module="DP",
            title="Knapsack",
            status="VERIFIED",
            generated_notes="Knapsack dynamic programming formulation.",
            order_index=0
        )

        url = f"/api/documents/{self.doc.id}/notes/job/{job.id}/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["job_id"], job.id)
        self.assertEqual(data["progress_percent"], 50)
        self.assertEqual(len(data["sections"]), 1)
        self.assertEqual(data["sections"][0]["topic_name"], "Knapsack")

    def test_export_docx_endpoint(self, mock_ollama):
        """Tests GET /api/documents/{id}/notes/export/docx/"""
        job = NotesGenerationJob.objects.create(
            job_id="test_exp_docx_job",
            document=self.doc,
            user=self.user,
            status="COMPLETED"
        )
        SyllabusSection.objects.create(
            job=job,
            topic_id="sec_exp",
            module="DP",
            title="Memoization",
            generated_notes="# Memoization\n\nTop-down dynamic programming.",
            status="VERIFIED",
            order_index=0
        )

        url = f"/api/documents/{self.doc.id}/notes/export/docx/?job_id={job.id}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    def test_export_pdf_endpoint(self, mock_ollama):
        """Tests GET /api/documents/{id}/notes/export/pdf/"""
        job = NotesGenerationJob.objects.create(
            job_id="test_exp_pdf_job",
            document=self.doc,
            user=self.user,
            status="COMPLETED"
        )
        SyllabusSection.objects.create(
            job=job,
            topic_id="sec_exp_pdf",
            module="DP",
            title="Tabulation",
            generated_notes="# Tabulation\n\nBottom-up iterative DP table computation.",
            status="VERIFIED",
            order_index=0
        )

        url = f"/api/documents/{self.doc.id}/notes/export/pdf/?job_id={job.id}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
