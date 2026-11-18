"""
=============================================================================
StudyAI — Complete Notes Generation, Verification & Export Engine (v4.0)
=============================================================================
Orchestrates:
1. Syllabus-Aware Coverage Planning (Subject -> Module -> Topic -> Subtopic)
2. Section-by-Section Pedagogical Generation (15 Academic Dimensions)
3. Source Grounding via Retrieved Semantic Chunks & Page References
4. Independent Quality Control, Completeness & Mathematical Verifier
5. Targeted Defect Repair with Configurable Retries
6. Persistent & Resumable Job State Tracking (NotesGenerationJob)
7. Word (.docx) & PDF (.pdf) Academic Export Engines
=============================================================================
"""

import os
import re
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from .models import Document, Chunk, NotesGenerationJob, SyllabusSection
from .document_service import destack_vertical_text, normalize_academic_math_and_ocr
from .summary_engine import (
    detect_document_structure,
    clean_heading_title,
    _format_as_latex_equation,
    _is_valid_mathematical_formula,
    SUMMARY_MODES
)
from .prompt_templates import ACADEMIC_NOTE_ANALYSIS_GUIDELINES
from .math_verification import verify_arithmetic_equalities
from .ai_provider_service import query_ai, check_ai_provider_status
from .ollama_service import get_configured_model
from .typography_system import DocumentTypography
from .academic_ir import AcademicDocumentIR, AcademicSectionIR, AcademicElementIR, AcademicElementType, GroundingType
from .deep_content_intelligence import DeepContentIntelligenceEngine
from .precision_layout_engine import PrecisionLayoutEngine
from .self_correcting_engine import (
    SelfRepairEngine,
    TopicCompletenessEngine,
    InformationDensityController,
    NumericalSolutionAuditor,
    HonestQualityDashboard
)

logger = logging.getLogger(__name__)

VERIFICATION_SCOPE_NOTICE = (
    "Automated checks assess structure, length, math formatting, and simple arithmetic only; "
    "factual accuracy is not independently verified. Compare claims with the uploaded document."
)


def _format_section_status(status: str) -> str:
    if status == "VERIFIED":
        return "Automated checks passed"
    return f"Review needed ({status.replace('_', ' ').lower()})"


# =============================================================================
# 1. Syllabus-Aware Coverage Planner
# =============================================================================

def normalize_notes_depth(depth: str) -> str:
    """Map API/UI depth aliases to the generator's supported depth levels."""
    normalized = (depth or "").strip().lower()
    if normalized in {"basic"}:
        return "basic"
    if normalized in {"advanced", "deep", "thorough"}:
        return "advanced"
    return "intermediate"


def _source_chunk_parts(chunk: Any) -> Tuple[str, Any, Any]:
    if hasattr(chunk, "text"):
        start = getattr(chunk, "page_start", None)
        end = getattr(chunk, "page_end", start)
        return str(chunk.text or ""), start, end
    if isinstance(chunk, dict):
        start = chunk.get("page_start")
        return str(chunk.get("text") or ""), start, chunk.get("page_end", start)
    return str(chunk or ""), None, None


def _source_page_label(start: Any, end: Any) -> str:
    if start is None:
        return "page unavailable"
    if end is None or str(end) == str(start):
        return f"Page {start}"
    return f"Pages {start}-{end}"


def plan_syllabus_checklist(
    document: Document,
    user_syllabus: Optional[List[Dict[str, Any]]] = None,
    mode: str = 'standard',
    depth: str = 'intermediate',
    language: str = 'en',
    user: Any = None
) -> NotesGenerationJob:
    """
    Creates a persistent NotesGenerationJob and plans a complete topic checklist
    using either an official/user-supplied syllabus or a document-derived outline.
    Maps relevant source chunks and page numbers to every topic.
    """
    job_uuid = uuid.uuid4().hex[:16]
    syllabus_source = 'official_syllabus' if user_syllabus else 'document_derived'

    job = NotesGenerationJob.objects.create(
        job_id=job_uuid,
        document=document,
        user=user if (user and hasattr(user, 'is_authenticated') and user.is_authenticated) else None,
        mode=mode,
        depth=normalize_notes_depth(depth),
        language=language,
        syllabus_source=syllabus_source,
        status='PLANNING',
        current_step_label='Planning syllabus coverage checklist...',
        progress_percent=5
    )

    planned_topics = []

    if user_syllabus and isinstance(user_syllabus, list) and len(user_syllabus) > 0:
        for idx, item in enumerate(user_syllabus, start=1):
            t_name = item.get("name") or item.get("title") or f"Topic {idx}"
            t_module = item.get("module") or "Module 1"
            t_parent = item.get("parent_topic", "")
            t_cov = item.get("required_coverage") or item.get("description", "")
            planned_topics.append({
                "topic_id": f"top-{idx}",
                "title": clean_heading_title(t_name),
                "parent_topic": t_parent,
                "module": t_module,
                "order_index": idx,
                "required_coverage": t_cov,
                "preferred_pages": item.get("pages", [])
            })
    else:
        # Document-Derived Syllabus Planning
        raw_text = document.raw_text
        if not raw_text and document.chunks.exists():
            raw_text = "\n\n".join(c.text for c in document.chunks.order_by('chunk_index'))

        doc_struct = detect_document_structure(raw_text, title=document.title, total_pages=document.page_count)

        for idx, sec in enumerate(doc_struct.sections, start=1):
            sec_title = clean_heading_title(sec["title"])
            sec_module = sec.get("module", f"Module {sec.get('module_number', 1)}")
            page_start = sec.get("page_start", 1)
            page_end = sec.get("page_end", 1)

            # Build required learning outcomes from detected elements
            defs = [d.get("term", "") for d in sec.get("definitions", []) if d.get("term")]
            thms = [t.get("name", "") for t in sec.get("theorems", []) if t.get("name")]
            algos = [a.get("name", "") for a in sec.get("algorithms", []) if a.get("name")]

            req_items = []
            if defs:
                req_items.append(f"Formal definitions of: {', '.join(defs[:4])}")
            if thms:
                req_items.append(f"Statements and proof ideas for: {', '.join(thms[:3])}")
            if algos:
                req_items.append(f"Algorithmic steps and procedures for: {', '.join(algos[:2])}")
            req_items.append("Step-by-step worked examples, mathematical notation, and exam insights.")

            planned_topics.append({
                "topic_id": f"sec-{idx}",
                "title": sec_title,
                "parent_topic": sec.get("parent_section", ""),
                "module": sec_module,
                "order_index": idx,
                "required_coverage": "; ".join(req_items),
                "page_start": page_start,
                "page_end": page_end
            })

    # Map relevant source chunks to every planned topic
    all_chunks = list(document.chunks.order_by('chunk_index').values(
        'id', 'chunk_index', 'page_start', 'page_end', 'section', 'text'
    ))

    manifest_entries = []

    for item in planned_topics:
        topic_title_lower = item["title"].lower()
        topic_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', topic_title_lower)) - {
            'chapter', 'section', 'module', 'theory', 'study', 'notes'
        }

        p_start = item.get("page_start")
        p_end = item.get("page_end")
        has_explicit_pages = bool(p_start and p_end)

        scored_chunks = []
        for c in all_chunks:
            c_pstart = c["page_start"]
            c_pend = c["page_end"]
            c_pages = set(range(c_pstart, c_pend + 1))
            c_text_lower = c["text"].lower()

            score = 0.0
            is_page_match = False

            if has_explicit_pages:
                # Page locality window: target pages with +/- 1 page tolerance for context continuity
                locality_window = set(range(max(1, p_start - 1), p_end + 2))
                exact_window = set(range(p_start, p_end + 1))
                if c_pages.intersection(exact_window):
                    score += 100.0
                    is_page_match = True
                elif c_pages.intersection(locality_window):
                    score += 40.0
                    is_page_match = True
                else:
                    # Penalize chunks located far from topic page
                    center_page = (p_start + p_end) / 2.0
                    dist = min(abs(c_pstart - center_page), abs(c_pend - center_page))
                    score -= dist * 4.0

            # Title phrase match in chunk
            if topic_title_lower in c_text_lower:
                score += 50.0

            # Content keyword overlap
            c_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', c_text_lower))
            overlap = len(topic_words.intersection(c_words))
            score += overlap * 10.0

            # Section metadata match
            if c["section"] and item["title"].lower() in c["section"].lower():
                score += 30.0

            if has_explicit_pages:
                if is_page_match or score >= 70.0:
                    scored_chunks.append((score, c))
            else:
                if score >= 20.0 or overlap >= 2:
                    scored_chunks.append((score, c))

        # Sort descending by score and pick top 4 targeted chunks (prevents global chunk flooding)
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c for _, c in scored_chunks[:4]]

        matched_chunk_ids = [c["id"] for c in top_chunks]
        matched_pages = set()
        for c in top_chunks:
            matched_pages.update(range(c["page_start"], c["page_end"] + 1))

        sec_record = SyllabusSection.objects.create(
            job=job,
            topic_id=item["topic_id"],
            title=item["title"],
            parent_topic=item.get("parent_topic", ""),
            module=item.get("module", "Core Module"),
            order_index=item["order_index"],
            required_coverage=item["required_coverage"],
            status='NOT_STARTED'
        )
        sec_record.set_source_chunks(matched_chunk_ids)
        sec_record.source_pages_json = json.dumps(sorted(list(matched_pages)))
        sec_record.save()

        manifest_entries.append({
            "topic_id": item["topic_id"],
            "title": item["title"],
            "module": item.get("module"),
            "pages": sorted(list(matched_pages)),
            "chunks_count": len(matched_chunk_ids),
            "status": "NOT_STARTED"
        })

    job.total_topics = len(planned_topics)
    job.coverage_manifest_json = json.dumps({
        "document_title": document.title,
        "subject": document.subject,
        "syllabus_source": syllabus_source,
        "total_topics": len(planned_topics),
        "manifest": manifest_entries
    })
    job.status = 'QUEUED'
    job.current_step_label = f"Checklist created with {len(planned_topics)} topics. Ready for generation."
    job.progress_percent = 10
    job.save()

    return job


# =============================================================================
# 2. Section-by-Section Pedagogical Generator
# =============================================================================

def generate_single_section_notes(
    section: SyllabusSection,
    source_chunks: Optional[List[Any]] = None,
    document_subject: str = "Computer Science & Engineering",
    mode: str = "standard",
    depth: str = "intermediate",
    relevant_chunks_text: Optional[str] = None,
    language: str = "en",
    reference_style_profile: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Generates comprehensive, pedagogically rich notes for a single syllabus section.
    Enforces the 15 academic dimensions required for complete study notes.
    """
    context_blocks = []
    if source_chunks:
        for c in source_chunks:
            text, page_start, page_end = _source_chunk_parts(c)
            p_label = _source_page_label(page_start, page_end)
            context_blocks.append(f"--- Source Context ({p_label}) ---\n{text}")
    elif relevant_chunks_text:
        context_blocks.append(
            f"--- Source Context ({_source_page_label(None, None)}) ---\n{relevant_chunks_text}"
        )

    context_text = "\n\n".join(context_blocks).strip()
    if not context_text:
        return (
            f"## {section.title}\n\n"
            "> There is no source text mapped to this topic. Notes were not generated "
            "because there is not enough evidence to explain it reliably."
        )
    if len(context_text) > 8000:
        context_text = context_text[:8000].rsplit("\n\n", 1)[0].strip()

    # Target word count and detail expectations based on depth
    depth_instructions = {
        'basic': "Focus on fundamental definitions, intuitive explanations, core formulas, and 1 introductory example. Target length: 300-450 words.",
        'intermediate': "Provide rigorous academic explanations, variable breakdowns, step-by-step mathematical derivations, algorithms, 2 concrete examples, and common traps. Target length: 500-800 words.",
        'advanced': "Deliver exhaustive textbook-level depth, formal mathematical proofs, invariants, algorithmic pseudocode, complete worked derivations, edge cases, and exam insights. Target length: 800-1200 words."
    }
    depth = normalize_notes_depth(depth)
    depth_guidance = depth_instructions[depth]
    profile_guidance = []
    if isinstance(reference_style_profile, dict):
        guidance = reference_style_profile.get("guidance")
        if isinstance(guidance, list):
            profile_guidance = [
                item for item in guidance
                if isinstance(item, str) and item.strip()
            ][:10]
    style_guidance_block = (
        "\n".join(f"- {item}" for item in profile_guidance)
        if profile_guidance else
        "- Use a clear, readable structure appropriate to the topic."
    )

    prompt = f"""You are an expert university professor and technical author writing a comprehensive textbook section.

Topic Title: "{section.title}"
Module: "{section.module}"
Subject: {document_subject}
Output language: {language} (preserve technical notation and source terminology)
Required Learning Outcomes: {section.required_coverage}

{depth_guidance}

Academic Note Analysis:
{ACADEMIC_NOTE_ANALYSIS_GUIDELINES}

Presentation guidance (style only; not a source of facts):
{style_guidance_block}
Use only the uploaded study document for factual claims. Do not copy or infer facts, examples, or explanations from the style reference.

Write naturally with clear Markdown headings. Use inline LaTeX for symbols in sentences and display LaTeX for standalone equations. Do not force dimensions that do not apply to this topic.

Source Context from Uploaded Document:
{context_text}

Section Study Notes (Markdown):
"""

    resp_text = ""
    st = check_ai_provider_status()

    if st.get("can_generate"):
        active_model = st.get("default_model") or get_configured_model() or "llama3:latest"
        timeout = getattr(settings, 'OLLAMA_TIMEOUT', 120)
        temp = getattr(settings, 'OLLAMA_TEMPERATURE', 0.2)

        out, success, err = query_ai(
            prompt,
            model=active_model,
            temperature=temp,
            timeout=timeout,
            num_predict=2500
        )
        if success and out and len(out.strip().split()) >= 150:
            resp_text = out.strip()

    # Grounded Deterministic Fallback if Ollama offline or output truncated
    if not resp_text:
        resp_text = _generate_deterministic_section_notes(section, source_chunks, document_subject, depth)

    # Phase 7: Post-process for precision line alignment, destacking, and math layout
    resp_text = destack_vertical_text(resp_text)
    resp_text = PrecisionLayoutEngine.reconstruct_logical_paragraphs(resp_text)
    resp_text = PrecisionLayoutEngine.align_list_items(resp_text)
    resp_text = PrecisionLayoutEngine.align_multiline_equations(resp_text)
    resp_text = normalize_academic_math_and_ocr(resp_text)

    return resp_text


def _generate_deterministic_section_notes(
    section: SyllabusSection,
    source_chunks: Optional[List[Dict[str, Any]]],
    document_subject: str,
    depth: str
) -> str:
    """
    Builds a transparent offline outline from source excerpts without inventing facts.
    """
    lines = [f"## {section.title}", ""]
    lines.extend([
        "> Offline mode organizes extracted source text; it does not add unsupported explanations or examples.",
        "",
        "### What the source says",
        ""
    ])

    source_chunks = source_chunks or []
    paragraphs = []
    formula_entries = []
    for chunk in source_chunks:
        chunk_text, page_start, page_end = _source_chunk_parts(chunk)
        page_label = _source_page_label(page_start, page_end)
        normalized_text = normalize_academic_math_and_ocr(destack_vertical_text(chunk_text))
        paragraphs.extend(
            f"{paragraph.strip()} (Source: {page_label})"
            for paragraph in re.split(r"\n\s*\n", normalized_text)
            if len(paragraph.strip()) > 30
            and not paragraph.strip().startswith(("Chapter", "Page", "---"))
        )
        formulas = re.findall(r"\$\$(.+?)\$\$|\$([^$\n]+)\$", normalized_text, re.S)
        formula_entries.extend(
            f"- `${(display or inline).strip()}$` (Source: {page_label})"
            for display, inline in formulas
        )

    paragraphs = list(dict.fromkeys(paragraphs))

    if paragraphs:
        lines.append("\n\n".join(paragraphs[:8]))
    else:
        lines.append("The mapped source text did not contain readable paragraphs for this topic.")

    formula_entries = list(dict.fromkeys(formula_entries))
    if formula_entries:
        lines.extend(["", "### Formulas found in the source", ""])
        lines.extend(formula_entries[:8])

    example_paragraphs = [
        paragraph for paragraph in paragraphs
        if re.search(r"\b(example|for instance|calculate|problem|solution|e\.g\.)\b", paragraph, re.I)
    ]
    lines.extend(["", "### Examples", ""])
    if example_paragraphs:
        lines.append("\n\n".join(example_paragraphs[:3]))
    else:
        lines.append("No worked example was identified in the mapped source text.")

    lines.extend([
        "",
        "### What is not established by this source",
        "",
        "A formal definition, step-by-step method, diagram, advantages, and disadvantages are included only when the source provides enough evidence. "
        "Use an online model or add more source material for a deeper explanation."
    ])
    return "\n".join(lines).strip()


# =============================================================================
# 3. Independent Quality-Control & Completeness Verifier
# =============================================================================

def verify_section_notes(
    notes_markdown: str,
    section: SyllabusSection,
    requested_depth: str = "intermediate"
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Performs deterministic, independent quality and completeness audit of generated notes.
    Evaluates:
    - Coverage of required subtopics
    - Mathematical formula validity and balanced delimiters
    - Length and depth adequacy
    - Absence of OCR garbage and truncated sentences
    Returns: (is_verified, score_percent, audit_report)
    """
    defects = []
    missing_items = []
    score = 100.0

    if not notes_markdown or len(notes_markdown.strip()) < 10:
        return False, 0.0, {
            "is_verified": False,
            "score": 0.0,
            "defects": ["Section output is empty or severely deficient."],
            "missing_items": ["All required section content"]
        }

    words = notes_markdown.strip().split()
    word_count = len(words)

    # 1. Depth & Length Check
    min_word_thresholds = {'basic': 180, 'intermediate': 320, 'advanced': 500}
    requested_depth = normalize_notes_depth(requested_depth)
    threshold = min_word_thresholds[requested_depth]

    if word_count < threshold:
        defects.append(f"Section length ({word_count} words) is below requested {requested_depth} threshold ({threshold} words).")
        score -= 25.0

    # 2. Heading Structure Check
    if not re.search(r'^#{1,3}\s+', notes_markdown, re.M):
        defects.append("Missing standard markdown headings (## or ###).")
        score -= 15.0

    # 3. Mathematical Delimiters & Formula Checks
    if notes_markdown.count('$$') % 2 != 0:
        defects.append("Unbalanced LaTeX display ($$) mathematical delimiters detected.")
        score -= 20.0
    elif (notes_markdown.replace('$$', '').count('$')) % 2 != 0:
        defects.append("Unbalanced LaTeX dollar ($) mathematical delimiters detected.")
        score -= 20.0

    if notes_markdown.count('(') != notes_markdown.count(')'):
        defects.append("Unbalanced parentheses detected in mathematical prose.")
        score -= 10.0

    if notes_markdown.count('{') != notes_markdown.count('}'):
        defects.append("Unbalanced curly brackets detected in mathematical expressions.")
        score -= 10.0

    calculation_audit = verify_arithmetic_equalities(notes_markdown)
    if calculation_audit["mismatches"]:
        for mismatch in calculation_audit["mismatches"]:
            defects.append(
                f"Arithmetic mismatch on line {mismatch['line']}: "
                f"{mismatch['expression']} calculates to {mismatch['calculated']}, "
                f"not {mismatch['claimed']}."
            )
        score -= 20.0

    # 4. OCR Garbage Detection
    ocr_artifacts = ['aja2', 'Andn-1', 'd@', '0010"', 'et = 6', 'Qi410i40', '+++', 'Rp = REP']
    found_artifacts = [art for art in ocr_artifacts if art.lower() in notes_markdown.lower()]
    if found_artifacts:
        defects.append(f"OCR noise artifacts detected: {', '.join(found_artifacts)}.")
        score -= 20.0

    # 5. Truncation Detection (dangling sentence at EOF)
    last_char = notes_markdown.strip()[-1]
    if last_char not in ['.', '!', '?', '`', '$', '*', ')', '}']:
        defects.append("Section output appears truncated mid-sentence at end of text.")
        score -= 25.0

    # 6. Worked Example / Derivation Presence Check
    if not re.search(r'\b(example|derivation|step\s*\d+|problem|solution)\b', notes_markdown, re.I):
        missing_items.append("Worked example or step-by-step derivation")
        defects.append("No worked example or derivation was provided for this section.")
        score -= 15.0

    final_score = max(0.0, min(100.0, score))
    is_verified = (final_score >= 80.0 and len(defects) == 0)

    audit_report = {
        "is_verified": is_verified,
        "score": final_score,
        "word_count": word_count,
        "defects": defects,
        "missing_items": missing_items,
        "verification_scope": "structure_length_math_formatting_and_simple_arithmetic",
        "factual_accuracy_verified": False,
        "calculation_audit": calculation_audit,
        "verified_at": timezone.now().isoformat()
    }

    return is_verified, final_score, audit_report


def repair_section_notes(
    notes_markdown: str = "",
    section: Optional[SyllabusSection] = None,
    defects: Optional[List[str]] = None,
    source_chunks: Optional[Any] = None,
    document_subject: str = "Computer Science",
    existing_notes: Optional[str] = None,
    relevant_chunks_text: Optional[str] = None,
    mode: str = "comprehensive",
    depth: str = "intermediate",
    language: str = "en",
    **kwargs
) -> str:
    """
    Performs targeted repair on a defective section without discarding valid content.
    Adds missing examples, repairs mathematical delimiters, or expands depth.
    """
    effective_notes = (existing_notes or notes_markdown or "").strip()
    effective_defects = defects or []
    repaired_lines = [effective_notes] if effective_notes else []

    title = section.title if section else "Core Topic"

    if section and section.title and section.title not in effective_notes:
        repaired_lines.insert(0, f"## {section.title}\n")

    # If unbalanced mathematical delimiters detected, close or repair them
    if any("dollar" in d.lower() or "delimiters" in d.lower() or "unbalanced" in d.lower() for d in effective_defects):
        dollar_count = "\n".join(repaired_lines).count('$')
        if dollar_count % 2 != 0:
            repaired_lines.append("$$")

    if any("length" in d.lower() or "brief" in d.lower() or "threshold" in d.lower() for d in effective_defects):
        repaired_lines.extend([
            "",
            "### Source limitation",
            "",
            "The available source does not support a longer explanation. More source material is needed; no filler has been added."
        ])

    if any("worked example" in d.lower() or "example" in d.lower() for d in effective_defects):
        repaired_lines.extend([
            "",
            "### Example limitation",
            "",
            "No worked example could be verified from the available source, so a numerical example has not been invented."
        ])

    # If truncated, close cleanly
    if any("truncated" in d.lower() for d in effective_defects):
        if repaired_lines[-1] and repaired_lines[-1][-1] not in ('.', '!', '?'):
            repaired_lines[-1] += "."

    repaired_text = "\n".join(repaired_lines).strip()
    repaired_text = destack_vertical_text(repaired_text)
    repaired_text = normalize_academic_math_and_ocr(repaired_text)

    return repaired_text


# =============================================================================
# 4. Job Orchestration & Resumable Execution
# =============================================================================

def process_notes_generation_job(job_id: str) -> NotesGenerationJob:
    """
    Executes the generation loop section-by-section.
    Updates progress percentage and status after each section.
    Fully resumable: picks up directly from the first non-verified section.
    """
    is_digit = str(job_id).isdigit()
    job = NotesGenerationJob.objects.filter(
        Q(id=int(job_id)) if is_digit else Q(job_id=str(job_id))
    ).first()
    if not job:
        logger.error(f"NotesGenerationJob {job_id} not found.")
        return None

    if job.status in ['COMPLETED', 'CANCELLED']:
        return job

    job.status = 'GENERATING'
    job.save()

    sections = list(job.sections.order_by('order_index'))
    total = len(sections)

    if total == 0:
        job.status = 'FAILED'
        job.error_message = 'No syllabus sections planned for this job.'
        job.save()
        return job

    # Fetch document chunks into memory lookup
    doc_chunks_lookup = {
        c.id: {
            "id": c.id,
            "chunk_index": c.chunk_index,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "section": c.section,
            "text": c.text
        }
        for c in job.document.chunks.all()
    }

    for idx, sec in enumerate(sections, start=1):
        if sec.status == 'VERIFIED' and sec.generated_notes:
            continue  # Resumability: skip already verified sections

        job.current_step_label = f"Generating Section {idx} of {total}: {sec.title}"
        job.progress_percent = int(10 + (idx / total) * 70)
        job.save(update_fields=['current_step_label', 'progress_percent', 'updated_at'])

        sec.status = 'IN_PROGRESS'
        sec.save(update_fields=['status'])

        # Resolve relevant chunks for this section
        chunk_ids = sec.get_source_chunks()
        matched_chunks = [doc_chunks_lookup[cid] for cid in chunk_ids if cid in doc_chunks_lookup]
        # 1. Generate Section Notes
        notes = generate_single_section_notes(
            section=sec,
            source_chunks=matched_chunks,
            document_subject=job.document.subject,
            mode=job.mode,
            depth=job.depth,
            language=job.language,
            reference_style_profile=job.get_reference_style_profile()
        )
        sec.generated_notes = notes
        sec.status = 'VERIFICATION_REQUIRED'
        sec.save()

        # 2. Independent Verification Audit
        is_verified, v_score, v_report = verify_section_notes(notes, sec, job.depth)
        sec.verification_score = v_score
        sec.set_verification_report(v_report)

        if is_verified:
            sec.status = 'VERIFIED'
            sec.save()
        else:
            # 3. Targeted Repair Loop
            sec.status = 'NEEDS_REPAIR'
            sec.retry_count += 1
            sec.save()

            if sec.retry_count <= sec.max_retries:
                repaired = repair_section_notes(notes, sec, v_report.get("defects", []), matched_chunks, job.document.subject)
                sec.generated_notes = repaired
                is_repaired_verified, r_score, r_report = verify_section_notes(repaired, sec, job.depth)
                sec.verification_score = r_score
                sec.set_verification_report(r_report)
                sec.status = 'VERIFIED' if is_repaired_verified else 'NEEDS_REPAIR'
                sec.save()
            else:
                sec.status = 'BLOCKED'
                sec.missing_content = "; ".join(v_report.get("defects", ["Max retries exceeded"]))
                sec.save()

    # 4. Final Document Assembly
    job.status = 'VERIFYING'
    job.current_step_label = 'Assembling final comprehensive document...'
    job.progress_percent = 90
    job.save()

    assembled_md = assemble_final_document(job)
    job.final_document_markdown = assembled_md

    # Audit final coverage
    verified_count = job.sections.filter(status='VERIFIED').count()
    failed_count = job.sections.filter(status__in=['BLOCKED', 'NEEDS_REPAIR']).count()

    job.total_topics = total
    job.completed_topics = verified_count
    job.verified_topics = verified_count
    job.failed_topics = failed_count

    # Generate Word and PDF exports
    job.current_step_label = 'Generating Word (.docx) and PDF (.pdf) exports...'
    job.save()

    try:
        docx_path = export_notes_to_docx(job)
        job.docx_export_path = docx_path
    except Exception as e:
        logger.warning(f"DOCX export warning on job {job_id}: {e}")

    try:
        pdf_path = export_notes_to_pdf(job)
        job.pdf_export_path = pdf_path
    except Exception as e:
        logger.warning(f"PDF export warning on job {job_id}: {e}")

    # Keep generated notes separate from the primary summary response.
    doc = job.document
    existing_sum = doc.get_summary()
    if not isinstance(existing_sum, dict):
        existing_sum = {}
    existing_sum["chatgpt_style_explanation"] = assembled_md
    doc.set_summary(existing_sum)
    doc.save(update_fields=['summary_json', 'updated_at'])

    if failed_count > 0:
        job.status = 'COMPLETED_WITH_WARNINGS'
        job.current_step_label = (
            f"Automated structure checks passed for {verified_count}/{total} sections "
            f"({failed_count} flagged for review); factual accuracy was not independently verified."
        )
    else:
        job.status = 'COMPLETED'
        job.current_step_label = (
            f"Automated structure checks passed for all {total} syllabus sections; "
            "factual accuracy was not independently verified."
        )

    job.progress_percent = 100
    job.save()

    return job


def assemble_final_document(job: NotesGenerationJob) -> str:
    """Assembles all sections into one cohesive, single-column study document."""
    lines = []
    lines.append(f"# {job.document.title}")
    lines.append("")
    lines.append(f"**Subject:** {job.document.subject} | **Study Mode:** {job.mode.replace('_', ' ').title()} ({job.depth.title()} Depth)")
    lines.append(f"**Source Document:** {job.document.filename or job.document.title} ({job.document.page_count} pages)")
    lines.append("")
    lines.append(
        f"> **Verification scope:** {VERIFICATION_SCOPE_NOTICE}"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    for sec in job.sections.order_by('order_index'):
        status_badge = f" [{_format_section_status(sec.status)}]"
        lines.append(f"- **{sec.order_index}. {sec.title}**{status_badge}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sections in syllabus order
    for sec in job.sections.order_by('order_index'):
        content = sec.generated_notes.strip()
        if content:
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")

    # Coverage Appendix
    lines.append("## Syllabus Coverage & Quality Audit Appendix")
    lines.append("")
    lines.append(VERIFICATION_SCOPE_NOTICE)
    lines.append("")
    lines.append(f"- **Total Topics Planned:** {job.total_topics}")
    lines.append(f"- **Verified Topics:** {job.verified_topics}")
    lines.append(f"- **Flagged / Blocked Topics:** {job.failed_topics}")
    lines.append("")

    return "\n".join(lines).strip()


# =============================================================================
# 5. Word (.docx) and PDF (.pdf) Academic Export Engines
# =============================================================================

def _export_notes_to_docx_fallback(job: NotesGenerationJob, out_file: Path) -> None:
    """
    Pure Python standard-library fallback generator for valid OpenXML .docx files.
    Used when python-docx is not installed, ensuring publication-grade output without crashes.
    """
    import zipfile
    import xml.sax.saxutils as sax

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Default Extension="xml" ContentType="application/xml"/>\n'
        '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
        '</Types>'
    )

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n'
        '</Relationships>'
    )

    body_xml = []
    # Title
    t_esc = sax.escape(job.document.title or "Study Notes")
    body_xml.append(f'<w:p><w:pPr><w:jc w:val="left"/><w:spacing w:after="80"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="44"/><w:color w:val="1E293B"/></w:rPr><w:t>{t_esc}</w:t></w:r></w:p>')

    # Subtitle / Metadata
    meta_text = sax.escape(
        f"Subject: {job.document.subject}  |  Mode: {job.mode.replace('_', ' ').title()}  |  "
        f"Automated checks: {job.verified_topics}/{job.total_topics} sections passed"
    )
    body_xml.append(f'<w:p><w:pPr><w:spacing w:after="240"/></w:pPr><w:r><w:rPr><w:i/><w:sz w:val="20"/><w:color w:val="64748B"/></w:rPr><w:t>{meta_text}</w:t></w:r></w:p>')
    notice_xml = sax.escape(VERIFICATION_SCOPE_NOTICE)
    body_xml.append(
        f'<w:p><w:pPr><w:spacing w:after="240"/></w:pPr><w:r><w:t>{notice_xml}</w:t></w:r></w:p>'
    )

    # Iterate through sections
    for sec in job.sections.order_by('order_index'):
        s_title = sax.escape(f"{sec.order_index}. {sec.title}")
        body_xml.append(f'<w:p><w:pPr><w:spacing w:before="280" w:after="120"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="4F46E5"/></w:rPr><w:t>{s_title}</w:t></w:r></w:p>')

        text = sec.generated_notes or ""
        for p_str in text.split("\n\n"):
            p_strip = p_str.strip()
            if not p_strip or p_strip.startswith(f"## {sec.title}"):
                continue
            if p_strip.startswith('### '):
                sub_esc = sax.escape(p_strip.replace('### ', ''))
                body_xml.append(f'<w:p><w:pPr><w:spacing w:before="160" w:after="80"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="24"/><w:color w:val="334155"/></w:rPr><w:t>{sub_esc}</w:t></w:r></w:p>')
            else:
                p_esc = sax.escape(p_strip)
                body_xml.append(f'<w:p><w:pPr><w:spacing w:after="120"/></w:pPr><w:r><w:rPr><w:sz w:val="22"/><w:color w:val="334155"/></w:rPr><w:t>{p_esc}</w:t></w:r></w:p>')

    # Coverage Appendix
    body_xml.append('<w:p><w:pPr><w:pageBreakBefore/><w:spacing w:before="200" w:after="160"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="1E293B"/></w:rPr><w:t>Syllabus Coverage Audit</w:t></w:r></w:p>')
    for sec in job.sections.order_by('order_index'):
        audit_esc = sax.escape(
            f"[{sec.order_index}] {sec.title} ({sec.module}) - Status: {_format_section_status(sec.status)}"
        )
        body_xml.append(f'<w:p><w:pPr><w:spacing w:after="80"/></w:pPr><w:r><w:rPr><w:sz w:val="20"/><w:color w:val="475569"/></w:rPr><w:t>{audit_esc}</w:t></w:r></w:p>')

    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        '  <w:body>\n'
        + '\n'.join(body_xml) +
        '\n  </w:body>\n'
        '</w:document>'
    )

    with zipfile.ZipFile(out_file, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/document.xml', doc_xml)


def _export_notes_to_pdf_fallback(job: NotesGenerationJob, out_file: Path) -> None:
    """
    Pure Python standard-library fallback generator for valid PDF-1.4 documents.
    Used when reportlab is not installed, guaranteeing export integrity and zero crashes.
    """
    def sanitize(text: str) -> str:
        clean = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        return "".join(c if 32 <= ord(c) < 127 else ' ' for c in clean)

    lines = [
        f"STUDY NOTES: {job.document.title}",
        f"Subject: {job.document.subject}  |  Mode: {job.mode.replace('_', ' ').title()}",
        f"Automated checks: {job.verified_topics}/{job.total_topics} sections passed",
        VERIFICATION_SCOPE_NOTICE,
        "=" * 68,
        ""
    ]

    for sec in job.sections.order_by('order_index'):
        lines.append(f"SECTION {sec.order_index}: {sec.title}")
        lines.append("-" * 50)
        for p in (sec.generated_notes or "").split("\n\n"):
            p_strip = p.strip()
            if not p_strip:
                continue
            words = p_strip.split()
            cur = ""
            for w in words:
                if len(cur) + len(w) + 1 > 72:
                    lines.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            if cur:
                lines.append(cur)
            lines.append("")

    lines.append("=" * 68)
    lines.append("SYLLABUS COVERAGE AUDIT")
    for sec in job.sections.order_by('order_index'):
        lines.append(
            f"  * #{sec.order_index} {sec.title} ({sec.module}): {_format_section_status(sec.status)}"
        )

    content_stream = "BT /F1 10 Tf 50 740 Td 14 TL\n"
    for line in lines[:200]:
        clean = sanitize(line)
        content_stream += f"({clean}) '\n"
    content_stream += "ET"

    stream_bytes = content_stream.encode('latin1', errors='replace')
    stream_len = len(stream_bytes)

    pdf_parts = [b"%PDF-1.4\n"]
    offsets = []

    offsets.append(sum(len(p) for p in pdf_parts))
    pdf_parts.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    offsets.append(sum(len(p) for p in pdf_parts))
    pdf_parts.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

    offsets.append(sum(len(p) for p in pdf_parts))
    pdf_parts.append(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n")

    offsets.append(sum(len(p) for p in pdf_parts))
    pdf_parts.append(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    offsets.append(sum(len(p) for p in pdf_parts))
    pdf_parts.append(f"5 0 obj\n<< /Length {stream_len} >>\nstream\n".encode('ascii') + stream_bytes + b"\nendstream\nendobj\n")

    xref_offset = sum(len(p) for p in pdf_parts)
    pdf_parts.append(b"xref\n0 6\n0000000000 65535 f \n")
    for off in offsets:
        pdf_parts.append(f"{off:010d} 00000 n \n".encode('ascii'))

    pdf_parts.append(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('ascii'))

    with open(out_file, 'wb') as f:
        for part in pdf_parts:
            f.write(part)


def _build_job_markdown(job: NotesGenerationJob) -> str:
    lines = [
        f"# {job.document.title}",
        f"*{job.document.subject} — Mode: {job.mode.replace('_', ' ').title()}*",
        "",
        VERIFICATION_SCOPE_NOTICE,
        ""
    ]
    for sec in job.sections.order_by('order_index'):
        lines.append(f"## {sec.order_index + 1}. {sec.title}")
        lines.append("")
        notes = (sec.generated_notes or "").strip()
        if notes.startswith(f"## {sec.title}") or notes.startswith(f"# {sec.title}"):
            notes = re.sub(r'^#+\s+[^\n]+\n*', '', notes)
        if notes:
            lines.append(notes)
            lines.append("")

    lines.append("## Syllabus Coverage Audit")
    lines.append("")
    lines.append("| # | Topic | Module | Status |")
    lines.append("|---|-------|--------|--------|")
    for sec in job.sections.order_by('order_index'):
        lines.append(f"| {sec.order_index + 1} | {sec.title} | {sec.module} | {sec.status} |")

    full_md = "\n".join(lines)
    try:
        raw_source_chunks = list(job.document.chunks.order_by('chunk_index')) if job.document.chunks.exists() else [job.document.raw_text or ""]
        repair_res = SelfRepairEngine.execute_self_repair_pipeline(
            raw_source_or_chunks=raw_source_chunks,
            generated_markdown=full_md,
            document_title=job.document.title,
            subject=job.document.subject,
            doc_id=job.document.id
        )
        return repair_res.get("repaired_markdown") or full_md
    except Exception as exc:
        logger.warning(f"Phase 8 Self-Repair pipeline fallback for job {job.job_id}: {exc}")
        return full_md


def export_notes_to_docx(job: NotesGenerationJob) -> str:
    """
    Generates a publication-grade Word document (.docx) from verified notes.
    Conforms to Phase 6 central typography, table styling, and A4 margins.
    Automatically uses pure Python OpenXML fallback if python-docx is unavailable.
    """
    export_dir = Path(settings.MEDIA_ROOT) / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)
    out_file = export_dir / f"StudyAI_Notes_{job.job_id}.docx"

    try:
        md_text = _build_job_markdown(job)
        return export_markdown_to_docx(
            title=job.document.title,
            markdown_text=md_text,
            subject=job.document.subject,
            doc_id=f"job_{job.job_id}",
            target_path=str(out_file)
        )
    except (ImportError, Exception) as exc:
        logger.info(f"Using standard docx generator fallback for job {job.job_id}: {exc}")
        _export_notes_to_docx_fallback(job, out_file)
        return str(out_file.resolve())


def export_notes_to_pdf(job: NotesGenerationJob) -> str:
    """
    Generates a publication-grade PDF from verified notes using ReportLab.
    Conforms to Phase 6 central typography, two-pass NumberedCanvas, and A4 margins.
    Automatically uses pure Python PDF generator fallback if reportlab is unavailable.
    """
    export_dir = Path(settings.MEDIA_ROOT) / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)
    out_file = export_dir / f"StudyAI_Notes_{job.job_id}.pdf"

    try:
        md_text = _build_job_markdown(job)
        return export_markdown_to_pdf(
            title=job.document.title,
            markdown_text=md_text,
            subject=job.document.subject,
            doc_id=f"job_{job.job_id}",
            target_path=str(out_file)
        )
    except (ImportError, Exception) as exc:
        logger.info(f"Using standard PDF generator fallback for job {job.job_id}: {exc}")
        _export_notes_to_pdf_fallback(job, out_file)
        return str(out_file.resolve())


def format_math_for_export(math_str: str) -> str:
    """Normalizes LaTeX equations into clean, readable academic notation for PDF and DOCX export."""
    s = (math_str or "").strip()
    s = re.sub(r'\\(?:begin|end)\{[a-zA-Z*]+\}', '', s)
    s = re.sub(r'\\(?:left|right)\b', '', s)
    s = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1) / (\2)', s)
    s = re.sub(r'\\sqrt\{([^{}]+)\}', r'√(\1)', s)
    s = re.sub(r'\\(?:times|cdot)\b', '×', s)
    s = re.sub(r'\\div\b', '÷', s)
    s = re.sub(r'\\pm\b', '±', s)
    s = re.sub(r'\\le\b', '≤', s)
    s = re.sub(r'\\ge\b', '≥', s)
    s = re.sub(r'\\ne\b', '≠', s)
    s = re.sub(r'\\approx\b', '≈', s)
    s = re.sub(r'\\infty\b', '∞', s)
    s = re.sub(r'\\sum\b', '∑', s)
    s = re.sub(r'\\prod\b', '∏', s)
    s = re.sub(r'\\int\b', '∫', s)
    s = re.sub(r'\\alpha\b', 'α', s)
    s = re.sub(r'\\beta\b', 'β', s)
    s = re.sub(r'\\gamma\b', 'γ', s)
    s = re.sub(r'\\delta\b', 'δ', s)
    s = re.sub(r'\\theta\b', 'θ', s)
    s = re.sub(r'\\lambda\b', 'λ', s)
    s = re.sub(r'\\pi\b', 'π', s)
    s = re.sub(r'\\sigma\b', 'σ', s)
    s = re.sub(r'\\mu\b', 'μ', s)
    s = re.sub(r'\\epsilon\b', 'ε', s)
    s = s.replace('&=', ' = ').replace('&', '  ')
    s = s.replace(r'\\', '\n')
    return s.strip()


def _add_formatted_runs_to_paragraph(p, text: str):
    """Parses bold, italic, and inline math runs into Word docx runs with mathematical formatting."""
    import re
    pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*|\$[^$\n]+\$|\\\([^\)]+\\\))'
    parts = re.split(pattern, text)
    for part in parts:
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            run = p.add_run(part[2:-2])
            run.font.bold = True
        elif part.startswith('*') and part.endswith('*'):
            run = p.add_run(part[1:-1])
            run.font.italic = True
        elif (part.startswith('$') and part.endswith('$')) or (part.startswith(r'\(') and part.endswith(r'\)')):
            math_content = part[1:-1] if part.startswith('$') else part[2:-2]
            clean_math = format_math_for_export(math_content)
            run = p.add_run(clean_math)
            run.font.italic = True
        else:
            p.add_run(part)


def resolve_clean_academic_title(title: str, text: str = "", subject: str = "") -> str:
    """
    Resolves an authentic academic document title according to Phase 5 Section 2 standards:
    1. Never uses raw filenames (e.g. 'BCS501-module-1-pdf.pdf', 'notes.docx', 'textbook.txt').
    2. Strips file extensions (.pdf, .docx, .pptx, .txt).
    3. If title is a file-slug or generic label (e.g. 'BCS501-module-1-pdf', 'document_1', 'upload_file'),
       scans the first 10 lines of the source text for an authentic academic heading/subject
       (e.g. 'SOFTWARE ENGINEERING AND PROJECT MANAGEMENT (BCS501)').
    4. Cleans trailing course codes or formats cleanly in Title Case / uppercase.
    5. Falls back to clean subject if title remains purely a generic slug.
    """
    raw_title = (title or "").strip()
    clean = re.sub(r'\.(pdf|docx|pptx|txt|html|md)$', '', raw_title, flags=re.IGNORECASE).strip()
    is_slug_or_filename = (
        bool(re.search(r'[-_](?:pdf|docx|txt|doc|vtu|module|part|sem|notes|v\d+)', clean, re.IGNORECASE)) or
        clean.lower().startswith(('document_', 'upload_', 'file_', 'export_')) or
        clean.lower() in {'studyai document', 'document', 'untitled', 'notes', 'export'} or
        bool(re.match(r'^[A-Z0-9]{3,8}[-_]module[-_]?\d+', clean, re.IGNORECASE))
    )

    if (is_slug_or_filename or len(clean) < 4) and text:
        text_lines = [l.strip() for l in text[:3000].splitlines() if l.strip()]
        for l in text_lines[:8]:
            if l.startswith(('---', 'Page', '===')) or len(l) < 5:
                continue
            m_h = re.match(r'^#+\s+(.*)$', l)
            candidate = m_h.group(1).strip() if m_h else l
            if len(candidate) > 6 and not candidate.lower().startswith(('chapter', 'module', 'unit', 'part')):
                candidate_clean = re.sub(r'\s*\([A-Z0-9\-\s]{3,12}\)\s*$', '', candidate).strip()
                if len(candidate_clean) > 5 and not candidate_clean.endswith(('.', ':', ';')):
                    return candidate_clean

    if is_slug_or_filename and subject and subject.lower() not in {'general', 'general academic', 'unknown'}:
        return subject.strip()

    if clean:
        clean = re.sub(r'[-_]+', ' ', clean).strip()
        if clean.islower():
            clean = clean.title()
        return clean

    return subject.strip() if (subject and subject.lower() not in {'general', 'general academic'}) else "Academic Study Guide"


def detect_callout_type(quote_text: str) -> tuple[str, str, str, str]:
    """
    Identifies academic callout type (Definition, Example, Important, Formula, Exam Tip)
    and returns (callout_type, clean_text, border_hex, fill_hex).
    """
    clean = (quote_text or "").strip()
    clean = re.sub(r'^(?:>\s*)+', '', clean).strip()
    if re.match(r'^(?:\[!NOTE\]|\*\*Definition:?\*\*|Definition:)\s*', clean, re.IGNORECASE):
        content = re.sub(r'^(?:\[!NOTE\]|\*\*Definition:?\*\*|Definition:)\s*', '', clean, flags=re.IGNORECASE).strip()
        return ("DEFINITION", content, "#4F46E5", "#EEF2FF")
    elif re.match(r'^(?:\[!EXAMPLE\]|\*\*Example:?\*\*|Example:)\s*', clean, re.IGNORECASE):
        content = re.sub(r'^(?:\[!EXAMPLE\]|\*\*Example:?\*\*|Example:)\s*', '', clean, flags=re.IGNORECASE).strip()
        return ("EXAMPLE", content, "#64748B", "#F8FAFC")
    elif re.match(r'^(?:\[!IMPORTANT\]|\*\*Important:?\*\*|Important:|\*\*Key Takeaway:?\*\*)\s*', clean, re.IGNORECASE):
        content = re.sub(r'^(?:\[!IMPORTANT\]|\*\*Important:?\*\*|Important:|\*\*Key Takeaway:?\*\*)\s*', '', clean, flags=re.IGNORECASE).strip()
        return ("IMPORTANT", content, "#F59E0B", "#FFFBEB")
    elif re.match(r'^(?:\[!FORMULA\]|\*\*Formula:?\*\*|Formula:)\s*', clean, re.IGNORECASE):
        content = re.sub(r'^(?:\[!FORMULA\]|\*\*Formula:?\*\*|Formula:)\s*', '', clean, flags=re.IGNORECASE).strip()
        return ("FORMULA", content, "#7C3AED", "#FAF5FF")
    elif re.match(r'^(?:\[!TIP\]|\*\*Exam Tip:?\*\*|Exam Tip:|\*\*Tip:?\*\*)\s*', clean, re.IGNORECASE):
        content = re.sub(r'^(?:\[!TIP\]|\*\*Exam Tip:?\*\*|Exam Tip:|\*\*Tip:?\*\*)\s*', '', clean, flags=re.IGNORECASE).strip()
        return ("EXAM_TIP", content, "#10B981", "#F0FDF4")
    else:
        return ("NOTE", clean, "#6366F1", "#EEF2FF")


def export_markdown_to_docx(
    title: str,
    markdown_text: str,
    subject: str = "General",
    doc_id: Any = "export",
    target_path: Optional[str] = None
) -> str:
    """
    Exports a structured Markdown explanation directly to a professional academic DOCX file.
    Follows Phase 5 and Phase 6 professional typography & document alignment:
    - Consistent A4 page layout with 1-inch margins
    - Never uses raw filename as document title (resolves genuine academic subject title)
    - Strict heading hierarchy with keep_with_next = True (zero orphaned headings)
    - Major chapters begin on a fresh page (page_break_before)
    - Document-wide typography: Arial font family, calibrated pt sizes, 1.2 line spacing
    - Hanging indentations on numbered and bullet lists
    - Styled tables with navy header (#1e293b), cantSplit row protection, tblHeader repeat
    - Semantic academic callout boxes (Definition, Example, Important, Formula, Exam Tip)
    - Formatted standalone and inline math formulas
    - Clean running header and footer with StudyAI academic branding
    """
    import time
    export_dir = Path(settings.MEDIA_ROOT) / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)
    if target_path:
        out_file = Path(target_path)
    else:
        clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(doc_id))
        out_file = export_dir / f"StudyAI_Document_{clean_id}_{int(time.time())}.docx"

    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import parse_xml, OxmlElement
    from docx.oxml.ns import nsdecls, qn

    doc = docx.Document()
    academic_title = resolve_clean_academic_title(title, markdown_text, subject)

    # 1. Page Margins & Dimensions (A4: 8.27 x 11.69 inches, 1.0 inch all around)
    for s in doc.sections:
        s.page_width = Inches(8.27)
        s.page_height = Inches(11.69)
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)
        
        # Header (Document title & subject, right-aligned)
        hdr = s.header
        hdr_p = hdr.paragraphs[0]
        hdr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hdr_run = hdr_p.add_run(f"{academic_title[:45]}  |  {subject[:30]}  |  StudyAI")
        hdr_run.font.name = 'Arial'
        hdr_run.font.size = Pt(8.5)
        hdr_run.font.color.rgb = RGBColor(148, 163, 184)
        
        # Footer (StudyAI Branding, center-aligned)
        ftr = s.footer
        ftr_p = ftr.paragraphs[0]
        ftr_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ftr_run = ftr_p.add_run(f"StudyAI  |  {subject[:35]}  |  Masterclass Edition")
        ftr_run.font.name = 'Arial'
        ftr_run.font.size = Pt(8.5)
        ftr_run.font.color.rgb = RGBColor(148, 163, 184)

    # Set document-wide default font to Arial
    for s_name in ['Normal', 'Heading 1', 'Heading 2', 'Heading 3', 'Heading 4', 'List Bullet']:
        if s_name in doc.styles:
            doc.styles[s_name].font.name = 'Arial'

    # 2. Document Title (Prominent and Centered, 26 pt Bold)
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run(academic_title)
    title_run.font.name = 'Arial'
    title_run.font.size = Pt(26)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(15, 23, 42)
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)

    # Metadata subtitle (9.5 pt Italic, Centered)
    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = meta_p.add_run(f"Subject / Domain: {subject}   •   StudyAI Masterclass Edition")
    meta_run.font.name = 'Arial'
    meta_run.font.size = Pt(9.5)
    meta_run.font.italic = True
    meta_run.font.color.rgb = RGBColor(100, 116, 139)
    meta_p.paragraph_format.space_after = Pt(18)

    lines = (markdown_text or "").split('\n')
    i = 0
    heading_count = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Chapter / Module Heading (H1: 20 pt Bold, PageBreak before major chapters)
        if stripped.startswith('# '):
            heading_count += 1
            if heading_count > 1:
                doc.add_page_break()
            h = doc.add_heading(level=1)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.space_before = Pt(18)
            h.paragraph_format.space_after = Pt(6)
            r = h.add_run(stripped[2:])
            r.font.name = 'Arial'
            r.font.size = Pt(20)
            r.font.bold = True
            r.font.color.rgb = RGBColor(30, 41, 59)
        elif stripped.startswith('## '):
            heading_count += 1
            h = doc.add_heading(level=2)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(4)
            r = h.add_run(stripped[3:])
            r.font.name = 'Arial'
            r.font.size = Pt(16)
            r.font.bold = True
            r.font.color.rgb = RGBColor(67, 56, 202)
        elif stripped.startswith('### '):
            heading_count += 1
            h = doc.add_heading(level=3)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(3)
            r = h.add_run(stripped[4:])
            r.font.name = 'Arial'
            r.font.size = Pt(13.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(51, 65, 85)
        elif stripped.startswith('#### '):
            heading_count += 1
            h = doc.add_heading(level=4)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(2)
            r = h.add_run(stripped[5:])
            r.font.name = 'Arial'
            r.font.size = Pt(11.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(71, 85, 105)

        # Numbered list item (hanging indent)
        elif re.match(r'^\s*(\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s+', stripped):
            m_num = re.match(r'^\s*(\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s+(.*)$', stripped)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.first_line_indent = Inches(-0.15)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2
            num_run = p.add_run(f"{m_num.group(1)}. ")
            num_run.font.name = 'Arial'
            num_run.font.bold = True
            num_run.font.color.rgb = RGBColor(67, 56, 202)
            _add_formatted_runs_to_paragraph(p, m_num.group(2))

        # Bullet list item (hanging indent)
        elif stripped.startswith(('- ', '* ', '• ')):
            bullet_content = re.sub(r'^[-*•]\s+', '', stripped)
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.first_line_indent = Inches(-0.15)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2
            _add_formatted_runs_to_paragraph(p, bullet_content)

        # Blockquote / Academic Callout Box
        elif stripped.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].strip())
                i += 1
            full_quote = " ".join(re.sub(r'^>\s*', '', ql) for ql in quote_lines)
            ctype, ctext, border_hex, fill_hex = detect_callout_type(full_quote)

            callout_tbl = doc.add_table(rows=1, cols=1)
            callout_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            cell = callout_tbl.cell(0, 0)
            try:
                shd = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), fill_hex.lstrip('#')))
                cell._tc.get_or_add_tcPr().append(shd)
                bds = parse_xml(r'''<w:tcBorders {}>
                    <w:top w:val="none"/>
                    <w:left w:val="single" w:sz="24" w:space="0" w:color="{}"/>
                    <w:bottom w:val="none"/>
                    <w:right w:val="none"/>
                </w:tcBorders>'''.format(nsdecls('w'), border_hex.lstrip('#')))
                cell._tc.get_or_add_tcPr().append(bds)
            except Exception:
                pass

            cp = cell.paragraphs[0]
            cp.paragraph_format.space_before = Pt(4)
            cp.paragraph_format.space_after = Pt(4)
            cp.paragraph_format.line_spacing = 1.2

            labels = {
                "DEFINITION": "Definition: ",
                "EXAMPLE": "Example: ",
                "IMPORTANT": "Important: ",
                "FORMULA": "Formula: ",
                "EXAM_TIP": "Exam Tip: "
            }
            if ctype in labels:
                lr = cp.add_run(labels[ctype])
                lr.font.name = 'Arial'
                lr.font.bold = True
                lr.font.size = Pt(10)
                c_rgb = {
                    "DEFINITION": RGBColor(79, 70, 229),
                    "EXAMPLE": RGBColor(100, 116, 139),
                    "IMPORTANT": RGBColor(217, 119, 6),
                    "FORMULA": RGBColor(124, 58, 237),
                    "EXAM_TIP": RGBColor(16, 185, 129)
                }.get(ctype, RGBColor(79, 70, 229))
                lr.font.color.rgb = c_rgb

            _add_formatted_runs_to_paragraph(cp, ctext)
            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_before = Pt(0)
            spacer.paragraph_format.space_after = Pt(4)
            continue

        # Tables with cantSplit, tblHeader, navy header, alternating rows
        elif stripped.startswith('|') and stripped.endswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2:
                parsed_rows = []
                for tline in table_lines:
                    cells = [c.strip() for c in tline.strip('|').split('|')]
                    if not all(re.match(r'^[\-:]+$', c) for c in cells if c):
                        parsed_rows.append(cells)
                if parsed_rows:
                    num_cols = max(len(r) for r in parsed_rows)
                    tbl = doc.add_table(rows=len(parsed_rows), cols=num_cols)
                    tbl.style = 'Table Grid'
                    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                    for r_idx, row_data in enumerate(parsed_rows):
                        row = tbl.rows[r_idx]
                        try:
                            trPr = row._tr.get_or_add_trPr()
                            trPr.append(parse_xml(r'<w:cantSplit xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                            if r_idx == 0:
                                trPr.append(parse_xml(r'<w:tblHeader xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                        except Exception:
                            pass

                        for c_idx, cell_text in enumerate(row_data):
                            if c_idx < num_cols:
                                cell = tbl.cell(r_idx, c_idx)
                                cell.text = cell_text
                                cp = cell.paragraphs[0]
                                if r_idx > 0 and re.match(r'^\s*[\$€£]?\s*-?\d+(?:\.\d+)?%?\s*$', cell_text):
                                    cp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                                elif r_idx > 0 and len(cell_text.strip()) <= 4:
                                    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                else:
                                    cp.alignment = WD_ALIGN_PARAGRAPH.LEFT

                                if r_idx == 0:
                                    shading = parse_xml(r'<w:shd {} w:fill="1E293B"/>'.format(nsdecls('w')))
                                    cell._tc.get_or_add_tcPr().append(shading)
                                    for cr in cp.runs:
                                        cr.font.name = 'Arial'
                                        cr.font.bold = True
                                        cr.font.color.rgb = RGBColor(255, 255, 255)
                                        cr.font.size = Pt(9.5)
                                elif r_idx % 2 == 1:
                                    shading = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
                                    cell._tc.get_or_add_tcPr().append(shading)
                                    for cr in cp.runs:
                                        cr.font.name = 'Arial'
                                        cr.font.size = Pt(9)
                                        cr.font.color.rgb = RGBColor(51, 65, 85)
                                else:
                                    for cr in cp.runs:
                                        cr.font.name = 'Arial'
                                        cr.font.size = Pt(9)
                                        cr.font.color.rgb = RGBColor(51, 65, 85)
            continue

        # Mathematical formulas / code blocks
        elif stripped.startswith(('$$', '```', r'\[', r'\begin{')):
            block_lines = []
            if stripped.startswith('$$') and stripped.endswith('$$') and len(stripped) > 2:
                block_lines.append(stripped[2:-2].strip())
            elif stripped.startswith('$$'):
                rem = stripped[2:].rstrip('$')
                if rem:
                    block_lines.append(rem)
                i += 1
                while i < len(lines) and not lines[i].strip().endswith('$$') and lines[i].strip() != '$$':
                    block_lines.append(lines[i])
                    i += 1
                if i < len(lines) and lines[i].strip() != '$$':
                    block_lines.append(lines[i].strip().rstrip('$'))
            elif stripped.startswith(r'\[') and stripped.endswith(r'\]') and len(stripped) > 4:
                block_lines.append(stripped[2:-2].strip())
            elif stripped.startswith(r'\['):
                rem = stripped[2:].rstrip(r'\]')
                if rem:
                    block_lines.append(rem)
                i += 1
                while i < len(lines) and not lines[i].strip().endswith(r'\]') and lines[i].strip() != r'\]':
                    block_lines.append(lines[i])
                    i += 1
                if i < len(lines) and lines[i].strip() != r'\]':
                    block_lines.append(lines[i].strip().rstrip(r'\]'))
            elif stripped.startswith(r'\begin{'):
                m_env = re.match(r'\\begin\{([a-zA-Z*]+)\}', stripped)
                env_name = m_env.group(1) if m_env else 'aligned'
                end_tag = f"\\end{{{env_name}}}"
                block_lines.append(stripped)
                i += 1
                while i < len(lines) and end_tag not in lines[i]:
                    block_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    block_lines.append(lines[i])
            elif stripped.startswith('```') and stripped.endswith('```') and len(stripped) > 3:
                block_lines.append(stripped.strip('`').strip())
            else:
                rem = stripped.lstrip('`')
                if rem:
                    block_lines.append(rem)
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    block_lines.append(lines[i])
                    i += 1

            raw_code = '\n'.join(block_lines).strip()
            if raw_code:
                code_text = format_math_for_export(raw_code)
                callout_tbl = doc.add_table(rows=1, cols=1)
                callout_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = callout_tbl.cell(0, 0)
                try:
                    shading = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
                    cell._tc.get_or_add_tcPr().append(shading)
                except Exception:
                    pass
                cp = cell.paragraphs[0]
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cp.paragraph_format.space_before = Pt(4)
                cp.paragraph_format.space_after = Pt(4)
                r = cp.add_run(code_text)
                r.font.name = 'Courier New'
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(30, 41, 59)
                spacer = doc.add_paragraph()
                spacer.paragraph_format.space_before = Pt(0)
                spacer.paragraph_format.space_after = Pt(4)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.2
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.first_line_indent = Inches(0)
            _add_formatted_runs_to_paragraph(p, stripped)

        i += 1

    doc.save(str(out_file))
    return str(out_file)


class _NumberedCanvas:
    """Factory creating ReportLab canvas with two-pass page numbering and textbook headers."""
    pass


def _create_numbered_canvas(doc_title: str, subject_domain: str):
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors

    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_decorations(num_pages)
                super().showPage()
            super().save()

        def draw_page_decorations(self, total_pages):
            self.saveState()
            self.setFont("Helvetica", 8.5)
            self.setFillColor(colors.HexColor('#64748b'))

            clean_title = resolve_clean_academic_title(doc_title, subject=subject_domain)[:45]
            clean_subj = (subject_domain or "Syllabus")[:30]

            # Running header on page 2 and onwards (A4 height 841.89 pt, width 595.28 pt)
            if self._pageNumber > 1:
                self.drawString(54, 808, f"{clean_title}  |  {clean_subj}  |  StudyAI")
                self.setStrokeColor(colors.HexColor('#e2e8f0'))
                self.setLineWidth(0.5)
                self.line(54, 800, 541, 800)

            # Running footer on all pages (left: branding, right: page number)
            self.drawString(54, 28, f"StudyAI  |  {clean_subj}  |  Masterclass Edition")
            page_text = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(541, 28, page_text)
            self.setStrokeColor(colors.HexColor('#e2e8f0'))
            self.setLineWidth(0.5)
            self.line(54, 38, 541, 38)

            self.restoreState()

    return NumberedCanvas


def export_markdown_to_pdf(
    title: str,
    markdown_text: str,
    subject: str = "General",
    doc_id: Any = "export",
    target_path: Optional[str] = None
) -> str:
    """
    Exports a structured Markdown explanation directly to a professional academic PDF file.
    Follows Phase 5 and Phase 6 professional typography & document alignment:
    - Consistent A4 page layout with balanced 54pt margins
    - Never uses raw filename as document title (resolves genuine academic subject title)
    - Strict heading hierarchy with keepWithNext = True (zero orphaned headings)
    - Major chapters begin on a fresh page (PageBreak)
    - Calibrated typography: Arial / Helvetica font family with calibrated pt sizes and 1.2 line spacing
    - Hanging indentations on numbered and bullet lists
    - Styled tables with navy header (#1e293b), repeatRows = 1 for multipage continuity, alternating rows
    - Semantic academic callout boxes (Definition, Example, Important, Formula, Exam Tip)
    - Centered mathematical derivations and clean inline math formatting
    - Two-pass NumberedCanvas with textbook running headers and footers
    """
    import os
    import time
    export_dir = Path(settings.MEDIA_ROOT) / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)
    if target_path:
        out_file = Path(target_path)
    else:
        clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(doc_id))
        out_file = export_dir / f"StudyAI_Document_{clean_id}_{int(time.time())}.pdf"

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable, Table, TableStyle, Preformatted, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Register Arial TTF if available on system
    has_arial = False
    if os.path.exists('C:/Windows/Fonts/arial.ttf'):
        try:
            pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Italic', 'C:/Windows/Fonts/ariali.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-BoldItalic', 'C:/Windows/Fonts/arialbi.ttf'))
            has_arial = True
        except Exception:
            has_arial = False

    font_family = 'Arial' if has_arial else 'Helvetica'
    bold_font = 'Arial-Bold' if has_arial else 'Helvetica-Bold'
    italic_font = 'Arial-Italic' if has_arial else 'Helvetica-Oblique'

    academic_title = resolve_clean_academic_title(title, markdown_text, subject)

    # Printable width: A4 width (595.28 pt) - 2 * 54 = 487.28 pt
    printable_width = 487.0

    pdf = SimpleDocTemplate(
        str(out_file),
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'MDTitle', parent=styles['Heading1'],
        fontName=bold_font, fontSize=26, leading=30,
        textColor=colors.HexColor('#0f172a'), alignment=TA_CENTER,
        spaceAfter=6, keepWithNext=True
    )
    meta_style = ParagraphStyle(
        'MDMeta', parent=styles['Normal'],
        fontName=italic_font, fontSize=9.5, leading=13,
        textColor=colors.HexColor('#64748b'), alignment=TA_CENTER,
        spaceAfter=16, keepWithNext=True
    )
    h1_style = ParagraphStyle(
        'MDH1', parent=styles['Heading2'],
        fontName=bold_font, fontSize=20, leading=24,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=18, spaceAfter=6, keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'MDH2', parent=styles['Heading3'],
        fontName=bold_font, fontSize=16, leading=20,
        textColor=colors.HexColor('#4338ca'),
        spaceBefore=14, spaceAfter=4, keepWithNext=True
    )
    h3_style = ParagraphStyle(
        'MDH3', parent=styles['Heading4'],
        fontName=bold_font, fontSize=13.5, leading=17,
        textColor=colors.HexColor('#334155'),
        spaceBefore=10, spaceAfter=3, keepWithNext=True
    )
    h4_style = ParagraphStyle(
        'MDH4', parent=styles['Heading4'],
        fontName=bold_font, fontSize=11.5, leading=15,
        textColor=colors.HexColor('#475569'),
        spaceBefore=8, spaceAfter=2, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'MDBody', parent=styles['Normal'],
        fontName=font_family, fontSize=10.5, leading=14,
        textColor=colors.HexColor('#334155'), spaceBefore=0, spaceAfter=6, alignment=TA_LEFT
    )
    bullet_style = ParagraphStyle(
        'MDBullet', parent=body_style,
        leftIndent=20, firstLineIndent=-12, spaceAfter=3
    )
    formula_style = ParagraphStyle(
        'MDFormula', parent=body_style,
        fontName='Courier', fontSize=9.5, leading=13,
        textColor=colors.HexColor('#0f172a'), alignment=TA_CENTER,
        backColor=colors.HexColor('#f8fafc'),
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=0.5, borderPadding=6, spaceAfter=6
    )

    story = [
        Paragraph(academic_title, title_style),
        Paragraph(f"Subject / Domain: {subject}   •   StudyAI Masterclass Edition", meta_style),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=14)
    ]

    lines = (markdown_text or "").split('\n')
    i = 0
    heading_count = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        clean_text = stripped.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        clean_text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', clean_text)
        clean_text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', clean_text)

        # Chapter / Module Heading (H1: 20 pt Bold, PageBreak before major chapters)
        if stripped.startswith('# '):
            heading_count += 1
            if heading_count > 1:
                story.append(PageBreak())
            story.append(Paragraph(clean_text[2:], h1_style))
        elif stripped.startswith('## '):
            heading_count += 1
            story.append(Paragraph(clean_text[3:], h2_style))
        elif stripped.startswith('### '):
            heading_count += 1
            story.append(Paragraph(clean_text[4:], h3_style))
        elif stripped.startswith('#### '):
            heading_count += 1
            story.append(Paragraph(clean_text[5:], h4_style))

        # Numbered list items (hanging indent)
        elif re.match(r'^\s*(\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s+', stripped):
            m_num = re.match(r'^\s*(\d+|[a-zA-Z]|[ivxlcdm]+)[\.\)]\s+(.*)$', clean_text)
            story.append(Paragraph(f"<b>{m_num.group(1)}.</b> {m_num.group(2)}", bullet_style))

        # Bullet list items (hanging indent)
        elif stripped.startswith(('- ', '* ', '• ')):
            bullet_clean = re.sub(r'^[-*•]\s+', '', clean_text)
            story.append(Paragraph(f"&bull; {bullet_clean}", bullet_style))

        # Blockquote / Academic Callout Box (Definition, Example, Important, Formula, Exam Tip)
        elif stripped.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].strip())
                i += 1
            full_quote = " ".join(re.sub(r'^>\s*', '', ql) for ql in quote_lines)
            ctype, ctext, border_hex, fill_hex = detect_callout_type(full_quote)

            labels = {
                "DEFINITION": "Definition: ",
                "EXAMPLE": "Example: ",
                "IMPORTANT": "Important: ",
                "FORMULA": "Formula: ",
                "EXAM_TIP": "Exam Tip: "
            }
            lbl = f"<b>{labels.get(ctype, '')}</b>" if ctype in labels else ""
            callout_clean = ctext.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            callout_clean = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', callout_clean)
            callout_clean = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', callout_clean)

            callout_p_style = ParagraphStyle(
                'MDCalloutInner', parent=body_style,
                fontSize=10, leading=13.5, textColor=colors.HexColor('#1e293b'), spaceAfter=0
            )
            cp = Paragraph(f"{lbl}{callout_clean}", callout_p_style)
            callout_tbl = Table([[cp]], colWidths=[printable_width])
            callout_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(fill_hex)),
                ('LINEBEFORE', (0, 0), (0, -1), 3.0, colors.HexColor(border_hex)),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(callout_tbl)
            continue

        # Tables (Formatted with TableStyle, alternating rows, cantSplit, repeatRows=1)
        elif stripped.startswith('|') and stripped.endswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2:
                parsed_rows = []
                for tline in table_lines:
                    cells = [c.strip() for c in tline.strip('|').split('|')]
                    if not all(re.match(r'^[\-:]+$', c) for c in cells if c):
                        parsed_rows.append(cells)
                if parsed_rows:
                    num_cols = max(len(r) for r in parsed_rows)
                    formatted_table_data = []
                    for r_idx, row in enumerate(parsed_rows):
                        row_cells = []
                        for c_idx in range(num_cols):
                            cell_val = row[c_idx] if c_idx < len(row) else ""
                            cell_clean = cell_val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            cell_clean = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', cell_clean)
                            if r_idx == 0:
                                row_cells.append(Paragraph(
                                    f"<b>{cell_clean}</b>",
                                    ParagraphStyle('TH', parent=body_style, textColor=colors.white, fontName=bold_font, fontSize=9, leading=11)
                                ))
                            else:
                                td_align = TA_RIGHT if re.match(r'^\s*[\$€£]?\s*-?\d+(?:\.\d+)?%?\s*$', cell_val) else (TA_CENTER if len(cell_val.strip()) <= 4 else TA_LEFT)
                                row_cells.append(Paragraph(
                                    cell_clean,
                                    ParagraphStyle('TD', parent=body_style, fontSize=8.5, leading=11, alignment=td_align)
                                ))
                        formatted_table_data.append(row_cells)

                    col_widths = PrecisionLayoutEngine.calculate_table_column_widths(parsed_rows, printable_width)
                    rep_table = Table(formatted_table_data, colWidths=col_widths, repeatRows=1)
                    rep_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
                    ]))
                    story.append(rep_table)
            continue

        # Mathematical formulas / code blocks
        elif stripped.startswith(('$$', '```', r'\[', r'\begin{')):
            block_lines = []
            if stripped.startswith('$$') and stripped.endswith('$$') and len(stripped) > 2:
                block_lines.append(stripped[2:-2].strip())
            elif stripped.startswith('$$'):
                rem = stripped[2:].rstrip('$')
                if rem:
                    block_lines.append(rem)
                i += 1
                while i < len(lines) and not lines[i].strip().endswith('$$') and lines[i].strip() != '$$':
                    block_lines.append(lines[i])
                    i += 1
                if i < len(lines) and lines[i].strip() != '$$':
                    block_lines.append(lines[i].strip().rstrip('$'))
            elif stripped.startswith(r'\[') and stripped.endswith(r'\]') and len(stripped) > 4:
                block_lines.append(stripped[2:-2].strip())
            elif stripped.startswith(r'\['):
                rem = stripped[2:].rstrip(r'\]')
                if rem:
                    block_lines.append(rem)
                i += 1
                while i < len(lines) and not lines[i].strip().endswith(r'\]') and lines[i].strip() != r'\]':
                    block_lines.append(lines[i])
                    i += 1
                if i < len(lines) and lines[i].strip() != r'\]':
                    block_lines.append(lines[i].strip().rstrip(r'\]'))
            elif stripped.startswith(r'\begin{'):
                m_env = re.match(r'\\begin\{([a-zA-Z*]+)\}', stripped)
                env_name = m_env.group(1) if m_env else 'aligned'
                end_tag = f"\\end{{{env_name}}}"
                block_lines.append(stripped)
                i += 1
                while i < len(lines) and end_tag not in lines[i]:
                    block_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    block_lines.append(lines[i])
            elif stripped.startswith('```') and stripped.endswith('```') and len(stripped) > 3:
                block_lines.append(stripped.strip('`').strip())
            else:
                rem = stripped.lstrip('`')
                if rem:
                    block_lines.append(rem)
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    block_lines.append(lines[i])
                    i += 1

            raw_code = '\n'.join(block_lines).strip()
            if raw_code:
                code_text = format_math_for_export(raw_code)
                story.append(Preformatted(code_text, formula_style))
        else:
            inline_math_clean = re.sub(
                r'\$([^$\n]+)\$|\\\(([^\)]+)\\\)',
                lambda m: f"<i>{format_math_for_export(m.group(1) or m.group(2))}</i>",
                clean_text
            )
            story.append(Paragraph(inline_math_clean, body_style))

        i += 1

    canvas_class = _create_numbered_canvas(academic_title, subject)
    pdf.build(story, canvasmaker=canvas_class)

    # Phase 5: Automated Visual Quality Audit on the generated PDF
    try:
        from .visual_audit_service import DocumentVisualQualityAuditor
        DocumentVisualQualityAuditor.audit_pdf_document(str(out_file), academic_title)
    except Exception as audit_err:
        logger.warning(f"Visual quality audit warning on exported PDF: {audit_err}")

    return str(out_file)
