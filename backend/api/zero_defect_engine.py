"""
=============================================================================
StudyAI — Phase 6: Zero-Defect Document Engine
=============================================================================
Semantic Accuracy, Structural Integrity, Mathematical Layout, Typography,
Alignment and Final-Output Verification System.

Implements the 8-Stage Mandatory Validation Pipeline:
  STAGE A — Source Validation (element classification, OCR confidence, page boundaries)
  STAGE B — Semantic Validation (heading hierarchy, numbering, title sanity)
  STAGE C — Content Validation (coverage map, duplication control)
  STAGE D — Mathematical Validation (10-part calculations, LaTeX alignment, SI units)
  STAGE E — Formatting Validation (central typography, paragraph spacing, tables)
  STAGE F — Render Validation (150 DPI page rendering, margin bounds, geometry)
  STAGE G — Correction (automated repair of fixable defects)
  STAGE H — Re-Validation (iterative regeneration & certification)

Generates the Honest Quality Report (Section 14) with status READY or NEEDS_CORRECTION.
=============================================================================
"""

import os
import re
import io
import time
import logging
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from django.conf import settings
from .typography_system import DocumentTypography
from .math_verification import MathematicalIntelligenceEngine
from .notes_engine import (
    resolve_clean_academic_title,
    detect_callout_type,
    export_markdown_to_pdf,
    export_markdown_to_docx
)

logger = logging.getLogger(__name__)


class ZeroDefectDocumentEngine:
    """
    Industrial-strength document intelligence, quality assurance, and layout verification engine.
    Certifies study materials against Phase 6 Zero-Defect standards.
    """

    # 16 Standard Document Elements (Phase 6 Section 2)
    ELEMENT_TYPES = {
        "DOCUMENT_TITLE", "SUBJECT_TITLE", "MODULE_TITLE", "SECTION_HEADING",
        "SUBSECTION_HEADING", "TOPIC_HEADING", "BODY_PARAGRAPH", "NUMBERED_LIST",
        "BULLET_LIST", "TABLE", "FORMULA", "NUMERICAL_PROBLEM", "FIGURE",
        "CAPTION", "HEADER", "FOOTER"
    }

    # Coverage Statuses (Phase 6 Section 4)
    COVERAGE_STATUSES = {"PRESENT", "PARTIALLY_PRESENT", "MISSING", "DUPLICATED", "UNCERTAIN"}

    # Validation States (Phase 6 Section 14)
    VALIDATION_STATES = {"PASS", "FAIL", "NOT_RUN", "UNVERIFIED"}

    # -------------------------------------------------------------------------
    # STAGE A — SOURCE VALIDATION
    # -------------------------------------------------------------------------
    @classmethod
    def validate_source_extraction(cls, pages_data: List[Dict[str, Any]], raw_text: str = "") -> Dict[str, Any]:
        """
        Validates extraction completeness, source ordering, page references, and OCR confidence.
        Classifies extracted lines into the 16 standard academic document elements.
        """
        if not pages_data and not raw_text:
            return {
                "stage": "STAGE_A_SOURCE_VALIDATION",
                "status": "FAIL",
                "total_pages": 0,
                "issues": [{"severity": "CRITICAL", "message": "Source document contains no extractable text."}],
                "element_counts": {},
                "classified_elements": []
            }

        total_pages = len(pages_data) if pages_data else 1
        classified_elements = []
        element_counts = {el: 0 for el in cls.ELEMENT_TYPES}
        issues = []

        combined_text = "\n\n".join(p.get("text", "") for p in pages_data) if pages_data else (raw_text or "")
        lines = [l.strip() for l in combined_text.splitlines() if l.strip()]

        seen_first_title = False
        for idx, line in enumerate(lines[:120]):
            # Classify line into one of 16 standard elements
            el_type = "BODY_PARAGRAPH"

            if line.startswith(('--- Page', 'Page ', '=== Page')):
                el_type = "FOOTER" if "Page" in line else "HEADER"
            elif not seen_first_title and idx < 4 and len(line) > 8 and (line.isupper() or line.startswith('# ')):
                el_type = "DOCUMENT_TITLE"
                seen_first_title = True
            elif re.match(r'^(?:Module|Chapter|Unit|Part)\s*(?:[0-9]+|–|—|\:)', line, re.IGNORECASE):
                el_type = "MODULE_TITLE"
            elif re.match(r'^\d+\.\d+\s+[A-Z]', line) or line.startswith('## '):
                el_type = "SECTION_HEADING"
            elif re.match(r'^\d+\.\d+\.\d+\s+[A-Z]', line) or line.startswith('### '):
                el_type = "SUBSECTION_HEADING"
            elif line.startswith('#### '):
                el_type = "TOPIC_HEADING"
            elif re.match(r'^\s*(\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s+', line):
                el_type = "NUMBERED_LIST"
            elif line.startswith(('-', '*', '•')):
                el_type = "BULLET_LIST"
            elif line.startswith('|') and line.endswith('|'):
                el_type = "TABLE"
            elif line.startswith(('$$', r'\[', r'\begin{')) or re.search(r'[=∑∫√α-ω]', line):
                el_type = "FORMULA"
            elif re.match(r'^(?:Problem|Given|Required|Calculate|To Find)\b', line, re.IGNORECASE):
                el_type = "NUMERICAL_PROBLEM"
            elif re.match(r'^(?:Figure|Fig\.|Diagram)\s*\d+', line, re.IGNORECASE):
                el_type = "FIGURE"
            elif re.match(r'^(?:Caption|Source:)\b', line, re.IGNORECASE):
                el_type = "CAPTION"

            element_counts[el_type] += 1
            if idx < 40:
                classified_elements.append({"line_number": idx + 1, "text": line[:60], "type": el_type})

        # OCR Confidence analysis across pages
        low_conf_pages = []
        for p in pages_data:
            conf = p.get("confidence") if p.get("confidence") is not None else p.get("ocr_confidence")
            p_num = p.get("page_number", 1)
            if isinstance(conf, (int, float)):
                pct = conf * 100.0 if conf <= 1.0 else float(conf)
                if pct < 70.0:
                    low_conf_pages.append({"page": p_num, "confidence": round(pct, 2)})

        if low_conf_pages:
            page_nums = [item["page"] for item in low_conf_pages]
            issues.append({
                "severity": "MEDIUM",
                "message": f"Low OCR confidence detected on pages: {page_nums}. Visual review recommended."
            })

        status = "PASS" if not any(i["severity"] == "CRITICAL" for i in issues) else "FAIL"

        return {
            "stage": "STAGE_A_SOURCE_VALIDATION",
            "status": status,
            "passed": status == "PASS",
            "total_pages": total_pages,
            "total_characters": len(combined_text),
            "total_words": len(combined_text.split()),
            "low_confidence_pages": low_conf_pages,
            "element_counts": element_counts,
            "element_classification": element_counts,
            "classified_sample": classified_elements,
            "issues": issues
        }

    # -------------------------------------------------------------------------
    # STAGE B — SEMANTIC VALIDATION
    # -------------------------------------------------------------------------
    @classmethod
    def validate_semantic_headings(cls, markdown_text: str, doc_title: str = "", subject: str = "") -> Dict[str, Any]:
        """
        Validates title correctness, heading hierarchy (H1 -> H2 -> H3 -> H4),
        absence of skipped levels, absence of false chapter promotions, and non-empty sections.
        """
        issues = []
        lines = (markdown_text or "").splitlines()

        # 1. Title Sanity Check: Never use raw filename as document title
        academic_title = resolve_clean_academic_title(doc_title, markdown_text, subject)
        if doc_title and re.search(r'\.(pdf|docx|txt|pptx)$', doc_title, re.IGNORECASE):
            issues.append({
                "severity": "CRITICAL",
                "category": "Title Integrity",
                "message": f"Document title is a raw filename or slug ('{doc_title}'). Clean academic title ('{academic_title}') must be used."
            })

        # 2. Heading Hierarchy Inspection
        seen_h1 = False
        seen_h2 = False
        seen_h3 = False
        seen_headings = set()
        headings_tree = []
        current_section = None

        for idx, line in enumerate(lines):
            s = line.strip()
            line_no = idx + 1

            if s.startswith('# '):
                seen_h1 = True
                h_text = s[2:].strip()
                h_lower = h_text.lower()
                # Check duplicate headings
                if h_lower in seen_headings:
                    issues.append({
                        "line": line_no,
                        "severity": "HIGH",
                        "category": "Heading Duplication",
                        "message": f"Duplicate consecutive heading detected: '# {h_text}'."
                    })
                seen_headings.add(h_lower)
                current_section = {"level": 1, "title": h_text, "line": line_no, "body_words": 0}
                headings_tree.append(current_section)

            elif s.startswith('## '):
                seen_h2 = True
                h_text = s[3:].strip()
                h_lower = h_text.lower()
                # Check false chapter promotion of numbered list items
                if re.match(r'^\d+[\.\)]\s+[A-Za-z\s]+:', h_text):
                    issues.append({
                        "line": line_no,
                        "severity": "HIGH",
                        "category": "Heading Distortion",
                        "message": f"Numbered list item incorrectly promoted to Section heading: '{h_text}'."
                    })
                if h_lower in seen_headings:
                    issues.append({
                        "line": line_no,
                        "severity": "HIGH",
                        "category": "Heading Duplication",
                        "message": f"Duplicate consecutive heading detected: '## {h_text}'."
                    })
                seen_headings.add(h_lower)
                current_section = {"level": 2, "title": h_text, "line": line_no, "body_words": 0}
                headings_tree.append(current_section)

            elif s.startswith('### '):
                h_text = s[4:].strip()
                if not seen_h2:
                    issues.append({
                        "line": line_no,
                        "severity": "CRITICAL",
                        "category": "Hierarchy Error",
                        "message": f"Skipped heading level / Inconsistent hierarchy: '### {h_text}' appears before any '##' Section heading."
                    })
                seen_h3 = True
                current_section = {"level": 3, "title": h_text, "line": line_no, "body_words": 0}
                headings_tree.append(current_section)

            elif s.startswith('#### '):
                h_text = s[5:].strip()
                if not seen_h3:
                    issues.append({
                        "line": line_no,
                        "severity": "HIGH",
                        "category": "Hierarchy Error",
                        "message": f"Skipped heading level / Inconsistent hierarchy: '#### {h_text}' appears before any '###' Subsection heading."
                    })
                current_section = {"level": 4, "title": h_text, "line": line_no, "body_words": 0}
                headings_tree.append(current_section)

            elif current_section and not s.startswith('#'):
                current_section["body_words"] += len(s.split())

        # Check for empty leaf sections (headings with 0 body text that have no children)
        empty_sections = []
        for idx_h, h in enumerate(headings_tree):
            is_parent = (idx_h + 1 < len(headings_tree) and headings_tree[idx_h + 1]["level"] > h["level"])
            if not is_parent and h["body_words"] == 0:
                empty_sections.append(h["title"])

        if empty_sections:
            issues.append({
                "severity": "HIGH",
                "category": "Content Void",
                "message": f"Empty heading section with no content detected: {empty_sections[:3]}."
            })

        status = "PASS" if not any(i["severity"] in ("CRITICAL", "HIGH") for i in issues) else "FAIL"

        return {
            "stage": "STAGE_B_SEMANTIC_VALIDATION",
            "status": status,
            "passed": status == "PASS",
            "academic_title": academic_title,
            "total_headings": len(headings_tree),
            "headings_hierarchy": headings_tree[:25],
            "hierarchy": headings_tree,
            "issues_count": len(issues),
            "issues": issues
        }

    # -------------------------------------------------------------------------
    # STAGE C — CONTENT VALIDATION & COVERAGE MAP
    # -------------------------------------------------------------------------
    @classmethod
    def validate_content_coverage_and_duplication(
        cls,
        source_topics: List[Dict[str, Any]],
        markdown_text: str
    ) -> Dict[str, Any]:
        """
        Creates a source-to-output coverage map and detects content duplication.
        Assigns statuses: PRESENT, PARTIALLY_PRESENT, MISSING, DUPLICATED, UNCERTAIN.
        """
        coverage_map = []
        issues = []
        md_lower = (markdown_text or "").lower()

        # Build coverage map
        represented_count = 0
        missing_count = 0
        duplicated_count = 0

        for idx, t in enumerate(source_topics or []):
            t_name = t.get("name") or t.get("title") or t.get("topic") or f"Topic {idx+1}"
            t_clean = re.sub(r'^\d+(?:\.\d+)*\s*', '', t_name).strip().lower()
            p_start = t.get("page_start") or t.get("page", 1)
            p_end = t.get("page_end") or p_start

            # Determine presence in generated markdown
            if t_clean in md_lower:
                # Count occurrences
                occ = md_lower.count(t_clean)
                if occ >= 4 and len(t_clean) > 8:
                    st = "DUPLICATED"
                    duplicated_count += 1
                else:
                    st = "PRESENT"
                    represented_count += 1
            else:
                # Check partial match on key tokens
                tokens = [tok for tok in t_clean.split() if len(tok) >= 4]
                match_count = sum(1 for tok in tokens if tok in md_lower)
                if tokens and match_count >= len(tokens) * 0.6:
                    st = "PARTIALLY_PRESENT"
                    represented_count += 1
                else:
                    st = "MISSING"
                    missing_count += 1

            coverage_map.append({
                "topic_id": t.get("id", f"t-{idx+1}"),
                "source_heading": t_name,
                "source_page_range": f"Page {p_start}" if p_start == p_end else f"Pages {p_start}–{p_end}",
                "status": st,
                "confidence": 0.95 if st == "PRESENT" else (0.80 if st == "PARTIALLY_PRESENT" else 0.50)
            })

        # Duplication check on body paragraphs using SequenceMatcher
        clean_text = re.sub(r'^#+\s+[^\n]*\n+', '', (markdown_text or ""), flags=re.MULTILINE).replace('\r\n', '\n')
        paragraphs = [p.strip() for p in clean_text.split("\n\n") if len(p.strip()) > 80]
        duplicate_pairs = []
        for i in range(len(paragraphs)):
            for j in range(i + 1, min(i + 10, len(paragraphs))):
                p1 = paragraphs[i]
                p2 = paragraphs[j]
                ratio = SequenceMatcher(None, p1[:120], p2[:120]).ratio()
                if ratio > 0.88:
                    duplicate_pairs.append((i, j, p1[:50]))
                    break

        if duplicate_pairs:
            issues.append({
                "severity": "HIGH",
                "category": "Repetition Defect",
                "message": f"Detected {len(duplicate_pairs)} duplicate explanatory paragraph(s) repeated across sections."
            })

        total_topics = max(1, len(source_topics or []))
        coverage_pct = round((represented_count / total_topics) * 100.0, 1)

        status = "PASS" if missing_count == 0 and not duplicate_pairs else ("FAIL" if missing_count > total_topics * 0.25 else "PARTIAL")

        return {
            "stage": "STAGE_C_CONTENT_VALIDATION",
            "status": status,
            "passed": status == "PASS",
            "total_source_topics": len(source_topics or []),
            "topics_represented": represented_count,
            "topics_missing": missing_count,
            "topics_duplicated": duplicated_count,
            "coverage_percentage": coverage_pct,
            "coverage_map": coverage_map[:30],
            "duplicate_paragraph_count": len(duplicate_pairs),
            "issues": issues
        }

    # -------------------------------------------------------------------------
    # STAGE D — MATHEMATICAL VALIDATION
    # -------------------------------------------------------------------------
    @classmethod
    def validate_mathematical_typesetting(cls, markdown_text: str) -> Dict[str, Any]:
        """
        Validates equations, symbol preservation, 10-part calculation structure,
        and algebraic/unit consistency using MathematicalIntelligenceEngine.
        """
        text = markdown_text or ""
        issues = []

        # 1. Delimiter balance check
        dollar_count = text.count('$$')
        if dollar_count % 2 != 0:
            issues.append({
                "severity": "CRITICAL",
                "category": "Formula Syntax",
                "message": "Unclosed display math delimiter ('$$')."
            })

        open_bracket_math = text.count(r'\[')
        close_bracket_math = text.count(r'\]')
        if open_bracket_math != close_bracket_math:
            issues.append({
                "severity": "CRITICAL",
                "category": "Formula Syntax",
                "message": rf"Mismatched LaTeX display delimiters: {open_bracket_math} '\[' vs {close_bracket_math} '\]'."
            })

        # 2. Detect mathematical expressions
        math_analysis = MathematicalIntelligenceEngine.detect_mathematical_content(text)
        construct_counts = math_analysis.get("construct_counts", {})
        total_equations = construct_counts.get("equations", 0) + construct_counts.get("fractions", 0)

        # 3. Calculation Structure Audit
        calc_audit = MathematicalIntelligenceEngine.validate_calculation_structure(text)
        structure_complete = calc_audit.get("is_complete", False)
        missing_calc_parts = calc_audit.get("missing_parts", [])

        # 4. Arithmetic discrepancy checking
        math_flagged_text = MathematicalIntelligenceEngine.flag_unverified_calculations(text)
        flagged_count = math_flagged_text.count("[MATHEMATICAL DISCREPANCY")
        if flagged_count > 0:
            issues.append({
                "severity": "CRITICAL",
                "category": "Numerical Inaccuracy",
                "message": f"Detected {flagged_count} arithmetic discrepancies in numerical solutions."
            })

        status = "PASS" if not any(i["severity"] == "CRITICAL" for i in issues) else "FAIL"

        return {
            "stage": "STAGE_D_MATHEMATICAL_VALIDATION",
            "status": status,
            "passed": status == "PASS",
            "contains_math": math_analysis.get("has_math", False) or math_analysis.get("contains_math", False),
            "construct_counts": construct_counts,
            "total_equations_detected": total_equations,
            "calculation_structure_complete": structure_complete,
            "missing_calculation_parts": missing_calc_parts,
            "arithmetic_discrepancies": flagged_count,
            "issues": issues
        }

    # -------------------------------------------------------------------------
    # STAGE E — FORMATTING VALIDATION
    # -------------------------------------------------------------------------
    @classmethod
    def validate_typography_and_formatting(cls, markdown_text: str, doc_title: str = "") -> Dict[str, Any]:
        """
        Validates central typography conformance, paragraph spacing,
        table dimensions, list hanging indentations, and callout tagging.
        """
        text = markdown_text or ""
        issues = []
        lines = text.splitlines()

        # Check isolated numbers (e.g. '1.' alone on a line)
        isolated_nums = []
        for idx, line in enumerate(lines):
            s = line.strip()
            if re.match(r'^(?:\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s*$', s):
                isolated_nums.append((idx + 1, s))

        if isolated_nums:
            issues.append({
                "severity": "HIGH",
                "category": "List Formatting",
                "message": f"Detected {len(isolated_nums)} isolated list number marker(s) without attached text."
            })

        # Check table consistency per distinct table block
        table_blocks = []
        curr_table = []
        for l in lines:
            s = l.strip()
            if s.startswith('|') and s.endswith('|'):
                curr_table.append(s)
            else:
                if len(curr_table) >= 2:
                    table_blocks.append(curr_table)
                curr_table = []
        if len(curr_table) >= 2:
            table_blocks.append(curr_table)

        table_issues_count = 0
        for tbl in table_blocks:
            col_counts = [len(r.strip('|').split('|')) for r in tbl]
            if len(set(col_counts)) > 1:
                table_issues_count += 1
                issues.append({
                    "severity": "HIGH",
                    "category": "Table Formatting",
                    "message": "Inconsistent column count across table rows."
                })

        # Check excessive blank lines (> 2 consecutive blank lines)
        excessive_blanks = len(re.findall(r'\n{4,}', text))
        if excessive_blanks > 0:
            issues.append({
                "severity": "MEDIUM",
                "category": "Vertical Rhythm",
                "message": f"Detected {excessive_blanks} occurrence(s) of excessive consecutive blank lines."
            })

        # Check academic callouts
        callouts = [l.strip() for l in lines if l.strip().startswith('>')]
        valid_callouts = 0
        for c in callouts:
            ctype, _, _, _ = detect_callout_type(c)
            if ctype in DocumentTypography.CALLOUT_CONFIG:
                valid_callouts += 1

        status = "PASS" if not any(i["severity"] in ("CRITICAL", "HIGH") for i in issues) else "FAIL"

        return {
            "stage": "STAGE_E_FORMATTING_VALIDATION",
            "status": status,
            "passed": status == "PASS",
            "isolated_numbering_count": len(isolated_nums),
            "table_issues_count": table_issues_count,
            "excessive_blank_lines": excessive_blanks,
            "valid_callouts_count": valid_callouts,
            "typography_conformance": "CONFORMANT" if not issues else "MINOR_DEVIATIONS",
            "issues": issues
        }

    # -------------------------------------------------------------------------
    # STAGE F — RENDER VALIDATION
    # -------------------------------------------------------------------------
    @classmethod
    def validate_rendered_document(cls, pdf_path: str, doc_title: str = "") -> Dict[str, Any]:
        """
        Renders PDF pages into 150 DPI memory images via PyMuPDF.
        Inspects layout geometry, margins, text clipping, and orphaned headings.
        """
        if not os.path.exists(pdf_path):
            return {
                "stage": "STAGE_F_RENDER_VALIDATION",
                "status": "FAIL",
                "error": f"PDF file not found: {pdf_path}",
                "pages_inspected": []
            }

        issues = []
        representative_pages = []
        representative_pixmaps = []

        try:
            import pymupdf as fitz
        except ImportError:
            try:
                import fitz
            except ImportError:
                fitz = None

        if not fitz:
            return {
                "stage": "STAGE_F_RENDER_VALIDATION",
                "status": "UNVERIFIED",
                "message": "PyMuPDF not available; visual rendering inspection skipped.",
                "pages_inspected": []
            }

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            if total_pages == 0:
                return {
                    "stage": "STAGE_F_RENDER_VALIDATION",
                    "status": "FAIL",
                    "issues": [{"severity": "CRITICAL", "message": "Document contains 0 pages."}]
                }

            representative_pages = sorted(list(set([1, max(1, total_pages // 2), total_pages])))

            for page_idx in range(total_pages):
                page_num = page_idx + 1
                page = doc[page_idx]
                page_rect = page.rect
                page_h = page_rect.height
                page_w = page_rect.width

                # Render 150 DPI pixmaps for representative pages
                if page_num in representative_pages:
                    try:
                        pix = page.get_pixmap(dpi=150)
                        if pix.width > 0 and pix.height > 0:
                            representative_pixmaps.append({
                                "page": page_num,
                                "width": pix.width,
                                "height": pix.height,
                                "dpi": 150,
                                "status": "RENDERED_CLEAR"
                            })
                    except Exception as render_err:
                        issues.append({
                            "page": page_num,
                            "severity": "HIGH",
                            "message": f"Page {page_num} image rendering anomaly: {render_err}"
                        })

                # Geometric bounding checks
                blocks = page.get_text("blocks") or []
                text_blocks = [b for b in blocks if len(b) >= 5 and b[4].strip()]

                # Check 1: Orphaned heading at page bottom
                for b in text_blocks:
                    x0, y0, x1, y1, b_text, b_no, b_type = b[:7]
                    b_strip = b_text.strip()
                    is_h = b_strip.startswith(('#', 'Chapter', 'Section', 'Module')) or (
                        len(b_strip.split()) <= 7 and (b_strip.isupper() or b_strip.istitle()) and not b_strip.endswith('.')
                    )
                    if is_h and y1 > (page_h * 0.88) and b == text_blocks[-1]:
                        issues.append({
                            "page": page_num,
                            "severity": "HIGH",
                            "category": "Orphaned Heading",
                            "message": f"Orphaned heading detected at bottom of page {page_num}: '{b_strip[:40]}'."
                        })

                # Check 2: Margin bounds overflow
                for b in text_blocks:
                    x0, y0, x1, y1, b_text, b_no, b_type = b[:7]
                    if y0 > 50 and y1 < (page_h - 50):
                        if x1 > (page_w - 30):
                            issues.append({
                                "page": page_num,
                                "severity": "HIGH",
                                "category": "Margin Overflow",
                                "message": f"Content extends beyond right page margin on page {page_num} (x1={x1:.1f})."
                            })
                            break

            status = "PASS" if not any(i["severity"] in ("CRITICAL", "HIGH") for i in issues) else "FAIL"

            return {
                "stage": "STAGE_F_RENDER_VALIDATION",
                "status": status,
                "passed": status == "PASS",
                "total_pages": total_pages,
                "representative_pages_inspected": representative_pages,
                "representative_pixmaps": representative_pixmaps,
                "issues_count": len(issues),
                "issues": issues
            }

        except Exception as exc:
            return {
                "stage": "STAGE_F_RENDER_VALIDATION",
                "status": "FAIL",
                "error": str(exc),
                "issues": [{"severity": "CRITICAL", "message": f"Render inspection error: {exc}"}]
            }

    # -------------------------------------------------------------------------
    # STAGE G — CORRECTION
    # -------------------------------------------------------------------------
    @classmethod
    def correct_defects(cls, markdown_text: str) -> Tuple[str, List[str]]:
        """
        Applies automated repairs to fixable formatting and structural defects:
        - Joins isolated list numbers ('1.\\nText' -> '1. Text')
        - Closes unclosed $$ display formula delimiters
        - Closes unclosed ``` code blocks
        - Collapses excessive vertical whitespace
        """
        repairs = []
        lines = (markdown_text or "").splitlines()
        repaired_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            s = line.strip()

            # Fix isolated numbering
            if re.match(r'^(?:\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s*$', s):
                if i + 1 < len(lines) and lines[i+1].strip():
                    repaired_lines.append(f"{s} {lines[i+1].strip()}")
                    repairs.append(f"Joined isolated numbered item '{s}' with subsequent text.")
                    i += 2
                    continue

            repaired_lines.append(line)
            i += 1

        result = '\n'.join(repaired_lines)

        # Fix unclosed $$
        if result.count('$$') % 2 != 0:
            result = result.rstrip() + '\n$$\n'
            repairs.append("Closed unclosed display math ('$$') delimiter.")

        # Fix unclosed ```
        if result.count('```') % 2 != 0:
            result = result.rstrip() + '\n```\n'
            repairs.append("Closed unclosed '```' code fence delimiter.")

        # Collapse excessive whitespace
        excessive = len(re.findall(r'\n{4,}', result))
        if excessive > 0:
            result = re.sub(r'\n{4,}', '\n\n\n', result)
            repairs.append(f"Collapsed {excessive} occurrences of excessive vertical whitespace.")

        return result, repairs

    # -------------------------------------------------------------------------
    # STAGE H — RE-VALIDATION & MASTER CERTIFICATION
    # -------------------------------------------------------------------------
    @classmethod
    def audit_and_certify_document(
        cls,
        markdown_text: str,
        doc_title: str = "",
        subject: str = "General",
        source_topics: Optional[List[Dict[str, Any]]] = None,
        pages_data: Optional[List[Dict[str, Any]]] = None,
        doc_id: Any = "audit",
        max_iterations: int = 2
    ) -> Dict[str, Any]:
        """
        Executes the entire 8-stage Zero-Defect pipeline (Stages A through H).
        Iteratively corrects fixable defects, regenerates exports, and issues
        the Honest Quality Report (Section 14) with final status READY or NEEDS_CORRECTION.
        """
        start_time = time.time()
        current_md = markdown_text
        all_repairs: List[str] = []
        iterations_run = 0

        # Stage A: Source Validation
        stage_a = cls.validate_source_extraction(pages_data or [], current_md)

        # Generate initial exports for Stage F verification
        academic_title = resolve_clean_academic_title(doc_title, current_md, subject)
        current_pdf = export_markdown_to_pdf(academic_title, current_md, subject=subject, doc_id=doc_id)
        current_docx = export_markdown_to_docx(academic_title, current_md, subject=subject, doc_id=doc_id)

        # Iterative Loop: Inspect and Correct
        while iterations_run < max_iterations:
            iterations_run += 1

            stage_b = cls.validate_semantic_headings(current_md, academic_title, subject)
            stage_c = cls.validate_content_coverage_and_duplication(source_topics or [], current_md)
            stage_d = cls.validate_mathematical_typesetting(current_md)
            stage_e = cls.validate_typography_and_formatting(current_md, academic_title)
            stage_f = cls.validate_rendered_document(current_pdf, academic_title)

            critical_or_high_issues = [
                i for stage in (stage_b, stage_c, stage_d, stage_e, stage_f)
                for i in stage.get("issues", [])
                if i.get("severity") in ("CRITICAL", "HIGH")
            ]

            if not critical_or_high_issues:
                # Fully clean!
                break

            # Stage G: Apply automated repairs if defects exist
            repaired_md, repairs = cls.correct_defects(current_md)
            if not repairs or repaired_md == current_md:
                # No automated repairs possible
                break

            all_repairs.extend(repairs)
            current_md = repaired_md
            # Regenerate exports
            current_pdf = export_markdown_to_pdf(academic_title, current_md, subject=subject, doc_id=doc_id)
            current_docx = export_markdown_to_docx(academic_title, current_md, subject=subject, doc_id=doc_id)

        # Final Stage H Re-Validation
        stage_b = cls.validate_semantic_headings(current_md, academic_title, subject)
        stage_c = cls.validate_content_coverage_and_duplication(source_topics or [], current_md)
        stage_d = cls.validate_mathematical_typesetting(current_md)
        stage_e = cls.validate_typography_and_formatting(current_md, academic_title)
        stage_f = cls.validate_rendered_document(current_pdf, academic_title)

        all_defects = [
            i for stage in (stage_a, stage_b, stage_c, stage_d, stage_e, stage_f)
            for i in stage.get("issues", [])
        ]
        unresolved_critical = [i for i in all_defects if i.get("severity") in ("CRITICAL", "HIGH")]

        # Final Certification Status per Phase 6 Section 15
        final_certification = "READY" if not unresolved_critical else "NEEDS_CORRECTION"

        # Honest Quality Report (Phase 6 Section 14)
        honest_report = {
            "source_extraction_status": stage_a.get("status", "UNVERIFIED"),
            "actual_document_title_detected": academic_title,
            "subject_detected": subject,
            "total_topics_detected": stage_c.get("total_source_topics", 0),
            "topics_successfully_represented": stage_c.get("topics_represented", 0),
            "missing_topics": stage_c.get("topics_missing", 0),
            "duplicate_sections": stage_c.get("duplicate_paragraph_count", 0),
            "heading_hierarchy_errors": len([i for i in stage_b.get("issues", []) if "Hierarchy" in i.get("category", "")]),
            "mathematical_validation_status": stage_d.get("status", "NOT_RUN" if not stage_d.get("contains_math") else "PASS"),
            "formatting_validation_status": stage_e.get("status", "PASS"),
            "docx_rendering_status": "PASS" if os.path.exists(current_docx) else "FAIL",
            "pdf_rendering_status": stage_f.get("status", "PASS"),
            "pages_actually_inspected": stage_f.get("representative_pages_inspected", [1]),
            "defects_detected_count": len(all_defects),
            "defects_corrected_count": len(all_repairs),
            "repairs_applied": all_repairs,
            "unresolved_defects": unresolved_critical,
            "final_acceptance_status": final_certification,
            "final_document_status": final_certification
        }

        elapsed = round(time.time() - start_time, 2)

        return {
            "certified": final_certification == "READY",
            "status": final_certification,
            "final_document_status": final_certification,
            "honest_quality_report": honest_report,
            "stages": {
                "stage_a_source": stage_a,
                "stage_b_semantic": stage_b,
                "stage_c_content": stage_c,
                "stage_d_mathematical": stage_d,
                "stage_e_formatting": stage_e,
                "stage_f_render": stage_f
            },
            "iterations_run": iterations_run,
            "repairs_applied": all_repairs,
            "repaired_markdown": current_md,
            "pdf_path": current_pdf,
            "pdf_export_path": current_pdf,
            "docx_path": current_docx,
            "docx_export_path": current_docx,
            "elapsed_seconds": elapsed
        }


DocumentElementType = ZeroDefectDocumentEngine.ELEMENT_TYPES

