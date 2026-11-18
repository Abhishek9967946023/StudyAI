"""
=============================================================================
StudyAI — AI Quality Evaluation Test Suite
=============================================================================
Verifies:
1. Benchmark dataset structure and 20 real academic documents
2. Verification algorithms for all 8 quality dimensions
3. Exact metric calculation without fabricated numbers
4. Database persistence and full traceability audit records
5. REST API endpoints for benchmark and report retrieval
=============================================================================
"""

import json
from django.test import TestCase, Client
from .benchmark_dataset import BENCHMARK_DOCUMENTS
from .evaluator import (
    verify_question_grounding,
    verify_citation_accuracy,
    verify_answer_correctness,
    verify_topic_correctness,
    verify_difficulty_correctness,
    detect_unsupported_question,
    evaluate_summary_relevance,
    evaluate_topic_relevance,
    evaluate_copilot_grounding,
    run_evaluation_benchmark,
    save_evaluation_run_to_db,
    get_latest_evaluation_report
)
from .models import EvaluationRun, EvaluationQuestionResult


class BenchmarkDatasetTests(TestCase):
    def test_benchmark_has_20_documents(self):
        self.assertEqual(len(BENCHMARK_DOCUMENTS), 20)

    def test_benchmark_document_schema(self):
        seen_ids = set()
        for doc in BENCHMARK_DOCUMENTS:
            self.assertIn("id", doc)
            self.assertNotIn(doc["id"], seen_ids)
            seen_ids.add(doc["id"])
            self.assertIn("title", doc)
            self.assertIn("subject", doc)
            self.assertIn("content", doc)
            self.assertGreater(len(doc["content"].split()), 80, f"Doc {doc['id']} text is too short")
            self.assertIn("key_entities", doc)
            self.assertGreater(len(doc["key_entities"]), 3)
            self.assertIn("copilot_grounded_query", doc)
            self.assertIn("copilot_ungrounded_query", doc)


class EvaluatorAlgorithmsTests(TestCase):
    def setUp(self):
        self.sample_text = (
            "The Transmission Control Protocol (TCP) is a connection-oriented transport protocol "
            "providing reliable, sequenced byte streams. TCP establishes connections using a three-way "
            "handshake: SYN, SYN-ACK, and ACK."
        )
        self.chunks = [{"chunk_index": 1, "page_start": 1, "text": self.sample_text}]

    def test_grounding_positive(self):
        q = {
            "question": "What three-way handshake packets does TCP transmit to establish connections?",
            "citation": "TCP establishes connections using a three-way handshake: SYN, SYN-ACK, and ACK.",
            "correctAnswer": "SYN, SYN-ACK, and ACK"
        }
        res = verify_question_grounding(q, self.sample_text, self.chunks)
        self.assertTrue(res["is_grounded"])
        self.assertGreater(res["grounding_score"], 0.5)

    def test_grounding_negative_unsupported(self):
        q = {
            "question": "What is the speed of photosynthesis in spinach chloroplasts during rainfall?",
            "citation": "Spinach produces chlorophyll rapidly.",
            "correctAnswer": "Chlorophyll synthesis"
        }
        res = verify_question_grounding(q, self.sample_text, self.chunks)
        self.assertFalse(res["is_grounded"])

    def test_citation_accuracy_exact_and_normalized(self):
        exact_citation = "TCP establishes connections using a three-way handshake: SYN, SYN-ACK, and ACK."
        res1 = verify_citation_accuracy(exact_citation, self.sample_text, self.chunks)
        self.assertTrue(res1["is_citation_correct"])
        self.assertEqual(res1["match_type"], "exact_verbatim")

        norm_citation = "tcp establishes connections using a three-way handshake syn syn-ack and ack"
        res2 = verify_citation_accuracy(norm_citation, self.sample_text, self.chunks)
        self.assertTrue(res2["is_citation_correct"])

        bogus_citation = "Quantum entanglement produces faster-than-light communication."
        res3 = verify_citation_accuracy(bogus_citation, self.sample_text, self.chunks)
        self.assertFalse(res3["is_citation_correct"])

    def test_answer_correctness(self):
        valid_q = {
            "options": ["SYN, SYN-ACK, and ACK", "FIN, ACK", "RST, PSH", "SYN only"],
            "correctAnswer": "SYN, SYN-ACK, and ACK",
            "correctIndex": 0
        }
        res = verify_answer_correctness(valid_q, self.sample_text, "SYN, SYN-ACK, and ACK")
        self.assertTrue(res["is_answer_correct"])

        missing_opt_q = {
            "options": ["Option A", "Option B"],
            "correctAnswer": "Option C",
            "correctIndex": 0
        }
        res2 = verify_answer_correctness(missing_opt_q, self.sample_text, "Option C")
        self.assertFalse(res2["is_answer_correct"])

    def test_topic_correctness(self):
        res1 = verify_topic_correctness("Computer Networks", "Computer Networks", "Transport Layer", self.sample_text)
        self.assertTrue(res1["is_topic_correct"])

        res2 = verify_topic_correctness("Ancient Roman Architecture", "Computer Networks", "Transport Layer", self.sample_text)
        self.assertFalse(res2["is_topic_correct"])

    def test_difficulty_correctness(self):
        easy_q = {
            "question": "What does TCP stand for?",
            "options": ["Transmission Control Protocol", "Total Call Plan"],
            "difficulty": "Easy"
        }
        res = verify_difficulty_correctness(easy_q)
        self.assertTrue(res["is_difficulty_reasonable"])

    def test_unsupported_question_detection(self):
        g_pass = {"is_grounded": True}
        c_pass = {"is_citation_correct": True}
        a_pass = {"is_answer_correct": True}
        self.assertFalse(detect_unsupported_question(g_pass, c_pass, a_pass))

        c_fail = {"is_citation_correct": False}
        self.assertTrue(detect_unsupported_question(g_pass, c_fail, a_pass))


class FullEvaluationSuiteTests(TestCase):
    def test_evaluation_benchmark_produces_100_questions(self):
        report = run_evaluation_benchmark(fast_deterministic=True)
        self.assertEqual(report["total_documents"], 20)
        self.assertEqual(report["total_questions"], 100)
        self.assertEqual(len(report["questions"]), 100)
        self.assertEqual(len(report["documents"]), 20)

        # Check required metrics are valid percentages
        metrics = report["metrics"]
        for key in ["grounding_accuracy", "citation_accuracy", "question_relevance", "answer_accuracy", "unsupported_question_rate"]:
            self.assertIn(key, metrics)
            val = metrics[key]
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 100.0)

        # Check 8 dimensions
        dimensions = report["dimensions"]
        self.assertEqual(len(dimensions), 8)

    def test_database_persistence_and_retrieval(self):
        report = run_evaluation_benchmark(fast_deterministic=True)
        saved_run = save_evaluation_run_to_db(report)
        self.assertIsNotNone(saved_run.id)
        self.assertEqual(EvaluationRun.objects.count(), 1)
        self.assertEqual(EvaluationQuestionResult.objects.count(), 100)

        # Retrieve latest report
        fetched = get_latest_evaluation_report(force_regenerate=False)
        self.assertEqual(fetched["run_id"], report["run_id"])
        self.assertEqual(fetched["total_questions"], 100)


class EvaluationAPITests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="eval_test@studyai.test", email="eval_test@studyai.test", password="Password123!")
        self.client = Client()
        self.client.force_login(self.user)

    def test_get_benchmark_endpoint(self):
        resp = self.client.get('/api/evaluation/benchmark/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["totalDocuments"], 20)
        self.assertEqual(data["targetQuestions"], 100)
        self.assertEqual(len(data["documents"]), 20)

    def test_get_latest_report_endpoint(self):
        resp = self.client.get('/api/evaluation/latest/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("metrics", data)
        self.assertIn("dimensions", data)
        self.assertEqual(data["total_questions"], 100)
        self.assertEqual(len(data["questions"]), 100)

    def test_post_run_evaluation_endpoint(self):
        resp = self.client.post(
            '/api/evaluation/run/',
            data=json.dumps({"fast": True}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("run_id", data)
        self.assertEqual(data["total_documents"], 20)
        self.assertEqual(data["total_questions"], 100)
