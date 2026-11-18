import re
from typing import Any


_HEADING_RE = re.compile(
    r"^\s*(?:#{1,6}\s+\S|(?:chapter|unit|module|section)\s+[\w.-]+|(?:\d+\.)+\s+\S)",
    re.IGNORECASE | re.MULTILINE
)
_EXAMPLE_RE = re.compile(r"\b(?:for example|e\.g\.|worked example|example\s+\d+)\b", re.IGNORECASE)
_DEFINITION_RE = re.compile(r"\b(?:is defined as|refers to|means|is called)\b", re.IGNORECASE)
_FORMULA_RE = re.compile(r"(?:\\(?:frac|sum|int|sqrt)|[=<>≤≥±∑∫√]|[A-Za-z]\s*=\s*[^=])")
_CITATION_RE = re.compile(r"(?:\[\d+\]|\(\w[^()\n]{0,40}\b(?:19|20)\d{2}\)|\bp{1,2}\.\s*\d+)", re.IGNORECASE)


def analyze_reference_style(text: str) -> dict[str, Any]:
    """Extract presentation metrics only; never retain or return reference claims."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Reference document contains no readable text.")

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    paragraph_word_counts = [
        len(re.findall(r"\b[\w'-]+\b", paragraph))
        for paragraph in paragraphs
    ]
    words = re.findall(r"\b[\w'-]+\b", text)
    lines = text.splitlines()
    sentence_count = len(re.findall(r"[.!?](?:\s|$)", text)) or 1
    bullet_count = sum(
        bool(re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line))
        for line in lines
    )
    heading_count = len(_HEADING_RE.findall(text))
    example_count = len(_EXAMPLE_RE.findall(text))
    formula_count = len(_FORMULA_RE.findall(text))
    definition_count = len(_DEFINITION_RE.findall(text))
    table_line_count = sum("|" in line for line in lines)
    citation_count = len(_CITATION_RE.findall(text))
    paragraph_count = len(paragraphs)
    mean_paragraph_words = round(sum(paragraph_word_counts) / paragraph_count, 1) if paragraph_count else 0
    mean_sentence_words = round(len(words) / sentence_count, 1)

    guidance = ["Organize explanations into clearly labeled sections."]
    if mean_paragraph_words >= 90:
        guidance.append("Use developed explanatory paragraphs, broken up with headings.")
    elif mean_paragraph_words and mean_paragraph_words <= 35:
        guidance.append("Prefer concise paragraphs and scannable lists.")
    if bullet_count / max(len(lines), 1) >= 0.12:
        guidance.append("Use short lists for grouped facts or steps.")
    if example_count:
        guidance.append("Add examples only when they are supported by the study document; do not reuse reference examples.")
    if formula_count:
        guidance.append("Set off formulas clearly and define variables only when supported by the study document.")
    if table_line_count:
        guidance.append("Use comparison tables when they clarify source-supported distinctions.")
    if heading_count >= 4:
        guidance.append("Maintain a multi-level heading hierarchy.")
    if citation_count:
        guidance.append("Keep source/page references visible near the claims they support.")
    if definition_count:
        guidance.append("Give key terms explicit definition treatments when present in the study source.")

    return {
        "version": 1,
        "metrics": {
            "word_count": len(words),
            "paragraph_count": paragraph_count,
            "mean_paragraph_words": mean_paragraph_words,
            "mean_sentence_words": mean_sentence_words,
            "heading_count": heading_count,
            "list_item_count": bullet_count,
            "example_marker_count": example_count,
            "formula_marker_count": formula_count,
            "definition_marker_count": definition_count,
            "table_line_count": table_line_count,
            "citation_marker_count": citation_count,
        },
        "guidance": guidance,
        "content_policy": (
            "This profile contains presentation metrics only. Reference facts, examples, "
            "and explanations must not be used as study-source evidence."
        ),
    }
