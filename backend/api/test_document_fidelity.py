from io import BytesIO
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from zipfile import ZipFile

from .document_pipeline import build_extraction_report
from .document_service import extract_text_from_docx, extract_text_from_pdf


class DocumentFidelityReportTests(TestCase):
    def test_report_flags_unreadable_pages_without_retaining_source_text(self):
        private_source_text = "PRIVATE source sentence must never be copied into telemetry"
        extraction = SimpleNamespace(
            doc_type="MIXED",
            is_scanned=True,
            ocr_applied=True,
            partial_success=True,
            failed_pages=[2],
            avg_confidence=62.5,
        )
        report = build_extraction_report(
            extraction,
            [
                {"page_number": 1, "text": private_source_text, "confidence": 95},
                {"page_number": 2, "text": "", "quality": "FAILED", "confidence": 0},
                {"page_number": 3, "text": "Recognized text", "confidence": 45},
            ],
            3,
        )

        self.assertEqual(report["unreadable_pages"], [2])
        self.assertEqual(report["failed_pages"], [2])
        self.assertEqual(report["low_confidence_pages"], [2, 3])
        self.assertEqual(report["average_ocr_confidence"], 62.5)
        self.assertTrue(report["partial_success"])
        self.assertNotIn(private_source_text, str(report))

    def test_missing_confidence_is_reported_as_unavailable(self):
        extraction = SimpleNamespace(
            doc_type="TEXT_BASED",
            is_scanned=False,
            ocr_applied=False,
            partial_success=False,
            failed_pages=[],
            avg_confidence=0,
        )
        report = build_extraction_report(
            extraction,
            [{"page_number": 1, "text": "Native text"}],
            1,
        )

        self.assertFalse(report["confidence_available"])
        self.assertIsNone(report["average_ocr_confidence"])
        self.assertEqual(report["unreadable_pages"], [])

    def test_table_extraction_report_flags_incomplete_pages_without_copying_content(self):
        private_table_text = "PRIVATE table cell contents"
        extraction = SimpleNamespace(
            doc_type="TEXT_BASED",
            is_scanned=False,
            ocr_applied=False,
            partial_success=False,
            failed_pages=[],
            avg_confidence=0,
        )

        report = build_extraction_report(
            extraction,
            [
                {
                    "page_number": 1,
                    "text": private_table_text,
                    "tables": [private_table_text],
                    "table_extraction_status": "EXTRACTED",
                    "image_count": 1,
                    "vector_graphic_count": 2,
                    "visual_extraction_status": "DETECTED_UNINTERPRETED",
                },
                {
                    "page_number": 2,
                    "text": "Other source text",
                    "tables": [],
                    "table_extraction_status": "OCR_REQUIRED",
                    "image_count": None,
                    "vector_graphic_count": None,
                    "visual_extraction_status": "OCR_REQUIRED",
                },
            ],
            2,
        )

        self.assertEqual(report["table_extraction"]["extracted_count"], 1)
        self.assertEqual(report["table_extraction"]["pages_with_tables"], [1])
        self.assertEqual(report["table_extraction"]["review_pages"], [2])
        self.assertEqual(
            report["table_extraction"]["status_by_page"],
            {1: "EXTRACTED", 2: "OCR_REQUIRED"},
        )
        self.assertEqual(report["visual_content"]["image_count"], 1)
        self.assertEqual(report["visual_content"]["vector_graphic_count"], 2)
        self.assertEqual(report["visual_content"]["detected_pages"], [1])
        self.assertEqual(report["visual_content"]["review_pages"], [1, 2])
        self.assertNotIn(private_table_text, str(report))

    def test_low_confidence_ocr_math_pages_need_manual_review(self):
        extraction = SimpleNamespace(
            doc_type="MIXED",
            is_scanned=True,
            ocr_applied=True,
            partial_success=False,
            failed_pages=[],
            avg_confidence=81.0,
        )

        report = build_extraction_report(
            extraction,
            [
                {"page_number": 1, "is_ocr": True, "confidence": 62.5, "text": "E = 25 J"},
                {"page_number": 2, "is_ocr": True, "confidence": 96.0, "text": "v = 10 m/s"},
                {"page_number": 3, "is_ocr": False, "confidence": 40.0, "text": "F = 12 N"},
                {"page_number": 4, "is_ocr": True, "text": "$$F = ma$$"},
            ],
            4,
        )

        self.assertEqual(report["math_review_pages"], [1, 4])


class PdfTableExtractionTests(TestCase):
    class FakePdfDocument:
        def __init__(self, page):
            self.page = page

        def __len__(self):
            return 1

        def __getitem__(self, index):
            if index != 0:
                raise IndexError(index)
            return self.page

    def extract_with_page(self, page):
        fitz_module = ModuleType("pymupdf")
        fitz_module.open = lambda **kwargs: self.FakePdfDocument(page)
        with patch.dict("sys.modules", {"pymupdf": fitz_module}), \
             patch(
                 "api.document_service.classify_pdf_document",
                 return_value={"doc_type": "TEXT_BASED", "page_count": 1},
             ), \
             patch("api.document_service.detect_scanned_pdf", return_value=(False, [])):
            return extract_text_from_pdf(b"%PDF-test")

    def test_native_pdf_table_rows_are_preserved_in_extracted_text(self):
        class FakeTable:
            def extract(self):
                return [["Algorithm", "Time"], ["Round Robin", "O(n)"]]

        page = SimpleNamespace(
            get_text=lambda mode: "This page contains enough native text for a document extraction test.",
            find_tables=lambda: SimpleNamespace(tables=[FakeTable()]),
            get_images=lambda full: [],
            get_drawings=lambda: [],
        )

        result = self.extract_with_page(page)

        self.assertIn("| Algorithm | Time |", result.full_text)
        self.assertIn("| Round Robin | O(n) |", result.pages_data[0]["text"])
        self.assertEqual(len(result.pages_data[0]["tables"]), 1)
        self.assertEqual(result.pages_data[0]["table_extraction_status"], "EXTRACTED")
        self.assertEqual(result.pages_data[0]["visual_extraction_status"], "NOT_DETECTED")

    def test_pdf_visual_objects_are_counted_but_not_claimed_as_understood(self):
        page = SimpleNamespace(
            get_text=lambda mode: "This page contains enough native text for a document extraction test.",
            find_tables=lambda: SimpleNamespace(tables=[]),
            get_images=lambda full: [("image-xref",)],
            get_drawings=lambda: [{"type": "s"}, {"type": "l"}],
        )

        result = self.extract_with_page(page)

        self.assertEqual(result.pages_data[0]["image_count"], 1)
        self.assertEqual(result.pages_data[0]["vector_graphic_count"], 2)
        self.assertEqual(
            result.pages_data[0]["visual_extraction_status"],
            "DETECTED_UNINTERPRETED",
        )

    def test_unsupported_table_detection_is_reported_as_unavailable(self):
        page = SimpleNamespace(
            get_text=lambda mode: "This page contains enough native text for a document extraction test."
        )

        result = self.extract_with_page(page)

        self.assertEqual(result.pages_data[0]["tables"], [])
        self.assertEqual(result.pages_data[0]["table_extraction_status"], "UNAVAILABLE")
        self.assertEqual(result.pages_data[0]["visual_extraction_status"], "UNAVAILABLE")
        self.assertNotIn("[Table", result.full_text)


class DocxTableExtractionTests(TestCase):
    def test_table_rows_and_columns_are_preserved_in_document_order(self):
        document_xml = b"""\
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:p><w:r><w:t>Intro text.</w:t></w:r></w:p>
            <w:tbl>
              <w:tr>
                <w:tc><w:p><w:r><w:t>Method</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Complexity</w:t></w:r></w:p></w:tc>
              </w:tr>
              <w:tr>
                <w:tc><w:p><w:r><w:t>Binary search</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>O(log n)</w:t></w:r></w:p></w:tc>
              </w:tr>
            </w:tbl>
            <w:p><w:r><w:t>Closing text.</w:t></w:r></w:p>
          </w:body>
        </w:document>
        """
        document = BytesIO()
        with ZipFile(document, "w") as archive:
            archive.writestr("word/document.xml", document_xml)

        text, pages_data, _ = extract_text_from_docx(document.getvalue())

        self.assertIn("[Table 1]\n| Method | Complexity |", text)
        self.assertIn("| Binary search | O(log n) |", text)
        self.assertLess(text.index("Intro text."), text.index("[Table 1]"))
        self.assertLess(text.index("[Table 1]"), text.index("Closing text."))
        self.assertEqual(pages_data[0]["text"], text)
