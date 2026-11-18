"""
=============================================================================
StudyAI — Source-Grounded Question Generation & Repair Pipeline
=============================================================================
Orchestrates:
1. Extraction of verified Knowledge Units from cleaned document chunks.
2. Coverage Planning across topics, cognitive levels, and question types.
3. Generation grounded exclusively in Knowledge Units (never raw OCR fragments).
4. Independent validation via QuestionValidator.
5. Automated targeted repair with bounded retries.
6. Replacement generation for rejected items.
7. Final quality gate guaranteeing only VERIFIED questions reach students.
=============================================================================
"""

import re
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from .knowledge_engine import KnowledgeUnit, get_or_extract_knowledge_units
from .question_validator import QuestionValidator, ValidationResult
from .ai_provider_service import query_ai, check_ai_provider_status
from .ollama_service import parse_json_safely

logger = logging.getLogger(__name__)


@dataclass
class GenerationSlot:
    slot_id: int
    topic: str
    subtopic: str
    question_type: str
    difficulty: str
    cognitive_level: str  # 'definition', 'conceptual', 'application', 'numerical', 'trace', 'construction'
    knowledge_unit: Optional[KnowledgeUnit] = None
    marks: int = 1


@dataclass
class GenerationStats:
    requested: int = 0
    generating: int = 0
    validating: int = 0
    verified: int = 0
    repairing: int = 0
    rejected: int = 0
    retries: int = 0


class GroundedQuestionGenerator:
    """
    Core engine for generating strictly source-grounded educational assessment items.
    """

    def __init__(self, model: str = 'llama3:latest', validator_model: str = 'heuristic+llama3'):
        self.model = model
        self.validator = QuestionValidator(model=validator_model)

    def create_coverage_plan(
        self,
        knowledge_units: List[KnowledgeUnit],
        count: int,
        topic_focus: str,
        difficulty: str,
        question_type: str,
        marks_per_question: int = 1
    ) -> List[GenerationSlot]:
        """
        Creates an educational coverage plan across diverse concepts and cognitive levels.
        Prevents repetitively generating questions on the exact same definition.
        """
        if not knowledge_units:
            return []

        # Determine question types sequence
        req_type = str(question_type or 'mixed').lower().strip()
        if req_type in ['tf', 'true/false', 'true_false']:
            types_pool = ['tf']
        elif req_type in ['short', 'short_answer', 'sa']:
            types_pool = ['short']
        elif req_type in ['long', 'long_answer', 'long answer']:
            types_pool = ['long']
        elif req_type in ['fill_blank', 'fill in the blank', 'fill-in-the-blank']:
            types_pool = ['fill_blank']
        elif req_type in ['numerical', 'math']:
            types_pool = ['numerical']
        elif req_type in ['mcq']:
            types_pool = ['mcq']
        elif req_type in ['msq', 'multiple_select', 'multiple select']:
            types_pool = ['msq']
        elif req_type in ['vtu', 'vtu_exam', 'vtu_blueprint']:
            # VTU University Exam Pattern:
            # - Part A: 2-Mark definitions/principles
            # - Part B: 5-Mark diagrams/comparisons
            # - Part C: 10-Mark comprehensive multi-part questions
            slots: List[GenerationSlot] = []
            ku_count = len(knowledge_units)
            vtu_specs = [
                ('short', 2, 'definition', 'Easy'),
                ('short', 2, 'conceptual', 'Easy'),
                ('long', 5, 'comparison', 'Medium'),
                ('long', 5, 'trace', 'Medium'),
                ('long', 10, 'application', 'Hard'),
                ('numerical', 10, 'construction', 'Hard'),
            ]
            for i in range(count):
                spec = vtu_specs[i % len(vtu_specs)]
                ku = knowledge_units[i % ku_count]
                slots.append(GenerationSlot(
                    slot_id=i + 1,
                    topic=ku.topic if topic_focus == 'All' else topic_focus,
                    subtopic=ku.subtopic,
                    question_type=spec[0],
                    difficulty=spec[3],
                    cognitive_level=spec[2],
                    knowledge_unit=ku,
                    marks=spec[1]
                ))
            return slots
        else:  # mixed / all
            types_pool = ['mcq', 'tf', 'short', 'msq', 'mcq', 'tf', 'numerical']

        cognitive_levels = ['definition', 'conceptual', 'application', 'trace', 'construction']
        diff_levels = ['easy', 'medium', 'hard'] if difficulty.lower() == 'adaptive' else [difficulty.lower()]

        slots: List[GenerationSlot] = []
        ku_count = len(knowledge_units)

        for i in range(count):
            ku = knowledge_units[i % ku_count]
            q_type = types_pool[i % len(types_pool)]
            cog = cognitive_levels[i % len(cognitive_levels)]
            diff = diff_levels[i % len(diff_levels)]

            slots.append(GenerationSlot(
                slot_id=i + 1,
                topic=ku.topic if topic_focus == 'All' else topic_focus,
                subtopic=ku.subtopic,
                question_type=q_type,
                difficulty=diff.capitalize(),
                cognitive_level=cog,
                knowledge_unit=ku,
                marks=marks_per_question
            ))

        return slots

    def generate_single_question_llm(self, slot: GenerationSlot) -> Optional[Dict[str, Any]]:
        """
        Generates a question from a verified KnowledgeUnit using an LLM prompt.
        """
        ku = slot.knowledge_unit
        if not ku:
            return None

        type_instructions = ""
        if slot.question_type == 'tf':
            type_instructions = """Question type: True/False.
Options MUST be EXACTLY: ["True", "False"].
Correct answer MUST be "True" or "False".
correct_index MUST be 0 for True or 1 for False."""
        elif slot.question_type == 'fill_blank':
            type_instructions = """Question type: Fill in the Blank.
Create one clear blank for a key term explicitly present in the Knowledge Unit.
Options MUST be [] and correct_answer MUST be the exact missing term."""
        elif slot.question_type == 'long':
            type_instructions = """Question type: Long Answer.
Ask for a structured explanation based only on the Knowledge Unit.
Options MUST be [] and correct_answer MUST be a detailed source-grounded reference answer."""
        elif slot.question_type == 'short':
            type_instructions = """Question type: Short Answer / Conceptual.
Options MUST be [].
Correct answer MUST be a concise 1-2 sentence reference answer.
correct_index MUST be null."""
        elif slot.question_type == 'numerical':
            type_instructions = """Question type: Numerical / Problem-Solving.
Include specific numbers, formulas, or algorithmic complexity values.
Options MUST be 4 distinct numerical/complexity choices.
Correct answer MUST be the exact correct choice from the options."""
        elif slot.question_type == 'msq':
            type_instructions = """Question type: Multiple Select (MSQ).
Provide 4 distinct options and at least 2 correct options in "correct_answers".
Every correct answer must exactly match an option. Include "correct_indices" as the zero-based indexes of all correct options.
Do not return a single "correct_answer"."""
        else:  # MCQ
            type_instructions = """Question type: Multiple Choice (MCQ).
Provide 4 plausible, mutually exclusive options in "options".
Options MUST NOT be generic placeholders like "Option A" or "Alternative Mechanism".
Exactly ONE option must be correct.
Provide "correct_answer" as the exact string of the correct option."""

        prompt = f"""You are StudyAI Assessment Designer.
Generate ONE high-quality educational exam question based STRICTLY on this verified Knowledge Unit.

Concept: {ku.concept}
Topic: {slot.topic}
Subtopic: {slot.subtopic}
Definition: {ku.definition}
Explanation: {ku.explanation}
Formula / Rules: {ku.formula or 'N/A'} {', '.join(ku.conditions_rules)}
Target Difficulty: {slot.difficulty}
Cognitive Goal: {slot.cognitive_level}
Marks: {slot.marks}. Calibrate expected answer depth to this mark value; do not pad or invent unsupported requirements.
For long-answer reference answers, 2 marks should cover the core definition and one key fact; 5 marks should use a concise, ordered set of supported points; 10 marks should provide a structured explanation with mechanisms, examples, formulas, or diagrams only when present in the Knowledge Unit.
{type_instructions}

STRICT PROHIBITIONS:
1. NEVER start the question with "According to the source text..." or "What completes this statement?".
2. NEVER ask questions about page numbers, chapter headers, or table-of-contents fragments.
3. NEVER make the question ask the student to reconstruct missing OCR text or underscores.
4. The question must test genuine understanding of "{ku.concept}".

Respond in VALID JSON with EXACTLY this structure:
{{
  "question": "<Thoughtful educational question prompt>",
  "type": "{slot.question_type}",
  "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"] or ["True", "False"] or [],
  "correct_answer": "<Exact string of correct choice>",
  "correct_answers": ["<Exact correct choice 1>", "<Exact correct choice 2>"],
  "correct_indices": [0, 2],
  "marks": {slot.marks},
  "correct_index": 0,
  "explanation": "<Pedagogical rationale explaining why the answer is correct>",
  "citation": "{ku.definition[:150]}",
  "difficulty": "{slot.difficulty}",
  "topic": "{slot.topic}",
  "subtopic": "{slot.subtopic}"
}}
"""

        resp_text, success, _ = query_ai(prompt, model=self.model, format_json=True, temperature=0.2, timeout=22)
        if success and resp_text:
            parsed = parse_json_safely(resp_text)
            if parsed and isinstance(parsed, dict) and "question" in parsed:
                return {
                    "id": f"q-gen-{slot.slot_id}",
                    "number": slot.slot_id,
                    "question": parsed.get("question"),
                    "type": slot.question_type,
                    "options": parsed.get("options", []),
                    "correctAnswer": (
                        parsed.get("correct_answers", parsed.get("correctAnswer", []))
                        if slot.question_type == 'msq'
                        else parsed.get("correct_answer")
                    ),
                    "correctIndex": parsed.get("correct_index"),
                    "correctIndices": parsed.get("correct_indices"),
                    "explanation": parsed.get("explanation", ""),
                    "citation": parsed.get("citation", ku.definition),
                    "topic": slot.topic,
                    "difficulty": slot.difficulty,
                    "source_page": ku.source_page,
                    "source_chunk": ku.source_chunk_id,
                    "knowledge_unit_id": ku.id
                }

        return None

    def generate_single_question_deterministic(self, slot: GenerationSlot) -> Dict[str, Any]:
        """
        High-precision deterministic template generator grounded exclusively in verified Knowledge Units.
        Guarantees educational validity when LLM is offline or in fast mode.
        """
        ku = slot.knowledge_unit
        concept = ku.concept if ku else "Core Concept"
        definition = ku.definition if ku else "Core educational definition."
        page = ku.source_page if ku else 1
        chunk_id = ku.source_chunk_id if ku else 1

        cog = slot.cognitive_level
        if slot.question_type == 'tf':
            is_true = (slot.slot_id % 2 == 1)
            if is_true:
                q_text = f"True or False: In {slot.subtopic}, {concept} satisfies the following principle: \"{definition}\""
                c_ans = "True"
                c_idx = 0
                expl = f"Directly confirmed in the syllabus study material: {definition}"
            else:
                negated = definition
                if " is " in definition:
                    negated = definition.replace(" is ", " is not ", 1)
                elif " can " in definition:
                    negated = definition.replace(" can ", " cannot ", 1)
                elif " always " in definition:
                    negated = definition.replace(" always ", " does not always ", 1)
                elif " permits " in definition:
                    negated = definition.replace(" permits ", " prohibits ", 1)
                elif " avoids " in definition:
                    negated = definition.replace(" avoids ", " causes ", 1)
                elif " maintains " in definition:
                    negated = definition.replace(" maintains ", " discards ", 1)
                else:
                    negated = f"Contrary to standard principles, {definition.lower()}"

                q_text = f"True or False: In {slot.subtopic}, {concept} satisfies the following principle: \"{negated}\""
                c_ans = "False"
                c_idx = 1
                expl = f"This assertion is false. The correct principle states: {definition}"

            return {
                "id": f"q-det-{slot.slot_id}",
                "number": slot.slot_id,
                "question": q_text,
                "type": "tf",
                "options": ["True", "False"],
                "correctAnswer": c_ans,
                "correctIndex": c_idx,
                "explanation": expl,
                "citation": definition,
                "topic": slot.topic,
                "difficulty": slot.difficulty,
                "source_page": page,
                "source_chunk": chunk_id,
                "knowledge_unit_id": ku.id if ku else None
            }

        elif slot.question_type == 'fill_blank':
            concept_pattern = re.compile(re.escape(concept), re.I)
            if concept_pattern.search(definition):
                cloze_text = concept_pattern.sub("_____", definition, count=1)
                q_text = f"Fill in the missing key term: {cloze_text}"
            else:
                q_text = (
                    "Fill in the missing concept described by this source definition: "
                    f"_____ — {definition}"
                )
            return {
                "id": f"q-det-{slot.slot_id}",
                "number": slot.slot_id,
                "question": q_text,
                "type": "fill_blank",
                "options": [],
                "correctAnswer": concept,
                "correctIndex": None,
                "explanation": f"The source defines {concept} as: {definition}",
                "citation": definition,
                "topic": slot.topic,
                "difficulty": slot.difficulty,
                "source_page": page,
                "source_chunk": chunk_id,
                "knowledge_unit_id": ku.id if ku else None
            }

        elif slot.question_type == 'long':
            answer_parts = [definition]
            if ku and ku.explanation and ku.explanation.strip() != definition.strip():
                answer_parts.append(ku.explanation)
            if ku and ku.formula:
                answer_parts.append(f"Related formula or rule: {ku.formula}")
            if ku and ku.conditions_rules:
                answer_parts.append("Conditions and rules: " + "; ".join(ku.conditions_rules))
            long_answer = "\n\n".join(answer_parts)

            if slot.marks == 5:
                q_text = (
                    f"[VTU Part B - 5 Marks] Provide a structured analysis of {concept} in {slot.subtopic}. "
                    "Explain its core mechanism, characteristics, and provide a neat diagram/table if applicable."
                )
                expl = (
                    f"Reference answer assembled from this verified source unit:\n\n{long_answer}\n\n"
                    f"[Mark Breakdown: 2 Marks for diagram/structure, 3 Marks for explanation and characteristics]\n"
                    f"[GROUND_TRUTH_SOURCE] (Source: Page {page})"
                )
            elif slot.marks == 10:
                q_text = (
                    f"[VTU Part C - 10 Marks] Comprehensively explain {concept} in {slot.subtopic}. "
                    "Detail its theoretical foundations, step-by-step working, advantages, limitations, and practical applications."
                )
                expl = (
                    f"Reference answer assembled from this verified source unit:\n\n{long_answer}\n\n"
                    f"[Mark Breakdown: 4 Marks for architecture/mechanism, 3 Marks for advantages/limitations, 3 Marks for practical example]\n"
                    f"[GROUND_TRUTH_SOURCE] (Source: Page {page})"
                )
            else:
                q_text = (
                    f"Give a structured explanation of {concept} in {slot.subtopic}, "
                    "using the source definition and any related mechanism, formula, or rules provided."
                )
                expl = f"Reference answer assembled from this verified source unit: {long_answer}"

            return {
                "id": f"q-det-{slot.slot_id}",
                "number": slot.slot_id,
                "question": q_text,
                "type": "long",
                "options": [],
                "marks": slot.marks,
                "correctAnswer": long_answer,
                "correctIndex": None,
                "explanation": expl,
                "citation": definition,
                "topic": slot.topic,
                "difficulty": slot.difficulty,
                "source_page": page,
                "source_chunk": chunk_id,
                "knowledge_unit_id": ku.id if ku else None
            }

        elif slot.question_type == 'msq' and ku:
            facts = [definition]
            if ku.explanation and ku.explanation.strip().lower() != definition.strip().lower():
                facts.append(ku.explanation.strip())
            if ku.formula:
                facts.append(f"Related formula or rule: {ku.formula}")
            facts.extend(rule.strip() for rule in ku.conditions_rules if rule.strip())
            facts = list(dict.fromkeys(facts))
            correct_options = facts[:2]
            if len(correct_options) < 2:
                correct_options = [definition]
            distractors = []
            for fact in correct_options:
                if " is " in fact:
                    distractors.append(fact.replace(" is ", " is not ", 1))
                elif " are " in fact:
                    distractors.append(fact.replace(" are ", " are not ", 1))
                elif " can " in fact:
                    distractors.append(fact.replace(" can ", " cannot ", 1))
                elif " has " in fact:
                    distractors.append(fact.replace(" has ", " does not have ", 1))
                else:
                    distractors.append(f"It is not true that {fact}")

            options = correct_options + distractors
            if len({option.strip().lower() for option in options}) != len(options):
                options = correct_options + [
                    f"This is not a property of {concept}: {correct_options[0]}",
                    f"This is not a property of {concept}: {correct_options[1]}"
                ]
            rot = slot.slot_id % len(options)
            options = options[rot:] + options[:rot]
            correct_indices = [index for index, option in enumerate(options) if option in correct_options]
            return {
                "id": f"q-det-{slot.slot_id}",
                "number": slot.slot_id,
                "question": f"Select all statements that correctly describe {concept} in {slot.subtopic}.",
                "type": "msq",
                "options": options,
                "correctAnswer": correct_options,
                "correctIndices": correct_indices,
                "explanation": f"The selected statements are grounded in the source: {'; '.join(correct_options)}",
                "citation": definition,
                "topic": slot.topic,
                "difficulty": slot.difficulty,
                "source_page": page,
                "source_chunk": chunk_id,
                "knowledge_unit_id": ku.id
            }

        elif slot.question_type == 'short':
            if slot.marks == 2:
                q_prefix = "[VTU Part A - 2 Marks] "
                expl_suffix = f"\n\n[Mark Breakdown: 2 Marks for exact definition/principle]\n[GROUND_TRUTH_SOURCE] (Source: Page {page})"
            else:
                q_prefix = ""
                expl_suffix = f"\n(Source: Page {page})"

            if cog == 'property':
                q_text = f"{q_prefix}Identify the key characteristics and operational properties of {concept} in {slot.subtopic}."
            elif cog == 'application':
                q_text = f"{q_prefix}Explain how {concept} is applied in practical system execution within {slot.subtopic}."
            elif cog == 'conceptual':
                q_text = f"{q_prefix}Explain the underlying principles and conceptual mechanism behind {concept}."
            elif cog == 'trace':
                q_text = f"{q_prefix}Trace the operational workflow and state transitions of {concept} in {slot.subtopic}."
            elif cog == 'construction':
                q_text = f"{q_prefix}Describe how {concept} is structured and organized within {slot.subtopic}."
            else:
                q_text = f"{q_prefix}In the study of {slot.topic}, explain the core role and formal definition of {concept}."

            return {
                "id": f"q-det-{slot.slot_id}",
                "number": slot.slot_id,
                "question": q_text,
                "type": "short",
                "options": [],
                "marks": slot.marks,
                "correctAnswer": definition,
                "correctIndex": None,
                "explanation": f"Grounded in verified curriculum concepts: {definition}{expl_suffix}",
                "citation": definition,
                "topic": slot.topic,
                "difficulty": slot.difficulty,
                "source_page": page,
                "source_chunk": chunk_id,
                "knowledge_unit_id": ku.id if ku else None
            }

        elif slot.question_type == 'numerical' and ku and ku.formula:
            q_text = f"For {concept}, identify the correct governing formula or expression:"
            options = [
                ku.formula,
                re.sub(r'[\+\-\*]', lambda m: '+' if m.group(0) == '-' else '-', ku.formula, count=1),
                f"O(n^2) where {concept} is applied",
                f"Undefined for non-deterministic configurations"
            ]
            options = list(dict.fromkeys(options))
            while len(options) < 4:
                options.append(f"Standard alternative {len(options)}")
            c_ans = ku.formula
            c_idx = 0

            return {
                "id": f"q-det-{slot.slot_id}",
                "number": slot.slot_id,
                "question": q_text,
                "type": "numerical",
                "options": options,
                "correctAnswer": c_ans,
                "correctIndex": c_idx,
                "explanation": f"The governing formula is formally established as: {ku.formula}",
                "citation": definition,
                "topic": slot.topic,
                "difficulty": slot.difficulty,
                "source_page": page,
                "source_chunk": chunk_id,
                "knowledge_unit_id": ku.id if ku else None
            }

        else:  # MCQ
            if cog == 'property':
                q_text = f"Which characteristic or property is true regarding {concept}?"
            elif cog == 'application':
                q_text = f"In practical system design, how is {concept} effectively applied?"
            elif cog == 'behavior':
                q_text = f"What is the operational function or behavior of {concept}?"
            elif cog == 'contrast':
                q_text = f"Which statement accurately distinguishes {concept} in {slot.subtopic}?"
            else:
                q_text = f"Which of the following best characterizes {concept}?"

            correct_option = definition
            distractors = [
                f"It is an unrestricted structure that violates the properties of {slot.subtopic}.",
                f"It operates exclusively without finite state constraints or transition rules.",
                f"It is defined inversely to standard deterministic transition semantics."
            ]
            options = [correct_option] + distractors
            rot = slot.slot_id % 4
            options = options[rot:] + options[:rot]
            c_idx = options.index(correct_option)

            return {
                "id": f"q-det-{slot.slot_id}",
                "number": slot.slot_id,
                "question": q_text,
                "type": "mcq",
                "options": options,
                "correctAnswer": correct_option,
                "correctIndex": c_idx,
                "explanation": f"{concept} is correctly characterized as follows: {definition}",
                "citation": definition,
                "topic": slot.topic,
                "difficulty": slot.difficulty,
                "source_page": page,
                "source_chunk": chunk_id,
                "knowledge_unit_id": ku.id if ku else None
            }


    def repair_question(self, question: Dict[str, Any], validation_res: ValidationResult, slot: GenerationSlot) -> Optional[Dict[str, Any]]:
        """
        Executes bounded targeted repair when a question fails validation with a repairable issue.
        """
        repaired = dict(question)
        ku = slot.knowledge_unit

        if validation_res.repair_action == "REGENERATE_OPTIONS":
            # Reconstruct options cleanly with valid distractors
            if ku:
                if slot.question_type == 'msq':
                    return self.generate_single_question_deterministic(slot)
                correct = ku.definition
                distractors = [
                    f"A concept unrelated to {slot.subtopic} operating under alternative semantics.",
                    f"An unbounded configuration that rejects the rules of {ku.concept}.",
                    f"A secondary mechanism with non-deterministic state growth."
                ]
                new_opts = [correct] + distractors
                rot = slot.slot_id % 4
                new_opts = new_opts[rot:] + new_opts[:rot]
                repaired["options"] = new_opts
                repaired["correctAnswer"] = correct
                repaired["correctIndex"] = new_opts.index(correct)
                return repaired

        elif validation_res.repair_action == "REGENERATE_ANSWER":
            if ku:
                repaired["correctAnswer"] = ku.definition
                repaired["explanation"] = f"Verified answer based on syllabus source: {ku.definition}"
                return repaired

        return None

    def generate_and_verify_exam(
        self,
        chunks: List[Dict[str, Any]],
        topic: str = "All",
        count: int = 5,
        difficulty: str = "medium",
        question_type: str = "mcq",
        fast_mode: bool = False,
        marks_per_question: int = 1
    ) -> Tuple[List[Dict[str, Any]], GenerationStats]:
        """
        Complete end-to-end question generation, validation, repair, and filtering pipeline.
        Guarantees that 100% of returned questions are VERIFIED.
        """
        stats = GenerationStats(requested=count)

        # Step 1: Extract verified Knowledge Units
        stats.generating = count
        kus = get_or_extract_knowledge_units(chunks, topic_focus=topic, model=self.model, fast_mode=fast_mode)
        if not kus:
            return [], stats

        # Step 2: Build Coverage Plan
        safe_marks = max(1, min(10, int(marks_per_question)))
        slots = self.create_coverage_plan(
            kus, count=count, topic_focus=topic, difficulty=difficulty,
            question_type=question_type, marks_per_question=safe_marks
        )

        verified_questions: List[Dict[str, Any]] = []
        rejected_questions: List[Dict[str, Any]] = []

        is_online = check_ai_provider_status().get("can_generate", False) and not fast_mode

        # Step 3: Generation & Validation Loop
        for slot in slots:
            candidate = None
            if is_online:
                candidate = self.generate_single_question_llm(slot)

            if not candidate:
                candidate = self.generate_single_question_deterministic(slot)
            candidate["marks"] = slot.marks

            # Step 4: Validate
            stats.validating += 1
            v_res = self.validator.validate_question(
                candidate,
                knowledge_unit=slot.knowledge_unit,
                existing_questions=verified_questions
            )

            # Step 5: Repair loop if needed
            if v_res.status == "NEEDS_REPAIR" and v_res.repairable:
                stats.repairing += 1
                stats.retries += 1
                repaired = self.repair_question(candidate, v_res, slot)
                if repaired:
                    v_res_repaired = self.validator.validate_question(
                        repaired,
                        knowledge_unit=slot.knowledge_unit,
                        existing_questions=verified_questions
                    )
                    if v_res_repaired.is_valid:
                        candidate = repaired
                        candidate["marks"] = slot.marks
                        v_res = v_res_repaired

            # Step 6: Final decision for this slot
            if v_res.is_valid:
                candidate["validation_status"] = "VERIFIED"
                candidate["validation_score"] = v_res.score
                candidate["validation_errors"] = []
                verified_questions.append(candidate)
                stats.verified += 1
            else:
                candidate["validation_status"] = "REJECTED"
                candidate["validation_score"] = v_res.score
                candidate["validation_errors"] = v_res.errors
                rejected_questions.append(candidate)
                stats.rejected += 1

        # Step 7: Replacement Generation if items were rejected
        if len(verified_questions) < count and len(kus) > 0:
            replacement_attempts = 0
            # Try alternate knowledge units not yet heavily used
            for extra_ku in kus:
                if len(verified_questions) >= count or replacement_attempts >= count:
                    break
                replacement_attempts += 1
                repl_slot = GenerationSlot(
                    slot_id=len(verified_questions) + 1,
                    topic=extra_ku.topic,
                    subtopic=extra_ku.subtopic,
                    question_type=question_type if question_type != 'mixed' else 'mcq',
                    difficulty=difficulty.capitalize(),
                    cognitive_level='conceptual',
                    knowledge_unit=extra_ku,
                    marks=safe_marks
                )
                repl_candidate = self.generate_single_question_deterministic(repl_slot)
                repl_candidate["marks"] = repl_slot.marks
                repl_v = self.validator.validate_question(
                    repl_candidate,
                    knowledge_unit=extra_ku,
                    existing_questions=verified_questions
                )
                if repl_v.is_valid:
                    repl_candidate["validation_status"] = "VERIFIED"
                    repl_candidate["validation_score"] = repl_v.score
                    repl_candidate["validation_errors"] = []
                    verified_questions.append(repl_candidate)
                    stats.verified += 1

        # Re-number verified questions sequentially
        for idx, q in enumerate(verified_questions, start=1):
            q["number"] = idx
            q["id"] = f"q-{idx}"

        return verified_questions, stats
