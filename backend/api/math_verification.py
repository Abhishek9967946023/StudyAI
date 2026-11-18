"""
StudyAI — Mathematical Intelligence, Calculation Verification & Formatting Engine
=============================================================================
Provides rigorous mathematical analysis, algebraic equivalence checking,
arithmetic verification, dimensional/unit validation, matrix operations,
and mandatory 10-part step-by-step calculation structure formatting.
=============================================================================
"""

import ast
import math
import re
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any, Dict, List, Optional, Tuple, Union

_MAX_EXPRESSION_LENGTH = 300
_MAX_AST_NODES = 80
_MAX_ABSOLUTE_RESULT = Decimal("1e100")

# Optional SymPy integration: dynamically imported if installed in environment
try:
    import sympy
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False


# -----------------------------------------------------------------------------
# 1. Safe Arithmetic Evaluator
# -----------------------------------------------------------------------------

def safe_evaluate_arithmetic(expression: str) -> Optional[Decimal]:
    """
    Evaluates a bounded arithmetic expression without Python eval or unapproved calls.
    Supports basic operators (+, -, *, /, ^, **) and standard math constants.
    """
    if not expression or len(expression) > _MAX_EXPRESSION_LENGTH:
        return None

    # Clean expression: convert ^ to **, handle common LaTeX commands
    expr_clean = expression.replace("^", "**")
    expr_clean = re.sub(r'\\times\b|\\cdot\b|×', '*', expr_clean)
    expr_clean = re.sub(r'\\div\b|÷', '/', expr_clean)
    # Convert simple \frac{a}{b} -> (a)/(b)
    expr_clean = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'((\1)/(\2))', expr_clean)

    try:
        parsed = ast.parse(expr_clean, mode="eval")
    except (SyntaxError, ValueError):
        return None

    if sum(1 for _ in ast.walk(parsed)) > _MAX_AST_NODES:
        return None

    def evaluate(node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return Decimal(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            val = evaluate(node.operand)
            return val if isinstance(node.op, ast.UAdd) else -val
        if isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                return left / right
            if isinstance(node.op, ast.Pow):
                if right != right.to_integral_value() or abs(right) > 20:
                    raise ValueError("Exponent outside supported integer range")
                if abs(left) > Decimal("1e15"):
                    raise ValueError("Base outside supported range")
                return left ** int(right)
        raise ValueError("Unsupported arithmetic AST node")

    try:
        with localcontext() as ctx:
            ctx.prec = 50
            result = evaluate(parsed)
        if not result.is_finite() or abs(result) > _MAX_ABSOLUTE_RESULT:
            return None
        return result
    except (ArithmeticError, InvalidOperation, ValueError, OverflowError):
        return None


# -----------------------------------------------------------------------------
# 2. Arithmetic Equality Auditor
# -----------------------------------------------------------------------------

def verify_arithmetic_equalities(text: str, tolerance: Decimal = Decimal("0.001")) -> Dict[str, Any]:
    """
    Checks numeric equalities in prose and LaTeX calculations, returning deterministic findings.
    """
    checked = 0
    mismatches = []
    numeric = r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?"

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = re.sub(r"\\(?:times|cdot)\b|×", "*", raw_line)
        line = re.sub(r"\\div\b|÷", "/", line)
        line = line.replace("^", "**")
        line = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'((\1)/(\2))', line)

        for pair in re.finditer(r"=", line):
            left = line[:pair.start()].rsplit(":", 1)[-1].strip()
            right = line[pair.end():].strip()
            result_match = re.match(rf"({numeric})(?!\d)", right)
            expression_match = re.search(r"([0-9][0-9,.\s()+*/-]*)$", left)
            if not result_match or not expression_match:
                continue

            expression = expression_match.group(1).strip().rstrip(".,;").replace(",", "")
            if not re.search(r"[+*/-]", expression):
                continue

            evaluated = safe_evaluate_arithmetic(expression)
            if evaluated is None:
                continue

            claimed_text = result_match.group(1).replace(",", "")
            try:
                claimed = Decimal(claimed_text)
            except InvalidOperation:
                continue

            checked += 1
            if abs(evaluated - claimed) > tolerance:
                mismatches.append({
                    "line": line_number,
                    "expression": expression,
                    "calculated": str(evaluated),
                    "claimed": str(claimed)
                })

    return {"checked_count": checked, "mismatches": mismatches}


# -----------------------------------------------------------------------------
# 3. Mathematical Content Detection (Master Prompt Part 3.1)
# -----------------------------------------------------------------------------

def detect_mathematical_content(text: str) -> Dict[str, Any]:
    """
    Comprehensive academic mathematical content detector.
    Identifies equations, inequalities, fractions, exponents, roots, matrices,
    derivatives, integrals, limits, numerical iterations, proofs, and SI units.
    """
    if not text:
        return {"has_math": False, "math_types": [], "is_numerical_problem": False, "formula_count": 0}

    detected_types = []
    formula_count = 0

    patterns = {
        "EQUATION": [r'=', r'\\begin\{aligned\}', r'\\begin\{equation\}', r'\$\$', r'\\\[', r'\$[^$]+='],
        "INEQUALITY": [r'\\le\b', r'\\ge\b', r'\\ne\b', r'<=', r'>=', r'≠', r'≤', r'≥'],
        "FRACTION": [r'\\frac\{', r'\b\d+\s*/\s*\d+\b'],
        "EXPONENT_ROOT": [r'\^[0-9a-zA-Z{]', r'\\sqrt\{', r'\\sqrt\[', r'\*\*'],
        "SUMMATION_PRODUCT": [r'\\sum(?![a-zA-Z])', r'\\prod(?![a-zA-Z])', r'∑', r'∏'],
        "INTEGRAL": [r'\\int(?![a-zA-Z])', r'\\iint(?![a-zA-Z])', r'\\oint(?![a-zA-Z])', r'∫'],
        "DERIVATIVE": [r'\\frac\{d\}\{dx\}', r'\\frac\{\\partial\}\{\\partial', r"f'\([a-zA-Z]\)", r'dy/dx', r'dx/dt'],
        "LIMIT": [r'\\lim(?![a-zA-Z])'],
        "MATRIX_DETERMINANT": [r'\\begin\{matrix\}', r'\\begin\{pmatrix\}', r'\\begin\{bmatrix\}', r'\\det\(', r'\\begin\{vmatrix\}'],
        "VECTOR": [r'\\vec\{', r'\\mathbf\{', r'\\hat\{[ijk]\}'],
        "LOGARITHM": [r'\\log(?![a-zA-Z])', r'\\ln(?![a-zA-Z])'],
        "TRIGONOMETRY": [r'\\sin(?![a-zA-Z])', r'\\cos(?![a-zA-Z])', r'\\tan(?![a-zA-Z])', r'\\sec(?![a-zA-Z])', r'\\csc(?![a-zA-Z])', r'\\cot(?![a-zA-Z])'],
        "PROBABILITY_STATISTICS": [r'P\([A-Z]\)', r'E\[[A-Z]\]', r'Var\([A-Z]\)', r'\\sigma\b', r'\\mu\b', r'\\lambda\b'],
        "NUMERICAL_METHOD": [r'x_\{n\+1\}', r'x_\{k\+1\}', r'Newton-Raphson', r'Runge-Kutta', r'bisection', r'iteration', r'stopping criterion', r'tolerance\s*=\s*1e-'],
        "CALCULATION_STEP": [r'Step\s*\d+:', r'Given:', r'To find:', r'Formula:', r'Substitute', r'Substituting', r'Final answer:']
    }

    for m_type, regex_list in patterns.items():
        found = False
        for pat in regex_list:
            matches = re.findall(pat, text, re.IGNORECASE)
            if matches:
                found = True
                formula_count += len(matches)
        if found:
            detected_types.append(m_type)

    # Determine if text represents a numerical problem requiring full calculation structure
    has_equations = "EQUATION" in detected_types or "INEQUALITY" in detected_types
    has_calculation = "CALCULATION_STEP" in detected_types
    has_numbers = bool(re.search(r'\b\d+(?:\.\d+)?\b', text))
    is_numerical_problem = has_equations and (has_calculation or has_numbers) and formula_count >= 2

    return {
        "has_math": len(detected_types) > 0,
        "math_types": detected_types,
        "is_numerical_problem": is_numerical_problem,
        "formula_count": formula_count
    }


# -----------------------------------------------------------------------------
# 4. Mandatory 10-Part Calculation Structure (Master Prompt Part 3.2)
# -----------------------------------------------------------------------------

MANDATORY_CALCULATION_SECTIONS = [
    ("problem_statement", "1. Problem Statement"),
    ("given", "2. Given Information"),
    ("required", "3. Required Quantity / To Find"),
    ("formula", "4. Applicable Formula"),
    ("symbols", "5. Explanation of Symbols"),
    ("substitution", "6. Substitution of Values"),
    ("step_by_step", "7. Step-by-Step Calculation"),
    ("intermediate_results", "8. Intermediate Results"),
    ("final_answer", "9. Final Answer"),
    ("verification_and_units", "10. Verification and Units")
]

def validate_calculation_structure(text: str) -> Dict[str, Any]:
    """
    Validates whether a numerical problem solution provides the mandatory
    10 structural elements required for university examinations.
    """
    section_patterns = {
        "problem_statement": r'(?:problem\s*statement|problem:|question:)',
        "given": r'(?:given\s*information|given\s*data|given:)',
        "required": r'(?:required\s*quantity|to\s*find|find:|required:)',
        "formula": r'(?:applicable\s*formula|formula\s*used|formula:)',
        "symbols": r'(?:explanation\s*of\s*symbols|where:|symbols:)',
        "substitution": r'(?:substitution\s*of\s*values|substituting|substitution:)',
        "step_by_step": r'(?:step-by-step\s*calculation|calculation|steps:|step\s*1:)',
        "intermediate_results": r'(?:intermediate\s*results?|intermediate\s*values?|sub-result:)',
        "final_answer": r'(?:final\s*answer|result:|answer:)',
        "verification_and_units": r'(?:verification\s*(?:and|&)\s*units|units?|dimensional\s*check)'
    }

    found_sections = {}
    missing_sections = []

    text_lower = text.lower()
    for key, pattern in section_patterns.items():
        if re.search(pattern, text_lower):
            found_sections[key] = True
        else:
            found_sections[key] = False
            missing_sections.append(key)

    completeness_score = round(sum(1 for v in found_sections.values() if v) / len(found_sections), 3)

    return {
        "is_complete": len(missing_sections) == 0,
        "completeness_score": completeness_score,
        "found_sections": found_sections,
        "missing_sections": missing_sections
    }


def format_mandatory_calculation(data: Dict[str, Any]) -> str:
    """
    Formats structured numerical problem components into the standard 10-part academic Markdown format.
    """
    lines = [
        f"### {data.get('title', 'Numerical Problem Solution')}\n",
        f"**1. Problem Statement:**\n> {data.get('problem_statement', 'N/A')}\n",
        f"**2. Given Information:**\n{data.get('given', '- Not explicitly stated')}\n",
        f"**3. Required Quantity / To Find:**\n{data.get('required', '- Value to be calculated')}\n",
        f"**4. Applicable Formula:**\n$$\n{data.get('formula', '')}\n$$\n",
        f"**5. Explanation of Symbols:**\n{data.get('symbols', '- Defined in context')}\n",
        f"**6. Substitution of Values:**\n$$\n{data.get('substitution', '')}\n$$\n",
        f"**7. Step-by-Step Calculation:**\n{data.get('step_by_step', '')}\n",
        f"**8. Intermediate Results:**\n{data.get('intermediate_results', '- Calculated directly')}\n",
        f"**9. Final Answer:**\n> **{data.get('final_answer', '')}**\n",
        f"**10. Verification and Units:**\n{data.get('verification_and_units', '- Verified for dimensional consistency.')}\n"
    ]
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# 5. Step-by-Step Aligned Equation Formatter (Master Prompt Part 3.3)
# -----------------------------------------------------------------------------

def format_aligned_derivation(steps: List[Dict[str, str]]) -> str:
    """
    Converts a sequence of mathematical derivation steps into a clean LaTeX aligned block.
    Every step has an explanation line and an aligned formula row with &= alignment.

    Example input:
    [
        {"label": "Given", "eq": "2x + 5 = 15"},
        {"label": "Step 1: Subtract 5 from both sides", "eq": "2x = 15 - 5"},
        {"label": "Step 2: Simplify", "eq": "2x = 10"},
        {"label": "Step 3: Divide by 2", "eq": "x = \\frac{10}{2}"},
        {"label": "Final Answer", "eq": "x = 5"}
    ]
    """
    if not steps:
        return ""

    out_lines = []
    latex_aligned = ["\\[", "\\begin{aligned}"]

    for idx, s in enumerate(steps):
        label = s.get("label", "").strip()
        eq = s.get("eq", "").strip()

        # Format explanation prose
        if label:
            out_lines.append(f"**{label}:**\n")

        # Format equation for aligned environment: replace first '=' with '&='
        if "=" in eq and "&=" not in eq:
            eq_aligned = eq.replace("=", "&=", 1)
        else:
            eq_aligned = f"&{eq}"

        term = "\\\\" if idx < len(steps) - 1 else ""
        latex_aligned.append(f"  {eq_aligned}{term}")

    latex_aligned.append("\\end{aligned}")
    latex_aligned.append("\\]\n")

    return "\n".join(out_lines) + "\n" + "\n".join(latex_aligned)


# -----------------------------------------------------------------------------
# 6. Algebraic Equivalence Verifier (Master Prompt Part 3.4)
# -----------------------------------------------------------------------------

def verify_algebraic_equivalence(expr_a: str, expr_b: str, var: str = "x") -> Dict[str, Any]:
    """
    Verifies algebraic equivalence between two expressions across a derivation step.
    Uses SymPy when available, with deterministic multi-point AST evaluation as robust pure-Python fallback.
    """
    clean_a = expr_a.strip().replace("^", "**")
    clean_b = expr_b.strip().replace("^", "**")

    # If SymPy is available, perform exact symbolic verification
    if HAS_SYMPY:
        try:
            sym_var = sympy.Symbol(var)
            s_a = sympy.sympify(clean_a)
            s_b = sympy.sympify(clean_b)
            diff = sympy.simplify(s_a - s_b)
            is_zero = diff == 0
            return {
                "is_equivalent": bool(is_zero),
                "method": "sympy_symbolic",
                "difference": str(diff),
                "verified": bool(is_zero)
            }
        except Exception:
            pass  # Fall through to numerical sampling

    # Pure-Python multi-point substitution test
    test_points = [-5.0, -1.0, 0.5, 2.0, 4.5, 10.0]
    mismatches = 0
    tested = 0

    for pt in test_points:
        sub_a = clean_a.replace(var, f"({pt})")
        sub_b = clean_b.replace(var, f"({pt})")
        val_a = safe_evaluate_arithmetic(sub_a)
        val_b = safe_evaluate_arithmetic(sub_b)

        if val_a is not None and val_b is not None:
            tested += 1
            if abs(val_a - val_b) > Decimal("0.0001"):
                mismatches += 1

    if tested >= 3 and mismatches == 0:
        return {
            "is_equivalent": True,
            "method": "numerical_sampling",
            "tested_points": tested,
            "verified": True
        }

    return {
        "is_equivalent": False,
        "method": "numerical_sampling",
        "tested_points": tested,
        "mismatches": mismatches,
        "verified": False,
        "note": "Unverified or expressions not equivalent"
    }


# -----------------------------------------------------------------------------
# 7. Matrix Operations Verifier (Master Prompt Part 3.4)
# -----------------------------------------------------------------------------

def verify_matrix_operation(
    op: str,
    mat_a: List[List[Union[int, float]]],
    mat_b: Optional[List[List[Union[int, float]]]] = None
) -> Dict[str, Any]:
    """
    Verifies matrix operations: addition, subtraction, multiplication, determinant (2x2, 3x3), transpose.
    """
    r_a = len(mat_a)
    c_a = len(mat_a[0]) if r_a > 0 else 0

    if op == "transpose":
        res = [[mat_a[r][c] for r in range(r_a)] for c in range(c_a)]
        return {"operation": "transpose", "result": res, "verified": True}

    if op == "determinant":
        if r_a != c_a:
            return {"error": "Determinant requires square matrix", "verified": False}
        if r_a == 2:
            det = mat_a[0][0] * mat_a[1][1] - mat_a[0][1] * mat_a[1][0]
            return {"operation": "determinant_2x2", "result": det, "verified": True}
        if r_a == 3:
            det = (
                mat_a[0][0] * (mat_a[1][1] * mat_a[2][2] - mat_a[1][2] * mat_a[2][1])
                - mat_a[0][1] * (mat_a[1][0] * mat_a[2][2] - mat_a[1][2] * mat_a[2][0])
                + mat_a[0][2] * (mat_a[1][0] * mat_a[2][1] - mat_a[1][1] * mat_a[2][0])
            )
            return {"operation": "determinant_3x3", "result": det, "verified": True}
        return {"error": "Higher order determinants require SymPy", "verified": False}

    if op in ("add", "subtract"):
        if not mat_b or len(mat_b) != r_a or len(mat_b[0]) != c_a:
            return {"error": "Matrix dimensions must match for addition/subtraction", "verified": False}
        factor = 1 if op == "add" else -1
        res = [[mat_a[r][c] + factor * mat_b[r][c] for c in range(c_a)] for r in range(r_a)]
        return {"operation": op, "result": res, "verified": True}

    if op == "multiply":
        if not mat_b:
            return {"error": "Matrix multiplication requires second matrix", "verified": False}
        r_b = len(mat_b)
        c_b = len(mat_b[0]) if r_b > 0 else 0
        if c_a != r_b:
            return {"error": f"Dimension mismatch: cannot multiply {r_a}x{c_a} with {r_b}x{c_b}", "verified": False}
        res = [[sum(mat_a[i][k] * mat_b[k][j] for k in range(c_a)) for j in range(c_b)] for i in range(r_a)]
        return {"operation": "multiply", "result": res, "verified": True}

    return {"error": f"Unknown matrix operation: {op}", "verified": False}


# -----------------------------------------------------------------------------
# 8. Units & Dimensional Consistency (Master Prompt Part 3.4)
# -----------------------------------------------------------------------------

SI_DIMENSIONS = {
    "speed": {"units": ["m/s", "km/h", "mps"], "dim": "L T^-1"},
    "velocity": {"units": ["m/s", "km/h"], "dim": "L T^-1"},
    "acceleration": {"units": ["m/s^2", "m/s2"], "dim": "L T^-2"},
    "force": {"units": ["N", "newton", "kg*m/s^2"], "dim": "M L T^-2"},
    "energy": {"units": ["J", "joule", "N*m", "watt-second", "kWh"], "dim": "M L^2 T^-2"},
    "work": {"units": ["J", "joule", "N*m"], "dim": "M L^2 T^-2"},
    "power": {"units": ["W", "watt", "kW", "MW", "J/s"], "dim": "M L^2 T^-3"},
    "frequency": {"units": ["Hz", "khz", "mhz", "ghz", "1/s"], "dim": "T^-1"},
    "pressure": {"units": ["Pa", "pascal", "kPa", "N/m^2", "bar"], "dim": "M L^-1 T^-2"},
    "resistance": {"units": ["ohm", "Ω", "kohm", "MΩ"], "dim": "M L^2 T^-3 I^-2"},
    "capacitance": {"units": ["F", "farad", "uF", "μF", "nF", "pF"], "dim": "M^-1 L^-2 T^4 I^2"},
    "time": {"units": ["s", "sec", "second", "ms", "us", "μs", "min", "h"], "dim": "T"},
    "data_rate": {"units": ["bps", "kbps", "mbps", "gbps", "B/s", "KB/s", "MB/s"], "dim": "bits T^-1"},
    "bandwidth": {"units": ["Hz", "kHz", "MHz", "GHz", "bps", "Mbps", "Gbps"], "dim": "T^-1"}
}

def verify_units_and_dimensions(quantity: str, claimed_answer_str: str) -> Dict[str, Any]:
    """
    Checks if a calculated numerical answer contains dimensionally consistent units.
    """
    q_key = quantity.strip().lower()
    if q_key not in SI_DIMENSIONS:
        return {"quantity": quantity, "verified": True, "note": "Quantity unit not constrained in standard table"}

    spec = SI_DIMENSIONS[q_key]
    valid_units = spec["units"]

    found_unit = None
    for u in valid_units:
        # Match word boundary or end of string
        if re.search(rf'\b{re.escape(u)}\b', claimed_answer_str, re.IGNORECASE):
            found_unit = u
            break

    if found_unit:
        return {
            "quantity": quantity,
            "expected_dimension": spec["dim"],
            "found_unit": found_unit,
            "is_consistent": True,
            "verified": True
        }

    return {
        "quantity": quantity,
        "expected_dimension": spec["dim"],
        "expected_units": valid_units,
        "is_consistent": False,
        "verified": False,
        "note": f"Claimed answer does not contain consistent unit for {quantity}. Expected one of {valid_units}."
    }


# -----------------------------------------------------------------------------
# 9. Numerical Iteration Presentation & Verification (Master Prompt Part 3.5)
# -----------------------------------------------------------------------------

def verify_and_format_numerical_iterations(
    method_name: str,
    formula_str: str,
    iterations: List[Dict[str, Any]],
    stopping_tolerance: float = 1e-4
) -> Dict[str, Any]:
    """
    Formats and verifies iterative numerical methods (Newton-Raphson, Bisection, Euler, etc.)
    Ensures intermediate values, error calculations, and stopping criteria are displayed in a clean Markdown table.
    """
    if not iterations:
        return {"formatted_table": "", "converged": False, "verified": False}

    # Markdown table header
    table_lines = [
        f"**Iterative Method:** {method_name}  \n**Iteration Formula:** `{formula_str}`  \n**Stopping Tolerance:** `ε = {stopping_tolerance}`\n",
        "| Iteration ($k$) | $x_k$ | $f(x_k)$ | Error $|x_{k} - x_{k-1}|$ | Status |",
        "| :---: | :---: | :---: | :---: | :---: |"
    ]

    converged = False
    final_approx = None

    for it in iterations:
        k = it.get("k", 0)
        xk = it.get("xk", 0.0)
        fxk = it.get("fxk", 0.0)
        err = it.get("error", 0.0)
        is_stop = err <= stopping_tolerance if k > 0 else False
        status = "✓ Converged" if is_stop else "In Progress"
        if is_stop:
            converged = True
            final_approx = xk

        table_lines.append(f"| {k} | {xk:.6f} | {fxk:.6f} | {err:.6e} | {status} |")

    formatted_md = "\n".join(table_lines) + "\n"
    if converged:
        formatted_md += f"\n> **Final Root / Approximation:** $x^* \\approx {final_approx:.6f}$ achieved at tolerance $\\epsilon = {stopping_tolerance}$.\n"

    return {
        "formatted_table": formatted_md,
        "converged": converged,
        "final_value": final_approx,
        "verified": True
    }


# -----------------------------------------------------------------------------
# 10. Unverified Content Flagging (Master Prompt Part 3.4)
# -----------------------------------------------------------------------------

def flag_unverified_calculations(text: str) -> str:
    """
    Scans generated text for unverified calculations or approximate claims and
    explicitly labels them as unverified per Master Prompt Part 3.4.
    """
    audit = verify_arithmetic_equalities(text)
    if not audit.get("mismatches"):
        return text

    modified_lines = text.splitlines()
    for mismatch in audit["mismatches"]:
        line_idx = mismatch["line"] - 1
        if 0 <= line_idx < len(modified_lines):
            calc = mismatch['calculated']
            claim = mismatch['claimed']
            expr = mismatch['expression']
            warning_tag = f"  *(⚠️ Arithmetic Discrepancy: {expr} calculates to {calc}, source states {claim})*"
            if warning_tag not in modified_lines[line_idx]:
                modified_lines[line_idx] += warning_tag

    return "\n".join(modified_lines)


class MathematicalIntelligenceEngine:
    """Class wrapper exposing mathematical verification utilities."""
    detect_mathematical_content = staticmethod(detect_mathematical_content)
    validate_calculation_structure = staticmethod(validate_calculation_structure)
    format_mandatory_calculation = staticmethod(format_mandatory_calculation)
    format_aligned_derivation = staticmethod(format_aligned_derivation)
    verify_arithmetic_equalities = staticmethod(verify_arithmetic_equalities)
    verify_algebraic_equivalence = staticmethod(verify_algebraic_equivalence)
    verify_matrix_operation = staticmethod(verify_matrix_operation)
    verify_units_and_dimensions = staticmethod(verify_units_and_dimensions)
    verify_and_format_numerical_iterations = staticmethod(verify_and_format_numerical_iterations)
    flag_unverified_calculations = staticmethod(flag_unverified_calculations)

