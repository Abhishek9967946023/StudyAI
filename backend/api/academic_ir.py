"""
=============================================================================
StudyAI — Structured Academic Content Intermediate Representation (IR) (Phase 7)
=============================================================================
Provides a strongly-typed, structured intermediate representation (IR)
for academic documents, eliminating fragile reliance on raw Markdown strings alone.
Enables programmatic topic restructuring, semantic de-duplication, source traceability,
grounding classification, and precision multi-format export.
=============================================================================
"""

import re
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set


class GroundingType(str, Enum):
    """Classifies the evidential grounding source of an academic element."""
    SOURCE_DERIVED = "SOURCE_DERIVED"               # Directly extracted or grounded in source text
    TEACHING_CONTEXT = "TEACHING_CONTEXT"           # Pedagogical explanation added to clarify concepts
    UNCERTAIN = "UNCERTAIN"                         # Insufficient source evidence or approximate inference


class AcademicElementType(str, Enum):
    """
    Standardized academic element classifications conforming to Phase 7 and Phase 8.
    Supports all 17 canonical block types with alias resolution.
    """
    # Canonical Phase 8 Block Types
    TITLE = "TITLE"
    HEADING = "HEADING"
    SUBHEADING = "SUBHEADING"
    PARAGRAPH = "PARAGRAPH"
    DEFINITION = "DEFINITION"
    EXPLANATION = "EXPLANATION"
    EXAMPLE = "EXAMPLE"
    LIST = "LIST"
    LIST_ITEM = "LIST_ITEM"
    TABLE = "TABLE"
    FORMULA = "FORMULA"
    NUMERICAL_SOLUTION = "NUMERICAL_SOLUTION"
    ALGORITHM = "ALGORITHM"
    DIAGRAM = "DIAGRAM"
    CAPTION = "CAPTION"
    NOTE = "NOTE"
    CONCLUSION = "CONCLUSION"

    # Backward-compatible Phase 7 Aliases
    DOCUMENT_TITLE = "DOCUMENT_TITLE"
    MODULE_CHAPTER = "MODULE_CHAPTER"               # H1
    MAIN_HEADING = "MAIN_HEADING"                   # H2
    TOPIC_HEADING = "TOPIC_HEADING"                 # H4
    BODY_PARAGRAPH = "BODY_PARAGRAPH"
    CONCEPTUAL_EXPLANATION = "CONCEPTUAL_EXPLANATION"
    MECHANISM_STEP = "MECHANISM_STEP"
    CLASSIFICATION_GROUP = "CLASSIFICATION_GROUP"
    CLASSIFICATION_ITEM = "CLASSIFICATION_ITEM"
    CALLOUT = "CALLOUT"
    EXAM_TIP = "EXAM_TIP"
    CROSS_REFERENCE = "CROSS_REFERENCE"

    @classmethod
    def from_str(cls, val: str) -> "AcademicElementType":
        """Resolves raw string or alias into a canonical AcademicElementType."""
        clean = (val or "").strip().upper().replace(" ", "_")
        aliases = {
            "TITLE": cls.TITLE,
            "DOCUMENT_TITLE": cls.DOCUMENT_TITLE,
            "HEADING": cls.HEADING,
            "MODULE_CHAPTER": cls.MODULE_CHAPTER,
            "MAIN_HEADING": cls.MAIN_HEADING,
            "SUBHEADING": cls.SUBHEADING,
            "PARAGRAPH": cls.PARAGRAPH,
            "BODY": cls.BODY_PARAGRAPH,
            "BODY_PARAGRAPH": cls.BODY_PARAGRAPH,
            "DEFINITION": cls.DEFINITION,
            "EXPLANATION": cls.EXPLANATION,
            "CONCEPTUAL_EXPLANATION": cls.CONCEPTUAL_EXPLANATION,
            "EXAMPLE": cls.EXAMPLE,
            "LIST": cls.LIST,
            "LIST_ITEM": cls.LIST_ITEM,
            "TABLE": cls.TABLE,
            "FORMULA": cls.FORMULA,
            "NUMERICAL_SOLUTION": cls.NUMERICAL_SOLUTION,
            "ALGORITHM": cls.ALGORITHM,
            "DIAGRAM": cls.DIAGRAM,
            "CAPTION": cls.CAPTION,
            "NOTE": cls.NOTE,
            "CALLOUT": cls.CALLOUT,
            "CONCLUSION": cls.CONCLUSION,
            "EXAM_TIP": cls.EXAM_TIP,
            "CROSS_REFERENCE": cls.CROSS_REFERENCE,
        }
        return aliases.get(clean, cls.BODY_PARAGRAPH)


@dataclass
class AcademicElementIR:
    """
    Represents a source-aware atomic content block within a structured academic document.
    Maintains original text alongside reconstructed text to guarantee zero accidental content loss.
    """
    element_id: str = field(default_factory=lambda: f"elem_{uuid.uuid4().hex[:8]}")
    element_type: AcademicElementType = AcademicElementType.BODY_PARAGRAPH
    heading_level: int = 0                          # 0 for body, 1-4 for headings
    text_content: str = ""

    # Phase 8 Source-Aware Tracking
    doc_id: Optional[str] = None
    original_sequence: int = 0
    original_text: str = ""
    reconstructed_text: str = ""
    parent_heading: Optional[str] = None
    related_block_ids: List[str] = field(default_factory=list)
    content_confidence: float = 1.0
    extraction_confidence: float = 1.0
    was_reconstructed: bool = False

    # Page and Grounding Metadata
    source_page_start: Optional[int] = None
    source_page_end: Optional[int] = None
    source_reference: Optional[str] = None          # e.g., "Page 12, Section 3.2"
    source_evidence: Optional[str] = None           # Raw excerpt supporting this element
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    grounding_type: GroundingType = GroundingType.SOURCE_DERIVED
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    validation_status: str = "PASS"                 # PASS, FAIL, UNVERIFIED, WARNING

    def compute_content_preservation_ratio(self) -> float:
        """
        Computes word-level preservation ratio between original_text and reconstructed text_content.
        Returns 1.0 if original_text is empty (newly generated element).
        """
        if not self.original_text:
            return 1.0
        orig_words = set(re.findall(r'\b[a-zA-Z0-9_-]{4,}\b', self.original_text.lower()))
        if not orig_words:
            return 1.0
        cur_text = (self.reconstructed_text or self.text_content).lower()
        preserved = sum(1 for w in orig_words if w in cur_text)
        return round(preserved / len(orig_words), 3)

    def is_content_loss_detected(self, threshold: float = 0.65) -> bool:
        """Returns True if meaningful content was accidentally dropped during reconstruction."""
        if not self.original_text:
            return False
        return self.compute_content_preservation_ratio() < threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_id": self.element_id,
            "element_type": self.element_type.value if isinstance(self.element_type, AcademicElementType) else str(self.element_type),
            "heading_level": self.heading_level,
            "text_content": self.text_content,
            "doc_id": self.doc_id,
            "original_sequence": self.original_sequence,
            "original_text": self.original_text,
            "reconstructed_text": self.reconstructed_text,
            "parent_heading": self.parent_heading,
            "related_block_ids": self.related_block_ids,
            "content_confidence": self.content_confidence,
            "extraction_confidence": self.extraction_confidence,
            "was_reconstructed": self.was_reconstructed,
            "source_page_start": self.source_page_start,
            "source_page_end": self.source_page_end,
            "source_reference": self.source_reference,
            "source_evidence": self.source_evidence,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "grounding_type": self.grounding_type.value if isinstance(self.grounding_type, GroundingType) else str(self.grounding_type),
            "metadata": self.metadata,
            "confidence": self.confidence,
            "validation_status": self.validation_status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AcademicElementIR":
        el_type_str = data.get("element_type", AcademicElementType.BODY_PARAGRAPH.value)
        el_type = AcademicElementType.from_str(el_type_str)

        grounding_str = data.get("grounding_type", GroundingType.SOURCE_DERIVED.value)
        try:
            grounding = GroundingType(grounding_str)
        except ValueError:
            grounding = GroundingType.SOURCE_DERIVED

        return cls(
            element_id=data.get("element_id", f"elem_{uuid.uuid4().hex[:8]}"),
            element_type=el_type,
            heading_level=data.get("heading_level", 0),
            text_content=data.get("text_content", ""),
            doc_id=data.get("doc_id"),
            original_sequence=data.get("original_sequence", 0),
            original_text=data.get("original_text", ""),
            reconstructed_text=data.get("reconstructed_text", ""),
            parent_heading=data.get("parent_heading"),
            related_block_ids=data.get("related_block_ids", []),
            content_confidence=data.get("content_confidence", 1.0),
            extraction_confidence=data.get("extraction_confidence", 1.0),
            was_reconstructed=data.get("was_reconstructed", False),
            source_page_start=data.get("source_page_start"),
            source_page_end=data.get("source_page_end"),
            source_reference=data.get("source_reference"),
            source_evidence=data.get("source_evidence"),
            parent_id=data.get("parent_id"),
            child_ids=data.get("child_ids", []),
            grounding_type=grounding,
            metadata=data.get("metadata", {}),
            confidence=data.get("confidence", 1.0),
            validation_status=data.get("validation_status", "PASS")
        )


@dataclass
class AcademicSectionIR:
    """Represents a coherent section or topic topic in the academic syllabus."""
    section_id: str = field(default_factory=lambda: f"sec_{uuid.uuid4().hex[:8]}")
    title: str = ""
    order_index: int = 0
    module_name: str = "Module 1"
    depth_level: str = "conceptual"                 # foundation, conceptual, technical_exam
    learning_outcomes: List[str] = field(default_factory=list)
    elements: List[AcademicElementIR] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "order_index": self.order_index,
            "module_name": self.module_name,
            "depth_level": self.depth_level,
            "learning_outcomes": self.learning_outcomes,
            "elements": [e.to_dict() for e in self.elements],
            "metadata": self.metadata
        }

    def to_markdown(self) -> str:
        """Renders this section and all child elements into compliant Markdown."""
        lines = [f"## {self.title}", ""]
        for elem in self.elements:
            lines.append(AcademicDocumentIR._render_element_markdown(elem))
            lines.append("")
        return "\n".join(lines).strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AcademicSectionIR":
        return cls(
            section_id=data.get("section_id", f"sec_{uuid.uuid4().hex[:8]}"),
            title=data.get("title", ""),
            order_index=data.get("order_index", 0),
            module_name=data.get("module_name", "Module 1"),
            depth_level=data.get("depth_level", "conceptual"),
            learning_outcomes=data.get("learning_outcomes", []),
            elements=[AcademicElementIR.from_dict(e) for e in data.get("elements", [])],
            metadata=data.get("metadata", {})
        )


@dataclass
class AcademicDocumentIR:
    """Root container representing a complete structured academic document."""
    doc_id: str = field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    title: str = "Academic Notes"
    subject: str = "General Academic"
    genre: str = "ACADEMIC"
    overview: str = ""
    sections: List[AcademicSectionIR] = field(default_factory=list)
    global_elements: List[AcademicElementIR] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "subject": self.subject,
            "genre": self.genre,
            "overview": self.overview,
            "sections": [s.to_dict() for s in self.sections],
            "global_elements": [e.to_dict() for e in self.global_elements],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AcademicDocumentIR":
        return cls(
            doc_id=data.get("doc_id", f"doc_{uuid.uuid4().hex[:8]}"),
            title=data.get("title", "Academic Notes"),
            subject=data.get("subject", "General Academic"),
            genre=data.get("genre", "ACADEMIC"),
            overview=data.get("overview", ""),
            sections=[AcademicSectionIR.from_dict(s) for s in data.get("sections", [])],
            global_elements=[AcademicElementIR.from_dict(e) for e in data.get("global_elements", [])],
            metadata=data.get("metadata", {})
        )

    def to_markdown(self) -> str:
        """
        Converts the strongly-typed AcademicDocumentIR into standard publication Markdown.
        Preserves heading hierarchy, callout formatting, LaTeX display mathematics,
        table geometry, and source reference citations.
        """
        lines = []

        # 1. Document Title
        lines.append(f"# {self.title}")
        lines.append("")

        # 2. Metadata subtitle
        if self.subject:
            lines.append(f"*{self.subject} — StudyAI Masterclass Edition*")
            lines.append("")

        # 3. Overview if available
        if self.overview:
            lines.append("## 1. Overview & Intellectual Context")
            lines.append("")
            lines.append(self.overview.strip())
            lines.append("")

        # 4. Global elements (e.g., initial definitions, context notes)
        for elem in self.global_elements:
            lines.append(self._render_element_markdown(elem))

        # 5. Sections
        for sec in sorted(self.sections, key=lambda s: s.order_index):
            lines.append(f"## {sec.order_index + 1}. {sec.title}")
            lines.append("")

            for elem in sec.elements:
                rendered = self._render_element_markdown(elem)
                if rendered:
                    lines.append(rendered)
                    lines.append("")

        return "\n".join(lines).strip()

    @staticmethod
    def _render_element_markdown(elem: AcademicElementIR) -> str:
        """Renders an individual AcademicElementIR into compliant Markdown."""
        text = elem.text_content.strip()
        etype = elem.element_type

        if etype == AcademicElementType.MODULE_CHAPTER:
            return f"# {text}"
        elif etype == AcademicElementType.MAIN_HEADING:
            return f"## {text}"
        elif etype == AcademicElementType.SUBHEADING:
            return f"### {text}"
        elif etype == AcademicElementType.TOPIC_HEADING:
            return f"#### {text}"
        elif etype == AcademicElementType.DEFINITION:
            term = elem.metadata.get("term", "")
            if term and not text.lower().startswith("definition"):
                return f"> **Definition ({term})**: {text}"
            return f"> **Definition**: {text}"
        elif etype == AcademicElementType.CALLOUT:
            tag = elem.metadata.get("callout_type", "NOTE").upper()
            return f"> **{tag.title()}**: {text}"
        elif etype == AcademicElementType.EXAM_TIP:
            return f"> **Exam Tip**: {text}"
        elif etype == AcademicElementType.FORMULA:
            formula = elem.metadata.get("formula", text)
            name = elem.metadata.get("name", "")
            prefix = f"**{name}**:\n" if name else ""
            if not formula.startswith("$$"):
                formula = f"$${formula}$$"
            return f"{prefix}{formula}"
        elif etype == AcademicElementType.NUMERICAL_SOLUTION:
            # Multi-line calculation structure
            return text
        elif etype == AcademicElementType.TABLE:
            return text
        elif etype == AcademicElementType.CROSS_REFERENCE:
            target = elem.metadata.get("target_section", "earlier section")
            return f"*(Refer to {target} for foundational definitions)*"
        else:
            # BODY_PARAGRAPH or generic
            ref = ""
            if elem.source_page_start is not None:
                if elem.source_page_end and elem.source_page_end != elem.source_page_start:
                    ref = f" *(Source: Pages {elem.source_page_start}–{elem.source_page_end})*"
                else:
                    ref = f" *(Source: Page {elem.source_page_start})*"
            return f"{text}{ref}"

    @classmethod
    def from_markdown(cls, markdown_text: str, doc_title: str = "Academic Notes", subject: str = "General Academic") -> "AcademicDocumentIR":
        """
        Parses Markdown text into a structured AcademicDocumentIR tree.
        Extracts sections, headings, definitions, tables, formulas, and body paragraphs.
        """
        doc_ir = cls(
            title=doc_title,
            subject=subject
        )
        lines = (markdown_text or "").replace('\r\n', '\n').splitlines()
        current_section: Optional[AcademicSectionIR] = None
        sec_idx = 0
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            # Heading 1
            if stripped.startswith('# '):
                h1_text = stripped[2:].strip()
                if not doc_ir.title or doc_ir.title == "Academic Notes":
                    doc_ir.title = h1_text
                i += 1
                continue

            # Heading 2 -> New Section
            if stripped.startswith('## '):
                h2_text = stripped[3:].strip()
                clean_title = re.sub(r'^\d+[\.\)]\s*', '', h2_text).strip()
                current_section = AcademicSectionIR(
                    title=clean_title,
                    order_index=sec_idx,
                    module_name="Module 1"
                )
                doc_ir.sections.append(current_section)
                sec_idx += 1
                i += 1
                continue

            # Heading 3 / 4 -> Subheading
            if stripped.startswith(('### ', '#### ')):
                lvl = 3 if stripped.startswith('### ') else 4
                h_text = stripped[4:] if lvl == 3 else stripped[5:]
                elem = AcademicElementIR(
                    element_type=AcademicElementType.SUBHEADING if lvl == 3 else AcademicElementType.TOPIC_HEADING,
                    heading_level=lvl,
                    text_content=h_text.strip(),
                    grounding_type=GroundingType.SOURCE_DERIVED
                )
                if current_section:
                    current_section.elements.append(elem)
                else:
                    doc_ir.global_elements.append(elem)
                i += 1
                continue

            # Blockquotes / Definitions / Callouts
            if stripped.startswith('>'):
                quote_lines = []
                while i < len(lines) and lines[i].strip().startswith('>'):
                    quote_lines.append(re.sub(r'^>\s*', '', lines[i].strip()))
                    i += 1
                full_quote = " ".join(quote_lines)

                # Determine type
                if re.search(r'\bdefinition\b', full_quote, re.IGNORECASE):
                    etype = AcademicElementType.DEFINITION
                elif re.search(r'\bexam tip\b', full_quote, re.IGNORECASE):
                    etype = AcademicElementType.EXAM_TIP
                else:
                    etype = AcademicElementType.CALLOUT

                elem = AcademicElementIR(
                    element_type=etype,
                    text_content=full_quote,
                    grounding_type=GroundingType.SOURCE_DERIVED
                )
                if current_section:
                    current_section.elements.append(elem)
                else:
                    doc_ir.global_elements.append(elem)
                continue

            # Formulas
            if stripped.startswith('$$'):
                formula_lines = []
                if stripped.endswith('$$') and len(stripped) > 2:
                    formula_lines.append(stripped[2:-2].strip())
                    i += 1
                else:
                    formula_lines.append(stripped[2:].strip())
                    i += 1
                    while i < len(lines) and not lines[i].strip().endswith('$$'):
                        formula_lines.append(lines[i].strip())
                        i += 1
                    if i < len(lines):
                        formula_lines.append(lines[i].strip().rstrip('$').strip())
                        i += 1

                formula_text = "\n".join(formula_lines)
                elem = AcademicElementIR(
                    element_type=AcademicElementType.FORMULA,
                    text_content=formula_text,
                    metadata={"formula": formula_text},
                    grounding_type=GroundingType.SOURCE_DERIVED
                )
                if current_section:
                    current_section.elements.append(elem)
                else:
                    doc_ir.global_elements.append(elem)
                continue

            # Tables
            if stripped.startswith('|') and stripped.endswith('|'):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                table_text = "\n".join(table_lines)
                elem = AcademicElementIR(
                    element_type=AcademicElementType.TABLE,
                    text_content=table_text,
                    grounding_type=GroundingType.SOURCE_DERIVED
                )
                if current_section:
                    current_section.elements.append(elem)
                else:
                    doc_ir.global_elements.append(elem)
                continue

            # Regular paragraph / list line
            elem = AcademicElementIR(
                element_type=AcademicElementType.BODY_PARAGRAPH,
                text_content=stripped,
                grounding_type=GroundingType.SOURCE_DERIVED
            )
            # Detect page reference in paragraph
            p_match = re.search(r'\*(?:\(?Source:\s*Pages?\s*(\d+)(?:[–\-](\d+))?\)?)?\*', stripped, re.IGNORECASE)
            if p_match and p_match.group(1):
                elem.source_page_start = int(p_match.group(1))
                if p_match.group(2):
                    elem.source_page_end = int(p_match.group(2))

            if current_section:
                current_section.elements.append(elem)
            else:
                doc_ir.global_elements.append(elem)
            i += 1

        return doc_ir
