"""
=============================================================================
StudyAI — Grounded Revision Card Engine Tests
=============================================================================
Validates:
1. Canonical Revision Card Data Contract (Section 4 & 16).
2. Answer Grounding & Anti-Placeholder Protection (Zero undefined, null, or generic placeholders).
3. Seven Pedagogical Categories (Definitions, Conceptual, Formulas, Solved Numericals, Comparisons, Algorithms, Traps).
4. RevisionTask Persistence, Sync, and Backfill.
5. REST API /api/v1/revision/plan Contract Compliance.
=============================================================================
"""

import json
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from .models import Document, Chunk, Topic, RevisionTask
from .revision_engine import (
    find_grounded_answer_for_topic,
    sync_revision_tasks_with_grounded_content,
    generate_grounded_revision_cards,
    clean_card_text,
    is_valid_text
)
from .views import get_revision_plan_view

User = get_user_model()


class RevisionEngineTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testrevisionuser", email="rev@example.com", password="password123")
        self.doc = Document.objects.create(
            title="Computer Networks GATE Study Guide",
            subject="Computer Networks",
            user=self.user,
            page_count=18,
            status="COMPLETED"
        )
        self.doc.set_summary({
            "study_guide": {
                "concepts": [
                    {
                        "term": "Bandwidth-Delay Product",
                        "definition": "The product of a data link's capacity and its round-trip time: BDP = R * RTT.",
                        "in_depth": "Represents the maximum number of unacknowledged in-flight bits required to fully saturate the link.",
                        "intuition": "Measures the data volume that fits inside the transmission pipe.",
                        "why_it_matters": "Determines the optimal TCP window size.",
                        "common_mistake": "Using one-way delay instead of RTT.",
                        "source_page": 4
                    }
                ],
                "formulas": [
                    {
                        "name": "Transmission Delay",
                        "formula": "T_{tx} = \\frac{L}{R}",
                        "intuition": "Time required to push all packet bits onto the link.",
                        "page": 3,
                        "section": "1.4 Delays"
                    }
                ],
                "examples": [
                    {
                        "title": "Sliding Window Efficiency",
                        "problem": "Calculate efficiency for window size W=7 when propagation delay is 20ms and transmission delay is 2ms.",
                        "result": "Efficiency eta = 33.3%",
                        "steps": ["a = T_prop / T_tx = 10", "eta = W / (1 + 2a) = 7 / 21 = 0.333"],
                        "why_it_works": "Window pipelining keeps the channel busy.",
                        "common_mistake": "Forgetting to multiply propagation delay by 2.",
                        "page": 7,
                        "section": "Flow Control"
                    }
                ],
                "algorithms": [
                    {
                        "name": "Dijkstra Link-State",
                        "purpose": "Finds shortest paths from single source to all nodes using non-negative link weights.",
                        "steps": ["Initialize distances to infinity", "Select minimum tentative node", "Relax outgoing edges"],
                        "complexity": "O(|V|^2) or O((|V| + |E|) log |V|)",
                        "common_mistakes": "Cannot handle negative weights",
                        "exam_pattern": "Step-by-step routing table construction",
                        "page": 12,
                        "section": "Routing Algorithms"
                    }
                ],
                "comparisons": [
                    {
                        "concept_a": "Circuit Switching",
                        "concept_b": "Packet Switching",
                        "summary": "Circuit switching reserves dedicated path and bandwidth; packet switching shares links via statistical multiplexing.",
                        "table_md": "| Feature | Circuit | Packet |\n|---|---|---|\n| Reservation | Dedicated | Statistical |",
                        "section": "Switching"
                    }
                ],
                "exam_traps": [
                    {
                        "trap": "Confusing bits and bytes in link rates",
                        "reality": "Link capacity is always in bits/s (b/s, Mb/s), while file size is typically in bytes (B).",
                        "tip": "Multiply byte sizes by 8 before calculating transmission delay."
                    }
                ]
            }
        })
        self.doc.save()

        self.t1 = Topic.objects.create(
            document=self.doc,
            name="Bandwidth-Delay Product",
            weight=90,
            source_page=4,
            description="Measures in-flight data volume."
        )
        self.t2 = Topic.objects.create(
            document=self.doc,
            name="Transmission Delay",
            weight=85,
            source_page=3,
            description="Packet serialization delay."
        )

    def test_clean_and_validation_filters(self):
        self.assertFalse(is_valid_text("undefined"))
        self.assertFalse(is_valid_text("null"))
        self.assertFalse(is_valid_text("[object Object]"))
        self.assertFalse(is_valid_text("  "))
        self.assertTrue(is_valid_text("Valid technical definition text."))

        self.assertEqual(clean_card_text("Topic: undefined"), "Topic")
        self.assertEqual(clean_card_text("null value None"), "value")

    def test_find_grounded_answer_for_topic(self):
        content = find_grounded_answer_for_topic(self.doc, "Bandwidth-Delay Product")
        self.assertIn("Bandwidth-Delay Product", content["question"])
        self.assertIn("capacity", content["answer"])
        self.assertIn("unacknowledged", content["explanation"])
        self.assertNotIn("undefined", content["answer"])

    def test_sync_revision_tasks_with_grounded_content(self):
        tasks = sync_revision_tasks_with_grounded_content(self.doc, user=self.user)
        self.assertGreaterEqual(len(tasks), 2)
        for t in tasks:
            self.assertTrue(is_valid_text(t.question))
            self.assertTrue(is_valid_text(t.answer))
            self.assertTrue(is_valid_text(t.explanation))
            self.assertNotIn("undefined", t.answer.lower())
            self.assertNotIn("core syllabus concept verified", t.answer.lower())

    def test_canonical_revision_cards_contract(self):
        plan_items, cards = generate_grounded_revision_cards(self.doc, user=self.user)
        self.assertGreater(len(cards), 5)
        
        categories = set(c["category"] for c in cards)
        self.assertIn("Remediation Topic", categories)
        self.assertIn("Mathematical Formula", categories)
        self.assertIn("Solved Numerical", categories)
        self.assertIn("Core Algorithm", categories)
        self.assertIn("Theoretical Distinction", categories)
        self.assertIn("Exam Trap", categories)

        for card in cards:
            # Canonical contract checks
            self.assertIn("id", card)
            self.assertIn("question", card)
            self.assertIn("prompt", card)
            self.assertIn("answer", card)
            self.assertIn("explanation", card)
            self.assertIn("topic", card)
            self.assertIn("difficulty", card)
            self.assertIn("source", card)
            self.assertIn("bulletPoints", card)

            # Strict content validity
            self.assertTrue(is_valid_text(card["question"]), f"Invalid question: {card}")
            self.assertTrue(is_valid_text(card["answer"]), f"Empty or invalid answer on card: {card}")
            self.assertNotIn("undefined", card["answer"].lower())
            self.assertNotIn("null", card["answer"].lower())
            self.assertNotIn("[object object]", card["answer"].lower())
            self.assertNotIn("core syllabus concept verified", card["answer"].lower())

    def test_get_revision_plan_api_view(self):
        rf = RequestFactory()
        req = rf.get(f'/api/v1/revision/plan?doc_id={self.doc.id}')
        req.user = self.user

        resp = get_revision_plan_view(req)
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(data["documentId"], self.doc.id)
        self.assertEqual(data["documentTitle"], self.doc.title)
        self.assertEqual(data["subject"], "Computer Networks")
        self.assertIn("items", data)
        self.assertIn("cards", data)
        self.assertGreater(len(data["cards"]), 0)

        first_card = data["cards"][0]
        self.assertTrue(is_valid_text(first_card.get("question")))
        self.assertTrue(is_valid_text(first_card.get("answer")))
        self.assertNotIn("undefined", first_card.get("answer"))

