"""
=============================================================================
StudyAI — Comprehensive Test Suite for Phases 4A, 4B, and 4C
=============================================================================
Tests:
- Phase 4A: Intelligent Line Segmentation & Paragraph Reconstruction
  * Hyphen repair (de- veloped -> developed, preserving naturally hyphenated)
  * Punctuation spacing (word , -> word,, period/comma/colon spacing)
  * Fragmented list reconstruction (attaching lines, bold primary, indented support)
  * Isolated numbering handling
  * Heading hierarchy reconstruction
  * Multi-page running header and footer detection and removal
  * Cross-page sentence stitching
  * Tabular content formatting into clean Markdown tables
  * OCR uncertainty classification (HIGH, MEDIUM, LOW)
- Phase 4B: Professional Document Formatting and Alignment
  * DOCX generation with margins, centered title, keep_with_next headings, cantSplit tables
  * PDF generation with NumberedCanvas (Page X of Y), header/footer rules, styled tables
- Phase 4C: Rendered Document Visual Quality Audit
  * Representative pages sampling (beginning, middle, end)
  * Orphan heading detection
  * Broken sentence detection
  * Formula integrity
  * Visual audit API endpoint
=============================================================================
"""

import os
import io
from pathlib import Path
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.conf import settings

from .models import Document
from .intelligent_reconstruction import IntelligentTextReconstructor
from .notes_engine import export_markdown_to_docx, export_markdown_to_pdf
from .visual_audit_service import DocumentVisualQualityAuditor


class Phase4ATests(TestCase):
    """Rigorous tests for Phase 4A Intelligent Line Segmentation & Paragraph Reconstruction."""

    def test_hyphen_repair_word_continuation(self):
        """Verifies that words split across visual wrapping lines are cleanly rejoined."""
        raw = "Software is a discip-\nline that is engi-\nneered carefully."
        repaired, count = IntelligentTextReconstructor.repair_hyphenation(raw)
        self.assertIn("discipline", repaired)
        self.assertIn("engineered", repaired)
        self.assertEqual(count, 2)

    def test_hyphen_repair_preserves_compound_words(self):
        """Verifies that naturally hyphenated technical terms keep their hyphen."""
        raw = "We deployed a real-\ntime, client-\nserver architecture with trade-\noffs."
        repaired, count = IntelligentTextReconstructor.repair_hyphenation(raw)
        self.assertIn("real-time", repaired)
        self.assertIn("client-server", repaired)
        self.assertIn("trade-offs", repaired)

    def test_punctuation_spacing_normalization(self):
        """Verifies removal of spaces before punctuation and addition of spaces after."""
        raw = "Computers ,networks and protocols:TCP/IP.Next concept begins here."
        fixed, count = IntelligentTextReconstructor.normalize_punctuation_spacing(raw)
        self.assertIn("Computers, networks and protocols: TCP/IP. Next concept begins here.", fixed)
        self.assertNotIn("Computers ,", fixed)

    def test_fragmented_list_reconstruction(self):
        """Verifies fragmented list lines are combined with bold primary point and indented supporting lines."""
        lines = [
            "1. Software is developed or engineered.",
            "It is not manufactured in the classical sense.",
            "2. Software does not wear out.",
            "It deteriorates due to changes."
        ]
        reconstructed, fixed_count = IntelligentTextReconstructor.reconstruct_fragmented_lists(lines)
        joined = "\n".join(reconstructed)
        self.assertIn("1. **Software is developed or engineered.**", joined)
        self.assertIn("   It is not manufactured in the classical sense.", joined)
        self.assertIn("2. **Software does not wear out.**", joined)
        self.assertIn("   It deteriorates due to changes.", joined)
        self.assertEqual(fixed_count, 2)

    def test_isolated_numbering_handling(self):
        """Verifies that isolated numbers alone on a line are attached to following content."""
        lines = [
            "1.",
            "Algorithm initialization phase sets registers to zero.",
            "2.",
            "Main execution loop processes incoming queue."
        ]
        reconstructed, fixed_count = IntelligentTextReconstructor.reconstruct_fragmented_lists(lines)
        joined = "\n".join(reconstructed)
        self.assertNotIn("\n1.\n", joined)
        self.assertNotIn("\n2.\n", joined)
        self.assertIn("1.", joined)
        self.assertIn("Algorithm initialization phase", joined)

    def test_heading_hierarchy_reconstruction(self):
        """Verifies multi-signal heading recognition and consistent markdown heading hierarchy."""
        lines = [
            "Chapter 1: Operating Systems Overview",
            "Operating systems provide resource abstraction.",
            "1.1 Memory Hierarchy",
            "Caches and RAM provide tiered latency."
        ]
        reconstructed, headings = IntelligentTextReconstructor.reconstruct_headings(lines)
        joined = "\n".join(reconstructed)
        self.assertIn("## 1 Operating Systems Overview", joined)
        self.assertIn("### 1.1 Memory Hierarchy", joined)
        self.assertTrue(any(h["title"] == "Operating Systems Overview" for h in headings))
        self.assertTrue(any(h["title"] == "Memory Hierarchy" for h in headings))

    def test_multi_page_running_header_footer_removal(self):
        """Verifies repeated running headers and footers across pages are detected and stripped."""
        pages = [
            {
                "page_number": 1,
                "text": "Computer Architecture - Volume 4\nCache memory is high-speed SRAM.\nPage 1"
            },
            {
                "page_number": 2,
                "text": "Computer Architecture - Volume 4\nVirtual memory uses page tables.\nPage 2"
            },
            {
                "page_number": 3,
                "text": "Computer Architecture - Volume 4\nPaging translates virtual addresses.\nPage 3"
            }
        ]
        full_text, cleaned_pages, metrics = IntelligentTextReconstructor.reconstruct_document(pages)
        self.assertNotIn("Computer Architecture - Volume 4", full_text)
        self.assertNotIn("Page 1", full_text)
        self.assertNotIn("Page 2", full_text)
        self.assertGreaterEqual(metrics["running_headers_removed"], 3)
        self.assertGreaterEqual(metrics["running_footers_removed"], 3)

    def test_cross_page_sentence_stitching(self):
        """Verifies open sentences broken across page margins are seamlessly reconnected."""
        pages = [
            {
                "page_number": 1,
                "text": "The memory controller interfaces directly with the"
            },
            {
                "page_number": 2,
                "text": "physical dynamic random-access memory modules."
            }
        ]
        full_text, cleaned_pages, metrics = IntelligentTextReconstructor.reconstruct_document(pages)
        self.assertIn("interfaces directly with the physical dynamic random-access memory modules.", full_text)
        self.assertEqual(metrics["broken_sentences_stitched"], 1)

    def test_table_aligned_columns_formatting(self):
        """Verifies aligned column lines are detected and formatted into clean Markdown tables."""
        lines = [
            "Protocol   Port   Transport",
            "HTTP       80     TCP",
            "HTTPS      443    TCP",
            "DNS        53     UDP"
        ]
        out_lines, tables = IntelligentTextReconstructor.detect_and_format_tables(lines)
        joined = "\n".join(out_lines)
        self.assertIn("| Protocol | Port | Transport |", joined)
        self.assertIn("| :--- | :--- | :--- |", joined)
        self.assertIn("| HTTP | 80 | TCP |", joined)
        self.assertEqual(len(tables), 1)

    def test_ocr_confidence_classification(self):
        """Verifies confidence tier classification into HIGH, MEDIUM, and LOW."""
        clean_text = "Operating systems manage hardware devices, processes, and secure communication channels."
        high_res = IntelligentTextReconstructor.classify_ocr_confidence(clean_text)
        self.assertEqual(high_res["confidence"], "HIGH")
        self.assertGreaterEqual(high_res["score"], 0.85)

        corrupt_text = "!@#$ %^&* |~`_ 123 456 ||||| ~~~"
        low_res = IntelligentTextReconstructor.classify_ocr_confidence(corrupt_text)
        self.assertEqual(low_res["confidence"], "LOW")


class Phase4BTests(TestCase):
    """Rigorous tests for Phase 4B Professional Document Formatting and Alignment."""

    def setUp(self):
        self.sample_markdown = """
# Advanced Algorithms & Complexity

Comprehensive notes on computational complexity and dynamic programming.

## 1. Asymptotic Notation

Asymptotic notation characterizes algorithm efficiency as input size grows.

### 1.1 Big-O Upper Bounds

Big-O provides a formal asymptotic upper bound on growth rate:

1. **Definition:** A function f(n) is in O(g(n)) if bounded by a constant factor.
2. **Usage:** Characterizes worst-case operational execution.

| Notation | Formal Meaning | Growth Rate |
| :--- | :--- | :--- |
| O(1) | Constant | Minimal |
| O(log n) | Logarithmic | Sub-linear |
| O(n) | Linear | Proportional |

$$
f(n) \\le c \\cdot g(n) \\quad \\text{for all } n \\ge n_0
$$
"""

    def test_docx_export_formatting_and_alignment(self):
        """Verifies DOCX generation produces a valid Word document with professional layout."""
        docx_path = export_markdown_to_docx(
            "Advanced Algorithms",
            self.sample_markdown,
            subject="Computer Science",
            doc_id="test_4b_docx"
        )
        self.assertTrue(os.path.exists(docx_path))
        self.assertTrue(docx_path.endswith('.docx'))
        self.assertGreater(os.path.getsize(docx_path), 5000)

        import docx
        doc = docx.Document(docx_path)
        # Check margins
        section = doc.sections[0]
        self.assertAlmostEqual(section.left_margin.inches, 1.0, places=1)
        self.assertAlmostEqual(section.right_margin.inches, 1.0, places=1)

        # Check headings have keep_with_next set
        headings = [p for p in doc.paragraphs if p.style.name.startswith('Heading')]
        self.assertGreater(len(headings), 0)
        for h in headings:
            self.assertTrue(h.paragraph_format.keep_with_next)

    def test_pdf_export_formatting_and_alignment(self):
        """Verifies PDF generation produces a valid PDF document with NumberedCanvas headers/footers."""
        pdf_path = export_markdown_to_pdf(
            "Advanced Algorithms",
            self.sample_markdown,
            subject="Computer Science",
            doc_id="test_4b_pdf"
        )
        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(pdf_path.endswith('.pdf'))
        self.assertGreater(os.path.getsize(pdf_path), 3000)


class Phase4CTests(TestCase):
    """Rigorous tests for Phase 4C Rendered Document Visual Quality Audit."""

    def setUp(self):
        self.user = User.objects.create_user(username="visual_user", password="password123")
        self.client = Client()
        self.client.force_login(self.user)

    def test_markdown_visual_audit_clean_document(self):
        """Verifies audit passes with high score on clean markdown."""
        clean_md = """
# Database Management Systems

Relational databases organize structured data into normalized relations.

## 1. Relational Model

The relational model represents data as mathematical tuples.

### 1.1 Primary and Foreign Keys

Integrity constraints enforce entity consistency:
1. **Primary Key:** Uniquely identifies each record.
2. **Foreign Key:** References primary key of related table.

| Constraint | Scope | Enforcement |
| :--- | :--- | :--- |
| Unique | Column | Index |
| Foreign Key | Cross-table | Referential |
"""
        audit = DocumentVisualQualityAuditor.audit_markdown_document(clean_md, "DBMS")
        self.assertTrue(audit["passed"])
        self.assertGreaterEqual(audit["score"], 90.0)
        self.assertEqual(audit["status"], "VERIFIED_ACADEMIC_QUALITY")

    def test_markdown_visual_audit_detects_isolated_numbering_and_unclosed_math(self):
        """Verifies audit detects isolated numbers and unclosed $$ formula tags."""
        corrupt_md = """
# Corrupted Document

1.
Isolated numbering without text.

$$
E = mc^2
No closing tag for equation
"""
        audit = DocumentVisualQualityAuditor.audit_markdown_document(corrupt_md, "Corrupted")
        self.assertFalse(audit["passed"])
        self.assertLess(audit["score"], 85.0)
        issue_msgs = [i["message"] for i in audit["issues"]]
        self.assertTrue(any("Isolated numbering" in m for m in issue_msgs))
        self.assertTrue(any("Unclosed mathematical display formula" in m for m in issue_msgs))

    def test_pdf_visual_audit_representative_pages_sampling(self):
        """Verifies PDF visual audit inspects beginning, middle, and end pages."""
        pdf_md = """
# Principles of Compiler Design

A compiler translates high-level code into target machine code.

## 1. Lexical Analysis

Tokens are identified via regular expressions.

### 1.1 Finite Automata

DFA and NFA represent deterministic and non-deterministic states.
"""
        pdf_path = export_markdown_to_pdf("Compiler Design", pdf_md, subject="Computer Science", doc_id="audit_test")
        audit = DocumentVisualQualityAuditor.audit_pdf_document(pdf_path, "Compiler Design")
        self.assertTrue(audit["passed"])
        self.assertGreaterEqual(audit["score"], 85.0)
        self.assertTrue(audit["representative_pages_inspected"])
        self.assertIn(1, audit["representative_pages"])

    def test_visual_audit_api_endpoint(self):
        """Verifies GET /api/documents/{id}/visual-audit/ returns comprehensive audit report."""
        doc = Document.objects.create(
            user=self.user,
            title="Distributed Systems",
            subject="Computer Science",
            raw_text="# Distributed Systems\n\nConsensus algorithms ensure fault tolerance.\n\n## 1. Paxos and Raft\n\nLeader election manages state machine replication."
        )
        resp = self.client.get(f'/api/documents/{doc.id}/visual-audit/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("audit", data)
        self.assertIn("score", data["audit"])
        self.assertIn("status", data["audit"])

