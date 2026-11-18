from decimal import Decimal
from unittest import TestCase

from .math_verification import (
    detect_mathematical_content,
    validate_calculation_structure,
    format_mandatory_calculation,
    format_aligned_derivation,
    verify_algebraic_equivalence,
    verify_matrix_operation,
    verify_units_and_dimensions,
    verify_and_format_numerical_iterations,
    flag_unverified_calculations,
    safe_evaluate_arithmetic,
    verify_arithmetic_equalities
)


class MathematicalIntelligenceTests(TestCase):
    def test_detect_mathematical_content_identifies_equations_and_calculus(self):
        text = r"Consider the function $f(x) = \int_0^x \frac{d}{dx}(\sin(t)) dt$ and $\lim_{x \to 0} f(x) = 0$."
        res = detect_mathematical_content(text)
        self.assertTrue(res["has_math"])
        self.assertIn("EQUATION", res["math_types"])
        self.assertIn("INTEGRAL", res["math_types"])
        self.assertIn("DERIVATIVE", res["math_types"])
        self.assertIn("LIMIT", res["math_types"])
        self.assertIn("TRIGONOMETRY", res["math_types"])

    def test_detect_mathematical_content_identifies_numerical_problems(self):
        text = (
            "Given: mass m = 10 kg, acceleration a = 5 m/s^2.\n"
            "Step 1: Formula F = m * a.\n"
            "Step 2: Calculate F = 10 * 5 = 50 N.\n"
            "Final answer: 50 N."
        )
        res = detect_mathematical_content(text)
        self.assertTrue(res["has_math"])
        self.assertTrue(res["is_numerical_problem"])
        self.assertIn("CALCULATION_STEP", res["math_types"])

    def test_validate_calculation_structure_complete(self):
        text = (
            "1. Problem Statement: Compute force.\n"
            "2. Given Information: mass 10 kg, acc 5 m/s2.\n"
            "3. Required Quantity: Force F.\n"
            "4. Applicable Formula: F = m * a\n"
            "5. Explanation of Symbols: m is mass, a is acc.\n"
            "6. Substitution of Values: F = 10 * 5\n"
            "7. Step-by-Step Calculation: Step 1: multiply.\n"
            "8. Intermediate Results: F = 50\n"
            "9. Final Answer: 50 N\n"
            "10. Verification and Units: Dimensional check [M L T^-2] matches Newton."
        )
        res = validate_calculation_structure(text)
        self.assertTrue(res["is_complete"])
        self.assertEqual(res["completeness_score"], 1.0)
        self.assertEqual(res["missing_sections"], [])

    def test_validate_calculation_structure_flags_missing(self):
        text = "Problem: find x. 2x = 10, so x = 5. Answer: 5."
        res = validate_calculation_structure(text)
        self.assertFalse(res["is_complete"])
        self.assertIn("given", res["missing_sections"])
        self.assertIn("verification_and_units", res["missing_sections"])

    def test_format_aligned_derivation(self):
        steps = [
            {"label": "Given", "eq": "2*x + 5 = 15"},
            {"label": "Step 1: Subtract 5", "eq": "2*x = 15 - 5"},
            {"label": "Step 2: Simplify", "eq": "2*x = 10"},
            {"label": "Step 3: Divide by 2", "eq": "x = 5"},
        ]
        out = format_aligned_derivation(steps)
        self.assertIn(r"\begin{aligned}", out)
        self.assertIn(r"2*x + 5 &= 15", out)
        self.assertIn(r"2*x &= 10", out)
        self.assertIn(r"x &= 5", out)
        self.assertIn(r"\end{aligned}", out)

    def test_verify_algebraic_equivalence(self):
        # 2x + 5 - 5 should be algebraically equivalent to 2x
        res = verify_algebraic_equivalence("2*x + 5 - 5", "2*x", var="x")
        self.assertTrue(res["is_equivalent"])
        self.assertTrue(res["verified"])

        # 2x != 3x
        res2 = verify_algebraic_equivalence("2*x", "3*x", var="x")
        self.assertFalse(res2["is_equivalent"])

    def test_verify_matrix_operations(self):
        # Transpose
        mat = [[1, 2, 3], [4, 5, 6]]
        trans = verify_matrix_operation("transpose", mat)
        self.assertEqual(trans["result"], [[1, 4], [2, 5], [3, 6]])

        # 2x2 Determinant
        m2 = [[2, 3], [1, 4]]
        det2 = verify_matrix_operation("determinant", m2)
        self.assertEqual(det2["result"], 2 * 4 - 3 * 1)  # 5

        # 3x3 Determinant
        m3 = [[1, 2, 3], [0, 4, 5], [1, 0, 6]]
        det3 = verify_matrix_operation("determinant", m3)
        # 1*(24-0) - 2*(0-5) + 3*(0-4) = 24 + 10 - 12 = 22
        self.assertEqual(det3["result"], 22)

        # Matrix Multiplication
        a = [[1, 2], [3, 4]]
        b = [[2, 0], [1, 2]]
        mult = verify_matrix_operation("multiply", a, b)
        # [[1*2 + 2*1, 1*0 + 2*2], [3*2 + 4*1, 3*0 + 4*2]] = [[4, 4], [10, 8]]
        self.assertEqual(mult["result"], [[4, 4], [10, 8]])

    def test_verify_units_and_dimensions(self):
        # Valid speed
        res1 = verify_units_and_dimensions("speed", "The vehicle travels at 25 m/s.")
        self.assertTrue(res1["is_consistent"])
        self.assertEqual(res1["found_unit"], "m/s")

        # Invalid power (given in meters)
        res2 = verify_units_and_dimensions("power", "Total power dissipated is 100 meters.")
        self.assertFalse(res2["is_consistent"])
        self.assertIn("Expected one of", res2["note"])

    def test_verify_and_format_numerical_iterations(self):
        iterations = [
            {"k": 0, "xk": 2.0, "fxk": 1.0, "error": 1.0},
            {"k": 1, "xk": 1.5, "fxk": 0.25, "error": 0.5},
            {"k": 2, "xk": 1.416667, "fxk": 0.006944, "error": 0.083333},
            {"k": 3, "xk": 1.414216, "fxk": 0.000006, "error": 0.00005}
        ]
        res = verify_and_format_numerical_iterations(
            "Newton-Raphson", "x_{k+1} = x_k - f(x_k)/f'(x_k)", iterations, stopping_tolerance=1e-4
        )
        self.assertTrue(res["converged"])
        self.assertIn("✓ Converged", res["formatted_table"])
        self.assertIn("1.414216", res["formatted_table"])

    def test_flag_unverified_calculations(self):
        text = "Calculation: 10 * 5 = 60."
        flagged = flag_unverified_calculations(text)
        self.assertIn("⚠️ Arithmetic Discrepancy", flagged)
        self.assertIn("calculates to 50", flagged)

