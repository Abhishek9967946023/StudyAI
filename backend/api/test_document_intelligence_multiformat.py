"""
Unit and integration tests for Multi-Format Ingestion (PDF, DOCX, PPTX, PNG, JPG, WEBP, TXT)
and Document Intelligence Classification and Prompt Generation.
"""

import io
import zipfile
from unittest.mock import patch
from django.test import TestCase
from PIL import Image

from api.document_service import (
    validate_file_content_signature,
    extract_text_from_pptx,
    extract_study_material,
    extract_text_from_image,
    ALLOWED_EXTENSIONS
)
from api.prompt_templates import (
    classify_document_genre,
    build_document_intelligence_prompt,
    DOCUMENT_TYPE_STRUCTURES,
    MASTER_DOCUMENT_INTELLIGENCE_PROMPT
)


class MultiFormatIngestionTests(TestCase):
    def test_allowed_extensions_includes_all_required_formats(self):
        expected = {'pdf', 'docx', 'pptx', 'txt', 'md', 'png', 'jpg', 'jpeg', 'webp'}
        self.assertTrue(expected.issubset(ALLOWED_EXTENSIONS))

    def test_validate_image_signatures(self):
        # 1. Valid PNG
        png_io = io.BytesIO()
        img = Image.new('RGB', (100, 100), color='white')
        img.save(png_io, format='PNG')
        png_bytes = png_io.getvalue()
        is_valid, msg = validate_file_content_signature(png_bytes, 'png')
        self.assertTrue(is_valid, msg)

        # 2. Corrupt PNG
        is_valid, msg = validate_file_content_signature(b'\x89PNG\r\n\x1a\ncorrupteddata', 'png')
        self.assertFalse(is_valid)

        # 3. Valid JPEG
        jpg_io = io.BytesIO()
        img.save(jpg_io, format='JPEG')
        jpg_bytes = jpg_io.getvalue()
        is_valid, msg = validate_file_content_signature(jpg_bytes, 'jpg')
        self.assertTrue(is_valid, msg)

        # 4. Valid WebP
        webp_io = io.BytesIO()
        img.save(webp_io, format='WEBP')
        webp_bytes = webp_io.getvalue()
        is_valid, msg = validate_file_content_signature(webp_bytes, 'webp')
        self.assertTrue(is_valid, msg)

    def test_pptx_native_xml_fallback(self):
        # Create a synthetic PPTX zip archive containing slide XML
        pptx_io = io.BytesIO()
        with zipfile.ZipFile(pptx_io, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<Types></Types>')
            zf.writestr('ppt/presentation.xml', '<presentation></presentation>')
            slide1_xml = (
                '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                '<p:cSld><p:spTree><p:sp><p:txBody>'
                '<a:p><a:r><a:t>Introduction to Computer Networks</a:t></a:r></a:p>'
                '<a:p><a:r><a:t>Layer 1: Physical Layer</a:t></a:r></a:p>'
                '</p:txBody></p:sp></p:spTree></p:cSld></p:sld>'
            )
            slide2_xml = (
                '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                '<p:cSld><p:spTree><p:sp><p:txBody>'
                '<a:p><a:r><a:t>Layer 2: Data Link Layer and Ethernet</a:t></a:r></a:p>'
                '</p:txBody></p:sp></p:spTree></p:cSld></p:sld>'
            )
            zf.writestr('ppt/slides/slide1.xml', slide1_xml)
            zf.writestr('ppt/slides/slide2.xml', slide2_xml)

        pptx_bytes = pptx_io.getvalue()

        # Validate signature
        is_valid, msg = validate_file_content_signature(pptx_bytes, 'pptx')
        self.assertTrue(is_valid, msg)

        # Extract text
        text, pages_data, count = extract_text_from_pptx(pptx_bytes)
        self.assertEqual(count, 2)
        self.assertIn("Introduction to Computer Networks", text)
        self.assertIn("Layer 2: Data Link Layer and Ethernet", text)
        self.assertEqual(len(pages_data), 2)
        self.assertEqual(pages_data[0]["page_number"], 1)
        self.assertEqual(pages_data[1]["page_number"], 2)


class DocumentIntelligenceClassificationTests(TestCase):
    def test_classify_legal_genre(self):
        legal_text = """
        CONFIDENTIALITY AND NON-DISCLOSURE AGREEMENT
        This Agreement is entered into by and between the parties hereto.
        Whereas, recipient agrees to indemnify and hold harmless the disclosing party.
        Section 12: Governing law and arbitration jurisdiction under the State of California.
        Breach of this clause shall result in liquidated damages and termination.
        """
        genre = classify_document_genre(legal_text, "NDA Agreement.pdf")
        self.assertEqual(genre, "LEGAL")

    def test_classify_research_genre(self):
        research_text = """
        Abstract: We investigate neural algorithmic reasoning on graph tasks.
        Methodology: We evaluate benchmark datasets using cross-entropy loss and ablation studies.
        Baseline comparisons demonstrate statistically significant improvements with p < 0.01.
        Future work and experimental limitations are discussed in the discussion section.
        """
        genre = classify_document_genre(research_text, "arXiv_paper.pdf")
        self.assertEqual(genre, "RESEARCH")

    def test_classify_business_genre(self):
        business_text = """
        Q3 Financial Performance Report & Executive Summary
        Quarterly revenue grew by 14% year-over-year, achieving $45M in ARR.
        EBITDA margins improved by 230 basis points. Market share risks and competitive opportunities
        for customer acquisition cost (CAC) optimization are outlined below.
        """
        genre = classify_document_genre(business_text, "Q3 Earnings Report.docx")
        self.assertEqual(genre, "BUSINESS")

    def test_classify_technical_genre(self):
        tech_text = """
        Kubernetes Microservices Architecture & Deployment Manual
        System configuration requires configuring API endpoints, container registries,
        and setting environment variables in deployment.yaml.
        Troubleshooting: If pod restarts with CrashLoopBackOff, inspect logs with kubectl logs.
        """
        genre = classify_document_genre(tech_text, "System Architecture Guide.pdf")
        self.assertEqual(genre, "TECHNICAL")

    def test_classify_academic_genre(self):
        academic_text = """
        Formal Languages and Automata Theory - Chapter 3
        Theorem 3.4: A language L is regular if and only if it is accepted by a deterministic finite automaton.
        Proof: By structural induction on regular expressions.
        Definition: The transition function δ: Q × Σ → Q satisfies the following invariant.
        """
        genre = classify_document_genre(academic_text, "Automata Theory Notes.pdf")
        self.assertEqual(genre, "ACADEMIC")

    def test_build_prompt_includes_grounding_rules_and_interrogation(self):
        prompt = build_document_intelligence_prompt(
            doc_title="Cloud Security Fundamentals",
            doc_genre="TECHNICAL",
            source_context="Identity and Access Management controls access to resources.",
            depth="exhaustive",
            output_style="technical"
        )
        self.assertIn("STRICT GROUNDING RULES", prompt)
        self.assertIn("Do not invent facts, examples, statistics, formulas", prompt)
        self.assertIn("CONCEPT INTERROGATION REQUIREMENT", prompt)
        self.assertIn("DEPTH: EXHAUSTIVE", prompt)
        self.assertIn("STYLE: TECHNICAL & SYSTEMIC", prompt)
        self.assertIn("Architecture", prompt)
        self.assertIn("Cloud Security Fundamentals", prompt)

    def test_common_document_representation_schema(self):
        from api.document_service import create_common_document_representation
        pages_sample = [
            {
                "page_number": 1,
                "text": "Executive Summary of Q3 earnings.",
                "headings": ["Executive Summary"],
                "tables": ["| Metric | Value |\n| ARR | $45M |"],
                "equations": [],
                "image_count": 1,
                "vector_graphic_count": 0,
                "is_ocr": False
            },
            {
                "page_number": 2,
                "text": "Detailed financial breakdown and risks.",
                "headings": ["Financial Breakdown"],
                "tables": [],
                "equations": ["$$ROI = \\frac{Gain - Cost}{Cost}$$"],
                "image_count": 0,
                "vector_graphic_count": 0,
                "is_ocr": False
            }
        ]
        cdr = create_common_document_representation(
            document_id=42,
            title="Q3 Performance",
            genre="BUSINESS",
            pages_data=pages_sample,
            is_scanned=False,
            ocr_applied=False
        )
        cdr_dict = cdr.to_dict()
        self.assertEqual(cdr_dict["document_id"], 42)
        self.assertEqual(cdr_dict["genre"], "BUSINESS")
        self.assertEqual(cdr_dict["page_count"], 2)
        self.assertEqual(cdr_dict["total_tables"], 1)
        self.assertEqual(cdr_dict["total_equations"], 1)
        self.assertEqual(cdr_dict["total_visuals"], 1)
        self.assertEqual(len(cdr_dict["pages"]), 2)

    def test_export_markdown_to_docx_and_pdf(self):
        import os
        from api.notes_engine import export_markdown_to_docx, export_markdown_to_pdf
        md_sample = (
            "# Document Overview\n\n"
            "This is a verified test document.\n\n"
            "## Architecture\n\n"
            "- Component A: Web Gateway\n"
            "- Component B: Core Engine\n\n"
            "| Column 1 | Column 2 |\n"
            "| --- | --- |\n"
            "| Data A | Data B |\n"
        )
        docx_path = export_markdown_to_docx("Test Doc", md_sample, "Computer Science", doc_id="test_export")
        self.assertTrue(os.path.isfile(docx_path))
        self.assertTrue(os.path.getsize(docx_path) > 1000)

        pdf_path = export_markdown_to_pdf("Test Doc", md_sample, "Computer Science", doc_id="test_export")
        self.assertTrue(os.path.isfile(pdf_path))
        self.assertTrue(os.path.getsize(pdf_path) > 1000)

