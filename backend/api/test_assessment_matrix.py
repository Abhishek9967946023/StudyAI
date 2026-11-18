from unittest.mock import patch

from django.test import SimpleTestCase

from .knowledge_engine import KnowledgeUnit
from .question_generator import GroundedQuestionGenerator
from .question_validator import QuestionValidator


class AssessmentMatrixTests(SimpleTestCase):
    def setUp(self):
        self.options = [
            "Water oxidation releases electrons.",
            "It occurs in the stroma.",
            "Protons accumulate in the lumen.",
            "It directly produces NADPH."
        ]
        self.question = {
            "question": "Which statements correctly describe water oxidation at Photosystem II?",
            "type": "msq",
            "options": self.options,
            "correctAnswer": [self.options[0], self.options[2]],
            "correctIndices": [0, 2],
            "citation": "Water oxidation releases electrons and protons into the thylakoid lumen."
        }

    def test_msq_requires_matching_answers_and_indices(self):
        validator = QuestionValidator()

        valid = validator.validate_question(self.question)
        self.assertTrue(valid.is_valid)

        invalid_question = {**self.question, "correctIndices": [0, 1]}
        invalid = validator.validate_question(invalid_question)
        self.assertFalse(invalid.is_valid)
        self.assertIn("MSQ correct_indices must match its correct answers", invalid.errors)

    @patch("api.question_generator.get_or_extract_knowledge_units")
    def test_deterministic_msq_generation_preserves_mark_tier(self, mock_extract):
        unit = KnowledgeUnit(
            id="ku-photosystem-ii",
            topic="Photosynthesis",
            subtopic="Water oxidation",
            concept="Water photolysis",
            definition="Water oxidation releases electrons that replenish Photosystem II.",
            explanation="The process also releases protons into the thylakoid lumen.",
            conditions_rules=["Oxygen is released as a by-product."]
        )
        mock_extract.return_value = [unit]
        generator = GroundedQuestionGenerator()

        questions, _ = generator.generate_and_verify_exam(
            chunks=[],
            count=1,
            question_type="msq",
            fast_mode=True,
            marks_per_question=10
        )

        self.assertEqual(len(questions), 1)
        generated = questions[0]
        self.assertEqual(generated["type"], "msq")
        self.assertEqual(generated["marks"], 10)
        self.assertGreaterEqual(len(generated["correctIndices"]), 2)
        self.assertEqual(
            {generated["options"][index] for index in generated["correctIndices"]},
            set(generated["correctAnswer"])
        )
