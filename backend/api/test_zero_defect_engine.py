"""
=============================================================================
StudyAI — Zero-Defect Document Engine Comprehensive Test Suite (Phase 6)
=============================================================================
Verifies all 8 stages of the Zero-Defect Document Verification Engine:
- Stage A: Source text & classification integrity (16 standard element types)
- Stage B: Semantic document structure & heading hierarchy
- Stage C: Content completeness, coverage mapping & duplicate detection
- Stage D: Mathematical typesetting & 10-part problem structure
- Stage E: Typography, table formatting & alignment
- Stage F: Visual page inspection via 150 DPI pixmaps
- Stage G: Automated defect correction loop
- Stage H: Honest Quality Report certification (READY vs NEEDS_CORRECTION)
=============================================================================
"""

import os
import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Document, Chunk
from .typography_system import DocumentTypography
from .zero_defect_engine import ZeroDefectDocumentEngine, DocumentElementType


class ZeroDefectEngineTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="zerodefect_user", password="password123")
        self.client = Client()
        self.client.force_login(self.user)

        self.doc = Document.objects.create(
            user=self.user,
            title="Operating Systems Memory Management",
            subject="Computer Science & Engineering",
            raw_text="Operating Systems\nMemory Management and Paging Systems.\nPaging is a memory management scheme."
        )

        Chunk.objects.create(
            document=self.doc,
            chunk_index=0,
            page_start=1,
            page_end=1,
            text="# Operating Systems\nMemory Management is essential."
        )
        Chunk.objects.create(
            document=self.doc,
            chunk_index=1,
            page_start=2,
            page_end=2,
            text="## Paging Mechanism\nPage tables translate logical addresses."
        )

    # -------------------------------------------------------------------------
    # STAGE A: Source Validation & Element Classification
    # -------------------------------------------------------------------------
    def test_stage_a_source_validation_and_classification(self):
        pages_data = [
            {
                "page_number": 1,
                "text": "Module 1: Operating Systems\n\n1. Process Management:\nProcesses execute sequentially.\n- State 1\n- State 2\n\n| Process | Burst |\n|---|---|\n| P1 | 10 |\n\n$$E = mc^2$$\n\nFigure 1: Architecture\nHeader: VTU Notes\nFooter: Page 1",
                "ocr_confidence": 0.95
            },
            {
                "page_number": 2,
                "text": "Low quality scanned page with faint ink.",
                "ocr_confidence": 0.55  # Below 0.70 threshold
            }
        ]

        result = ZeroDefectDocumentEngine.validate_source_extraction(pages_data, "Sample output markdown")

        self.assertEqual(result["total_pages"], 2)
        self.assertEqual(len(result["low_confidence_pages"]), 1)
        self.assertEqual(result["low_confidence_pages"][0]["page"], 2)
        self.assertGreater(result["total_characters"], 50)
        self.assertGreater(result["total_words"], 10)

        # Verify element classifications
        classification = result["element_classification"]
        self.assertIn("MODULE_TITLE", classification)
        self.assertIn("TABLE", classification)
        self.assertIn("FORMULA", classification)
        self.assertIn("NUMBERED_LIST", classification)
        self.assertIn("BULLET_LIST", classification)

    # -------------------------------------------------------------------------
    # STAGE B: Semantic Heading Hierarchy
    # -------------------------------------------------------------------------
    def test_stage_b_semantic_headings_and_hierarchy_clean(self):
        clean_md = """# Operating Systems & Architecture

## Module 1: Process Synchronization
### Critical Section Problem
#### Peterson's Algorithm
Peterson's algorithm provides a software solution for two processes.

### Semaphores
Semaphores are integer synchronization variables.
"""
        res = ZeroDefectDocumentEngine.validate_semantic_headings(clean_md, "Operating Systems & Architecture", "Computer Science")
        self.assertTrue(res["passed"])
        self.assertEqual(len(res["issues"]), 0)
        self.assertEqual(len(res["hierarchy"]), 5)

    def test_stage_b_semantic_headings_flags_skipped_level_and_raw_slug(self):
        flawed_md = """# vtu-os-module1-notes-2024.pdf

## Module 1: Processes
#### Deep Subsection Skipping H3
This section skipped H3 heading.

## Module 1: Processes
Duplicate heading consecutive.

### Empty Subsection
"""
        res = ZeroDefectDocumentEngine.validate_semantic_headings(flawed_md, "vtu-os-module1-notes-2024.pdf", "General")
        self.assertFalse(res["passed"])
        issue_msgs = [i["message"] for i in res["issues"]]

        # 1. Raw slug rejected
        self.assertTrue(any("raw filename" in m.lower() or "slug" in m.lower() for m in issue_msgs))
        # 2. Skipped level (H2 to H4)
        self.assertTrue(any("skipped heading level" in m.lower() or "inconsistent hierarchy" in m.lower() for m in issue_msgs))
        # 3. Duplicate consecutive heading
        self.assertTrue(any("duplicate" in m.lower() for m in issue_msgs))
        # 4. Empty heading without content
        self.assertTrue(any("empty" in m.lower() or "content" in m.lower() for m in issue_msgs))

    # -------------------------------------------------------------------------
    # STAGE C: Content Coverage & Duplication Mapping
    # -------------------------------------------------------------------------
    def test_stage_c_content_coverage_and_duplicate_detection(self):
        source_topics = [
            {"topic": "Process Synchronization", "module": "Module 1"},
            {"topic": "Deadlock Avoidance and Prevention", "module": "Module 2"},
            {"topic": "Quantum Computing Superposition", "module": "Module 3"}  # Not in output
        ]

        duplicate_paragraph = "Critical section execution requires mutual exclusion, progress, and bounded waiting across threads. " * 3

        output_md = f"""# Operating Systems Notes

## Module 1: Process Synchronization
Process synchronization ensures that concurrently executing processes do not produce race conditions on shared data.

### Deadlock Avoidance
Deadlock avoidance uses Banker's algorithm to ensure the system never enters an unsafe state.

### Redundant Topic Section
{duplicate_paragraph}

### Duplicate Section Repeated
{duplicate_paragraph}
"""
        res = ZeroDefectDocumentEngine.validate_content_coverage_and_duplication(source_topics, output_md)

        # Verify coverage statuses
        statuses = [item["status"] for item in res["coverage_map"]]
        self.assertIn("PRESENT", statuses)
        self.assertIn("MISSING", statuses)
        self.assertEqual(res["topics_missing"], 1)

        # Verify duplicate detection (SequenceMatcher)
        self.assertGreaterEqual(res["duplicate_paragraph_count"], 1)
        self.assertFalse(res["passed"])

    # -------------------------------------------------------------------------
    # STAGE D: Mathematical Typesetting
    # -------------------------------------------------------------------------
    def test_stage_d_mathematical_typesetting_delimiters_and_derivation(self):
        clean_math_md = """# Memory Calculations

## Effective Access Time
For a paging system with hit ratio $\alpha$:

$$EAT = \alpha \times (t_{TLB} + t_{mem}) + (1 - \alpha) \times (t_{TLB} + 2 \times t_{mem})$$

### Calculation:
- **Given Parameters**: Hit ratio $\alpha = 0.8$, $t_{mem} = 100$ ns.
- **Formula**: $$EAT = 0.8 \times 100 + 0.2 \times 200 = 80 + 40 = 120$$ ns.
- **Final Result**: $120$ ns.
"""
        res = ZeroDefectDocumentEngine.validate_mathematical_typesetting(clean_math_md)
        self.assertTrue(res["passed"])
        self.assertTrue(res["contains_math"])

    def test_stage_d_mathematical_typesetting_flags_unclosed_delimiters(self):
        unclosed_math_md = """# Flawed Math Notes

Here is an unclosed formula $$E = mc^2 and some text.

And another unclosed $x + y = 10 without closing dollar.
"""
        res = ZeroDefectDocumentEngine.validate_mathematical_typesetting(unclosed_math_md)
        self.assertFalse(res["passed"])
        issue_msgs = [i["message"] for i in res["issues"]]
        self.assertTrue(any("unclosed" in m.lower() and "delimiter" in m.lower() for m in issue_msgs))

    # -------------------------------------------------------------------------
    # STAGE E: Typography & Formatting Integrity
    # -------------------------------------------------------------------------
    def test_stage_e_typography_and_formatting(self):
        flawed_formatting_md = """# Operating Systems Guide

1.
Isolated number without sentence.

| Header 1 | Header 2 | Header 3 |
|---|---|---|
| Row 1 Col 1 | Row 1 Col 2 |
| Row 2 Col 1 | Row 2 Col 2 | Row 2 Col 3 |




Excessive blank lines above.
"""
        res = ZeroDefectDocumentEngine.validate_typography_and_formatting(flawed_formatting_md, "Operating Systems Guide")
        self.assertFalse(res["passed"])
        issue_msgs = [i["message"] for i in res["issues"]]

        self.assertTrue(any("isolated" in m.lower() and "number" in m.lower() for m in issue_msgs))
        self.assertTrue(any("inconsistent column" in m.lower() for m in issue_msgs))
        self.assertTrue(any("excessive consecutive blank lines" in m.lower() for m in issue_msgs))

    # -------------------------------------------------------------------------
    # STAGE F: Rendered Document Visual Quality
    # -------------------------------------------------------------------------
    def test_stage_f_rendered_document_inspection(self):
        clean_md = """# Operating Systems Masterclass

## Module 1: Memory Architecture
Memory management is the functionality of an operating system which handles or manages primary memory.

| Property | Value |
|---|---|
| Page Size | 4 KB |
| Frame Count | 1024 |

$$EAT = 120\text{ ns}$$
"""
        from .notes_engine import export_markdown_to_pdf
        pdf_path = export_markdown_to_pdf("Operating Systems Masterclass", clean_md, "Computer Science", doc_id="test_stage_f")
        self.assertTrue(os.path.exists(pdf_path))

        res = ZeroDefectDocumentEngine.validate_rendered_document(pdf_path, "Operating Systems Masterclass")
        self.assertTrue(res["passed"])
        self.assertGreater(res["total_pages"], 0)
        self.assertTrue(len(res["representative_pages_inspected"]) >= 1)

    # -------------------------------------------------------------------------
    # STAGE G & H: Automated Repair & Master Certification Loop
    # -------------------------------------------------------------------------
    def test_stage_g_and_h_correction_and_certification(self):
        flawed_md = """# VTU Notes

## Module 1: Process Management
1.
CPU scheduling algorithms decide which process runs.

Unclosed formula $$T_{avg} = 15\text{ ms}

```python
def schedule():
    return "FCFS"




Excessive blank lines here.
"""
        result = ZeroDefectDocumentEngine.audit_and_certify_document(
            markdown_text=flawed_md,
            doc_title="VTU Operating Systems Notes",
            subject="Computer Science",
            source_topics=[{"topic": "Process Management", "module": "Module 1"}],
            doc_id="test_cert_loop"
        )

        # Honest quality report assertions
        honest = result["honest_quality_report"]
        self.assertIn(honest["final_document_status"], ("READY", "NEEDS_CORRECTION"))
        self.assertGreater(honest["defects_corrected_count"], 0)
        self.assertTrue(any("unclosed" in r.lower() and "$$" in r for r in result["repairs_applied"]))
        self.assertTrue(any("isolated number" in r.lower() for r in result["repairs_applied"]))
        self.assertTrue(os.path.exists(result["pdf_export_path"]))
        self.assertTrue(os.path.exists(result["docx_export_path"]))

    # -------------------------------------------------------------------------
    # API ENDPOINT VERIFICATION
    # -------------------------------------------------------------------------
    def test_zero_defect_audit_api_endpoints(self):
        # 1. GET endpoint
        url_get = f"/api/documents/{self.doc.id}/zero-defect-audit/"
        response = self.client.get(url_get)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(str(data["document_id"]), str(self.doc.id))
        self.assertIn("certification", data)
        self.assertIn("honest_quality_report", data["certification"])

        # 2. POST endpoint (with repair application)
        url_post = f"/api/documents/{self.doc.id}/zero-defect-audit/"
        post_response = self.client.post(url_post)
        self.assertEqual(post_response.status_code, 200)
        post_data = post_response.json()
        self.assertTrue(post_data["success"])

        # 3. Versioned v1 route
        url_v1 = f"/api/v1/materials/{self.doc.id}/zero-defect-audit"
        v1_resp = self.client.get(url_v1)
        self.assertEqual(v1_resp.status_code, 200)
        self.assertTrue(v1_resp.json()["success"])
