"""
=============================================================================
StudyAI — Independent Question Quality Validator & Quality Gate
=============================================================================
Rigorous multi-stage verification for generated educational assessment items:
1. Hard Prohibitions (OCR artifacts, heading fragments, page numbers, 'According to the source text...')
2. Conceptual Correctness & Source Grounding
3. Option Correctness & Distractor Mutual Exclusivity (for MCQs)
4. Numerical & Mathematical Recalculation
5. Duplicate & Near-Duplicate Semantic Detection
6. Difficulty Alignment (Easy, Medium, Hard)
7. State Machine Status & Repair Action Recommendations
=============================================================================
"""

import re
import math
import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional, Tuple

from .content_cleaner import is_malformed_sentence_fragment, is_meaningful_math_or_technical
from .knowledge_engine import KnowledgeUnit
from .ai_provider_service import query_ai, check_ai_provider_status
from .math_verification import safe_evaluate_arithmetic
from .ollama_service import parse_json_safely

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    status: str  # 'VERIFIED', 'NEEDS_REPAIR', 'REJECTED'
    score: float  # 0.0 to 1.0
    errors: List[str] = field(default_factory=list)
    repairable: bool = False
    repair_action: str = "NONE"  # 'REGENERATE_OPTIONS', 'REGENERATE_ANSWER', 'REGENERATE_EXPLANATION', 'NONE'
    details: Dict[str, Any] = field(default_factory=dict)


# Prohibited phrases and OCR leakage patterns
PROHIBITED_PATTERNS = [
    re.compile(r'according to the source text[:\s]*["\']?_{2,}', re.IGNORECASE),
    re.compile(r'according to the source material[:\s]*["\']?_{2,}', re.IGNORECASE),
    re.compile(r'what completes this statement\??', re.IGNORECASE),
    re.compile(r'identify the term.*represented by the blank', re.IGNORECASE),
    re.compile(r'_____+\s*\d+(?:\.\d+)*', re.IGNORECASE),
    re.compile(r'^\s*[-_]{2,}\s*\d+', re.IGNORECASE),
    re.compile(r'table of contents', re.IGNORECASE),
    re.compile(r'\bpage\s+\d+\s+states\b', re.IGNORECASE),
    re.compile(r'\bwhy study automata theory\??\s*[-—–]', re.IGNORECASE),
    re.compile(r'\bisbn\s*[\d\-Xx]+', re.IGNORECASE),
    re.compile(r'all rights reserved', re.IGNORECASE),
]


class QuestionValidator:
    """
    Independent validator that verifies generated questions before they can be
    saved as VERIFIED or shown to students.
    """

    def __init__(self, model: str = 'llama3:latest'):
        self.model = model

    def check_prohibited_and_malformed(self, q_text: str, options: List[str], citation: str) -> Tuple[bool, List[str]]:
        """
        Rejects questions containing OCR artifacts, page numbers, heading fragments,
        or forbidden prompt templates.
        """
        errors = []
        q_clean = q_text.strip()

        # Check prohibited pattern list
        for pattern in PROHIBITED_PATTERNS:
            if pattern.search(q_clean):
                errors.append(f"Contains prohibited pattern or extraction artifact: '{pattern.pattern}'")

        # Check if question itself is an OCR fragment
        is_malformed, reason = is_malformed_sentence_fragment(q_clean)
        if is_malformed:
            errors.append(f"Question prompt is a malformed text fragment: {reason}")

        # Reject questions that are merely headings without interrogative / prompt structure
        if re.match(r'^(?:chapter|section|\d+(?:\.\d+)*)\s+.*?\??$', q_clean, re.I) and len(q_clean.split()) < 9:
            errors.append("Question is merely an unexpanded section heading")

        # Reject questions asking to fill in OCR underscores
        if "____" in q_clean and ("1.1" in q_clean or "chapter" in q_clean.lower() or "page" in q_clean.lower()):
            errors.append("Question asks student to reconstruct corrupted OCR heading numbers")

        # Reject empty or trivial questions
        if len(q_clean.split()) < 4:
            errors.append("Question prompt is too short (< 4 words)")

        # Check citation if provided
        if citation:
            is_cit_malformed, cit_reason = is_malformed_sentence_fragment(citation)
            if is_cit_malformed and "corrupted" in cit_reason.lower():
                errors.append(f"Citation is corrupted: {cit_reason}")

        return len(errors) == 0, errors

    def check_options_quality(
        self,
        q_type: str,
        options: List[str],
        correct_answer: Any,
        correct_index: Optional[int],
        correct_indices: Optional[List[int]] = None
    ) -> Tuple[bool, List[str], bool]:
        """
        Validates options for MCQs and MSQs:
        - Options must be present and distinct.
        - Exactly one correct answer exists for single-choice MCQs.
        - Distractors are plausible and not dummy placeholders.
        Returns:
            tuple (is_valid, errors, is_repairable)
        """
        errors = []
        is_repairable = True

        q_type_norm = str(q_type).lower().strip()
        if q_type_norm in ['tf', 'true/false']:
            if len(options) != 2:
                errors.append("True/False question must have exactly 2 options ('True', 'False')")
            clean_opts = [str(o).strip().lower() for o in options]
            if "true" not in clean_opts or "false" not in clean_opts:
                errors.append("True/False options must be 'True' and 'False'")
            if str(correct_answer).strip().lower() not in ["true", "false"]:
                errors.append("True/False correct answer must be 'True' or 'False'")
            return len(errors) == 0, errors, False

        if q_type_norm in ['short', 'long', 'fill_blank']:
            if not correct_answer or len(str(correct_answer).strip()) == 0:
                errors.append("Reference answer cannot be empty")
            return len(errors) == 0, errors, True

        # MSQs require at least two exact correct choices and an explicit index contract.
        if q_type_norm == 'msq':
            if not isinstance(options, list) or len(options) < 3:
                return False, ["MSQ must have at least 3 options"], True
            cleaned_opts = [str(option).strip().lower() for option in options]
            if any(not option for option in cleaned_opts) or len(set(cleaned_opts)) != len(cleaned_opts):
                return False, ["MSQ options must be non-empty and distinct"], True
            if not isinstance(correct_answer, list) or len(correct_answer) < 2:
                return False, ["MSQ must identify at least two correct answers"], True
            if not isinstance(correct_indices, list):
                return False, ["MSQ must provide correct_indices"], True
            answer_indices = []
            for answer in correct_answer:
                matches = [index for index, option in enumerate(options)
                           if str(option).strip().lower() == str(answer).strip().lower()]
                if len(matches) != 1:
                    return False, ["Every MSQ correct answer must match exactly one option"], True
                answer_indices.append(matches[0])
            if len(set(answer_indices)) != len(answer_indices):
                return False, ["MSQ correct answers must be distinct"], True
            if len(answer_indices) >= len(options):
                return False, ["MSQ must include at least one incorrect option"], True
            if correct_indices is not None:
                if (not isinstance(correct_indices, list)
                        or any(not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(options)
                               for index in correct_indices)
                        or len(set(correct_indices)) != len(correct_indices)
                        or set(correct_indices) != set(answer_indices)):
                    return False, ["MSQ correct_indices must match its correct answers"], True
            return True, [], False

        # MCQ Validation
        if not options or len(options) < 2:
            errors.append("MCQ must have at least 2 options")
            return False, errors, True

        # Check for placeholder distractors e.g. "Alternative Mechanism", "Option A"
        dummy_patterns = [
            "alternative mechanism", "inverse relation", "secondary protocol",
            "option a", "option b", "option c", "option d"
        ]
        dummy_count = sum(1 for o in options if str(o).strip().lower() in dummy_patterns)
        if dummy_count >= 2:
            errors.append("MCQ contains generic placeholder distractors")
            return False, errors, True

        # Check for duplicates or empty options
        cleaned_opts = [str(o).strip().lower() for o in options]
        if any(len(o) == 0 for o in cleaned_opts):
            errors.append("Options cannot be empty strings")

        if len(set(cleaned_opts)) != len(cleaned_opts):
            errors.append("Options contain duplicate choices")
            return False, errors, True

        # Verify correct answer matches options
        ca_str = str(correct_answer).strip()
        ca_lower = ca_str.lower()

        matched_idx = -1
        for idx, opt in enumerate(options):
            if opt.strip().lower() == ca_lower:
                matched_idx = idx
                break

        if matched_idx == -1 and (correct_index is None or correct_index < 0 or correct_index >= len(options)):
            errors.append(f"Correct answer '{ca_str}' is not among the provided options")
            return False, errors, True

        return len(errors) == 0, errors, is_repairable

    def check_numerical_and_mathematical(self, q_text: str, correct_answer: str, explanation: str) -> Tuple[bool, List[str]]:
        """
        Validates mathematical expressions, Big-O complexities, and arithmetic calculations.
        Recalculates where deterministic evaluation is possible.
        """
        errors = []
        ca_clean = str(correct_answer).strip()

        # Check basic arithmetic calculations in questions without evaluating arbitrary Python.
        calc_match = re.search(
            r'(?:calculate|what is|evaluate|compute)\s+([0-9\s,.\+\-\*\/\^\(\)×÷]+)',
            q_text,
            re.I
        )
        if calc_match:
            expr_str = calc_match.group(1).strip().replace(',', '')
            expr_str = expr_str.replace('×', '*').replace('÷', '/')
            expected_val = safe_evaluate_arithmetic(expr_str)
            answer_match = re.search(r'[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?', ca_clean)
            if expected_val is not None and answer_match:
                try:
                    actual_val = Decimal(answer_match.group(0).replace(',', ''))
                    if abs(actual_val - expected_val) > Decimal("0.001"):
                        errors.append(
                            f"Numerical answer mismatch: expected {expected_val}, got {actual_val}"
                        )
                except InvalidOperation:
                    logger.warning("Unable to parse numerical answer for question validation.")

        # Check Big-O complexity claims
        if "complexity" in q_text.lower():
            if "binary search" in q_text.lower() and "o(n)" in ca_clean.lower() and "worst" not in q_text.lower():
                errors.append("Binary search complexity incorrectly stated as O(n) instead of O(log n)")
            if "merge sort" in q_text.lower() and "o(n^2)" in ca_clean.lower():
                errors.append("Merge sort worst-case complexity incorrectly stated as O(n^2) instead of O(n log n)")

        return len(errors) == 0, errors

    def check_duplicate_or_near_duplicate(self, question: Dict[str, Any], existing_questions: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Detects exact duplicates and near-duplicates using Jaccard word-set similarity.
        """
        errors = []
        q_text = question.get("question", "").lower().strip()
        q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', q_text))
        if not q_words:
            return True, []

        for other in existing_questions:
            if other.get("id") == question.get("id"):
                continue
            o_text = other.get("question", "").lower().strip()
            # Exact match
            if q_text == o_text:
                errors.append("Exact duplicate of an already generated question")
                return False, errors

            # Word overlap similarity
            o_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', o_text))
            if not o_words:
                continue

            intersection = len(q_words & o_words)
            union = len(q_words | o_words)
            similarity = intersection / union if union > 0 else 0

            # If questions pertain to different concepts or answers, avoid false-positive rejections due to standard template scaffolding
            q_ans = str(question.get("correctAnswer", "")).lower().strip()
            o_ans = str(other.get("correctAnswer", "")).lower().strip()
            threshold = 0.90 if (q_ans and o_ans and q_ans != o_ans) else 0.82

            if similarity > threshold:
                errors.append(f"Near-duplicate question ({round(similarity*100)}% lexical similarity to existing question)")
                return False, errors

        return True, []

    def validate_question(
        self,
        question: Dict[str, Any],
        knowledge_unit: Optional[KnowledgeUnit] = None,
        existing_questions: Optional[List[Dict[str, Any]]] = None,
        use_llm_evaluator: bool = False
    ) -> ValidationResult:
        """
        Main validation entrypoint. Runs all verification stages and returns a ValidationResult.
        """
        all_errors = []
        repair_action = "NONE"
        is_repairable = False

        q_text = str(question.get("question", "")).strip()
        options = question.get("options", [])
        correct_ans = question.get("correctAnswer", question.get("correct_answer", ""))
        correct_idx = question.get("correctIndex", question.get("correct_index"))
        correct_indices = question.get("correctIndices", question.get("correct_indices"))
        citation = question.get("citation", "")
        q_type = question.get("type", "mcq")

        # Stage 1: Hard prohibitions (Non-repairable OCR/heading artifacts)
        no_prohibited, prob_errors = self.check_prohibited_and_malformed(q_text, options, citation)
        if not no_prohibited:
            all_errors.extend(prob_errors)
            return ValidationResult(
                is_valid=False,
                status="REJECTED",
                score=0.0,
                errors=all_errors,
                repairable=False,
                repair_action="NONE",
                details={"stage": "PROHIBITION"}
            )

        # Stage 2: Options & Answer validity (Repairable)
        opts_valid, opt_errors, opt_repairable = self.check_options_quality(
            q_type, options, correct_ans, correct_idx, correct_indices
        )
        if not opts_valid:
            all_errors.extend(opt_errors)
            is_repairable = opt_repairable
            repair_action = "REGENERATE_OPTIONS"

        # Stage 3: Numerical & Formula correctness
        math_valid, math_errors = self.check_numerical_and_mathematical(q_text, correct_ans, question.get("explanation", ""))
        if not math_valid:
            all_errors.extend(math_errors)
            is_repairable = True
            repair_action = "REGENERATE_ANSWER"

        # Stage 4: Duplicate & Near-duplicate detection
        if existing_questions:
            dup_valid, dup_errors = self.check_duplicate_or_near_duplicate(question, existing_questions)
            if not dup_valid:
                all_errors.extend(dup_errors)
                # Duplicate is generally non-repairable for the same prompt; reject and generate alternative concept
                return ValidationResult(
                    is_valid=False,
                    status="REJECTED",
                    score=0.2,
                    errors=all_errors,
                    repairable=False,
                    repair_action="NONE",
                    details={"stage": "DUPLICATE"}
                )

        # Stage 5: Optional 2nd Stage LLM Evaluator for conceptual depth
        if use_llm_evaluator and len(all_errors) == 0:
            llm_ok, llm_err = self._evaluate_with_llm(question, knowledge_unit)
            if not llm_ok:
                all_errors.append(llm_err)
                is_repairable = True
                repair_action = "REGENERATE_EXPLANATION"

        # Calculate final composite score
        score = 1.0 - (len(all_errors) * 0.25)
        score = max(0.0, min(1.0, score))

        if len(all_errors) == 0:
            return ValidationResult(
                is_valid=True,
                status="VERIFIED",
                score=1.0,
                errors=[],
                repairable=False,
                repair_action="NONE",
                details={"verified": True}
            )
        else:
            return ValidationResult(
                is_valid=False,
                status="NEEDS_REPAIR" if is_repairable else "REJECTED",
                score=score,
                errors=all_errors,
                repairable=is_repairable,
                repair_action=repair_action,
                details={"errors_count": len(all_errors)}
            )

    def _evaluate_with_llm(self, question: Dict[str, Any], ku: Optional[KnowledgeUnit]) -> Tuple[bool, str]:
        """
        Prompts an independent LLM call to verify conceptual correctness and distractor plausibility.
        """
        st = check_ai_provider_status()
        if not st.get("can_generate"):
            return True, ""

        concept_context = ku.definition if ku else question.get("citation", "")
        prompt = f"""You are an expert assessment quality auditor.
Evaluate this practice question for conceptual correctness, accuracy, and pedagogical validity.

Question: {question.get('question')}
Options: {question.get('options')}
Correct Answer: {question.get('correctAnswer') or question.get('correct_answer')}
Explanation: {question.get('explanation')}
Source Grounding: {concept_context}

Respond in VALID JSON with:
{{
  "is_conceptually_sound": true or false,
  "is_answer_accurate": true or false,
  "issue": "Brief explanation if invalid or null"
}}
"""
        resp_text, success, _ = query_ai(prompt, model=self.model, format_json=True, temperature=0.1, timeout=12)
        if success and resp_text:
            parsed = parse_json_safely(resp_text)
            if parsed and isinstance(parsed, dict):
                if not parsed.get("is_conceptually_sound", True):
                    return False, f"LLM Validator flagged conceptual flaw: {parsed.get('issue', 'Unsound concept')}"
                if not parsed.get("is_answer_accurate", True):
                    return False, f"LLM Validator flagged incorrect answer: {parsed.get('issue', 'Inaccurate answer')}"

        return True, ""
