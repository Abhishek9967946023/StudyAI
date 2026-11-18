"""
=============================================================================
StudyAI — Knowledge Unit Extraction Engine
=============================================================================
Converts cleaned document text and semantic chunks into structured Knowledge Units:
- topic
- subtopic
- concept
- definition
- explanation
- formula (if applicable)
- conditions/rules
- example (if available)
- source page & chunk ID
- confidence score

All exam questions must strictly originate from verified Knowledge Units,
never directly from arbitrary uncleaned text chunks.
=============================================================================
"""

import re
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple

from .content_cleaner import (
    clean_and_classify_document_content,
    is_malformed_sentence_fragment,
    is_malformed_concept_name,
    is_meaningful_math_or_technical,
    LineType
)
from .ai_provider_service import query_ai, check_ai_provider_status
from .ollama_service import parse_json_safely

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeUnit:
    id: str
    topic: str
    subtopic: str
    concept: str
    definition: str
    explanation: str
    formula: Optional[str] = None
    conditions_rules: List[str] = field(default_factory=list)
    example: Optional[str] = None
    source_page: int = 1
    source_pages: str = "1"
    source_chunk_id: Optional[int] = None
    confidence: float = 1.0
    cognitive_tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeUnit':
        return cls(
            id=str(data.get("id", "ku-1")),
            topic=str(data.get("topic", "General")),
            subtopic=str(data.get("subtopic", "General")),
            concept=str(data.get("concept", "")),
            definition=str(data.get("definition", "")),
            explanation=str(data.get("explanation", "")),
            formula=data.get("formula"),
            conditions_rules=data.get("conditions_rules", []) or [],
            example=data.get("example"),
            source_page=int(data.get("source_page", 1)),
            source_pages=str(data.get("source_pages", str(data.get("source_page", 1)))),
            source_chunk_id=data.get("source_chunk_id"),
            confidence=float(data.get("confidence", 0.9)),
            cognitive_tags=data.get("cognitive_tags", []) or []
        )


def is_valid_knowledge_unit(unit: KnowledgeUnit) -> Tuple[bool, str]:
    """
    Validates that a knowledge unit contains authentic educational substance
    and does not wrap OCR artifacts, headers, or corrupted fragments.
    """
    if not unit.concept or len(unit.concept.strip()) < 2:
        return False, "Concept title is missing or too short"

    is_malformed_c, reason_c = is_malformed_concept_name(unit.concept)
    if is_malformed_c:
        return False, f"Concept is malformed: {reason_c}"

    if not unit.definition or len(unit.definition.strip()) < 12:
        return False, "Definition is too short or missing substantive explanation"

    is_malformed_d, reason_d = is_malformed_sentence_fragment(unit.definition)
    if is_malformed_d:
        return False, f"Definition is malformed: {reason_d}"

    # Verify concept is not merely a page number, chapter number, or header
    if re.match(r'^(?:chapter|section|\d+(\.\d+)*)\b', unit.concept.strip(), re.I) and len(unit.concept.split()) < 4:
        return False, "Concept is merely a chapter or section label"

    return True, ""


def extract_knowledge_units_heuristic(chunks: List[Dict[str, Any]], topic_focus: str = "All") -> List[KnowledgeUnit]:
    """
    High-precision deterministic extractor for Knowledge Units from cleaned chunk text.
    Works independently of LLM availability, extracting verified definitions,
    theorems, formulas, and concepts across all informative sentences.
    """
    units: List[KnowledgeUnit] = []
    ku_idx = 1

    for c in chunks:
        raw_text = c.get("text", "")
        page_num = int(c.get("page_start", 1))
        page_end = int(c.get("page_end", page_num))
        chunk_id = c.get("chunk_index")
        section = c.get("section", "Core Concepts")

        # Step 1: Clean and classify lines
        cleaned_text, classified = clean_and_classify_document_content(raw_text)
        if not cleaned_text:
            continue

        # Step 2: Split into paragraphs and semantic blocks
        blocks = re.split(r'\n{2,}', cleaned_text)

        current_heading = section or "General"
        for block in blocks:
            b_stripped = block.strip()
            if not b_stripped:
                continue

            # Update heading context if block starts with markdown heading
            if b_stripped.startswith("### "):
                current_heading = b_stripped.replace("### ", "").strip()
                continue

            # Identify candidate definitions, properties, or algorithms
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', b_stripped) if len(s.strip()) > 15]
            if not sentences:
                continue

            # Check if block contains formulas or equations
            formula_match = re.search(r'(\$\$[\s\S]+?\$\$|\$[^\$]+?\$|L\([A-Za-z0-9\+\*\s]+\)\s*=\s*[^\.\n]+|\b[OΘΩ]\s*\([^)]+\)|[δ]\s*\([^)]+\)\s*=\s*[^\.\n]+)', b_stripped)
            formula_str = formula_match.group(0).strip() if formula_match else None

            # Look for definition markers
            for s in sentences:
                concept_name = ""

                # Pattern A: Definition marker with broad educational verbs
                m_def = re.search(r'^(?:A|An|The)?\s*([A-Za-z0-9\s\-\(\)]{2,35})\s+(?:is defined as|is a|is an|refers to|denotes|consists of|represents|is composed of|allocates|provides|permits|maintains|avoids|suffers from|uses|is)\s+(.+)$', s, re.I)
                if m_def:
                    concept_name = m_def.group(1).strip()

                # Pattern B: Theorem / Definition / Property
                if not concept_name:
                    m_thm = re.search(r'^(?:Definition|Theorem|Lemma|Property|Principle)\s*(?:\d+(?:\.\d+)*)?\s*[:\-\—]\s*(.+)$', s, re.I)
                    if m_thm:
                        concept_name = f"{current_heading} Principle"

                # Pattern C: Automata / Formal languages specific definitions
                if not concept_name:
                    m_automata = re.search(r'\b(DFA|NFA|Turing Machine|Grammar|PDA|Regular Expression)\b.*?(?:transition|state|alphabet|accepts|language)', s, re.I)
                    if m_automata:
                        concept_name = m_automata.group(1).upper()

                # Fallback: take leading informative noun phrase before verb (up to 3 words)
                if not concept_name:
                    words = s.split()
                    if len(words) >= 4 and words[0].lower() not in ['if', 'when', 'however', 'moreover']:
                        candidate_lead = " ".join(words[:3]).rstrip(",:;")
                        candidate_lead = re.sub(r'^(?:A|An|The)\s+', '', candidate_lead, flags=re.I)
                        if len(candidate_lead) >= 3:
                            concept_name = candidate_lead

                if concept_name:
                    concept_name = concept_name.strip(" .:,;()[]{}")
                    is_m_c, _ = is_malformed_concept_name(concept_name)
                    if is_m_c or len(concept_name) < 2:
                        continue

                    # Determine cognitive tags
                    cog_tags = ["definition", "conceptual"]
                    if formula_str:
                        cog_tags.append("numerical")
                    if any(k in s.lower() for k in ["construction", "design", "convert", "algorithm"]):
                        cog_tags.append("construction")
                    if any(k in s.lower() for k in ["trace", "step", "input", "allocates", "permits"]):
                        cog_tags.append("trace")

                    unit = KnowledgeUnit(
                        id=f"ku-{ku_idx}",
                        topic=topic_focus if topic_focus != "All" else current_heading,
                        subtopic=current_heading,
                        concept=concept_name,
                        definition=s,
                        explanation=b_stripped[:350],
                        formula=formula_str,
                        conditions_rules=[],
                        example=None,
                        source_page=page_num,
                        source_pages=f"{page_num}-{page_end}" if page_end > page_num else str(page_num),
                        source_chunk_id=chunk_id,
                        confidence=0.92,
                        cognitive_tags=cog_tags
                    )

                    valid, _ = is_valid_knowledge_unit(unit)
                    if valid:
                        units.append(unit)
                        ku_idx += 1

    return units



def extract_knowledge_units_with_llm(chunks: List[Dict[str, Any]], topic_focus: str = "All", model: str = "llama3:latest") -> List[KnowledgeUnit]:
    """
    Uses Ollama to extract rich, structured knowledge units from cleaned chunk context.
    Falls back seamlessly to high-yield heuristic extraction if Ollama is unavailable.
    """
    st = check_ai_provider_status()
    if not st.get("can_generate"):
        return extract_knowledge_units_heuristic(chunks, topic_focus=topic_focus)

    # Gather cleaned context from top chunks
    context_parts = []
    for c in chunks[:8]:
        cleaned, _ = clean_and_classify_document_content(c.get("text", ""))
        if cleaned:
            p = c.get("page_start", 1)
            context_parts.append(f"[Page {p} | Chunk {c.get('chunk_index')}]:\n{cleaned[:1200]}")

    combined_context = "\n\n".join(context_parts)
    if not combined_context:
        return extract_knowledge_units_heuristic(chunks, topic_focus=topic_focus)

    prompt = f"""You are StudyAI Knowledge Architect.
Read the cleaned document material below and extract structured educational Knowledge Units.
Focus topic: "{topic_focus}".

RULES:
1. Extract ONLY genuine educational concepts, theorems, algorithms, or definitions.
2. NEVER extract page numbers, chapter headers, table-of-contents entries, or OCR noise as concepts.
3. Every unit must have a complete concept, rigorous definition, and grounded explanation.

Respond in VALID JSON with EXACTLY this structure:
{{
  "knowledge_units": [
    {{
      "concept": "Name of concept (e.g. Deterministic Finite Automaton)",
      "topic": "{topic_focus if topic_focus != 'All' else 'Core Subject'}",
      "subtopic": "Subtopic name",
      "definition": "Precise 1-2 sentence academic definition",
      "explanation": "Detailed pedagogical explanation based on the text",
      "formula": "LaTeX formula if applicable or null",
      "conditions_rules": ["Rule 1", "Rule 2"],
      "example": "Practical example if in text or null",
      "source_page": 1,
      "cognitive_tags": ["definition", "conceptual", "application"]
    }}
  ]
}}

Source Material:
{combined_context[:3800]}
"""

    resp_text, success, _ = query_ai(prompt, model=model, format_json=True, temperature=0.1, timeout=25)
    if success and resp_text:
        parsed = parse_json_safely(resp_text)
        if parsed and isinstance(parsed, dict) and "knowledge_units" in parsed:
            raw_kus = parsed.get("knowledge_units", [])
            valid_units = []
            for idx, item in enumerate(raw_kus, start=1):
                ku = KnowledgeUnit(
                    id=f"ku-ai-{idx}",
                    topic=item.get("topic", topic_focus),
                    subtopic=item.get("subtopic", "General"),
                    concept=item.get("concept", ""),
                    definition=item.get("definition", ""),
                    explanation=item.get("explanation", ""),
                    formula=item.get("formula"),
                    conditions_rules=item.get("conditions_rules", []),
                    example=item.get("example"),
                    source_page=int(item.get("source_page", 1)),
                    source_pages=str(item.get("source_page", 1)),
                    confidence=0.95,
                    cognitive_tags=item.get("cognitive_tags", ["conceptual"])
                )
                is_valid, _ = is_valid_knowledge_unit(ku)
                if is_valid:
                    valid_units.append(ku)

            if len(valid_units) >= 3:
                return valid_units

    # Fallback to heuristic knowledge units
    return extract_knowledge_units_heuristic(chunks, topic_focus=topic_focus)


def get_or_extract_knowledge_units(chunks: List[Dict[str, Any]], topic_focus: str = "All", model: str = "llama3:latest", fast_mode: bool = False) -> List[KnowledgeUnit]:
    """
    Standard entrypoint for obtaining verified Knowledge Units for question generation.
    """
    if fast_mode:
        return extract_knowledge_units_heuristic(chunks, topic_focus=topic_focus)
    return extract_knowledge_units_with_llm(chunks, topic_focus=topic_focus, model=model)
