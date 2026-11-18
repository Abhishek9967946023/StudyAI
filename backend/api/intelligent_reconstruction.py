"""
=============================================================================
StudyAI — Phase 4A: Intelligent Line Segmentation & Paragraph Reconstruction
=============================================================================
Transforms fragmented, incorrectly segmented, or poorly aligned extracted text
(especially scanned PDFs and OCR outputs) into clean, logically structured,
and professionally readable content WITHOUT changing its original meaning.

Core Pillars:
A. Distinguish line breaks from paragraph breaks (continuations vs. new ideas)
B. Sentence reconstruction (cross-page stitching, hyphen repair, spacing fixes)
C. Paragraph segmentation (coherent explanations, no monolithic blocks)
D. Numbered list and bullet reconstruction (attach fragments, nested indent)
E. Heading & subheading reconstruction (multi-signal hierarchy, no orphan headings)
F. Page headers, footers, and boundary handling (detect repeated running headers)
G. Multi-column and visually complex page reading sequence
H. Tables and structured content extraction into aligned Markdown
I. OCR uncertainty classification (HIGH, MEDIUM, LOW confidence)
=============================================================================
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# Known English / Technical words that should be unhyphenated when split across lines
# (e.g. de-veloped -> developed, algo-rithm -> algorithm)
KNOWN_PREFIXES = {
    'de', 're', 'in', 'un', 'dis', 'mis', 'pre', 'post', 'sub', 'inter',
    'trans', 'over', 'under', 'multi', 'semi', 'non', 'micro', 'macro',
    'auto', 'tele', 'comput', 'struc', 'oper', 'deterio', 'engi', 'pro',
    'algo', 'infor', 'charac', 'imple', 'distri', 'paral', 'seque'
}

# Naturally hyphenated compounds that MUST keep their hyphen
NATURALLY_HYPHENATED = {
    'client-server', 'trade-off', 'trade-offs', 'step-by-step', 'real-time',
    'end-to-end', 'built-in', 'state-of-the-art', 'peer-to-peer', 'round-trip',
    'bandwidth-delay', 'stop-and-wait', 'go-back-n', 'cut-through', 'store-and-forward',
    'fault-tolerant', 'high-level', 'low-level', 'object-oriented', 'first-principles',
    'user-friendly', 'three-way', 'two-phase', 'read-only', 'write-only', 'single-page',
    'multi-threading', 'open-source', 'cross-platform', 'cost-effective'
}

# Common abbreviations where period does NOT indicate sentence termination
COMMON_ABBREVIATIONS = {
    'e.g.', 'i.e.', 'etc.', 'et al.', 'vs.', 'fig.', 'figs.', 'no.', 'vol.',
    'dr.', 'prof.', 'dept.', 'approx.', 'univ.', 'p.', 'pp.', 'ch.', 'sec.',
    'eq.', 'eqs.', 'ref.', 'refs.', 'min.', 'max.', 'avg.', 'st.'
}


@dataclass
class ReconstructedLine:
    text: str
    line_type: str  # CONTINUATION, NEW_SENTENCE, NEW_PARAGRAPH, LIST_ITEM, HEADING, TABLE, CAPTION, HEADER_FOOTER, MATH
    confidence: float = 1.0
    original_line_num: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconstructionResult:
    reconstructed_text: str
    headings: List[Dict[str, Any]]
    lists: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    confidence_summary: Dict[str, Any]
    uncertain_segments: List[Dict[str, Any]]
    metrics: Dict[str, int]
    pages_data: List[Dict[str, Any]] = field(default_factory=list)


class IntelligentTextReconstructor:
    """
    Production-grade text reconstruction engine implementing Phase 4A requirements.
    Operates both page-by-page and across multi-page boundaries.
    """

    @classmethod
    def reconstruct_document(cls, pages_data: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Main entry point for multi-page documents.
        1. Detects and removes repeated running headers and footers across pages.
        2. Reconnects sentences broken across page boundaries.
        3. Reconstructs lists, headings, and paragraphs per page.
        4. Classifies OCR confidence.
        
        Returns:
            Tuple of (full_reconstructed_text, cleaned_pages_data, reconstruction_metrics)
        """
        if not pages_data:
            return "", [], {"confidence_score": 1.0}

        metrics = {
            "hyphens_repaired": 0,
            "broken_sentences_stitched": 0,
            "running_headers_removed": 0,
            "running_footers_removed": 0,
            "lists_reconstructed": 0,
            "tables_structured": 0,
            "spacing_corrections": 0,
            "uncertain_segments_count": 0
        }

        # Step 1: Detect and remove running headers/footers across pages
        cleaned_pages, hf_metrics = cls.detect_and_remove_running_headers_footers(pages_data)
        metrics["running_headers_removed"] += hf_metrics.get("headers_removed", 0)
        metrics["running_footers_removed"] += hf_metrics.get("footers_removed", 0)

        # Step 2: Reconstruct sentences, lists, and paragraphs within each page
        for p in cleaned_pages:
            raw_page_text = p.get("text", "")
            if not raw_page_text.strip():
                continue

            page_res = cls.reconstruct_page_text(raw_page_text, page_number=p.get("page_number", 1))
            p["text"] = page_res["text"]
            p["reconstructed_lines"] = page_res.get("lines", [])
            if "confidence" not in p:
                p["confidence"] = page_res.get("confidence", "HIGH")
            p["reconstruction_confidence"] = page_res.get("confidence", "HIGH")
            p["confidence_score"] = page_res.get("confidence_score", 1.0)
            p["tables"] = page_res.get("tables", [])
            
            metrics["hyphens_repaired"] += page_res["metrics"].get("hyphens_repaired", 0)
            metrics["spacing_corrections"] += page_res["metrics"].get("spacing_corrections", 0)
            metrics["lists_reconstructed"] += page_res["metrics"].get("lists_reconstructed", 0)
            metrics["tables_structured"] += len(page_res.get("tables", []))
            metrics["uncertain_segments_count"] += len(page_res.get("uncertain_segments", []))

        # Step 3: Reconnect sentences broken across consecutive page boundaries
        cleaned_pages, stitched_count = cls.reconnect_cross_page_sentences(cleaned_pages)
        metrics["broken_sentences_stitched"] += stitched_count

        # Assemble full reconstructed text preserving page citations
        full_text_parts = []
        for p in cleaned_pages:
            p_text = p.get("text", "").strip()
            if p_text:
                full_text_parts.append(p_text)

        full_reconstructed = "\n\n".join(full_text_parts).strip()
        full_reconstructed = re.sub(r'\n{3,}', '\n\n', full_reconstructed)

        return full_reconstructed, cleaned_pages, metrics

    # -------------------------------------------------------------------------
    # A & B. Sentence Reconstruction & Hyphenation Repair
    # -------------------------------------------------------------------------

    @classmethod
    def repair_hyphenation(cls, text: str) -> Tuple[str, int]:
        """
        Reconnects words split by visual line wrapping:
        - Checks whether the split word is a natural continuation (de- veloped -> developed).
        - Preserves genuine hyphenated compound words (client-server, real-time).
        """
        repaired_count = 0

        def replace_hyphen(m):
            nonlocal repaired_count
            part1 = m.group(1)
            part2 = m.group(2)
            joined = f"{part1}{part2}".lower()
            hyphenated = f"{part1}-{part2}".lower()

            # Preserve if known compound word
            if hyphenated in NATURALLY_HYPHENATED:
                return f"{part1}-{part2}"

            # If part2 starts with lowercase and is an alphabetic word fragment, stitch it
            if part2[0].islower() and len(part1) >= 2 and len(part2) >= 2:
                repaired_count += 1
                return f"{part1}{part2}"

            # Check known prefix
            if part1.lower() in KNOWN_PREFIXES:
                repaired_count += 1
                return f"{part1}{part2}"

            # Default: keep hyphen if uncertain
            return f"{part1}-{part2}"

        # Match word ending with hyphen, newline, optional whitespace, continuation word
        pattern = re.compile(r'\b([a-zA-Z]{2,})[-–—]\s*\n\s*([a-zA-Z]{2,})\b')
        fixed = pattern.sub(replace_hyphen, text)

        # Also match inline broken hyphens with spaces: "de- veloped"
        inline_pattern = re.compile(r'\b([a-zA-Z]{2,})[-–—]\s+([a-z]{3,})\b')
        def replace_inline(m):
            nonlocal repaired_count
            p1, p2 = m.group(1), m.group(2)
            hyphenated = f"{p1}-{p2}".lower()
            if hyphenated in NATURALLY_HYPHENATED:
                return f"{p1}-{p2}"
            repaired_count += 1
            return f"{p1}{p2}"

        fixed = inline_pattern.sub(replace_inline, fixed)
        return fixed, repaired_count

    @classmethod
    def normalize_punctuation_spacing(cls, text: str) -> Tuple[str, int]:
        """
        Restores missing spaces between words and removes unnecessary spaces before punctuation.
        Preserves mathematical expressions, LaTeX delimiters, URLs, abbreviations, and technical symbols.
        """
        corrections = 0

        # Protect mathematical expressions and LaTeX delimiters from punctuation normalization
        math_spans = []
        def save_math(m):
            math_spans.append(m.group(0))
            return f"__MATH_SPAN_{len(math_spans)-1}__"

        protected = re.sub(r'\$\$[^\$]+?\$\$|\\\[[\s\S]+?\\\]|\$[^\$]+?\$|\\\([\s\S]+?\\\)', save_math, text)

        # 1. Remove spaces before punctuation: "word , text" -> "word, text"
        # Avoid math operators like "- 5" or "+ 3"
        s1 = re.sub(r'\s+([,.:;?!])', r'\1', protected)
        if s1 != protected:
            corrections += 1
            protected = s1

        # 2. Fix missing space after commas, colons, semicolons: "word,next" -> "word, next"
        # Guard against time (10:30) and ratios (1:5) and URLs (https://)
        def fix_comma_colon(m):
            nonlocal corrections
            punc = m.group(1)
            next_char = m.group(2)
            if punc == ':' and next_char.isdigit():
                return m.group(0)  # Time or ratio
            if m.group(0).startswith(('http', 'ftp', 'urn')):
                return m.group(0)
            corrections += 1
            return f"{punc} {next_char}"

        s2 = re.sub(r'([,;:])([a-zA-Z])', fix_comma_colon, protected)
        if s2 != protected:
            protected = s2

        # 3. Fix missing space after period followed by uppercase letter: "world.The" -> "world. The"
        # Guard against abbreviations like "e.g.", "i.e.", "et al.", "3.14"
        def fix_period_space(m):
            nonlocal corrections
            word_before = m.group(1)
            char_after = m.group(2)
            token = f"{word_before.lower()}."
            if token in COMMON_ABBREVIATIONS or len(word_before) == 1:
                return m.group(0)  # Initial or abbreviation
            corrections += 1
            return f"{word_before}. {char_after}"

        s3 = re.sub(r'\b([a-zA-Z]{2,})\.([A-Z])', fix_period_space, protected)
        if s3 != protected:
            protected = s3

        # 4. Remove space inside parentheses: "( word )" -> "(word)"
        protected = re.sub(r'\(\s+', '(', protected)
        protected = re.sub(r'\s+\)', ')', protected)

        # Restore protected mathematical expressions
        for idx, span in enumerate(math_spans):
            protected = protected.replace(f"__MATH_SPAN_{idx}__", span)

        return protected, corrections

    # -------------------------------------------------------------------------
    # D. Numbered Lists & Bullet Reconstruction
    # -------------------------------------------------------------------------

    @classmethod
    def reconstruct_fragmented_lists(cls, lines: List[str]) -> Tuple[List[str], int]:
        """
        Transforms fragmented list lines into structured, logically unified list entries.
        Example:
            1. Software is developed or engineered.
            It is not manufactured in the classical sense.
            2. Software does not wear out.
            It deteriorates due to changes.
        Reconstructs into:
            1. **Software is developed or engineered, not manufactured in the classical sense.**
            2. **Software does not wear out.**
               Software may deteriorate as changes and modifications are introduced.
        """
        reconstructed = []
        lists_fixed = 0
        i = 0
        n = len(lines)

        re_list_start = re.compile(r'^\s*(\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s+(.*)$')
        re_bullet_start = re.compile(r'^\s*([-*•▪o])\s+(.*)$')

        while i < n:
            line = lines[i].rstrip()
            stripped = line.strip()

            if not stripped:
                reconstructed.append("")
                i += 1
                continue

            # Check for isolated number alone on a line: "1." or "2."
            re_isolated_num = re.match(r'^\s*(\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s*$', stripped)
            if re_isolated_num and i + 1 < n and lines[i + 1].strip():
                num = re_isolated_num.group(1)
                next_content = lines[i + 1].strip()
                line = f"{num}. {next_content}"
                stripped = line
                i += 1  # Consumed next line
                lists_fixed += 1

            m_num = re_list_start.match(stripped)
            m_bul = re_bullet_start.match(stripped)

            if m_num or m_bul:
                lists_fixed += 1
                prefix = f"{m_num.group(1)}." if m_num else f"{m_bul.group(1)}"
                content = m_num.group(2).strip() if m_num else m_bul.group(2).strip()
                supporting_lines = []

                # Lookahead: collect continuation lines that belong to this list item
                j = i + 1
                while j < n:
                    next_line = lines[j].strip()
                    if not next_line:
                        # Empty line: check if next-next line is a continuation
                        if j + 1 < n and re.match(r'^[a-z]', lines[j + 1].strip()):
                            j += 1
                            continue
                        break

                    # If next line is a new list item or heading, stop collecting
                    if re_list_start.match(next_line) or re_bullet_start.match(next_line) or next_line.startswith(('#', '###', 'Chapter', 'Section')):
                        break

                    # If next line starts with lowercase or continuation word, it's part of this item
                    if next_line[0].islower() or len(next_line.split()) < 12 or not content.endswith(('.', ':', ';', '!', '?')):
                        supporting_lines.append(next_line)
                        j += 1
                    else:
                        break

                i = j - 1  # Advance main index

                # Format list item professionally:
                # If content has a leading title or is short, bold the primary proposition
                if supporting_lines:
                    # Attach first sentence or combine if short
                    combined_first = content
                    if not combined_first.endswith('.'):
                        combined_first = f"{combined_first}."
                    
                    # Indent supporting points with 3 spaces
                    indent_supporting = "\n   " + " ".join(supporting_lines)
                    reconstructed.append(f"{prefix} **{combined_first}**{indent_supporting}")
                else:
                    # Single line list item
                    reconstructed.append(f"{prefix} {content}")
            else:
                reconstructed.append(line)

            i += 1

        return reconstructed, lists_fixed

    # -------------------------------------------------------------------------
    # E. Heading and Subheading Reconstruction
    # -------------------------------------------------------------------------

    @classmethod
    def reconstruct_headings(cls, lines: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Identifies headings using multi-signal classification:
        - Numbering patterns (1., 1.1, Chapter 2)
        - Capitalization & length
        - Semantic relationship
        Applies a consistent hierarchy:
        # Title
        ## Chapter / Main Section
        ### Subsection / Topic
        #### Sub-subsection / Deep Concept
        """
        reconstructed = []
        headings = []
        
        re_numbered_head = re.compile(r'^(?:chapter|section|module|unit)?\s*(\d+(?:\.\d+)*)[:\s\-–—]+([A-Z][a-zA-Z0-9\s\-,:?]+)$', re.I)

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                reconstructed.append("")
                continue

            # Skip if already a markdown heading, table, bullet, or code/math block
            # (Guard: do NOT skip numbered headings like 1.1 or 2.1)
            if stripped.startswith(('#', '|', '-', '*', '```', '$$', '>')) or (re.match(r'^\d+\.\s+', stripped) and not re.match(r'^\d+\.\d+', stripped)):
                reconstructed.append(line)
                continue

            # Signal 1: Numbered heading pattern
            m = re_numbered_head.match(stripped)
            if m:
                num_parts = m.group(1).split('.')
                title = m.group(2).strip()
                depth = len(num_parts)
                level = min(max(depth + 1, 2), 4)  # 2 to 4 hashes
                hashes = '#' * level
                h_line = f"\n{hashes} {m.group(1)} {title}\n"
                reconstructed.append(h_line)
                headings.append({"title": title, "number": m.group(1), "level": level})
                continue

            # Signal 2: Short title-cased or uppercase line without ending punctuation
            words = stripped.split()
            if 1 <= len(words) <= 7 and len(stripped) < 65 and not stripped.endswith(('.', ':', ';', '!', '?', ',')):
                # Ensure it's not a common sentence fragment or table text
                if stripped.isupper() or all(w[0].isupper() for w in words if w and w[0].isalpha()):
                    # Check if it contains a verb indicating a normal sentence
                    has_sentence_verb = any(v in f" {stripped.lower()} " for v in [' is ', ' are ', ' was ', ' were ', ' has ', ' have ', ' will '])
                    if not has_sentence_verb:
                        h_line = f"\n### {stripped}\n"
                        reconstructed.append(h_line)
                        headings.append({"title": stripped, "level": 3})
                        continue

            reconstructed.append(line)

        return reconstructed, headings

    # -------------------------------------------------------------------------
    # F. Page Headers, Footers & Boundaries
    # -------------------------------------------------------------------------

    @classmethod
    def detect_and_remove_running_headers_footers(cls, pages_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Detects repeated running headers and footers across pages by frequency analysis.
        Removes running headers from the main explanation while preserving page citations.
        """
        if len(pages_data) < 2:
            return pages_data, {"headers_removed": 0, "footers_removed": 0}

        top_lines_freq: Dict[str, int] = {}
        bottom_lines_freq: Dict[str, int] = {}

        # Sample top and bottom lines of each page
        for p in pages_data:
            lines = [l.strip() for l in p.get("text", "").splitlines() if l.strip()]
            if lines:
                top_line = lines[0]
                if len(top_line) > 3 and not top_line.startswith('#'):
                    top_lines_freq[top_line] = top_lines_freq.get(top_line, 0) + 1
            if len(lines) >= 2:
                bottom_line = lines[-1]
                if len(bottom_line) > 3:
                    bottom_lines_freq[bottom_line] = bottom_lines_freq.get(bottom_line, 0) + 1

        # A line is a running header if it appears in >= 40% of pages (minimum 2 pages)
        threshold = max(2, int(len(pages_data) * 0.4))
        running_headers = {line for line, count in top_lines_freq.items() if count >= threshold}
        running_footers = {line for line, count in bottom_lines_freq.items() if count >= threshold}

        headers_removed = 0
        footers_removed = 0

        cleaned_pages = []
        for p in pages_data:
            p_copy = dict(p)
            lines = p.get("text", "").splitlines()
            new_lines = []
            for idx, line in enumerate(lines):
                s = line.strip()
                # Check top running header
                if idx <= 2 and s in running_headers:
                    headers_removed += 1
                    continue
                # Check bottom running footer
                if idx >= len(lines) - 3 and s in running_footers:
                    footers_removed += 1
                    continue
                # Check standalone page numbers e.g. "Page 14" or pure digits
                if re.match(r'^(?:page\s*\d+|\b\d+\b|[-–—]\s*\d+\s*[-–—])$', s, re.I):
                    footers_removed += 1
                    continue
                new_lines.append(line)

            p_copy["text"] = "\n".join(new_lines)
            cleaned_pages.append(p_copy)

        return cleaned_pages, {"headers_removed": headers_removed, "footers_removed": footers_removed}

    @classmethod
    def reconnect_cross_page_sentences(cls, pages_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Reconnects sentences broken across consecutive page boundaries.
        If Page N ends without punctuation and Page N+1 starts with lowercase/continuation,
        smoothly stitches the sentence.
        """
        stitched = 0
        for i in range(len(pages_data) - 1):
            curr_p = pages_data[i]
            next_p = pages_data[i + 1]

            curr_lines = [l for l in curr_p.get("text", "").splitlines() if l.strip()]
            next_lines = [l for l in next_p.get("text", "").splitlines() if l.strip()]

            if not curr_lines or not next_lines:
                continue

            last_line = curr_lines[-1].strip()
            first_line = next_lines[0].strip()

            # Condition 1: Last line ends without terminal punctuation or with a hyphen
            ends_open = not last_line.endswith(('.', ':', ';', '!', '?', '#'))
            # Condition 2: First line of next page starts with lowercase letter or continuation
            starts_continuation = first_line and first_line[0].islower()

            if ends_open and starts_continuation:
                stitched += 1
                if last_line.endswith(('-', '–', '—')):
                    stitched_word = f"{last_line[:-1]}{first_line}"
                else:
                    stitched_word = f"{last_line} {first_line}"

                # Update current page to end with stitched sentence
                curr_lines[-1] = stitched_word
                curr_p["text"] = "\n".join(curr_lines)

                # Remove the continuation fragment from next page
                next_p["text"] = "\n".join(next_lines[1:])

        return pages_data, stitched

    # -------------------------------------------------------------------------
    # C. Paragraph Segmentation & Cohesion
    # -------------------------------------------------------------------------

    @classmethod
    def is_math_or_calculation_line(cls, line: str) -> bool:
        """
        Detects if a line is an equation, LaTeX math block, calculation step, or derivation line.
        These lines must be preserved as separate lines rather than merged into prose paragraphs.
        """
        s = line.strip()
        if not s:
            return False
        if s.startswith(('$$', r'\[', r'\]', r'\begin{', r'\end{', r'\(', r'\)')):
            return True
        if re.match(r'^(?:step\s*\d+:|given:|to\s*find:|required:|formula:|substitution:|final\s*answer:|where:)', s, re.I):
            return True
        if '&=' in s or s.endswith(r'\\'):
            return True
        if re.search(r'\\(?:frac|sum|int|sqrt|alpha|beta|theta|partial|times|cdot)\b', s):
            return True
        # Isolated equation like '2x + 5 = 15' or 'x = 10 / 2'
        if '=' in s and len(s) < 80:
            parts = s.split('=', 1)
            lhs = parts[0].strip()
            # If LHS has 1 to 4 tokens and contains numbers or operators, treat as equation
            if len(lhs.split()) <= 4 and re.search(r'[\d\+\-\*/\^]', s) and not s.endswith(('.', '!', '?')):
                return True
        return False

    @classmethod
    def reconstruct_paragraphs(cls, lines: List[str]) -> List[str]:
        """
        Groups lines into logically connected explanatory paragraphs.
        Avoids monolithic walls of text and avoids 1-sentence micro-paragraphs.
        Guarantees that mathematical steps and derivations remain on separate lines.
        """
        paragraphs = []
        current_para = []

        for line in lines:
            stripped = line.strip()

            # Empty line or Markdown heading or table triggers flush of current paragraph
            if not stripped or stripped.startswith(('#', '|', '```', '$$', '>', '1.', '2.', '3.', '-', '*')):
                if current_para:
                    paragraphs.append(" ".join(current_para))
                    current_para = []
                if stripped:
                    paragraphs.append(line)
                continue

            # Mathematical formulas and derivation steps must never be collapsed into prose
            if cls.is_math_or_calculation_line(stripped):
                if current_para:
                    paragraphs.append(" ".join(current_para))
                    current_para = []
                paragraphs.append(stripped)
                continue

            # Check if line starts a new concept / topic transition
            re_topic_transition = re.compile(
                r'^(?:for example|consider|in contrast|furthermore|moreover|on the other hand|in summary|specifically|importantly|in conclusion)[:,\s]',
                re.I
            )
            if re_topic_transition.match(stripped) and len(current_para) >= 2:
                paragraphs.append(" ".join(current_para))
                current_para = [stripped]
                continue

            current_para.append(stripped)

            # Prevent monolithic runaway paragraphs (> 180 words)
            para_word_count = sum(len(p.split()) for p in current_para)
            if para_word_count >= 140 and stripped.endswith(('.', '!', '?')):
                paragraphs.append(" ".join(current_para))
                current_para = []

        if current_para:
            paragraphs.append(" ".join(current_para))

        return paragraphs

    # -------------------------------------------------------------------------
    # H. Tables & Structured Content
    # -------------------------------------------------------------------------

    @classmethod
    def detect_and_format_tables(cls, lines: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Detects tabular rows (pipe-delimited, tab-delimited, or multi-space aligned)
        and formats them into clean GitHub-flavored Markdown tables.
        """
        out_lines = []
        tables = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i].rstrip()
            stripped = line.strip()

            # Case 1: Already Markdown pipe table
            if stripped.startswith('|') and stripped.endswith('|'):
                table_block = []
                while i < n and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    table_block.append(lines[i].strip())
                    i += 1
                if len(table_block) >= 2:
                    out_lines.extend(table_block)
                    tables.append({"type": "markdown_table", "rows": len(table_block)})
                continue

            # Case 2: Tab-delimited or multi-space aligned column rows (>= 2 columns, >= 2 rows)
            parts = re.split(r'\t+|\s{3,}', stripped)
            if len(parts) >= 2 and not stripped.startswith(('#', '-', '*', '1.', '2.')):
                candidate_table = [parts]
                j = i + 1
                while j < n:
                    nxt = lines[j].strip()
                    if not nxt:
                        break
                    nxt_parts = re.split(r'\t+|\s{3,}', nxt)
                    if len(nxt_parts) >= 2 and abs(len(nxt_parts) - len(parts)) <= 1:
                        candidate_table.append(nxt_parts)
                        j += 1
                    else:
                        break

                if len(candidate_table) >= 2:
                    # Construct Markdown Table
                    max_cols = max(len(r) for r in candidate_table)
                    header_row = candidate_table[0] + [""] * (max_cols - len(candidate_table[0]))
                    sep_row = [":---"] * max_cols
                    md_table = [
                        "| " + " | ".join(header_row) + " |",
                        "| " + " | ".join(sep_row) + " |"
                    ]
                    for row in candidate_table[1:]:
                        padded_row = row + [""] * (max_cols - len(row))
                        md_table.append("| " + " | ".join(padded_row) + " |")

                    out_lines.append("")
                    out_lines.extend(md_table)
                    out_lines.append("")
                    tables.append({"type": "aligned_table", "rows": len(candidate_table)})
                    i = j
                    continue

            out_lines.append(line)
            i += 1

        return out_lines, tables

    # -------------------------------------------------------------------------
    # I. OCR Confidence Classification
    # -------------------------------------------------------------------------

    @classmethod
    def classify_ocr_confidence(cls, text: str) -> Dict[str, Any]:
        """
        Classifies extracted text confidence:
        - HIGH: clear text, standard vocabulary, clean punctuation
        - MEDIUM: minor formatting or OCR spacing corrections applied
        - LOW: high symbol corruption ratio or fragmented sentences
        """
        if not text or not text.strip():
            return {"confidence": "LOW", "score": 0.0, "uncertain_segments": []}

        words = text.split()
        if not words:
            return {"confidence": "LOW", "score": 0.0, "uncertain_segments": []}

        # Metric 1: Alphanumeric character ratio
        alnums = sum(1 for c in text if c.isalnum() or c in ' \t\n')
        alnum_ratio = alnums / max(1, len(text))

        # Metric 2: Gibberish or unprintable symbols
        symbol_noise = len(re.findall(r'[|!_~`#$^&*]{3,}', text))

        # Metric 3: Broken hyphen fragments
        broken_hyphens = len(re.findall(r'\b[a-zA-Z]{1,2}-[a-zA-Z]{1,2}\b', text))

        score = 1.0
        score -= max(0.0, (0.75 - alnum_ratio) * 1.5)
        score -= min(0.3, symbol_noise * 0.05)
        score -= min(0.2, broken_hyphens * 0.04)
        score = max(0.1, min(1.0, score))

        uncertain_segments = []
        if score < 0.7:
            # Find specific lines with low confidence
            for idx, line in enumerate(text.splitlines()[:50]):
                l_strip = line.strip()
                if l_strip and len(l_strip) > 10:
                    l_alnum = sum(1 for c in l_strip if c.isalnum() or c in ' ') / len(l_strip)
                    if l_alnum < 0.55:
                        uncertain_segments.append({
                            "line_num": idx + 1,
                            "text": l_strip[:80],
                            "reason": "High symbol corruption or OCR noise"
                        })

        confidence_tier = "HIGH" if score >= 0.85 else ("MEDIUM" if score >= 0.65 else "LOW")

        return {
            "confidence": confidence_tier,
            "score": round(score, 3),
            "uncertain_segments": uncertain_segments
        }

    # -------------------------------------------------------------------------
    # Full Page Pipeline
    # -------------------------------------------------------------------------

    @classmethod
    def reconstruct_page_text(cls, raw_text: str, page_number: int = 1) -> Dict[str, Any]:
        """
        Executes the full Phase 4A reconstruction pipeline on a single page of text.
        """
        if not raw_text:
            return {"text": "", "lines": [], "confidence": "HIGH", "confidence_score": 1.0, "metrics": {}, "tables": [], "uncertain_segments": []}

        metrics = {
            "hyphens_repaired": 0,
            "spacing_corrections": 0,
            "lists_reconstructed": 0
        }

        # 1. Hyphen repair
        t1, hyphens_fixed = cls.repair_hyphenation(raw_text)
        metrics["hyphens_repaired"] += hyphens_fixed

        # 2. Punctuation spacing normalization
        t2, spacing_fixed = cls.normalize_punctuation_spacing(t1)
        metrics["spacing_corrections"] += spacing_fixed

        # 3. Line-by-line processing
        raw_lines = t2.splitlines()

        # 4. List reconstruction
        lines_with_lists, lists_fixed = cls.reconstruct_fragmented_lists(raw_lines)
        metrics["lists_reconstructed"] += lists_fixed

        # 5. Table detection and formatting (Executed BEFORE headings so aligned table rows are preserved)
        lines_with_tables, tables = cls.detect_and_format_tables(lines_with_lists)

        # 6. Heading reconstruction
        lines_with_headings, headings = cls.reconstruct_headings(lines_with_tables)

        # 7. Paragraph segmentation
        final_paragraphs = cls.reconstruct_paragraphs(lines_with_headings)

        reconstructed_text = "\n\n".join([p for p in final_paragraphs if p.strip()]).strip()
        reconstructed_text = re.sub(r'\n{3,}', '\n\n', reconstructed_text)

        # 8. OCR confidence classification
        conf_data = cls.classify_ocr_confidence(reconstructed_text)

        return {
            "text": reconstructed_text,
            "lines": final_paragraphs,
            "headings": headings,
            "tables": tables,
            "confidence": conf_data["confidence"],
            "confidence_score": conf_data["score"],
            "uncertain_segments": conf_data["uncertain_segments"],
            "metrics": metrics
        }
