"""
=============================================================================
StudyAI — Document Processing Diagnostic & Pipeline Audit Engine
=============================================================================
Enables detailed inspection of each pipeline stage for debugging and quality assurance:
1. Raw extracted PDF text
2. OCR text & confidence
3. Cleaned & normalized text
4. Semantic chunks
5. Detected document structure & sections
6. Ollama model configuration & prompts
7. Final API response & Markdown verification
8. Automated corruption audits (vertical text, formula cards, OCR artifacts)
=============================================================================
"""

import re
from typing import Dict, Any, Optional
from django.conf import settings
from .models import Document
from .ollama_service import check_ollama_status, get_configured_model
from .summary_engine import clean_academic_text, detect_document_structure


def audit_markdown_for_corruption(markdown: str) -> Dict[str, Any]:
    """
    Audits generated markdown for known corruption patterns:
    - Vertical single-character runs (T \n h \n e ...)
    - Artificial category card headings
    - Synthetic formula intro sentences
    - Corrupted OCR characters inside math
    """
    if not markdown:
        return {
            "is_clean": True,
            "issues": []
        }

    issues = []
    
    # 1. Check for single character vertical lines (>= 3 consecutive lines with 1 char)
    lines = markdown.split('\n')
    single_char_run = 0
    max_run = 0
    for l in lines:
        s = l.strip()
        if len(s) == 1 and s.isalpha():
            single_char_run += 1
            if single_char_run > max_run:
                max_run = single_char_run
        elif s != '':
            single_char_run = 0

    if max_run >= 3:
        issues.append(f"Vertical character stacking detected (longest run: {max_run} characters)")

    # 2. Check for legacy artificial category cards
    legacy_headings = [
        "Core Theoretical Concepts & Architecture",
        "Document Definitions & Terminology",
        "High-Yield Formulas, Rules & Principles",
        "Process, Workflows & Step-by-Step Mechanisms",
        "Exam Traps & Critical Takeaways",
        "Quick Revision Checklist & Key Highlights",
        "Syllabus Modules & Source Mapping"
    ]
    for h in legacy_headings:
        if h in markdown:
            issues.append(f"Legacy artificial category heading found: '{h}'")

    # 3. Check for synthetic formula introductory sentences
    if re.search(r'The mathematical formulation for (?:mathematical formulation|kleene star|formula)', markdown, re.I):
        issues.append("Synthetic formula introductory sentence found ('The mathematical formulation for...')")

    # 4. Check for OCR artifacts in formulas
    if re.search(r'aja2|--\+d@|---\s*a,\.', markdown):
        issues.append("OCR corruption artifacts found in formulas (e.g. 'aja2', '--+d@')")

    return {
        "is_clean": len(issues) == 0,
        "max_vertical_char_run": max_run,
        "issues_count": len(issues),
        "issues": issues
    }


def get_document_pipeline_diagnostics(doc_id: int) -> Dict[str, Any]:
    """
    Runs end-to-end diagnostic trace on a document in development/debug mode.
    """
    doc = Document.objects.filter(id=doc_id).first()
    if not doc:
        return {"error": f"Document ID {doc_id} not found"}

    summary_data = doc.get_summary() or {}
    markdown = summary_data.get("response") or summary_data.get("markdown_content") or summary_data.get("summary") or ""

    # Stage 1: Raw extraction inspection
    raw_preview = doc.raw_text[:1500] if doc.raw_text else ""
    raw_lines = doc.raw_text.split('\n') if doc.raw_text else []
    raw_vertical_run = 0
    cur = 0
    for l in raw_lines:
        s = l.strip()
        if len(s) == 1 and s.isalpha():
            cur += 1
            if cur > raw_vertical_run:
                raw_vertical_run = cur
        elif s != '':
            cur = 0

    # Stage 2: Normalized text inspection
    cleaned_text, cleaned_pages = clean_academic_text(doc.raw_text)
    
    # Stage 3: Chunks inspection
    chunks_qs = doc.chunks.order_by('chunk_index')
    chunks_data = [
        {
            "chunk_index": c.chunk_index,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "char_count": len(c.text),
            "snippet": c.text[:250] + "..." if len(c.text) > 250 else c.text
        }
        for c in chunks_qs[:4]
    ]

    # Stage 4: Structure detection inspection
    doc_struct = detect_document_structure(cleaned_text, title=doc.title, total_pages=doc.page_count)
    sections_summary = [
        {
            "section_id": s.get("section_id"),
            "title": s.get("title"),
            "pages": f"{s.get('page_start')}-{s.get('page_end')}",
            "formulas_count": len(s.get("formulas", [])),
            "definitions_count": len(s.get("definitions", [])),
            "examples_count": len(s.get("examples", []))
        }
        for s in doc_struct.sections[:10]
    ]

    # Stage 5: Ollama configuration inspection
    ollama_info = check_ollama_status()

    # Stage 6: Corruption audit
    audit_results = audit_markdown_for_corruption(markdown)

    return {
        "doc_id": doc.id,
        "title": doc.title,
        "page_count": doc.page_count,
        "file_type": doc.file_type,
        "total_chars_raw": len(doc.raw_text),
        "total_chars_cleaned": len(cleaned_text),
        "total_chunks": chunks_qs.count(),
        "stage_1_raw_preview": raw_preview,
        "stage_1_raw_max_vertical_run": raw_vertical_run,
        "stage_2_cleaned_preview": cleaned_text[:1500],
        "stage_3_chunks_sample": chunks_data,
        "stage_4_detected_sections_sample": sections_summary,
        "stage_5_ollama_config": {
            "is_online": ollama_info.get("is_online", False),
            "configured_model": get_configured_model(),
            "models_available": ollama_info.get("models", []),
            "context_length": getattr(settings, 'OLLAMA_CONTEXT_LENGTH', 8192),
            "temperature": getattr(settings, 'OLLAMA_TEMPERATURE', 0.2),
            "timeout": getattr(settings, 'OLLAMA_TIMEOUT', 120),
            "num_predict": getattr(settings, 'OLLAMA_NUM_PREDICT', 3000)
        },
        "stage_6_final_markdown_length": len(markdown),
        "stage_6_final_markdown_preview": markdown[:2000],
        "stage_6_corruption_audit": audit_results
    }
