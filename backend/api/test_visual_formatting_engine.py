"""
Unit and Integration Test Suite for StudyAI Phase 5:
Professional Typography, Document Alignment & Visual Formatting Accuracy Engine.
"""

import os
import re
from pathlib import Path
from django.test import TestCase
from django.conf import settings
from .notes_engine import (
    resolve_clean_academic_title,
    detect_callout_type,
    export_markdown_to_docx,
    export_markdown_to_pdf
)
from .visual_audit_service import DocumentVisualQualityAuditor


class VisualFormattingAccuracyEngineTests(TestCase):
    """Test suite validating Phase 5 typography, document alignment, and visual QC."""

    def setUp(self):
        self.sample_markdown = """# Chapter 1: INTRODUCTION TO SOFTWARE PROCESS

Software Engineering is an analytical and disciplined approach to computer software development.

## 1.1 The Nature of Software

Software is custom engineered rather than manufactured in the classical industrial sense.

### 1.1.1 Software Characteristics

Software exhibits fundamental differences from hardware:
1. Software does not wear out over time.
2. Software is custom built in many application environments.
3. Software complexity increases exponentially with scale.

> **Definition:** Software comprises executable programs, associated data structures, and operational documentation.

> **Important:** Unlike hardware, software failures are caused by design defects rather than physical wear.

> **Exam Tip:** Clearly distinguish software engineering from routine computer programming for 5 marks.

| Characteristic | Hardware | Software |
| :--- | :--- | :--- |
| Wear mechanism | Physical degradation | Latent design defects |
| Manufacturing | Assembly-line based | Custom engineered |
| Failure curve | Bathtub curve | Inflection curve |

$$
E = a \times (KLOC)^b
$$

$$\\begin{aligned}
S &= v_0 t + \\frac{1}{2} a t^2 \\\\
S &= (0)(10) + \\frac{1}{2}(9.8)(10)^2 \\\\
S &= 490 \\text{ m}
\\end{aligned}$$
"""

    def test_resolve_clean_academic_title(self):
        """1. Verifies filename slugs are never used as document titles when genuine subject titles exist."""
        # Test 1: BCS501 benchmark filename slug with document text
        doc_text = "SOFTWARE ENGINEERING AND PROJECT MANAGEMENT (BCS501)\n\nMODULE –1\nCHAPTER 1 --INTRODUCTION"
        resolved_title = resolve_clean_academic_title(
            title="BCS501-module-1-pdf.pdf",
            text=doc_text,
            subject="Software Engineering & Project Management"
        )
        self.assertEqual(resolved_title, "SOFTWARE ENGINEERING AND PROJECT MANAGEMENT")

        # Test 2: Raw slug falling back to clean subject
        resolved_fallback = resolve_clean_academic_title(
            title="module_1_notes.docx",
            text="",
            subject="Computer Networks"
        )
        self.assertEqual(resolved_fallback, "Computer Networks")

        # Test 3: Genuine title preserved cleanly
        resolved_clean = resolve_clean_academic_title(
            title="Database Management Systems",
            text="",
            subject="Computer Science"
        )
        self.assertEqual(resolved_clean, "Database Management Systems")

    def test_detect_callout_type(self):
        """2. Verifies semantic callout detection for Definition, Example, Important, Formula, and Exam Tip."""
        # Definition
        ctype, ctext, b_hex, f_hex = detect_callout_type("> **Definition:** Software is a program.")
        self.assertEqual(ctype, "DEFINITION")
        self.assertIn("Software is a program", ctext)
        self.assertEqual(b_hex, "#4F46E5")

        # Important
        ctype, ctext, b_hex, f_hex = detect_callout_type("> **Important:** Do not wear out.")
        self.assertEqual(ctype, "IMPORTANT")
        self.assertEqual(b_hex, "#F59E0B")

        # Exam Tip
        ctype, ctext, b_hex, f_hex = detect_callout_type("> **Exam Tip:** Draw Waterfall model.")
        self.assertEqual(ctype, "EXAM_TIP")
        self.assertEqual(b_hex, "#10B981")

        # Formula
        ctype, ctext, b_hex, f_hex = detect_callout_type("> **Formula:** E = mc^2")
        self.assertEqual(ctype, "FORMULA")
        self.assertEqual(b_hex, "#7C3AED")

    def test_docx_export_phase5_typography_and_layout(self):
        """3. Verifies DOCX export adheres to A4 size, 1-inch margins, Arial font, and keep_with_next."""
        docx_path = export_markdown_to_docx(
            "BCS501-module-1-pdf.pdf",
            self.sample_markdown,
            subject="Software Engineering & Project Management",
            doc_id="test_phase5_docx"
        )
        self.assertTrue(os.path.exists(docx_path))
        self.assertTrue(docx_path.endswith('.docx'))
        self.assertGreater(os.path.getsize(docx_path), 5000)

        import docx
        doc = docx.Document(docx_path)
        section = doc.sections[0]

        # Verify A4 Page Dimensions (8.27 in x 11.69 in) and 1.0 inch margins
        self.assertAlmostEqual(section.page_width.inches, 8.27, places=1)
        self.assertAlmostEqual(section.page_height.inches, 11.69, places=1)
        self.assertAlmostEqual(section.left_margin.inches, 1.0, places=1)
        self.assertAlmostEqual(section.right_margin.inches, 1.0, places=1)

        # Verify title does NOT contain raw .pdf extension
        first_p = doc.paragraphs[0]
        self.assertNotIn(".pdf", first_p.text)

        # Verify keep_with_next on all heading paragraphs
        headings = [p for p in doc.paragraphs if p.style.name.startswith('Heading')]
        self.assertGreater(len(headings), 0)
        for h in headings:
            self.assertTrue(h.paragraph_format.keep_with_next)

        # Verify tables have cantSplit and tblHeader
        self.assertGreater(len(doc.tables), 0)

    def test_pdf_export_phase5_typography_and_layout(self):
        """4. Verifies PDF export adheres to A4 dimensions, balanced margins, and NumberedCanvas decorations."""
        pdf_path = export_markdown_to_pdf(
            "BCS501-module-1-pdf.pdf",
            self.sample_markdown,
            subject="Software Engineering & Project Management",
            doc_id="test_phase5_pdf"
        )
        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(pdf_path.endswith('.pdf'))
        self.assertGreater(os.path.getsize(pdf_path), 5000)

        # Inspect PDF with PyMuPDF
        import pymupdf as fitz
        doc = fitz.open(pdf_path)
        self.assertGreater(len(doc), 0)

        # Verify A4 dimensions (595.28 pt x 841.89 pt approx)
        page0 = doc[0]
        self.assertAlmostEqual(page0.rect.width, 595.28, delta=2.0)
        self.assertAlmostEqual(page0.rect.height, 841.89, delta=2.0)

        # Verify title on first page does not contain raw .pdf
        p0_text = page0.get_text("text")
        self.assertNotIn("BCS501-module-1-pdf.pdf", p0_text)

    def test_visual_audit_representative_pixmaps_generation(self):
        """5. Verifies 150 DPI representative page images are rendered and inspected."""
        pdf_path = export_markdown_to_pdf(
            "Software Architecture",
            self.sample_markdown,
            subject="Computer Science",
            doc_id="test_pixmaps"
        )
        audit = DocumentVisualQualityAuditor.audit_pdf_document(pdf_path, "Software Architecture")
        self.assertTrue(audit["passed"])
        self.assertGreaterEqual(audit["score"], 85.0)
        self.assertTrue(audit["representative_pages_inspected"])
        self.assertGreater(len(audit["representative_pixmaps"]), 0)

        pixmap = audit["representative_pixmaps"][0]
        self.assertEqual(pixmap["dpi"], 150)
        self.assertGreater(pixmap["width"], 0)
        self.assertGreater(pixmap["height"], 0)
        self.assertEqual(pixmap["status"], "RENDERED_CLEAR")

    def test_visual_audit_category_scores_breakdown(self):
        """6. Verifies all 5 Phase 5 QC categories (Structural, Typography, Alignment, Pagination, Content) are computed."""
        audit = DocumentVisualQualityAuditor.audit_markdown_document(self.sample_markdown, "Software Engineering")
        self.assertTrue(audit["passed"])
        self.assertIn("category_scores", audit)
        scores = audit["category_scores"]
        self.assertIn("structural", scores)
        self.assertIn("typography", scores)
        self.assertIn("alignment", scores)
        self.assertIn("pagination", scores)
        self.assertIn("content_preservation", scores)
        self.assertGreaterEqual(scores["structural"], 15.0)
        self.assertGreaterEqual(scores["typography"], 15.0)
        self.assertGreaterEqual(scores["alignment"], 15.0)
        self.assertGreaterEqual(scores["pagination"], 15.0)
        self.assertGreaterEqual(scores["content_preservation"], 15.0)

    def test_render_inspect_correct_render_loop(self):
        """7. Verifies the Render-Inspect-Correct-Render loop auto-repairs defects and re-audits cleanly."""
        corrupted_markdown = """# Software Engineering Principles

Software engineering applies systematic engineering approaches.

## 1. Process Framework

1.
Communication with stakeholders.

$$
E = mc^2
"""
        initial_pdf = export_markdown_to_pdf(
            "Software Engineering Principles",
            corrupted_markdown,
            subject="Computer Science",
            doc_id="test_loop_corrupt"
        )

        loop_audit = DocumentVisualQualityAuditor.audit_and_correct_pdf_document(
            pdf_path=initial_pdf,
            markdown_text=corrupted_markdown,
            doc_title="Software Engineering Principles",
            subject="Computer Science",
            doc_id="test_loop_corrupt",
            max_iterations=2
        )

        self.assertTrue(loop_audit["passed"])
        self.assertGreaterEqual(loop_audit["score"], 85.0)
        self.assertGreaterEqual(len(loop_audit["repairs_applied"]), 1)
        self.assertTrue(os.path.exists(loop_audit["final_pdf_path"]))
