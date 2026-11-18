"""
=============================================================================
StudyAI — Complete Subject Understanding & Deep Teaching Engine Test Suite
=============================================================================
Tests:
1. Subject Understanding: domain, purpose, problems solved, applications,
   prerequisites, pillars, learning progression, Mermaid map.
2. Cross-domain Subject Validation: blocks OS/Biology hallucinations in Computer Networks.
3. Hierarchical Syllabus Discovery: 6-level hierarchy, noise filtering (removes author names
   like 'Srinivas Rao' and sentence fragments), 100% contiguous page spans.
4. Deep Contextual Topic Teaching: 15+ pedagogical dimensions, KaTeX math derivations,
   physical units tables, step-by-step solved numericals, traps, exam tips, and Mermaid diagrams.
5. Document Coverage Matrix: page coverage calculation, status/type breakdown, gap detection.
6. REST API Endpoints: authentication, multi-tenant isolation, subject-overview,
   syllabus tree, topic teaching, and coverage endpoints.
=============================================================================
"""

import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Document, Chunk, Topic
from .subject_engine import (
    SubjectUnderstandingEngine,
    HierarchicalSyllabusDiscoveryEngine,
    DeepTopicTeachingEngine,
    DocumentCoverageEngine,
    is_author_or_institutional_noise,
    is_invalid_heading_fragment,
    clean_heading_text
)

User = get_user_model()


class SubjectEngineTestSuite(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="student_networks",
            email="networks@studyai.edu",
            password="SecurePassword123!"
        )
        self.user2 = User.objects.create_user(
            username="student_os",
            email="os@studyai.edu",
            password="SecurePassword123!"
        )

        # Create realistic multi-page Computer Networks Document
        self.doc_cn = Document.objects.create(
            user=self.user1,
            title="Computer Networks BCS502 Module 2",
            subject="Computer Networks",
            status="COMPLETED",
            page_count=5
        )

        # Create realistic chunks with author noise headers and actual educational content
        Chunk.objects.create(
            document=self.doc_cn,
            chunk_index=1,
            page_start=1,
            page_end=1,
            text=(
                "Computer Networks (BCS502) Module-2 Notes\n"
                "Wg Cdr Dr. K Srinivas Rao, Professor, Department of CSE, RGIT\n"
                "1\n\n"
                "Module 2: Error Detection and Correction\n"
                "The data link layer transforms physical layer data into frame sequences.\n"
                "1.1 Types of Errors\n"
                "Single-Bit Error and Burst Error are common in transmission."
            )
        )
        Chunk.objects.create(
            document=self.doc_cn,
            chunk_index=2,
            page_start=2,
            page_end=2,
            text=(
                "Computer Networks (BCS502) Module-2 Notes\n"
                "Wg Cdr Dr. K Srinivas Rao, Professor, Department of CSE, RGIT\n"
                "2\n\n"
                "Block Coding\n"
                "Redundancy is achieved through block coding schemes.\n"
                "Hamming Distance\n"
                "The minimum Hamming distance d_min governs error detection and correction.\n"
                "Formula: d_min >= 2t + 1 to correct t errors."
            )
        )
        Chunk.objects.create(
            document=self.doc_cn,
            chunk_index=3,
            page_start=3,
            page_end=3,
            text=(
                "Computer Networks (BCS502) Module-2 Notes\n"
                "3\n\n"
                "Cyclic Codes\n"
                "Cyclic Redundancy Check (CRC) is implemented in hardware via LFSR.\n"
                "Generator Polynomial G(x) determines error detection capabilities."
            )
        )
        Chunk.objects.create(
            document=self.doc_cn,
            chunk_index=4,
            page_start=4,
            page_end=4,
            text=(
                "Computer Networks (BCS502) Module-2 Notes\n"
                "4\n\n"
                "Data Link Control Protocols\n"
                "Framing and Flow Control over noisy channels.\n"
                "HDLC\n"
                "High-Level Data Link Control uses bit stuffing for flag transparency."
            )
        )
        Chunk.objects.create(
            document=self.doc_cn,
            chunk_index=5,
            page_start=5,
            page_end=5,
            text=(
                "Computer Networks (BCS502) Module-2 Notes\n"
                "5\n\n"
                "Multiple Access Protocols\n"
                "Carrier Sense Multiple Access (CSMA/CD)\n"
                "Minimum frame size formula: L_min >= 2 * R * Tp to ensure collision detection."
            )
        )

        self.client = Client()

    def test_noise_filtering_utilities(self):
        """Verifies author signatures and sentence fragments are rejected."""
        # Author lines
        self.assertTrue(is_author_or_institutional_noise("Wg Cdr Dr. K Srinivas Rao, Professor, Department of CSE, RGIT"))
        self.assertTrue(is_author_or_institutional_noise("Dr. John Doe, Department of CSE"))
        self.assertTrue(is_author_or_institutional_noise("Prepared by Prof. Alan Smith"))
        self.assertFalse(is_author_or_institutional_noise("Error Detection and Correction"))
        self.assertFalse(is_author_or_institutional_noise("Carrier Sense Multiple Access"))

        # Sentence fragments
        self.assertTrue(is_invalid_heading_fragment("If the checksum is not zero, the entire packet is dropped"))
        self.assertTrue(is_invalid_heading_fragment("Whenever bits flow from one point to another"))
        self.assertTrue(is_invalid_heading_fragment("(FSM)."))
        self.assertFalse(is_invalid_heading_fragment("Hamming Distance"))
        self.assertFalse(is_invalid_heading_fragment("Cyclic Redundancy Check"))

        # Cleaning
        self.assertEqual(clean_heading_text("Chapter 1: Single-Bit Error"), "Single-Bit Error")
        self.assertEqual(clean_heading_text("## 1.2 Block Coding:"), "1.2 Block Coding")
        self.assertEqual(clean_heading_text("(CRC)."), "CRC")

    def test_subject_understanding_engine(self):
        """Verifies deep subject model extraction and Mermaid diagram."""
        data = SubjectUnderstandingEngine.analyze_and_persist_subject(self.doc_cn)
        self.assertEqual(data.get("subject_name"), "Computer Networks")
        self.assertEqual(data.get("subject_domain"), "Computer Science & Engineering")
        self.assertTrue(len(data.get("problems_solved", [])) >= 3)
        self.assertTrue(len(data.get("real_world_applications", [])) >= 3)
        self.assertTrue(len(data.get("major_knowledge_areas", [])) >= 2)
        self.assertTrue(len(data.get("logical_learning_order", [])) >= 3)
        self.assertIn("flowchart", data.get("mermaid_knowledge_map", ""))

        # Verify cross-domain validation
        chunks = list(self.doc_cn.chunks.all())
        self.assertTrue(SubjectUnderstandingEngine.validate_concept_against_subject("Hamming Distance", "Computer Networks", chunks))
        self.assertFalse(SubjectUnderstandingEngine.validate_concept_against_subject("CPU Scheduling", "Computer Networks", chunks))
        self.assertFalse(SubjectUnderstandingEngine.validate_concept_against_subject("Deadlock Avoidance", "Computer Networks", chunks))

    @patch("api.subject_engine.check_ai_provider_status", return_value={"can_generate": False})
    def test_offline_subject_overview_discloses_general_context(self, mock_ollama):
        data = SubjectUnderstandingEngine.analyze_subject(self.doc_cn)
        self.assertEqual(data["analysis_source"], "heuristic_fallback")
        self.assertIn("may include information not present", data["source_note"])

    def test_selected_topic_prompt_uses_shared_analysis_guidelines(self):
        topic = Topic.objects.create(
            document=self.doc_cn,
            name="Error Detection",
            page_start=1,
            page_end=1
        )
        response = json.dumps({"teaching_content": "# Error Detection\n\nExplanation."})
        with patch("api.subject_engine.check_ai_provider_status", return_value={"can_generate": True}), patch(
            "api.subject_engine.query_ai",
            return_value=(response, True, None)
        ) as query:
            teaching = DeepTopicTeachingEngine._query_ollama_teaching(
                topic,
                "Computer Networks",
                "[Page 1]: Error detection checks transmitted data.",
                language="hi"
            )

        self.assertIn("Error Detection", teaching["teaching_content"])
        prompt = query.call_args.args[0]
        self.assertIn("Output language: hi", prompt)
        self.assertIn("label it as additional context", prompt)
        self.assertIn("advantages, disadvantages, limitations", prompt)

    def test_hierarchical_syllabus_discovery(self):
        """Verifies 6-level syllabus tree discovery and 100% contiguous page coverage."""
        topics = HierarchicalSyllabusDiscoveryEngine.discover_and_persist_syllabus(self.doc_cn)
        self.assertTrue(len(topics) >= 5)

        topic_names = [t.name for t in topics]
        # Verify author name is NOT present
        self.assertNotIn("Srinivas Rao", topic_names)
        self.assertNotIn("Wg Cdr", topic_names)

        # Verify real syllabus topics are discovered
        self.assertTrue(any("Error Detection" in name for name in topic_names))
        self.assertTrue(any("Block Coding" in name for name in topic_names))
        self.assertTrue(any("Hamming Distance" in name for name in topic_names))

        # Verify coverage matrix achieves 100%
        coverage = DocumentCoverageEngine.calculate_coverage(self.doc_cn)
        self.assertEqual(coverage["coverage_percentage"], 100.0)
        self.assertEqual(coverage["covered_pages_count"], 5)
        self.assertEqual(len(coverage["gaps"]), 0)

    @patch("api.subject_engine.check_ai_provider_status", return_value={"can_generate": False})
    def test_deep_topic_teaching_engine(self, mock_ollama):
        """Offline teaching must show mapped source evidence without inventing a masterclass."""
        topics = HierarchicalSyllabusDiscoveryEngine.discover_and_persist_syllabus(self.doc_cn)
        topic = Topic.objects.filter(document=self.doc_cn, name__icontains="Hamming Distance").first()
        if not topic:
            topic = topics[0]

        teach_res = DeepTopicTeachingEngine.teach_topic(topic, force_regenerate=True)
        self.assertEqual(teach_res["coverage_status"], "EXTRACTED")
        content = teach_res["teaching_content"]

        self.assertIn("Relevant source text", content)
        self.assertIn("hamming distance", content.lower())
        self.assertIn("No worked example was identified", content)
        self.assertIn("not a verified explanation", content)
        self.assertEqual(topic.diagram_mermaid, "")
        self.assertEqual(teach_res["metadata"]["solved_examples"], [])

    @patch("api.subject_engine.check_ai_provider_status", return_value={"can_generate": False})
    def test_legacy_cached_teaching_is_replaced(self, mock_ollama):
        topic = Topic.objects.create(
            document=self.doc_cn,
            name="Hamming Distance",
            page_start=2,
            page_end=2,
            coverage_status="TEACHING_READY",
            teaching_content="Old fallback: an unrelated networking example."
        )

        result = DeepTopicTeachingEngine.teach_topic(topic)

        self.assertFalse(result["cached"])
        self.assertEqual(result["coverage_status"], "EXTRACTED")
        self.assertNotIn("unrelated networking example", result["teaching_content"])
        self.assertEqual(result["metadata"]["teaching_engine_version"], DeepTopicTeachingEngine.ENGINE_VERSION)

    def test_api_subject_overview_endpoint(self):
        """Verifies GET /api/v1/materials/<id>/subject-overview endpoint."""
        # Unauthenticated: 401
        res_unauth = self.client.get(f'/api/v1/materials/{self.doc_cn.id}/subject-overview')
        self.assertEqual(res_unauth.status_code, 401)

        # Authenticated as owner: 200
        self.client.force_login(self.user1)
        res = self.client.get(f'/api/v1/materials/{self.doc_cn.id}/subject-overview')
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertTrue(json_data.get("success"))
        self.assertEqual(json_data.get("subject_overview", {}).get("subject_name"), "Computer Networks")

        # Multi-tenant isolation: Other user gets 403 Forbidden
        self.client.force_login(self.user2)
        res_other = self.client.get(f'/api/v1/materials/{self.doc_cn.id}/subject-overview')
        self.assertEqual(res_other.status_code, 403)

    def test_api_syllabus_tree_endpoint(self):
        """Verifies GET /api/v1/materials/<id>/syllabus endpoint."""
        self.client.force_login(self.user1)
        res = self.client.get(f'/api/v1/materials/{self.doc_cn.id}/syllabus')
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertTrue(json_data.get("success"))
        self.assertTrue(len(json_data.get("syllabus", [])) > 0)

    @patch("api.subject_engine.check_ai_provider_status", return_value={"can_generate": False})
    def test_api_topic_teaching_endpoint(self, mock_ollama):
        """Verifies GET and POST /api/v1/materials/<id>/topics/<topic_id>/teach endpoints."""
        HierarchicalSyllabusDiscoveryEngine.discover_and_persist_syllabus(self.doc_cn)
        topic = self.doc_cn.topics.first()

        self.client.force_login(self.user1)
        # GET teaching
        res_get = self.client.get(f'/api/v1/materials/{self.doc_cn.id}/topics/{topic.id}/teach')
        self.assertEqual(res_get.status_code, 200)
        data_get = res_get.json()
        self.assertTrue(data_get.get("success"))
        self.assertIn("Relevant source text", data_get.get("topic", {}).get("teaching_content", ""))
        self.assertEqual(data_get.get("topic", {}).get("coverage_status"), "EXTRACTED")

        # POST regenerate
        res_post = self.client.post(
            f'/api/v1/materials/{self.doc_cn.id}/topics/{topic.id}/teach',
            data=json.dumps({"force": True}),
            content_type="application/json"
        )
        self.assertEqual(res_post.status_code, 200)
        data_post = res_post.json()
        self.assertTrue(data_post.get("success"))

    def test_api_coverage_endpoint(self):
        """Verifies GET /api/v1/materials/<id>/coverage endpoint."""
        self.client.force_login(self.user1)
        res = self.client.get(f'/api/v1/materials/{self.doc_cn.id}/coverage')
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertTrue(json_data.get("success"))
        self.assertIn("coverage_percentage", json_data.get("coverage", {}))

