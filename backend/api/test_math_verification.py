from decimal import Decimal
from unittest import TestCase

from .math_verification import safe_evaluate_arithmetic, verify_arithmetic_equalities
from .question_validator import QuestionValidator


class MathVerificationTests(TestCase):
    def test_safe_evaluator_handles_basic_expressions(self):
        self.assertEqual(safe_evaluate_arithmetic("2 ^ 4 + 3 * (5 - 2)"), Decimal("25"))

    def test_safe_evaluator_rejects_names_calls_and_unbounded_exponents(self):
        self.assertIsNone(safe_evaluate_arithmetic("__import__('os').system('whoami')"))
        self.assertIsNone(safe_evaluate_arithmetic("2 ** 1000000"))
        self.assertIsNone(safe_evaluate_arithmetic("answer + 1"))

    def test_arithmetic_audit_checks_latex_style_calculation_and_flags_mismatch(self):
        valid = verify_arithmetic_equalities(
            r"Step 2: $EAT = 0.99 \times 100 + 0.01 \times 10000000 = 100099$ ns."
        )
        self.assertEqual(valid["checked_count"], 1)
        self.assertEqual(valid["mismatches"], [])

        invalid = verify_arithmetic_equalities("Calculation: 15 * 4 = 50.")
        self.assertEqual(invalid["checked_count"], 1)
        self.assertEqual(invalid["mismatches"][0]["calculated"], "60")
        self.assertEqual(invalid["mismatches"][0]["claimed"], "50")

    def test_question_validator_detects_incorrect_numerical_answer(self):
        validator = QuestionValidator()
        valid, errors = validator.check_numerical_and_mathematical("What is 2 + 3?", "5", "")
        self.assertTrue(valid)
        self.assertEqual(errors, [])

        valid, errors = validator.check_numerical_and_mathematical("What is 2 + 3?", "6", "")
        self.assertFalse(valid)
        self.assertIn("Numerical answer mismatch", errors[0])
