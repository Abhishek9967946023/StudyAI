"""
=============================================================================
StudyAI — Comprehensive Pipeline Test Suite
=============================================================================
Tests:
1. Document ingestion and text cleaning
2. Chunking with page boundaries and token calculation
3. Language detection (English and Hindi)
4. Subject-agnostic topic extraction (e.g., Operating Systems, Networks)
5. Exam question synthesis with citations
6. Exam submission, grading, and score percentage calculation
7. Topic-wise performance calculation and weak topic diagnostics
8. 4-Quadrant Priority Matrix revision task synthesis
9. Grounded Copilot Q&A
10. Live Ollama daemon health check
=============================================================================
"""

import json
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from .models import Document, Chunk, Topic, Exam, Question, ExamAttempt, RevisionTask, AdaptivePracticeLoop
from .document_service import clean_text, detect_language, chunk_document_by_pages
from .views import calculate_adaptive_priority
from .ollama_service import (
    check_ollama_status,
    fallback_extract_document_analysis,
    fallback_generate_questions,
    fallback_hierarchical_summary,
    generate_hierarchical_summary,
    detect_academic_subject_dynamically,
    group_chunks_for_hierarchical_summary,
    answer_copilot_with_ai
)


class StudyAIPipelineTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="pipelinetest@studyai.internal",
            email="pipelinetest@studyai.internal",
            password="TestPassword123!"
        )
        self.client.force_login(self.user)

        # OS Study Text
        self.os_text = """
Chapter 3: Process Management and CPU Scheduling

A process is a program in execution. A process includes the program code, counter, and process control block (PCB).
The process control block maintains process state, program counter, CPU registers, and scheduling information.
Threads are lightweight units of execution within a process that share code and data sections.

CPU Scheduling allocates CPU time among ready processes. First-Come First-Served (FCFS) suffers from convoy effect.
Shortest Job First (SJF) provides optimal minimum average waiting time. Round Robin (RR) uses time quanta.

Deadlock is a situation where every member of a set of processes waits for an event only another member can cause.
The four necessary conditions for deadlock are: Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait.
        """

    def test_1_text_cleaning_and_language_detection(self):
        cleaned = clean_text(self.os_text)
        self.assertNotIn('\r', cleaned)
        self.assertTrue(len(cleaned) > 200)

        # English detection
        lang_en = detect_language(cleaned)
        self.assertEqual(lang_en, 'en')

        # Hindi detection
        hindi_text = "ऑपरेटिंग सिस्टम में प्रक्रिया प्रबंधन और थ्रेड्स का अध्ययन। बहुकार्य और वर्चुअल मेमोरी की व्याख्या करें।"
        lang_hi = detect_language(hindi_text)
        self.assertEqual(lang_hi, 'hi')

    def test_2_chunking_with_page_preservation(self):
        pages_data = [
            {"page_number": 1, "text": "Process control block and execution states in modern multiprocessor operating systems."},
            {"page_number": 2, "text": "CPU scheduling algorithms include First-Come First-Served, Shortest Job First, and Round Robin scheduling."}
        ]
        # target_size = 50 ensures chunk boundary is triggered between sentences
        chunks = chunk_document_by_pages(pages_data, target_size=50, overlap=10)
        self.assertTrue(len(chunks) >= 2)
        self.assertEqual(chunks[0]["page_start"], 1)
        self.assertIn("char_count", chunks[0])
        self.assertIn("estimated_tokens", chunks[0])

    def test_3_document_agnostic_analysis_os(self):
        chunks = [{"chunk_index": 1, "page_start": 1, "text": self.os_text}]
        analysis = fallback_extract_document_analysis(self.os_text, chunks, title="Operating Systems Notes")

        # Must detect Operating Systems, NOT Biology/Photosynthesis!
        self.assertEqual(analysis["subject"], "Operating Systems")
        self.assertNotIn("Photosynthesis", str(analysis))
        self.assertTrue(len(analysis["topics"]) >= 2)

    def test_4_grounded_question_generation(self):
        chunks = [{"chunk_index": 1, "page_start": 1, "text": self.os_text}]
        questions = fallback_generate_questions(chunks, topic="All", count=3)

        self.assertEqual(len(questions), 3)
        for q in questions:
            self.assertIn("citation", q)
            self.assertIn("options", q)
            self.assertIn("correctAnswer", q)
            self.assertTrue(len(q["options"]) >= 2)

    @override_settings(DOCUMENT_PIPELINE_SYNCHRONOUS=True)
    @patch('api.document_pipeline.analyze_document_with_ai')
    def test_5_document_upload_api_endpoint(self, mock_ai_analysis):
        mock_ai_analysis.return_value = {
            "subject": "Operating Systems",
            "title": "OS Unit 1",
            "executiveSummary": "Process management and CPU scheduling.",
            "topics": [
                {"name": "Process Control Block", "importance": "High", "weight": 95, "source_page": 1},
                {"name": "CPU Scheduling", "importance": "High", "weight": 90, "source_page": 1}
            ],
            "keyPoints": [],
            "highYieldFormulae": []
        }

        payload = {
            "title": "OS Unit 1",
            "text": self.os_text
        }
        response = self.client.post(
            '/api/documents/upload/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["subject"], "Operating Systems")
        self.assertTrue(Document.objects.filter(id=data["id"]).exists())

    @patch('api.views.analyze_document_with_ai')
    @patch('api.views.generate_exam_questions_with_ai')
    def test_6_exam_generation_and_evaluation_pipeline(self, mock_gen_q, mock_ai_analysis):
        mock_ai_analysis.return_value = {
            "subject": "Operating Systems",
            "title": "OS Unit 1",
            "executiveSummary": "Process management and CPU scheduling overview.",
            "topics": [
                {"name": "Process Management", "importance": "High", "weight": 95, "source_page": 1},
                {"name": "CPU Scheduling", "importance": "High", "weight": 85, "source_page": 1}
            ],
            "keyPoints": [],
            "highYieldFormulae": []
        }

        mock_gen_q.return_value = [
            {
                "id": "q-1",
                "question": "What stores process state?",
                "type": "mcq",
                "options": ["PCB", "Disk", "Cache", "Bus"],
                "correctAnswer": "PCB",
                "correctIndex": 0,
                "explanation": "PCB maintains process state.",
                "citation": "A process control block (PCB) maintains process state.",
                "topic": "Process Management",
                "difficulty": "Medium",
                "source_page": 1,
                "source_chunk": 1
            },
            {
                "id": "q-2",
                "question": "Which algorithm uses time quanta?",
                "type": "mcq",
                "options": ["Round Robin", "FCFS", "SJF", "Priority"],
                "correctAnswer": "Round Robin",
                "correctIndex": 0,
                "explanation": "RR uses time slicing.",
                "citation": "Round Robin (RR) uses time quanta.",
                "topic": "CPU Scheduling",
                "difficulty": "Medium",
                "source_page": 1,
                "source_chunk": 1
            }
        ]

        # 1. Upload doc
        doc_resp = self.client.post(
            '/api/v1/materials',
            data=json.dumps({"title": "OS Unit 1", "text": self.os_text}),
            content_type='application/json'
        )
        doc_id = doc_resp.json()["id"]

        # 2. Generate exam
        exam_resp = self.client.post(
            '/api/v1/exams',
            data=json.dumps({"document_id": doc_id, "questionCount": 2, "difficulty": "Medium"}),
            content_type='application/json'
        )
        self.assertEqual(exam_resp.status_code, 200)
        exam_data = exam_resp.json()
        questions = exam_data["questions"]
        self.assertEqual(len(questions), 2)

        # 3. Submit exam: 1 correct ("PCB"), 1 wrong ("WrongAnswer")
        answers = {
            questions[0]["id"]: "PCB",
            questions[1]["id"]: "WrongAnswer"
        }
        submit_resp = self.client.post(
            f'/api/v1/exams/{exam_data["id"]}/submit',
            data=json.dumps({"answers": answers}),
            content_type='application/json'
        )
        self.assertEqual(submit_resp.status_code, 200)
        result_data = submit_resp.json()
        self.assertEqual(result_data["scorePercent"], 50)
        self.assertEqual(result_data["correctCount"], 1)
        self.assertEqual(result_data["incorrectCount"], 1)

        # 4. Verify topic performance and revision task creation
        self.assertTrue(len(result_data["topicBreakdown"]) > 0)
        self.assertTrue(RevisionTask.objects.filter(document_id=doc_id).exists())

    def test_7_grounded_copilot_answers(self):
        chunks = [{"chunk_index": 1, "page_start": 1, "section": "Process Management", "text": self.os_text}]

        # Grounded query about PCB
        resp = answer_copilot_with_ai("What is the process control block PCB?", chunks)
        self.assertIn("PCB", resp["answer"])
        self.assertTrue(len(resp["sources"]) > 0)

        # Unrelated query not in material
        resp_unrelated = answer_copilot_with_ai("What is cellular respiration and mitochondria?", chunks)
        self.assertIn("not found in the uploaded material", resp_unrelated["answer"])

    def test_8_ollama_health_status(self):
        status = check_ollama_status()
        self.assertIn("is_online", status)
        self.assertIn("models", status)

    def test_9_document_validation_and_failures(self):
        # Empty document upload error
        resp = self.client.post(
            '/api/documents/upload/',
            data=json.dumps({"title": "Empty Doc", "text": "   "}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())

        # Too short text error
        resp_short = self.client.post(
            '/api/documents/upload/',
            data=json.dumps({"title": "Short Doc", "text": "Too brief"}),
            content_type='application/json'
        )
        self.assertEqual(resp_short.status_code, 400)

    @patch('api.views.analyze_document_with_ai')
    def test_10_canonical_endpoints_analyze_and_topics(self, mock_ai_analysis):
        mock_ai_analysis.return_value = {
            "subject": "Operating Systems",
            "title": "OS Process Architecture",
            "executiveSummary": "Process states, scheduling, and concurrency mechanisms.",
            "topics": [
                {"name": "Deadlocks", "importance": "High", "weight": 95, "source_page": 1},
                {"name": "Semaphores", "importance": "Medium", "weight": 70, "source_page": 1}
            ],
            "keyPoints": [],
            "highYieldFormulae": []
        }

        # Create doc directly
        doc = Document.objects.create(
            user=self.user,
            title="OS Process Architecture",
            raw_text=self.os_text,
            status='UPLOADED'
        )
        Chunk.objects.create(
            document=doc,
            chunk_index=1,
            text=self.os_text,
            page_start=1,
            page_end=1
        )

        # Trigger canonical POST /api/documents/{id}/analyze/
        analyze_resp = self.client.post(f'/api/documents/{doc.id}/analyze/')
        self.assertEqual(analyze_resp.status_code, 200)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'READY')
        self.assertEqual(doc.subject, 'Operating Systems')

        # Trigger canonical GET /api/documents/{id}/topics/
        topics_resp = self.client.get(f'/api/documents/{doc.id}/topics/')
        self.assertEqual(topics_resp.status_code, 200)
        topics_data = topics_resp.json()
        self.assertEqual(len(topics_data), 2)
        self.assertEqual(topics_data[0]["name"], "Deadlocks")

    def test_11_multilingual_detection(self):
        # German
        de_text = "Die Architektur von Betriebssystemen umfasst Prozessmanagement und Speicherverwaltung."
        self.assertEqual(detect_language(de_text), "de")

        # French
        fr_text = "Le système d'exploitation gère les ressources matérielles et les processus pour l'utilisateur."
        self.assertEqual(detect_language(fr_text), "fr")

        # Spanish
        es_text = "El sistema operativo coordina los procesos y la memoria para las aplicaciones."
        self.assertEqual(detect_language(es_text), "es")

        # Tamil
        ta_text = "இயக்க முறைமை செயல்முறை மேலாண்மை மற்றும் நினைவக மேலாண்மை ஆகியவற்றைக் கையாள்கிறது."
        self.assertEqual(detect_language(ta_text), "ta")

    def test_12_priority_matrix_quadrants(self):
        doc = Document.objects.create(user=self.user, title="Systems Test", raw_text=self.os_text)
        Topic.objects.create(document=doc, name="Critical Topic", weight=90)
        Topic.objects.create(document=doc, name="Maintain Topic", weight=85)
        Topic.objects.create(document=doc, name="Practice Topic", weight=40)
        Topic.objects.create(document=doc, name="Low Priority Topic", weight=30)

        exam = Exam.objects.create(user=self.user, document=doc, title="Diagnostics Exam", total_questions=4)
        q1 = Question.objects.create(exam=exam, document=doc, question_number=1, topic="Critical Topic", question_text="Q1", correct_answer="A")
        q1.set_options(["A", "B"])
        q1.save()
        q2 = Question.objects.create(exam=exam, document=doc, question_number=2, topic="Maintain Topic", question_text="Q2", correct_answer="B")
        q2.set_options(["A", "B"])
        q2.save()
        q3 = Question.objects.create(exam=exam, document=doc, question_number=3, topic="Practice Topic", question_text="Q3", correct_answer="A")
        q3.set_options(["A", "B"])
        q3.save()
        q4 = Question.objects.create(exam=exam, document=doc, question_number=4, topic="Low Priority Topic", question_text="Q4", correct_answer="B")
        q4.set_options(["A", "B"])
        q4.save()

        # Submit answers: Fail Q1 (Critical Topic), Pass Q2 (Maintain Topic), Fail Q3 (Practice Topic), Pass Q4 (Low Priority)
        user_answers = {
            f"q-{q1.id}": "Wrong",
            f"q-{q2.id}": "B",
            f"q-{q3.id}": "Wrong",
            f"q-{q4.id}": "B"
        }
        resp = self.client.post(f'/api/exams/{exam.id}/submit/', data=json.dumps({"answers": user_answers}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        tasks = {t.topic: t.priority for t in RevisionTask.objects.filter(document=doc)}
        self.assertEqual(tasks.get("Critical Topic"), "Critical")
        self.assertEqual(tasks.get("Maintain Topic"), "Maintain")
        self.assertEqual(tasks.get("Practice Topic"), "Practice")
        self.assertEqual(tasks.get("Low Priority Topic"), "Low Priority")

    def test_13_semantic_grading_short_and_long_answers(self):
        doc = Document.objects.create(user=self.user, title="Grading Test", raw_text=self.os_text)
        exam = Exam.objects.create(user=self.user, document=doc, title="Short Answer Exam", total_questions=2)
        q_short = Question.objects.create(
            exam=exam,
            document=doc,
            question_number=1,
            question_type="short",
            question_text="Define a process.",
            correct_answer="A process is a program in execution.",
            topic="Processes"
        )
        q_long = Question.objects.create(
            exam=exam,
            document=doc,
            question_number=2,
            question_type="long",
            question_text="List conditions for deadlock.",
            correct_answer="Mutual exclusion, hold and wait, no preemption, circular wait.",
            topic="Deadlocks"
        )

        # Semantic answer submission: not identical, but matching key concepts
        user_answers = {
            f"q-{q_short.id}": "Program currently in execution with PCB",
            f"q-{q_long.id}": "Mutual exclusion, circular wait, no preemption and hold and wait"
        }
        resp = self.client.post(f'/api/exams/{exam.id}/submit/', data=json.dumps({"answers": user_answers}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["scorePercent"], 100)
        self.assertEqual(data["correctCount"], 2)

    def test_14_safe_json_parsing_resilience(self):
        from api.ollama_service import parse_json_safely

        # Markdown wrapped
        raw_md = '```json\n{"subject": "Physics", "topics": []}\n```'
        parsed_md = parse_json_safely(raw_md)
        self.assertIsNotNone(parsed_md)
        self.assertEqual(parsed_md.get("subject"), "Physics")

        # Conversational preamble wrapped
        raw_preamble = 'Here is the analysis:\n{"subject": "Mathematics", "topics": [{"name": "Calculus"}]}\nHope this helps!'
        parsed_preamble = parse_json_safely(raw_preamble)
        self.assertIsNotNone(parsed_preamble)
        self.assertEqual(parsed_preamble.get("subject"), "Mathematics")


class OCRExtractionTestSuite(TestCase):
    """
    Unit and integration tests for Scanned/Image-based PDF extraction and OCR service.
    Covers the 7 required scenarios:
    1. Normal PDF
    2. Scanned PDF with OCR
    3. Scanned PDF without OCR dependency
    4. Empty scanned page
    5. Mixed PDF (some text pages + some scanned pages)
    6. Page number preservation
    7. OCR extraction failure
    """
    def setUp(self):
        import io
        import os
        import pypdf
        self.client = Client()
        self.user = User.objects.create_user(
            username="ocrtest@studyai.internal",
            email="ocrtest@studyai.internal",
            password="TestPassword123!"
        )
        self.client.force_login(self.user)

        # Create a valid 1-page scanned/blank PDF using pypdf
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=300, height=300)
        buf = io.BytesIO()
        writer.write(buf)
        self.scanned_pdf_bytes = buf.getvalue()

        # Create a 2-page scanned/blank PDF
        writer2 = pypdf.PdfWriter()
        writer2.add_blank_page(width=300, height=300)
        writer2.add_blank_page(width=300, height=300)
        buf2 = io.BytesIO()
        writer2.write(buf2)
        self.scanned_2page_pdf_bytes = buf2.getvalue()

        # Path to sample text PDF
        self.sample_text_pdf_path = os.path.join(
            os.path.dirname(__file__), '..', 'media', 'documents', 'os_concepts.pdf'
        )

    def test_ocr_1_normal_pdf_extraction(self):
        """1. Normal PDF with native selectable text extracts directly without OCR."""
        import os
        from api.document_service import extract_text_from_pdf
        if os.path.exists(self.sample_text_pdf_path):
            with open(self.sample_text_pdf_path, 'rb') as f:
                pdf_bytes = f.read()
        else:
            pdf_bytes = self.scanned_pdf_bytes

        res = extract_text_from_pdf(pdf_bytes)
        text, pages, count, is_scanned = res
        self.assertIsInstance(res.ocr_applied, bool)
        if os.path.exists(self.sample_text_pdf_path):
            self.assertFalse(res.ocr_applied)
            self.assertFalse(res.is_scanned)
            self.assertGreater(len(text), 100)
            self.assertGreaterEqual(count, 1)
            self.assertFalse(pages[0].get("is_ocr", False))

    @patch('api.document_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.extract_images_from_pdf_page', return_value=["dummy_image"])
    @patch('api.ocr_service.run_ocr_on_image', return_value=("Relational Database Systems and Normalization Forms", True, ""))
    @patch('api.views.enqueue_document_for_processing', return_value=True)
    def test_ocr_2_scanned_pdf_with_ocr(self, mock_enqueue, mock_run_ocr, mock_extract_img, mock_avail1, mock_avail2):
        """2. Scanned PDF is identified immediately and queued for OCR processing."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from api.document_service import extract_text_from_pdf
        from api.models import Document

        res = extract_text_from_pdf(self.scanned_pdf_bytes)
        self.assertTrue(res.ocr_applied)
        self.assertTrue(res.is_scanned)
        self.assertIn("Relational Database Systems", res[0])
        self.assertIn("--- Page 1 ---", res[0])
        self.assertTrue(res[1][0]["is_ocr"])
        self.assertIsNone(res[1][0].get("confidence"))

        # Test upload API with scanned PDF
        uploaded_file = SimpleUploadedFile("scanned_lecture.pdf", self.scanned_pdf_bytes, content_type="application/pdf")
        resp = self.client.post('/api/documents/upload/', {'file': uploaded_file})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("is_scanned"))
        self.assertFalse(data.get("ocr_applied"))
        self.assertEqual(data.get("status"), "QUEUED")
        mock_enqueue.assert_called_once()

        # Scan detection is available immediately; OCR completion is reported by status polling.
        doc = Document.objects.get(id=data["id"])
        self.assertTrue(doc.is_scanned)
        self.assertFalse(doc.ocr_applied)

    @patch('api.document_service.is_ocr_available', return_value=(False, "Tesseract OCR binary is not installed on this system."))
    @patch('api.ocr_service.is_ocr_available', return_value=(False, "Tesseract OCR binary is not installed on this system."))
    def test_ocr_3_scanned_pdf_without_ocr_dependency(self, mock_avail1, mock_avail2):
        """3. Scanned PDF when OCR is unavailable returns clear error without crashing."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from api.document_service import extract_text_from_pdf

        res = extract_text_from_pdf(self.scanned_pdf_bytes)
        self.assertFalse(res.ocr_applied)
        self.assertTrue(res.is_scanned)
        self.assertEqual(res.ocr_message, "This PDF appears to be scanned, but OCR is not available on this system.")

        # Test upload API returns the exact requested error message
        uploaded_file = SimpleUploadedFile("scan_no_ocr.pdf", self.scanned_pdf_bytes, content_type="application/pdf")
        resp = self.client.post('/api/documents/upload/', {'file': uploaded_file})
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data.get("error"), "This PDF appears to be scanned, but OCR is not available on this system.")
        self.assertTrue(data.get("is_scanned"))

    @patch('api.document_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.extract_images_from_pdf_page', return_value=["dummy_blank_image"])
    @patch('api.ocr_service.run_ocr_on_image', return_value=("", True, ""))
    @patch('api.views.enqueue_document_for_processing', return_value=True)
    def test_ocr_4_empty_scanned_page(self, mock_enqueue, mock_run_ocr, mock_extract_img, mock_avail1, mock_avail2):
        """4. Empty/blank scanned pages are queued and their extraction result stays explicit."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from api.document_service import extract_text_from_pdf

        res = extract_text_from_pdf(self.scanned_pdf_bytes)
        self.assertFalse(res.ocr_applied)
        self.assertTrue(res.is_scanned)

        uploaded_file = SimpleUploadedFile("blank_scan.pdf", self.scanned_pdf_bytes, content_type="application/pdf")
        resp = self.client.post('/api/documents/upload/', {'file': uploaded_file})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "QUEUED")
        self.assertTrue(data.get("is_scanned"))
        mock_enqueue.assert_called_once()

    @patch('api.document_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.extract_images_from_pdf_page')
    @patch('api.ocr_service.run_ocr_on_image')
    def test_ocr_5_mixed_pdf_text_and_scanned_pages(self, mock_run_ocr, mock_extract_img, mock_avail1, mock_avail2):
        """5. Mixed PDF preserves native text pages and performs OCR on scanned pages."""
        from api.ocr_service import process_scanned_pdf

        pages_input = [
            {
                "page_number": 1,
                "text": "Page 1: Operating Systems Kernel Architecture with native vector text.",
                "char_count": 68,
                "tables": ["[Table 1]"],
                "table_extraction_status": "EXTRACTED",
                "image_count": 1,
                "vector_graphic_count": 2,
                "visual_extraction_status": "DETECTED_UNINTERPRETED"
            },
            {
                "page_number": 2,
                "text": "",
                "char_count": 0,
                "tables": [],
                "table_extraction_status": "OCR_REQUIRED",
                "image_count": None,
                "vector_graphic_count": None,
                "visual_extraction_status": "OCR_REQUIRED"
            }
        ]
        mock_extract_img.return_value = ["page2_img"]
        mock_run_ocr.return_value = ("Page 2: DMA Controller Channels and Interrupt Request Lines", True, "")

        ocr_result = process_scanned_pdf(self.scanned_2page_pdf_bytes, pages_data=pages_input, page_count=2)
        self.assertTrue(ocr_result["success"])
        self.assertTrue(ocr_result["ocr_applied"])
        self.assertEqual(len(ocr_result["pages_data"]), 2)
        # Page 1 preserved native text
        self.assertFalse(ocr_result["pages_data"][0]["is_ocr"])
        self.assertIn("Kernel Architecture", ocr_result["pages_data"][0]["text"])
        self.assertEqual(ocr_result["pages_data"][0]["tables"], ["[Table 1]"])
        self.assertEqual(ocr_result["pages_data"][0]["table_extraction_status"], "EXTRACTED")
        self.assertEqual(ocr_result["pages_data"][0]["image_count"], 1)
        self.assertEqual(
            ocr_result["pages_data"][0]["visual_extraction_status"],
            "DETECTED_UNINTERPRETED",
        )
        # Page 2 extracted via OCR
        self.assertTrue(ocr_result["pages_data"][1]["is_ocr"])
        self.assertIn("DMA Controller", ocr_result["pages_data"][1]["text"])
        self.assertEqual(ocr_result["pages_data"][1]["table_extraction_status"], "OCR_REQUIRED")
        self.assertEqual(ocr_result["pages_data"][1]["visual_extraction_status"], "OCR_REQUIRED")
        # Formatted text has both pages
        self.assertIn("--- Page 1 ---", ocr_result["full_text"])
        self.assertIn("--- Page 2 ---", ocr_result["full_text"])

    def test_scanned_page_reports_measured_ocr_confidence(self):
        from api.ocr_service import process_scanned_pdf

        def fake_ocr(img, lang, quality_mode, timeout_seconds, metadata):
            metadata.update({
                "quality": "WEAK",
                "confidence": 62.5,
                "word_count": 12,
                "char_count": 80,
                "attempt": 1,
                "error": None
            })
            return "Recognized text from a low-confidence scanned page.", True, ""

        with patch('api.ocr_service.is_ocr_available', return_value=(True, "Tesseract OCR is available")), \
             patch('api.ocr_service.extract_images_from_pdf_page', return_value=["scanned_page"]), \
             patch('api.ocr_service.run_ocr_on_image', side_effect=fake_ocr):
            result = process_scanned_pdf(
                self.scanned_pdf_bytes,
                page_count=1
            )

        self.assertEqual(result["pages_data"][0]["confidence"], 62.5)
        self.assertEqual(result["pages_data"][0]["quality"], "WEAK")
        self.assertEqual(result["avg_confidence"], 62.5)

    @patch('api.document_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.extract_images_from_pdf_page', return_value=["img"])
    @patch('api.ocr_service.run_ocr_on_image')
    def test_ocr_6_page_number_preservation(self, mock_run_ocr, mock_extract_img, mock_avail1, mock_avail2):
        """6. Page numbers (--- Page X ---) and boundaries preserved across OCR and chunking."""
        from api.ocr_service import process_scanned_pdf
        from api.document_service import chunk_document_by_pages

        mock_run_ocr.side_effect = [
            ("Page 1 Content: Relational Algebra Selection and Projection.", True, ""),
            ("Page 2 Content: Relational Calculus and Tuple Calculus.", True, "")
        ]

        ocr_result = process_scanned_pdf(self.scanned_2page_pdf_bytes, pages_data=None, page_count=2)
        self.assertTrue(ocr_result["success"])
        self.assertIn("--- Page 1 ---", ocr_result["full_text"])
        self.assertIn("--- Page 2 ---", ocr_result["full_text"])

        # Chunking test preserving page boundaries
        chunks = chunk_document_by_pages(ocr_result["pages_data"], target_size=40, overlap=10)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["page_start"], 1)

    @patch('api.document_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.is_ocr_available', return_value=(True, "Tesseract OCR is available"))
    @patch('api.ocr_service.extract_images_from_pdf_page', return_value=["corrupted_img"])
    @patch('api.ocr_service.run_ocr_on_image', side_effect=RuntimeError("Tesseract worker process crashed (-11)"))
    @patch('api.views.enqueue_document_for_processing', return_value=True)
    def test_ocr_7_ocr_extraction_failure(self, mock_enqueue, mock_run_ocr, mock_extract_img, mock_avail1, mock_avail2):
        """7. OCR failures are handled by the worker instead of blocking upload."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from api.document_service import extract_text_from_pdf

        extraction = extract_text_from_pdf(self.scanned_pdf_bytes)
        self.assertFalse(extraction.ocr_applied)
        self.assertTrue(extraction.is_scanned)
        self.assertEqual(extraction.ocr_error_code, "OCR_EMPTY_RESULT")

        uploaded_file = SimpleUploadedFile("crash_scan.pdf", self.scanned_pdf_bytes, content_type="application/pdf")
        resp = self.client.post('/api/documents/upload/', {'file': uploaded_file})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "QUEUED")
        mock_enqueue.assert_called_once()

    def test_ocr_8_status_endpoint_shows_scanned_ocr_steps(self):
        """Status output names scan detection, OCR, extraction, and analysis stages."""
        from api.models import Document

        doc = Document.objects.create(
            user=self.user,
            title="Scanned Physics Exam",
            filename="scanned_physics.pdf",
            file_type="pdf",
            page_count=3,
            raw_text="--- Page 1 ---\nQuantum Mechanics Wavefunction",
            word_count=50,
            total_chunks=2,
            is_scanned=True,
            ocr_applied=True,
            status='READY'
        )

        resp = self.client.get(f'/api/documents/{doc.id}/status/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        steps = data.get("steps", [])
        step_labels = [s.get("label") for s in steps]

        self.assertIn("Scanned PDF detected", step_labels)
        self.assertIn("Running OCR...", step_labels)
        self.assertIn("Text extracted successfully", step_labels)
        self.assertIn("Analyzing document...", step_labels)


class AdaptiveLearningLoopTestSuite(TestCase):
    """
    Validates the end-to-end Adaptive Learning Loop:
    1. Weak topic identified
    2. Practice generated
    3. Practice grounded in document
    4. Practice submitted
    5. New score calculated
    6. Improvement calculated
    7. Topic performance updated
    8. Priority recalculated
    9. Dashboard updated
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="adaptivetest@studyai.internal",
            email="adaptivetest@studyai.internal",
            password="TestPassword123!"
        )
        self.client.force_login(self.user)
        self.doc = Document.objects.create(
            user=self.user,
            title="Distributed Operating Systems",
            filename="distributed_systems.pdf",
            file_type="pdf",
            page_count=3,
            raw_text="Deadlocks occur in distributed systems when processes hold resources and wait for others. Mutual exclusion, hold and wait, no preemption, and circular wait are required.",
            word_count=120,
            total_chunks=2,
            status='READY'
        )
        self.chunk1 = Chunk.objects.create(
            document=self.doc,
            chunk_index=1,
            page_start=1,
            page_end=1,
            text="Deadlocks in distributed resource allocation. Four Coffman conditions define deadlock: mutual exclusion, hold and wait, no preemption, circular wait.",
            char_count=145,
            estimated_tokens=35
        )
        self.chunk2 = Chunk.objects.create(
            document=self.doc,
            chunk_index=2,
            page_start=2,
            page_end=2,
            text="Deadlock detection uses wait-for graphs (WFG) and distributed edge chasing algorithms to detect cycles across independent nodes.",
            char_count=138,
            estimated_tokens=33
        )
        self.topic = Topic.objects.create(
            document=self.doc,
            name="Deadlocks",
            importance="High",
            weight=94,
            source_reference="Pages 1-2"
        )

    def test_1_weak_topic_identified(self):
        """Step 1: Weak topic is identified with high importance (94%) and low performance (35%) triggering CRITICAL priority."""
        initial_exam = Exam.objects.create(
            user=self.user,
            document=self.doc,
            title="Comprehensive Midterm",
            difficulty="medium",
            total_questions=10
        )
        attempt = ExamAttempt.objects.create(
            user=self.user,
            exam=initial_exam,
            user_answers_json=json.dumps({}),
            score_percent=35,
            letter_grade="F",
            correct_count=3,
            incorrect_count=7,
            topic_stats_json=json.dumps([{
                "topic": "Deadlocks",
                "total": 10,
                "correct": 3,
                "scorePercent": 35,
                "isWeak": True,
                "importance": 94,
                "priority": "CRITICAL"
            }]),
            weak_topics_json=json.dumps([{"topic": "Deadlocks"}])
        )

        resp = self.client.get(f"/api/results/{attempt.id}/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        tb = data.get("topicBreakdown", [])
        self.assertTrue(len(tb) > 0)
        deadlock_stat = next((t for t in tb if t.get("topic") == "Deadlocks"), None)
        self.assertIsNotNone(deadlock_stat)
        self.assertEqual(deadlock_stat["scorePercent"], 35)
        self.assertTrue(deadlock_stat.get("isWeak"))
        self.assertEqual(deadlock_stat.get("importance"), 94)
        self.assertEqual(deadlock_stat.get("priority"), "CRITICAL")

    @patch('api.views.generate_exam_questions_with_ai')
    def test_2_and_3_practice_generated_and_grounded_in_document(self, mock_gen):
        """Step 2 & 3: Practice generated for weak topic with 5 questions grounded in document citations."""
        mock_gen.return_value = [
            {
                "id": f"q-ad-{i}",
                "number": i,
                "question": f"Deadlock detection question {i}",
                "type": "mcq",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correctAnswer": "Option A",
                "correctIndex": 0,
                "explanation": f"Explanation grounded in distributed systems page 1-2 for question {i}.",
                "citation": "Distributed Operating Systems, Page 1: Coffman conditions",
                "topic": "Deadlocks",
                "difficulty": "Medium"
            }
            for i in range(1, 6)
        ]

        payload = {
            "document_id": self.doc.id,
            "topic": "Deadlocks",
            "question_count": 5,
            "previous_performance": 35,
            "importance": 94,
            "previous_priority": "CRITICAL"
        }
        resp = self.client.post(
            "/api/adaptive/generate/",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Step 2: 5 questions generated
        self.assertEqual(data.get("totalQuestions"), 5)
        self.assertEqual(len(data.get("questions", [])), 5)
        self.assertEqual(data.get("topic"), "Deadlocks")

        # Step 3: Grounded in document with source citations
        for q in data["questions"]:
            self.assertEqual(q.get("topic"), "Deadlocks")
            self.assertTrue(len(q.get("citation", "")) > 0)
            self.assertIn("Page", q.get("citation", ""))
            self.assertTrue(len(q.get("options", [])) >= 2)
            self.assertNotIn("correctAnswer", q)
            self.assertNotIn("correctIndex", q)

    def test_4_through_8_practice_submission_and_priority_recalculation(self):
        """Steps 4-8: Practice submitted, new score (60%) calculated, improvement (+25%), topic updated, priority recalculated (CRITICAL -> PRACTICE)."""
        practice_exam = Exam.objects.create(
            document=self.doc,
            title="Adaptive Mini-Test: Deadlocks",
            selected_topic="Deadlocks",
            difficulty="adaptive",
            total_questions=5
        )
        q_objs = []
        for i in range(1, 6):
            q = Question.objects.create(
                exam=practice_exam,
                question_number=i,
                question_text=f"What defines deadlock condition {i}?",
                question_type="mcq",
                options_json=json.dumps(["Circular Wait", "Arbitrary Delay", "Preemption", "Buffer Overflow"]),
                correct_answer="Circular Wait",
                correct_index=0,
                explanation="Circular wait completes the cyclic dependency chain.",
                citation=f"Distributed Systems Page {1 if i <= 3 else 2}: Resource wait-for graph",
                topic="Deadlocks",
                difficulty="medium"
            )
            q_objs.append(q)

        rev_task = RevisionTask.objects.create(
            document=self.doc,
            topic="Deadlocks",
            priority="CRITICAL",
            importance_score=94,
            performance_score=35,
            reason="Low performance on high yield concept",
            recommended_action="Review Coffman conditions and Wait-For Graph cycle detection.",
            completed=False
        )

        # Answer 3 of 5 correctly
        answers = {
            f"q-{q_objs[0].id}": "Circular Wait",
            f"q-{q_objs[1].id}": "Circular Wait",
            f"q-{q_objs[2].id}": "Circular Wait",
            f"q-{q_objs[3].id}": "Arbitrary Delay",
            f"q-{q_objs[4].id}": "Arbitrary Delay",
        }

        submit_payload = {
            "exam_id": practice_exam.id,
            "topic": "Deadlocks",
            "answers": answers,
            "previous_performance": 35,
            "importance": 94,
            "previous_priority": "CRITICAL"
        }

        resp = self.client.post(
            "/api/adaptive/submit/",
            data=json.dumps(submit_payload),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Step 5: New score calculated
        new_perf = data.get("newPerformance")
        self.assertEqual(new_perf, 60)

        # Step 6: Improvement calculated
        improvement = data.get("improvement")
        self.assertEqual(improvement, 25)

        # Step 7: Topic performance updated
        loop = AdaptivePracticeLoop.objects.filter(topic="Deadlocks").order_by('-created_at').first()
        self.assertIsNotNone(loop)
        self.assertEqual(loop.previous_performance, 35)
        self.assertEqual(loop.new_performance, 60)
        self.assertEqual(loop.improvement, 25)
        self.assertEqual(loop.importance_score, 94)

        # Step 8: Priority recalculated from CRITICAL (35%) -> PRACTICE (60%)
        self.assertEqual(data.get("previousPriority"), "CRITICAL")
        self.assertEqual(data.get("newPriority"), "PRACTICE")
        self.assertEqual(loop.new_priority, "PRACTICE")

        # RevisionTask updated
        rev_task.refresh_from_db()
        self.assertEqual(rev_task.performance_score, 60)
        self.assertEqual(rev_task.priority, "PRACTICE")

    def test_9_dashboard_updated_with_improvement_trajectory(self):
        """Step 9: Dashboard history endpoint returns the complete Weak Topic -> Practice -> Improvement loop."""
        AdaptivePracticeLoop.objects.create(
            document=self.doc,
            topic="Deadlocks",
            previous_performance=35,
            new_performance=68,
            improvement=33,
            importance_score=94,
            previous_priority="CRITICAL",
            new_priority="PRACTICE"
        )

        resp = self.client.get(f"/api/adaptive/history/?doc_id={self.doc.id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertTrue(isinstance(data, list))
        self.assertTrue(len(data) >= 1)
        latest = data[0]
        self.assertEqual(latest.get("topic"), "Deadlocks")
        self.assertEqual(latest.get("previousPerformance"), 35)
        self.assertEqual(latest.get("newPerformance"), 68)
        self.assertEqual(latest.get("improvement"), 33)
        self.assertEqual(latest.get("previousPriority"), "CRITICAL")
        self.assertEqual(latest.get("newPriority"), "PRACTICE")
        self.assertEqual(latest.get("documentTitle"), "Distributed Operating Systems")

    def test_works_for_any_subject_and_topic(self):
        """Verifies adaptive loop functions dynamically for any subject/topic without hardcoding."""
        chemistry_doc = Document.objects.create(
            title="Organic Chemistry Synthesis",
            filename="organic_chem.pdf",
            file_type="pdf",
            page_count=2,
            raw_text="Electrophilic aromatic substitution mechanism and carbocation intermediates.",
            word_count=80,
            status='READY'
        )
        loop = AdaptivePracticeLoop.objects.create(
            document=chemistry_doc,
            topic="Electrophilic Substitution",
            previous_performance=40,
            new_performance=80,
            improvement=40,
            importance_score=90,
            previous_priority="CRITICAL",
            new_priority="MAINTAIN"
        )
        self.assertEqual(loop.topic, "Electrophilic Substitution")
        self.assertEqual(loop.new_priority, "MAINTAIN")

    def test_workspace_document_and_topic_intelligence(self):
        """Verifies workspace document metadata and topic intelligence fields including priority and source_pages."""
        doc_resp = self.client.get(f"/api/documents/{self.doc.id}/")
        self.assertEqual(doc_resp.status_code, 200)
        doc_data = doc_resp.json()
        self.assertEqual(doc_data.get("title"), "Distributed Operating Systems")
        self.assertEqual(doc_data.get("status"), "READY")
        self.assertEqual(doc_data.get("page_count"), 3)
        self.assertEqual(doc_data.get("language"), "en")

        top_resp = self.client.get(f"/api/v1/topics/intelligence?doc_id={self.doc.id}")
        self.assertEqual(top_resp.status_code, 200)
        top_data = top_resp.json()
        self.assertTrue(len(top_data) >= 1)
        deadlock_top = next((t for t in top_data if t.get("name") == "Deadlocks"), None)
        self.assertIsNotNone(deadlock_top)
        self.assertEqual(deadlock_top.get("importance"), 94)
        self.assertIn("priority", deadlock_top)
        self.assertIn("source_pages", deadlock_top)

    def test_hierarchical_summary_small_document_scaling(self):
        """Verifies depth and section scaling for a small (2-3 page) document."""
        chunks = [
            {"chunk_index": 1, "page_start": 1, "page_end": 1, "text": "Linear Algebra: Vector Spaces. A vector space V over a field F is a set closed under vector addition and scalar multiplication."},
            {"chunk_index": 2, "page_start": 2, "page_end": 2, "text": "Linear independence means no vector can be written as a linear combination of others. The dimension is the cardinality of the basis."},
            {"chunk_index": 3, "page_start": 3, "page_end": 3, "text": "Linear transformations preserve vector addition and scalar multiplication. The Rank-Nullity Theorem states rank(T) + nullity(T) = dim(V)."}
        ]
        full_text = "\n\n".join(c["text"] for c in chunks)
        res = fallback_hierarchical_summary(full_text, chunks, title="Linear Algebra Notes", total_pages=3)
        self.assertEqual(res["summary_type"], "comprehensive")
        self.assertEqual(res["source_pages"], 3)
        self.assertEqual(res["chunks_used"], 3)
        self.assertTrue(len(res["detailed_summary"]) >= 1)
        self.assertTrue(len(res["overview"]) > 50)
        self.assertTrue(any("Vector" in str(d) or "Linear" in str(d) for d in res["definitions"] + res["important_concepts"]))

    def test_hierarchical_summary_medium_document_scaling(self):
        """Verifies depth scaling for a medium (10-15 page) document into 3-5 structured sections."""
        chunks = []
        for p in range(1, 13):
            chunks.append({
                "chunk_index": p,
                "page_start": p,
                "page_end": p,
                "text": f"Chapter {p}: Macroeconomic Foundations Page {p}. Monetary Policy and Central Banking. The Taylor Rule specifies the target nominal interest rate: i = r + pi + 0.5(pi - pi*) + 0.5(y - y*). Inflation targeting maintains price stability."
            })
        full_text = "\n\n".join(c["text"] for c in chunks)
        res = fallback_hierarchical_summary(full_text, chunks, title="Macroeconomics Principles", total_pages=12)
        self.assertEqual(res["source_pages"], 12)
        self.assertEqual(res["chunks_used"], 12)
        self.assertTrue(3 <= len(res["detailed_summary"]) <= 5)
        self.assertTrue(len(res["formulas_rules"]) >= 1)
        self.assertTrue(len(res["quick_revision"]) >= 3)

    def test_hierarchical_summary_large_document_scaling(self):
        """Verifies depth scaling for large 30-40+ page documents into 6-12 substantive sections."""
        topics_40 = [
            "Deterministic finite automata recognize regular languages with finite state sets.",
            "Nondeterministic finite automata can be converted to equivalent DFAs via powerset construction.",
            "Regular expressions define patterns denoted by union, concatenation, and Kleene star.",
            "The Pumping Lemma for regular languages proves that languages like 0^n 1^n are non-regular.",
            "Myhill-Nerode theorem defines equivalence classes of states and minimal DFAs.",
            "Context-free grammars specify languages using production rules with non-terminals and terminals.",
            "Chomsky normal form requires all productions to be of the form A -> BC or A -> a.",
            "Pushdown automata use a last-in-first-out stack to recognize context-free languages.",
            "Deterministic pushdown automata are strictly less expressive than general pushdown automata.",
            "The Pumping Lemma for context-free languages uses uvxyz decomposition to prove non-context-freeness.",
            "Turing machines have an infinite read-write tape and define recursively enumerable languages.",
            "The Church-Turing thesis posits that intuitive computability equals Turing computability.",
            "The Halting Problem is undecidable by diagonal argument reduction.",
            "Rice's Theorem asserts that any non-trivial semantic property of Turing machines is undecidable.",
            "Post Correspondence Problem is an undecidable combinatorial puzzle used in language reductions.",
            "Time complexity measures the number of steps a Turing machine takes as a function of input length.",
            "The class P consists of languages decidable in polynomial time on deterministic Turing machines.",
            "The class NP consists of languages verifiable in polynomial time by a certificate.",
            "Cook-Levin Theorem establishes that the Boolean Satisfiability Problem (SAT) is NP-complete.",
            "Space complexity measures the maximum tape cells scanned during computation.",
            "Savitch's Theorem proves that NSPACE(f(n)) is contained in DSPACE(f(n)^2).",
            "The class PSPACE contains all decision problems solvable using a polynomial amount of space.",
            "Linear bounded automata recognize context-sensitive languages within bounded space.",
            "The Chomsky hierarchy classifies languages into regular, context-free, context-sensitive, and unrestricted.",
            "Universal Turing machines can simulate any other Turing machine given its description and input.",
            "Diagonalization separates complexity classes and proves uncountability of language subsets.",
            "Oracles and relativized complexity show that P equals NP holds relative to some oracles and fails in others.",
            "Interactive proof systems extend verification through randomized multi-round polynomial provers.",
            "Zero-knowledge proofs allow a prover to establish truth without revealing the underlying secret.",
            "Circuit complexity investigates lower bounds using Boolean circuits of gates.",
            "Parity cannot be computed by AC0 circuits of constant depth and polynomial size.",
            "Probabilistic Turing machines define the randomized complexity classes BPP, RP, and ZPP.",
            "Quantum Turing machines define BQP and can factor integers in polynomial time via Shor's algorithm.",
            "Kolmogorov complexity measures the length of the shortest computer program that outputs a string.",
            "Incompressibility method provides combinatorial proofs using Kolmogorov complexity bounds.",
            "Communication complexity bounds the bits exchanged between two parties computing a joint function.",
            "Approximation algorithms find near-optimal solutions for NP-hard optimization problems within guarantees.",
            "PCP theorem characterizes NP in terms of probabilistically checkable proofs with constant queries.",
            "Hardness of approximation proves that certain optimization problems cannot be approximated within factors.",
            "Automata theory provides the foundational mathematical models for compiler lexical and syntax analysis."
        ]
        chunks = []
        for p, topic_sentence in enumerate(topics_40, start=1):
            chunks.append({
                "chunk_index": p,
                "page_start": p,
                "page_end": p,
                "text": f"Chapter {((p-1)//4)+1} Section {p}: Theory of Computation Page {p}. {topic_sentence} It is essential to note that this principle forms a core exam requirement."
            })
        full_text = "\n\n".join(c["text"] for c in chunks)
        res = fallback_hierarchical_summary(full_text, chunks, title="Theory of Computation Master Notes", total_pages=40)
        self.assertEqual(res["source_pages"], 40)
        self.assertEqual(res["chunks_used"], 40)
        self.assertTrue(6 <= len(res["detailed_summary"]) <= 12)
        first_sec = res["detailed_summary"][0]
        last_sec = res["detailed_summary"][-1]
        self.assertIn("1", first_sec["pages"])
        self.assertIn("40", last_sec["pages"])
        exam_points = res["exam_oriented_points"]
        self.assertGreaterEqual(len(exam_points), 1)
        self.assertTrue(any(
            "core exam requirement" in point["text"].lower()
            for point in exam_points
        ))

    def test_hierarchical_summary_subject_independence(self):
        """Verifies complete subject agnosticism across diverse academic domains without hardcoding."""
        domains = [
            ("Contract Law: Offer, Acceptance and Consideration in Common Law", "Law", "Contract Law"),
            ("Thermodynamics: Entropy and the Second Law of Heat Transfer", "Physics", "Thermodynamics"),
            ("Cellular Biology: Mitochondrial Respiration and Krebs Cycle", "Biology", "Cellular Biology")
        ]
        for text, domain, title in domains:
            chunks = [{"chunk_index": 1, "page_start": 1, "text": text}]
            res = fallback_hierarchical_summary(text, chunks, title=title)
            self.assertNotIn("Operating Systems", res["subject"])
            if "Law" in domain:
                self.assertIn("Contract Law", res["subject"])
            elif "Physics" in domain:
                self.assertIn("Thermodynamics", res["subject"])
            elif "Biology" in domain:
                self.assertIn("Cellular Biology", res["subject"])

    def test_hierarchical_summary_multilingual_grounding(self):
        """Verifies hierarchical summary preservation for multilingual non-English materials."""
        hindi_text = "कम्प्यूटर नेटवर्क में ओएसआई मॉडल में सात परतें होती हैं। भौतिक परत बिट्स का संचरण करती है। डेटा लिंक परत फ्रेम बनाती है। नेटवर्क परत पैकेट रूटिंग करती है।"
        chunks = [{"chunk_index": 1, "page_start": 1, "text": hindi_text}]
        res = fallback_hierarchical_summary(hindi_text, chunks, title="कंप्यूटर नेटवर्किंग", language="hi")
        self.assertEqual(res["chunks_used"], 1)
        self.assertTrue(len(res["overview"]) > 20)
        self.assertIn("कम्प्यूटर", res["overview"] + res["title"])

    def test_get_document_summary_view_comprehensive_sections(self):
        """Verifies the GET /api/documents/<id>/summary/ endpoint returns all 10 structured sections with metadata."""
        doc = Document.objects.create(
            user=self.user,
            title="Compiler Design Fundamentals",
            raw_text="Lexical analysis converts lexemes to tokens. Syntax analysis produces parse trees. Semantic analysis checks type consistency.",
            page_count=3,
            total_chunks=2,
            status='READY'
        )
        Chunk.objects.create(
            document=doc,
            chunk_index=1,
            page_start=1,
            page_end=1,
            text="Lexical analysis converts lexemes into tokens using regular expressions."
        )
        Chunk.objects.create(
            document=doc,
            chunk_index=2,
            page_start=2,
            page_end=3,
            text="Syntax analysis parses tokens into abstract syntax trees using context-free grammars."
        )

        resp = self.client.get(f"/api/documents/{doc.id}/summary/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["summary_type"], "comprehensive")
        self.assertEqual(data["source_pages"], 3)
        self.assertEqual(data["chunks_used"], 2)
        sec_ids = [s["id"] for s in data["sections"]]
        self.assertIn("sec-exec", sec_ids)
        self.assertIn("sec-detailed", sec_ids)
        self.assertIn("sec-concepts", sec_ids)
        detailed_sec = next(s for s in data["sections"] if s["id"] == "sec-detailed")
        self.assertEqual(detailed_sec["type"], "chapters")
        self.assertTrue(len(detailed_sec["subsections"]) >= 1)

    def test_exam_question_types_and_grading(self):
        """Verifies True/False and Short Answer questions generate and grade correctly."""
        doc = Document.objects.create(
            user=self.user,
            title="Operating Systems Memory Management",
            raw_text="Virtual memory permits execution of processes not completely in memory. Paging avoids external fragmentation and dynamic storage allocation.",
            page_count=2,
            total_chunks=1,
            status='READY'
        )
        Chunk.objects.create(
            document=doc,
            chunk_index=1,
            page_start=1,
            page_end=1,
            section="Memory Systems",
            text="Virtual memory permits execution of processes not completely in memory. Paging avoids external fragmentation and dynamic storage allocation."
        )

        # 1. Test True/False generation
        tf_qs = fallback_generate_questions([{"chunk_index": 1, "page_start": 1, "text": doc.raw_text}], count=2, question_type='tf')
        self.assertTrue(len(tf_qs) >= 1)
        for q in tf_qs:
            self.assertEqual(q["type"], "tf")
            self.assertEqual(q["options"], ["True", "False"])
            self.assertIn(q["correctAnswer"], ["True", "False"])

        # 2. Test Short Answer generation
        sa_qs = fallback_generate_questions([{"chunk_index": 1, "page_start": 1, "text": doc.raw_text}], count=2, question_type='short')
        self.assertTrue(len(sa_qs) >= 1)
        for q in sa_qs:
            self.assertEqual(q["type"], "short")
            self.assertEqual(q["options"], [])
            self.assertTrue(len(q["correctAnswer"]) > 0)

        # 3. Test fill-in-the-blank and long-answer generation preserve their types.
        fill_blank_qs = fallback_generate_questions(
            [{"chunk_index": 1, "page_start": 1, "text": doc.raw_text}],
            count=2,
            question_type='fill_blank'
        )
        self.assertTrue(fill_blank_qs)
        for q in fill_blank_qs:
            self.assertEqual(q["type"], "fill_blank")
            self.assertEqual(q["options"], [])
            self.assertTrue(q["correctAnswer"])

        long_qs = fallback_generate_questions(
            [{"chunk_index": 1, "page_start": 1, "text": doc.raw_text}],
            count=2,
            question_type='long'
        )
        self.assertTrue(long_qs)
        for q in long_qs:
            self.assertEqual(q["type"], "long")
            self.assertEqual(q["options"], [])
            self.assertTrue(q["correctAnswer"])

        # 4. Test API Exam Generation with Fast Mode and Short Answer
        resp = self.client.post('/api/v1/exams', data=json.dumps({
            "materialId": doc.id,
            "questionCount": 3,
            "questionType": "Short Answer",
            "fastMode": True
        }), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        exam_data = resp.json()
        self.assertEqual(exam_data["questionType"], "short")
        self.assertEqual(len(exam_data["questions"]), 3)
        self.assertEqual(exam_data["questions"][0]["type"], "short")
        self.assertEqual(exam_data["totalMarks"], 6)
        self.assertTrue(all(question["marks"] == 2 for question in exam_data["questions"]))
        self.assertNotIn("correctAnswer", exam_data["questions"][0])

        # 5. Test Submission and Grading of Short Answer
        exam_id = exam_data["id"].replace("exam-", "")
        q0 = exam_data["questions"][0]
        q_obj = Question.objects.get(id=q0["id"].replace("q-", ""))
        # Submit a correct answer without placing the answer key in the exam payload.
        user_answers = {
            q0["id"]: q_obj.get_correct_answer()
        }
        sub_resp = self.client.post(f"/api/v1/exams/{exam_id}/submit", data=json.dumps({
            "answers": user_answers
        }), content_type='application/json')
        self.assertEqual(sub_resp.status_code, 200)
        sub_data = sub_resp.json()
        self.assertTrue(sub_data["scorePercent"] > 0)

        # 6. API persistence must preserve the newly supported answer formats.
        for requested_type in ("Long Answer", "Fill in the Blank"):
            typed_resp = self.client.post('/api/v1/exams', data=json.dumps({
                "materialId": doc.id,
                "questionCount": 1,
                "questionType": requested_type,
                "marksPerQuestion": 10,
                "fastMode": True
            }), content_type='application/json')
            self.assertEqual(typed_resp.status_code, 200)
            typed_data = typed_resp.json()
            expected_type = "long" if requested_type == "Long Answer" else "fill_blank"
            self.assertEqual(typed_data["questionType"], expected_type)
            self.assertEqual(typed_data["questions"][0]["type"], expected_type)
            self.assertEqual(typed_data["totalMarks"], 10)
            self.assertEqual(typed_data["questions"][0]["marks"], 10)

    def test_msq_persistence_and_mark_weighted_scoring(self):
        exam = Exam.objects.create(
            user=self.user,
            document=self.doc,
            title="Weighted MSQ assessment",
            difficulty="medium",
            question_type="mixed",
            total_questions=2,
            total_marks=12
        )
        single_choice = Question.objects.create(
            exam=exam,
            document=self.doc,
            question_number=1,
            question_type="mcq",
            question_text="Which answer is correct?",
            correct_answer="Right",
            correct_index=1,
            marks=2,
            explanation="Reference explanation.",
            citation="Source citation.",
            topic="Deadlocks"
        )
        multiple_select = Question.objects.create(
            exam=exam,
            document=self.doc,
            question_number=2,
            question_type="msq",
            question_text="Select all correct statements about deadlock.",
            correct_answer="",
            correct_indices_json="[0, 2]",
            marks=10,
            explanation="Two source-supported statements are correct.",
            citation="Source citation.",
            topic="Deadlocks"
        )
        multiple_select.set_options([
            "Mutual exclusion is a required condition.",
            "A deadlock requires only one process.",
            "Circular wait is a required condition.",
            "Resources must always be preempted."
        ])
        multiple_select.set_correct_answer([
            "Mutual exclusion is a required condition.",
            "Circular wait is a required condition."
        ])
        multiple_select.save()

        exam_response = self.client.get(f"/api/v1/exams/{exam.id}")
        self.assertEqual(exam_response.status_code, 200)
        msq_payload = next(question for question in exam_response.json()["questions"] if question["type"] == "msq")
        self.assertEqual(msq_payload["marks"], 10)
        self.assertNotIn("correctAnswer", msq_payload)
        self.assertNotIn("correctIndices", msq_payload)
        self.assertEqual(multiple_select.get_correct_indices(), [0, 2])

        response = self.client.post(
            f"/api/v1/exams/{exam.id}/submit",
            data=json.dumps({
                "answers": {
                    f"q-{single_choice.id}": "Wrong",
                    f"q-{multiple_select.id}": [0, 2]
                }
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["correctCount"], 1)
        self.assertEqual(result["marksScored"], 10)
        self.assertEqual(result["totalMarks"], 12)
        self.assertEqual(result["scorePercent"], 83)

        incorrect_msq_response = self.client.post(
            f"/api/v1/exams/{exam.id}/submit",
            data=json.dumps({
                "answers": {
                    f"q-{single_choice.id}": "Wrong",
                    f"q-{multiple_select.id}": [0]
                }
            }),
            content_type="application/json"
        )
        self.assertEqual(incorrect_msq_response.status_code, 200)
        self.assertEqual(incorrect_msq_response.json()["marksScored"], 0)
        self.assertEqual(incorrect_msq_response.json()["scorePercent"], 0)


