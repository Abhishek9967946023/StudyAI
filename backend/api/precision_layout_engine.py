"""
=============================================================================
StudyAI — Precision Line Alignment & Technical Layout Engine (Phase 7)
=============================================================================
Provides micro-typographic and structural precision formatting:
1. High-fidelity sentence continuation & logical paragraph reconstruction
2. Hanging list indentation calculation (marker alignment & wrapped line indent)
3. Technical procedure & pseudocode step indentation
4. Standardized 10-part numerical problem solver formatting
5. LaTeX multi-line derivation alignment (aligned environments)
6. Table column width distribution and multi-page break split protection
=============================================================================
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional

from .typography_system import DocumentTypography

logger = logging.getLogger(__name__)

# Known prefixes where hyphenation at line breaks was an artifact of column justification
KNOWN_PREFIXES = {
    'de', 're', 'in', 'un', 'dis', 'mis', 'pre', 'post', 'sub', 'inter',
    'trans', 'over', 'under', 'multi', 'semi', 'non', 'micro', 'macro',
    'auto', 'tele', 'comput', 'struc', 'oper', 'deterio', 'engi', 'pro',
    'algo', 'infor', 'charac', 'imple', 'distri', 'paral', 'seque'
}

# Naturally hyphenated compounds that MUST keep their hyphens
NATURALLY_HYPHENATED = {
    'client-server', 'trade-off', 'trade-offs', 'step-by-step', 'real-time',
    'end-to-end', 'built-in', 'state-of-the-art', 'peer-to-peer', 'round-trip',
    'bandwidth-delay', 'stop-and-wait', 'go-back-n', 'cut-through', 'store-and-forward',
    'fault-tolerant', 'high-level', 'low-level', 'object-oriented', 'first-principles',
    'user-friendly', 'three-way', 'two-phase', 'read-only', 'write-only', 'single-page',
    'multi-threading', 'open-source', 'cross-platform', 'cost-effective'
}

COMMON_ABBREVIATIONS = {
    'e.g.', 'i.e.', 'etc.', 'et al.', 'vs.', 'fig.', 'figs.', 'no.', 'vol.',
    'dr.', 'prof.', 'dept.', 'approx.', 'univ.', 'p.', 'pp.', 'ch.', 'sec.',
    'eq.', 'eqs.', 'ref.', 'refs.', 'min.', 'max.', 'avg.', 'st.'
}


class PrecisionLayoutEngine:
    """
    Precision typography, paragraph reconstruction, list alignment, and layout engine.
    """

    # -------------------------------------------------------------------------
    # 1. Logical Paragraph Reconstruction & Line Segmentation
    # -------------------------------------------------------------------------

    @classmethod
    def reconstruct_logical_paragraphs(cls, text: str) -> str:
        """
        Transforms fragmented or artificially line-broken extracted text into clean,
        logically coherent paragraphs.
        - Joins broken lines within sentences
        - Repairs soft hyphenations (algo- rithm -> algorithm)
        - Preserves headings, list items, tables, code blocks, and formulas intact
        """
        if not text:
            return ""

        # Normalize line endings
        normalized = text.replace('\r\n', '\n')
        lines = normalized.split('\n')
        reconstructed = []
        i = 0

        while i < len(lines):
            line = lines[i]
            s = line.strip()

            if not s:
                reconstructed.append("")
                i += 1
                continue

            # 1. Structural Boundaries — Do NOT merge across these
            is_boundary = (
                s.startswith(('#', '>', '|', '```', '$$', r'\[', r'\begin{')) or
                re.match(r'^(?:[-*•]|\d+[\.\)]|[a-zA-Z][\.\)])\s+', s) or
                re.match(r'^(?:Algorithm|Step\s+\d|Procedure|Table|Figure)\b', s, re.I)
            )

            if is_boundary:
                reconstructed.append(line)
                i += 1
                continue

            # 2. Check if current line continues onto the next line
            curr_text = line
            while i + 1 < len(lines):
                next_line = lines[i + 1]
                next_s = next_line.strip()

                if not next_s:
                    break

                # If next line is a boundary, stop merging
                next_is_boundary = (
                    next_s.startswith(('#', '>', '|', '```', '$$', r'\[', r'\begin{')) or
                    re.match(r'^(?:[-*•]|\d+[\.\)]|[a-zA-Z][\.\)])\s+', next_s) or
                    re.match(r'^(?:Algorithm|Step\s+\d|Procedure|Table|Figure)\b', next_s, re.I)
                )
                if next_is_boundary:
                    break

                # Punctuation & Continuation Rules:
                # Does current line end with terminating punctuation?
                ends_with_terminator = bool(re.search(r'[.!?:]\s*$', curr_text.rstrip()))
                # Does next line begin with lowercase letter?
                starts_with_lowercase = bool(re.match(r'^[a-z]', next_s))
                # Does current line end with hyphen?
                ends_with_hyphen = curr_text.rstrip().endswith('-')

                if ends_with_hyphen:
                    # Hyphen repair
                    clean_curr = curr_text.rstrip()[:-1].rstrip()
                    first_word_next = next_s.split()[0]
                    compound = f"{clean_curr.split()[-1]}-{first_word_next}".lower()

                    if compound in NATURALLY_HYPHENATED:
                        curr_text = f"{clean_curr}-{next_s}"
                    else:
                        curr_text = f"{clean_curr}{next_s}"
                    i += 1
                elif not ends_with_terminator or starts_with_lowercase:
                    # Sentence continuation
                    curr_text = f"{curr_text.rstrip()} {next_s}"
                    i += 1
                else:
                    break

            reconstructed.append(curr_text)
            i += 1

        return '\n'.join(reconstructed)

    # -------------------------------------------------------------------------
    # 2. List & Technical Step Alignment
    # -------------------------------------------------------------------------

    @classmethod
    def align_list_items(cls, text: str) -> str:
        """
        Ensures consistent list formatting:
        - Joins isolated list numbers ('1.\nText' -> '1. Text')
        - Normalizes bullet points ('*' or '+' to standard '-')
        - Enforces clean sequential numbered lists
        """
        lines = text.replace('\r\n', '\n').split('\n')
        aligned_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            s = line.strip()

            # Join isolated list numbers
            if re.match(r'^(?:\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s*$', s):
                if i + 1 < len(lines) and lines[i + 1].strip():
                    aligned_lines.append(f"{s} {lines[i + 1].strip()}")
                    i += 2
                    continue

            # Standardize bullet markers
            if re.match(r'^\s*[*+•]\s+', line):
                line = re.sub(r'^(\s*)[*+•]\s+', r'\1- ', line)

            aligned_lines.append(line)
            i += 1

        return '\n'.join(aligned_lines)

    # -------------------------------------------------------------------------
    # 3. 10-Part Step-by-Step Numerical Problem Formatting
    # -------------------------------------------------------------------------

    @classmethod
    def format_step_by_step_numerical_solution(cls, problem_data: Dict[str, Any]) -> str:
        """
        Formats a numerical calculation into the standardized 10-part pedagogical structure:
        1. Problem Statement
        2. Given Information
        3. Required Quantity
        4. Applicable Formula
        5. Explanation of Symbols
        6. Substitution of Values
        7. Step-by-Step Calculation (Aligned LaTeX)
        8. Intermediate Results
        9. Final Answer
        10. Verification and Units Check
        """
        lines = []

        statement = (problem_data.get("statement") or problem_data.get("problem") or problem_data.get("problem_statement") or "").strip()
        given = problem_data.get("given", {})
        required = problem_data.get("required", "").strip()
        formula = problem_data.get("formula", "").strip()
        symbols = problem_data.get("symbols", {})
        substitution = problem_data.get("substitution", "").strip()
        calculation_steps = problem_data.get("calculation_steps", [])
        intermediate_results = problem_data.get("intermediate_results", [])
        final_answer = problem_data.get("final_answer", "").strip()
        units = problem_data.get("units", "").strip()
        verification = problem_data.get("verification", "").strip()

        # 1. Problem Statement
        if statement:
            lines.append(f"**Problem Statement**:\n{statement}\n")

        # 2. Given Data
        if given:
            lines.append("**Given Data**:")
            if isinstance(given, dict):
                for k, v in given.items():
                    lines.append(f"- ${k} = {v}$")
            elif isinstance(given, list):
                for item in given:
                    lines.append(f"- {item}")
            lines.append("")

        # 3. Required Quantity
        if required:
            lines.append(f"**To Determine**: {required}\n")

        # 4. Applicable Formula
        if formula:
            clean_f = formula.strip('$')
            lines.append(f"**Governing Formula**:\n$${clean_f}$$\n")

        # 5. Explanation of Symbols
        if symbols and isinstance(symbols, dict):
            lines.append("**Symbols Definition**:")
            for sym, desc in symbols.items():
                lines.append(f"- ${sym}$: {desc}")
            lines.append("")

        # 6. Substitution
        if substitution:
            lines.append(f"**Value Substitution**:\n$${substitution.strip('$')}$$\n")

        # 7. Step-by-Step Calculation (Aligned Environment)
        if calculation_steps:
            lines.append("**Step-by-Step Derivation**:")
            aligned_lines = [r"\[", r"\begin{aligned}"]
            for step in calculation_steps:
                if isinstance(step, dict):
                    lhs = step.get("lhs", "")
                    rhs = step.get("rhs", "")
                    just = f"&& \\text{{({step['justification']})}}" if step.get("justification") else ""
                    aligned_lines.append(f"  {lhs} &= {rhs} {just} \\\\")
                elif isinstance(step, str):
                    if '=' in step:
                        parts = step.split('=', 1)
                        aligned_lines.append(f"  {parts[0].strip()} &= {parts[1].strip()} \\\\")
                    else:
                        aligned_lines.append(f"  &{step.strip()} \\\\")
            aligned_lines.extend([r"\end{aligned}", r"\]", ""])
            lines.append("\n".join(aligned_lines))

        # 8. Intermediate Results
        if intermediate_results:
            lines.append("**Intermediate Results**:")
            if isinstance(intermediate_results, dict):
                for k, v in intermediate_results.items():
                    lines.append(f"- **{k}**: {v}")
            elif isinstance(intermediate_results, list):
                for ir in intermediate_results:
                    lines.append(f"- {ir}")
            lines.append("")

        # 9. Final Answer
        if final_answer:
            unit_str = f" {units}" if units else ""
            lines.append(f"> **Final Result**: **{final_answer}{unit_str}**\n")

        # 10. Verification
        if verification:
            lines.append(f"*Dimensional Verification*: {verification}\n")

        return "\n".join(lines).strip()

    # -------------------------------------------------------------------------
    # 4. Multi-Line LaTeX Equation Alignment
    # -------------------------------------------------------------------------

    @classmethod
    def align_multiline_equations(cls, markdown_text: str) -> str:
        """
        Normalizes multi-line mathematical calculations to use LaTeX aligned environments:
        \\[ \\begin{aligned} LHS &= RHS \\\\ ... \\end{aligned} \\]
        Ensures operators and equal signs align vertically without text clipping.
        """
        # Find multi-line $$ blocks with chained equals
        def format_aligned_block(match):
            inner = match.group(1).strip()
            raw_lines = [l.strip() for l in re.split(r'\\\\|\n', inner) if l.strip()]
            if len(raw_lines) >= 2 and any('=' in l for l in raw_lines) and not inner.startswith(r'\begin{'):
                aligned_body = []
                for l in raw_lines:
                    if '=' in l and '&' not in l:
                        parts = l.split('=', 1)
                        aligned_body.append(f"{parts[0].strip()} &= {parts[1].strip()} \\\\")
                    else:
                        aligned_body.append(f"{l} \\\\")
                return f"\\[\n\\begin{{aligned}}\n" + "\n".join(aligned_body) + f"\n\\end{{aligned}}\n\\]"
            return match.group(0)

        pattern = r'\$\$(.+?)\$\$'
        return re.sub(pattern, format_aligned_block, markdown_text, flags=re.DOTALL)

    # -------------------------------------------------------------------------
    # 5. Table Geometry & Multi-Page Continuity
    # -------------------------------------------------------------------------

    @classmethod
    def calculate_table_column_widths(
        cls,
        table_rows: List[List[str]],
        total_printable_width: float = DocumentTypography.PRINTABLE_WIDTH_PT
    ) -> List[float]:
        """
        Calculates proportional, aesthetically balanced column widths for ReportLab tables.
        Prevents text wrapping in narrow columns while allocating adequate space to explanatory cells.
        """
        if not table_rows:
            return [total_printable_width]

        num_cols = max(len(r) for r in table_rows)
        if num_cols == 0:
            return [total_printable_width]

        # Calculate max character length per column
        col_max_lengths = [0] * num_cols
        for row in table_rows:
            for c_idx in range(num_cols):
                val = row[c_idx] if c_idx < len(row) else ""
                col_max_lengths[c_idx] = max(col_max_lengths[c_idx], len(val.strip()))

        # If column holds only small numbers / codes (length <= 5), assign minimal width
        total_weight = 0
        weights = []
        for l in col_max_lengths:
            w = max(10, min(100, l))
            weights.append(w)
            total_weight += w

        widths = [(w / total_weight) * total_printable_width for w in weights]
        return widths
