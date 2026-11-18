"""
=============================================================================
StudyAI — Document Content Cleaning & Classification Layer
=============================================================================
Identifies, classifies, and filters:
- PAGE_NUMBER
- HEADER
- FOOTER
- CHAPTER / SECTION HEADINGS
- TABLE_OF_CONTENTS
- FIGURE_CAPTION
- REFERENCE / CITATION
- ISBN / COPYRIGHT
- OCR_ERROR / ARTIFACTS
- CONTENT (Educational substance)

Preserves technical numbers, algorithm bounds, formulas, ports, and equations.
=============================================================================
"""

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional


class LineType(str, Enum):
    CONTENT = "CONTENT"
    HEADING = "HEADING"
    PAGE_NUMBER = "PAGE_NUMBER"
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    TABLE_OF_CONTENTS = "TABLE_OF_CONTENTS"
    FIGURE_CAPTION = "FIGURE_CAPTION"
    REFERENCE = "REFERENCE"
    OCR_ERROR = "OCR_ERROR"
    UNKNOWN = "UNKNOWN"


@dataclass
class ClassifiedLine:
    text: str
    line_number: int
    classification: LineType
    confidence: float = 1.0
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# Regex patterns for classification
RE_PAGE_NUMBER = re.compile(
    r'^(?:page\s*\d+|p\.\s*\d+|\b\d+\b|\b\d+\s*/\s*\d+\b|[-–—]\s*\d+\s*[-–—]|\[\s*\d+\s*\]|\b[ivxlcdm]+\b)$',
    re.IGNORECASE
)

RE_COPYRIGHT_ISBN = re.compile(
    r'(?:©|copyright|\(c\)|all rights reserved|isbn(?:-1[03])?:?\s*[\d\-Xx]+|issn|printed in|published by|library of congress)',
    re.IGNORECASE
)

RE_URL = re.compile(
    r'^(?:https?://|www\.)\S+$',
    re.IGNORECASE
)

RE_TOC_LINE = re.compile(
    r'(?:(?:chapter|section|module|unit)?\s*\d+(?:\.\d+)*\s+.*?[\.\-–—\s]{3,}\s*\d+$|^table of contents$|^contents$)',
    re.IGNORECASE
)

RE_FIGURE_CAPTION = re.compile(
    r'^(?:fig(?:ure)?\.?|table|chart|graph|diagram|algorithm|listing)\s*\d+(?:[\.\-]\d+)*\s*[:\.\-–—]',
    re.IGNORECASE
)

RE_REFERENCE_LINE = re.compile(
    r'^(?:\[\d+\]|\(\d+\)|\d+\.)\s+[A-Z][a-zA-Z\s,]+(?:et\s+al\.?|\(\d{4}\)|[,\.]\s*(?:\"|\'|“|«)?\w+)',
    re.IGNORECASE
)

RE_HEADING_NUMBERED = re.compile(
    r'^(?:chapter|section|unit|module|lecture)?\s*(?:\d+(?:\.\d+)*)[:\s\-–—]+([A-Z][a-zA-Z0-9\s\-,:?]+)$',
    re.IGNORECASE
)

RE_STANDALONE_NUMBERING = re.compile(
    r'^(?:_{2,}|\s)*\d+(?:\s+\d+(?:\.\d+)*)+\s*$'
)

RE_OCR_GIBBERISH = re.compile(
    r'(?:[|!_~`#$^&*]{4,}|[^\x00-\x7F]{4,}|(?:\b[a-zA-Z]\b\s+){4,})'
)


def is_meaningful_math_or_technical(text: str) -> bool:
    """
    Checks if a line contains mathematical equations, LaTeX, algorithmic complexity,
    or technical notation that must NOT be removed even if short or containing numbers.
    """
    cleaned = text.strip()
    if not cleaned:
        return False

    # LaTeX patterns
    if '$$' in cleaned or '$' in cleaned or '\\' in cleaned:
        return True

    # Mathematical / formal language notations
    math_symbols = ['∈', '∉', '∅', '⊆', '∪', '∩', '→', '↔', '≤', '≥', '∑', '∏', '∫', 'δ', 'Σ', 'Γ', 'ε', 'λ']
    if any(s in cleaned for s in math_symbols):
        return True

    # Big-O / complexity notation
    if re.search(r'\b[OΘΩ]\s*\([^)]+\)', cleaned):
        return True

    # Automata or state transition notation (e.g., δ(q0, 0) = q1 or Q = {q0, q1})
    if re.search(r'\b[δ]\s*\([^)]+\)\s*=', cleaned) or re.search(r'[A-Z]\s*=\s*\{[^}]*\}', cleaned):
        return True

    # Technical IP address or port assignment
    if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', cleaned) or re.search(r'\bport\s+\d+\b', cleaned, re.I):
        return True

    return False


def classify_line(line: str, line_num: int = 1, prev_line: str = "", next_line: str = "") -> ClassifiedLine:
    """
    Classifies an individual line of extracted text into its structural category.
    """
    raw_stripped = line.strip()

    if not raw_stripped:
        return ClassifiedLine(text=line, line_number=line_num, classification=LineType.UNKNOWN, reason="Empty line")

    # Guard: Math and technical symbols are always preserved as CONTENT
    if is_meaningful_math_or_technical(raw_stripped):
        return ClassifiedLine(text=line, line_number=line_num, classification=LineType.CONTENT, reason="Math/technical notation")

    # 1. OCR Corruption / Malformed Fragment Detection
    # E.g. "_____ 1 1.1 Why Study Automata Theory?" or "_____ 1"
    if re.match(r'^(?:_{2,}|\s*-\s*)+\s*\d+', raw_stripped):
        return ClassifiedLine(
            text=line,
            line_number=line_num,
            classification=LineType.OCR_ERROR,
            reason="Leading underscore or dash corrupted numbering artifact"
        )

    # Isolated repeated non-word gibberish
    if RE_OCR_GIBBERISH.search(raw_stripped) and len(raw_stripped) < 40 and not re.search(r'[a-zA-Z]{4,}', raw_stripped):
        return ClassifiedLine(
            text=line,
            line_number=line_num,
            classification=LineType.OCR_ERROR,
            reason="Unstructured OCR noise/gibberish"
        )

    # 2. Standalone Page Numbers
    if RE_PAGE_NUMBER.match(raw_stripped):
        # Ensure it's not a single mathematical digit in an equation flow
        if len(raw_stripped) <= 6 and not prev_line.endswith(('=', '+', '-', '*', '/')):
            return ClassifiedLine(
                text=line,
                line_number=line_num,
                classification=LineType.PAGE_NUMBER,
                reason="Isolated page number"
            )

    # 3. Copyright / ISBN / Publishing metadata
    if RE_COPYRIGHT_ISBN.search(raw_stripped):
        return ClassifiedLine(
            text=line,
            line_number=line_num,
            classification=LineType.FOOTER,
            reason="Copyright, ISBN, or publishing boilerplate"
        )

    # 4. URLs
    if RE_URL.match(raw_stripped):
        return ClassifiedLine(
            text=line,
            line_number=line_num,
            classification=LineType.FOOTER,
            reason="Standalone web link"
        )

    # 5. Table of contents lines
    if RE_TOC_LINE.match(raw_stripped) or (raw_stripped.lower() in ["table of contents", "contents"]):
        return ClassifiedLine(
            text=line,
            line_number=line_num,
            classification=LineType.TABLE_OF_CONTENTS,
            reason="Table of contents entry or heading"
        )

    # 6. Figure / Table captions
    if RE_FIGURE_CAPTION.match(raw_stripped):
        return ClassifiedLine(
            text=line,
            line_number=line_num,
            classification=LineType.FIGURE_CAPTION,
            reason="Figure or table caption"
        )

    # 7. Citations / References list entry
    if RE_REFERENCE_LINE.match(raw_stripped):
        return ClassifiedLine(
            text=line,
            line_number=line_num,
            classification=LineType.REFERENCE,
            reason="Academic reference list entry"
        )

    # 8. Standalone Numbering (e.g. "1 1.1")
    if RE_STANDALONE_NUMBERING.match(raw_stripped):
        return ClassifiedLine(
            text=line,
            line_number=line_num,
            classification=LineType.HEADER,
            reason="Isolated section numbering without content"
        )

    # 9. Headings / Section titles
    if RE_HEADING_NUMBERED.match(raw_stripped):
        return ClassifiedLine(
            text=line,
            line_number=line_num,
            classification=LineType.HEADING,
            reason="Numbered chapter or section heading"
        )

    # Short title-cased or uppercase line without terminal punctuation
    if len(raw_stripped) < 70 and not raw_stripped.endswith(('.', ':', ';', '!', '?')):
        words = raw_stripped.split()
        if 1 <= len(words) <= 8:
            if raw_stripped.isupper() or all(w[0].isupper() for w in words if w and w[0].isalpha()):
                return ClassifiedLine(
                    text=line,
                    line_number=line_num,
                    classification=LineType.HEADING,
                    reason="Unpunctuated heading line"
                )

    # 10. Default Content
    return ClassifiedLine(
        text=line,
        line_number=line_num,
        classification=LineType.CONTENT,
        reason="Educational body content"
    )


def clean_and_classify_document_content(raw_text: str) -> Tuple[str, List[ClassifiedLine]]:
    """
    Processes extracted text line-by-line, classifying each line and stripping
    irrelevant headers, footers, page numbers, TOC entries, and OCR artifacts
    while rigorously preserving educational content, technical numbering, and formulas.

    Returns:
        tuple (cleaned_usable_text, list_of_all_classified_lines)
    """
    if not raw_text:
        return "", []

    lines = raw_text.splitlines()
    classified: List[ClassifiedLine] = []
    usable_lines: List[str] = []

    total = len(lines)
    for idx, line in enumerate(lines):
        prev_line = lines[idx - 1].strip() if idx > 0 else ""
        next_line = lines[idx + 1].strip() if idx < total - 1 else ""

        cl = classify_line(line, line_num=idx + 1, prev_line=prev_line, next_line=next_line)
        classified.append(cl)

        # Content filtering rules for question generation context:
        # Keep CONTENT, and keep HEADING as section separators if informative
        if cl.classification == LineType.CONTENT:
            usable_lines.append(line.strip())
        elif cl.classification == LineType.HEADING:
            # Add heading with markdown prefix to provide concept context without raw OCR noise
            clean_head = re.sub(r'^(?:_{2,}|\s*-\s*)+', '', line.strip())
            if clean_head and len(clean_head) > 3:
                usable_lines.append(f"\n### {clean_head}\n")

    cleaned_text = "\n".join(usable_lines)
    # Normalize excessive blank lines
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text).strip()

    return cleaned_text, classified


def is_malformed_concept_name(concept: str) -> Tuple[bool, str]:
    """
    Checks if an extracted concept title/term is corrupted OCR, heading number, or noise.
    Valid concept terms can be short (e.g. 'DFA', 'Paging', 'Process').
    """
    if not concept or not concept.strip():
        return True, "Empty concept name"
    c = concept.strip()
    if re.search(r'^(?:_{2,}|-+\s*|\.\.\.\s*)\s*\d+', c):
        return True, "Corrupted underline or section number"
    if re.match(r'^\d+(?:\.\d+)*\s*$', c):
        return True, "Pure numbering without term"
    if re.search(r'\b[a-zA-Z]{1,2}-[a-zA-Z]{1,2}\b', c):
        return True, "Hyphenated broken OCR word fragment"
    alnums = sum(1 for ch in c if ch.isalnum() or ch in ' \t-')
    if len(c) > 0 and (alnums / len(c)) < 0.6:
        return True, "Symbol noise in concept name"
    return False, ""


def is_malformed_sentence_fragment(fragment: str) -> Tuple[bool, str]:
    """
    Detects whether a sentence or text excerpt is an OCR artifact, broken heading,
    incomplete fragment, or unsuitable for question generation.

    Returns:
        tuple (is_malformed: bool, reason: str)
    """
    if not fragment or not fragment.strip():
        return True, "Empty text fragment"

    f = fragment.strip()

    # Rule 1: Starts with masking, blanks, underscores, or OCR dashes + numbers
    if re.search(r'^(?:_{2,}|-+\s*|\.\.\.\s*)\s*\d+', f):
        return True, "Starts with corrupted OCR underline or section digits"

    # Rule 2: Chapter or section title pattern without a verb or predicate
    # e.g. "1 1.1 Why Study Automata Theory?" or "Chapter 2: Finite Automata"
    if re.match(r'^(?:chapter|section|\d+(?:\.\d+)*)\s+.*?\?*$', f, re.I) and len(f.split()) < 10:
        # Check if it has a complete predicate/verb
        verbs = ['is', 'are', 'was', 'were', 'defines', 'states', 'contains', 'consists', 'has', 'have', 'shows', 'proves', 'permits', 'avoids', 'allocates', 'maintains']
        if not any(f" {v} " in f.lower() for v in verbs):
            return True, "Standalone heading or section title fragment lacking predicate"

    # Rule 3: Corrupted character ratio (too many non-alphanumeric, non-math symbols)
    alnums = sum(1 for c in f if c.isalnum() or c in ' \t\n')
    if len(f) > 0 and (alnums / len(f)) < 0.55 and not is_meaningful_math_or_technical(f):
        return True, f"High symbol corruption ratio: {alnums}/{len(f)}"

    # Rule 4: Broken word artifacts e.g. "au- tomata" or "w- h- y"
    if re.search(r'\b[a-zA-Z]{1,2}-[a-zA-Z]{1,2}\b', f):
        return True, "Hyphenated broken OCR word fragment"

    # Rule 5: Trailing broken sentence without terminal punctuation and < 4 words
    words = f.split()
    if len(words) < 4 and not is_meaningful_math_or_technical(f):
        return True, "Insufficient word count for educational statement"

    return False, ""

