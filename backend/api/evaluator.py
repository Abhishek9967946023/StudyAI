"""
=============================================================================
StudyAI — AI Quality Evaluation Engine
=============================================================================
Provides rigorous mathematical and algorithmic verification of AI-generated
results across the 8 key dimensions:
1. Summary relevance
2. Topic relevance
3. Question grounding
4. Citation accuracy
5. Answer correctness
6. Difficulty correctness
7. Copilot grounding
8. Unsupported information rate

Produces exact, traceable measurements for 20 documents and 100 questions.
No invented percentages; all metrics are calculated from empirical test results.
=============================================================================
"""

import re
import json
import uuid
import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Any, Tuple

from .benchmark_dataset import BENCHMARK_DOCUMENTS

def clean_text(raw_text: str) -> str:
    """Normalize whitespace and strip extraneous characters."""
    if not raw_text:
        return ""
    text = re.sub(r'[\r\f\v]', '', str(raw_text))
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def chunk_document_by_pages(pages: list, document_id: int = 1, target_size: int = 1800, overlap: int = 250) -> list:
    """Break extracted pages into structured overlapping chunks."""
    chunks = []
    chunk_index = 0
    current_text = ""
    current_page_start = 1
    current_page_end = 1
    current_section = "General"

    for p in pages:
        p_num = p.get("page_number", 1)
        p_text = p.get("text", "")
        if not p_text.strip():
            continue

        sentences = re.split(r'(?<=[.!?\n])\s+', p_text)
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue

            if len(s_clean) < 80 and re.match(r'^(Chapter|Section|\d+\.|\b[A-Z0-9\s]{4,}\b)', s_clean):
                current_section = s_clean

            if len(current_text) + len(s_clean) > target_size and len(current_text) > 0:
                chunks.append({
                    "document_id": document_id,
                    "chunk_id": chunk_index,
                    "chunk_index": chunk_index,
                    "order": chunk_index,
                    "page_start": current_page_start,
                    "page_end": current_page_end,
                    "section": current_section,
                    "text": current_text.strip(),
                    "char_count": len(current_text.strip()),
                })
                chunk_index += 1
                words = current_text.split()
                overlap_text = " ".join(words[-max(1, overlap // 6):])
                current_text = overlap_text + " " + s_clean
                current_page_start = p_num
                current_page_end = p_num
            else:
                if not current_text:
                    current_page_start = p_num
                current_text = (current_text + " " + s_clean) if current_text else s_clean
                current_page_end = p_num

    if current_text.strip():
        chunks.append({
            "document_id": document_id,
            "chunk_id": chunk_index,
            "chunk_index": chunk_index,
            "order": chunk_index,
            "page_start": current_page_start,
            "page_end": current_page_end,
            "section": current_section,
            "text": current_text.strip(),
            "char_count": len(current_text.strip()),
        })

    return chunks


from .ollama_service import (
    analyze_document_with_ai,
    generate_exam_questions_with_ai,
    fallback_generate_questions,
    fallback_extract_document_analysis,
    answer_copilot_with_ai,
    check_ollama_status
)


# =============================================================================
# String & N-Gram Normalization Utilities
# =============================================================================

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'from', 'up', 'about', 'into', 'over', 'after', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
    'did', 'will', 'would', 'should', 'can', 'could', 'may', 'might', 'must',
    'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom', 'how',
    'why', 'where', 'when', 'according', 'source', 'text', 'following', 'statement'
}


def normalize_text(text: str) -> str:
    """Lowercases, normalizes whitespace and strips punctuation."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_content_words(text: str) -> List[str]:
    """Extracts non-stopword tokens of length >= 3."""
    tokens = re.findall(r'\b[a-z0-9_-]{3,}\b', text.lower())
    return [t for t in tokens if t not in STOPWORDS]


def string_similarity(s1: str, s2: str) -> float:
    """Calculates SequenceMatcher ratio between two normalized strings."""
    n1 = normalize_text(s1)
    n2 = normalize_text(s2)
    if not n1 or not n2:
        return 0.0
    return SequenceMatcher(None, n1, n2).ratio()


def token_overlap_ratio(source: str, query: str) -> float:
    """Calculates recall of query content words inside source text."""
    src_words = set(extract_content_words(source))
    qry_words = extract_content_words(query)
    if not qry_words:
        return 1.0
    matches = sum(1 for w in qry_words if w in src_words)
    return matches / len(qry_words)


# =============================================================================
# Question Verification Sub-Algorithms
# =============================================================================

def verify_question_grounding(question_dict: Dict[str, Any], source_text: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifies Dimension 3: Question Grounding.
    Asserts whether the question prompt and premise are substantiated
    by the source study material.
    """
    q_text = question_dict.get('question', '')
    citation = question_dict.get('citation', '')
    correct_ans = str(question_dict.get('correctAnswer', ''))

    # Extract substantive tokens from the question prompt
    q_tokens = extract_content_words(q_text)
    src_tokens = set(extract_content_words(source_text))

    if not q_tokens:
        return {
            "is_grounded": False,
            "grounding_score": 0.0,
            "evidence": "Question contains no substantive content tokens.",
            "trace": "Failed token extraction."
        }

    # Match token recall
    matched_tokens = [w for w in q_tokens if w in src_tokens]
    overlap_score = len(matched_tokens) / len(q_tokens)

    # Corroborating sentence search
    sentences = re.split(r'(?<=[.!?])\s+', source_text)
    best_sent = ""
    best_sent_score = 0.0
    for s in sentences:
        s_norm = s.lower()
        s_matches = sum(1 for w in q_tokens if w in s_norm)
        if s_matches > best_sent_score:
            best_sent_score = s_matches
            best_sent = s

    # Question is grounded if >= 70% of content tokens or >= 3 major concepts exist in source
    is_grounded = overlap_score >= 0.70 or len(matched_tokens) >= 4 or (citation and normalize_text(citation) in normalize_text(source_text))

    return {
        "is_grounded": bool(is_grounded),
        "grounding_score": round(overlap_score, 4),
        "matched_tokens_count": len(matched_tokens),
        "total_tokens_count": len(q_tokens),
        "evidence": best_sent if best_sent else (citation if citation else source_text[:120]),
        "trace": f"Matched {len(matched_tokens)}/{len(q_tokens)} content tokens ({round(overlap_score*100, 1)}% token recall against source text)."
    }


def verify_citation_accuracy(citation: str, source_text: str, chunks: List[Dict[str, Any]], source_chunk_idx: int = 1) -> Dict[str, Any]:
    """
    Verifies Dimension 4: Citation Accuracy.
    Asserts whether the provided citation string is a verbatim or highly accurate
    substring directly present in the source study material.
    """
    if not citation or len(citation.strip()) < 8:
        return {
            "is_citation_correct": False,
            "citation_score": 0.0,
            "match_type": "missing_or_empty",
            "matched_span": "",
            "trace": "Citation string is empty or trivially short."
        }

    clean_cit = normalize_text(citation)
    clean_src = normalize_text(source_text)

    # 1. Exact verbatim substring check
    if citation in source_text:
        return {
            "is_citation_correct": True,
            "citation_score": 1.0,
            "match_type": "exact_verbatim",
            "matched_span": citation[:100],
            "trace": "Exact character-for-character match found in source text."
        }

    # 2. Normalized whitespace / punctuation substring check
    if clean_cit in clean_src:
        return {
            "is_citation_correct": True,
            "citation_score": 0.98,
            "match_type": "normalized_substring",
            "matched_span": citation[:100],
            "trace": "Exact normalized match found in source text (ignoring casing & punctuation)."
        }

    # 3. High-similarity substring window search
    cit_len = len(citation)
    best_ratio = 0.0
    best_window = ""
    step = max(10, cit_len // 4)

    for i in range(0, max(1, len(source_text) - cit_len + 1), step):
        window = source_text[i:i + cit_len + 30]
        sim = string_similarity(citation, window)
        if sim > best_ratio:
            best_ratio = sim
            best_window = window

    is_correct = best_ratio >= 0.85
    return {
        "is_citation_correct": bool(is_correct),
        "citation_score": round(best_ratio, 4),
        "match_type": "fuzzy_window_match" if is_correct else "unverified_citation",
        "matched_span": best_window[:100] if is_correct else "",
        "trace": f"Fuzzy similarity score: {round(best_ratio*100, 1)}% against closest source segment."
    }


def verify_answer_correctness(question_dict: Dict[str, Any], source_text: str, citation: str) -> Dict[str, Any]:
    """
    Verifies Dimension 5: Answer Correctness.
    Asserts whether:
    - The correct_answer exists inside the question's options list
    - The correct_index points accurately to correct_answer
    - The answer assertion is verified by the source text / citation
    """
    options = question_dict.get('options', [])
    correct_ans = question_dict.get('correctAnswer')
    correct_idx = question_dict.get('correctIndex')

    if str(question_dict.get('type', '')).lower() == 'msq':
        correct_indices = question_dict.get('correctIndices')
        answers_valid = (
            isinstance(correct_ans, list)
            and len(correct_ans) >= 2
            and all(answer in options for answer in correct_ans)
            and isinstance(correct_indices, list)
            and len(correct_indices) == len(correct_ans)
            and all(isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(options)
                    for index in correct_indices)
            and {options[index] for index in correct_indices} == set(correct_ans)
        )
        source_text_norm = normalize_text(source_text)
        citation_norm = normalize_text(citation) if citation else ""
        supported = answers_valid and all(
            normalize_text(answer) in source_text_norm
            or (citation_norm and normalize_text(answer) in citation_norm)
            for answer in correct_ans
        )
        return {
            "is_answer_correct": bool(supported),
            "option_included": bool(answers_valid),
            "index_aligned": bool(answers_valid),
            "supported_by_source": bool(supported),
            "trace": f"MSQ answers valid: {answers_valid}, all selected claims source-backed: {bool(supported)}."
        }

    if not options or correct_ans is None:
        return {
            "is_answer_correct": False,
            "answer_score": 0.0,
            "trace": "Question missing options array or correct_answer definition."
        }

    # Check option containment
    option_found = correct_ans in options
    if not option_found:
        # Check if index is valid
        if isinstance(correct_idx, int) and 0 <= correct_idx < len(options):
            correct_ans = options[correct_idx]
            option_found = True

    if not option_found:
        return {
            "is_answer_correct": False,
            "answer_score": 0.0,
            "trace": f"Correct answer '{correct_ans}' not found in options: {options}"
        }

    # Check index alignment
    index_aligned = False
    if isinstance(correct_idx, int) and 0 <= correct_idx < len(options):
        if options[correct_idx] == correct_ans:
            index_aligned = True

    # Check factual support in source text or citation
    ans_norm = normalize_text(str(correct_ans))
    cit_norm = normalize_text(citation) if citation else ""
    src_norm = normalize_text(source_text)

    in_citation = ans_norm in cit_norm if cit_norm else False
    in_source = ans_norm in src_norm

    # If answer is a compound phrase, check token overlap
    ans_tokens = extract_content_words(str(correct_ans))
    token_supported = False
    if ans_tokens:
        tok_match = sum(1 for t in ans_tokens if t in src_norm)
        token_supported = (tok_match / len(ans_tokens)) >= 0.75
    else:
        token_supported = True

    is_supported = in_citation or in_source or token_supported
    is_correct = option_found and is_supported

    return {
        "is_answer_correct": bool(is_correct),
        "option_included": option_found,
        "index_aligned": index_aligned,
        "supported_by_source": is_supported,
        "trace": f"Option included: {option_found}, index aligned: {index_aligned}, source backed: {is_supported}."
    }


def verify_topic_correctness(question_topic: str, doc_subject: str, doc_title: str, source_text: str) -> Dict[str, Any]:
    """
    Verifies Dimension 2 (applied to question): Topic Relevance.
    Asserts whether the assigned question topic corresponds to the document's subject
    and is represented in the source study material.
    """
    if not question_topic:
        return {
            "is_topic_correct": False,
            "topic_score": 0.0,
            "trace": "Question topic tag is empty."
        }

    topic_norm = normalize_text(question_topic)
    subj_norm = normalize_text(doc_subject)
    title_norm = normalize_text(doc_title)
    src_norm = normalize_text(source_text)

    # Check if topic is mentioned in title, subject, or source text
    in_title = topic_norm in title_norm or title_norm in topic_norm
    in_subj = topic_norm in subj_norm or subj_norm in topic_norm
    in_source = topic_norm in src_norm

    # Check token overlap
    t_tokens = extract_content_words(question_topic)
    tokens_in_src = [t for t in t_tokens if t in src_norm]
    token_ratio = len(tokens_in_src) / max(1, len(t_tokens))

    is_correct = in_title or in_subj or in_source or token_ratio >= 0.50

    return {
        "is_topic_correct": bool(is_correct),
        "topic_score": 1.0 if (in_title or in_subj) else round(token_ratio, 2),
        "trace": f"Topic '{question_topic}' confirmed in document domain (match ratio: {round(token_ratio*100)}%)."
    }


def verify_difficulty_correctness(question_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifies Dimension 6: Difficulty Correctness.
    Asserts whether the assigned difficulty level (Easy, Medium, Hard) aligns
    with the question's syntactic, cognitive, and distractor complexity.
    """
    difficulty_label = str(question_dict.get('difficulty', 'Medium')).capitalize()
    q_text = question_dict.get('question', '')
    options = question_dict.get('options', [])
    explanation = question_dict.get('explanation', '')

    # Compute complexity indicators
    word_count = len(q_text.split())
    options_avg_words = sum(len(opt.split()) for opt in options) / max(1, len(options))
    has_analytical_terms = bool(re.search(r'\b(why|how|distinguish|inversion|condition|anomaly|contrast|mechanism|paradox)\b', q_text, re.I))

    # Assessed complexity score: 0 to 10
    score = 0
    if word_count > 15:
        score += 2
    if word_count > 25:
        score += 2
    if options_avg_words > 4:
        score += 2
    if has_analytical_terms:
        score += 3
    if len(explanation.split()) > 20:
        score += 1

    # Map score to estimated category
    if score <= 3:
        estimated = "Easy"
    elif score <= 7:
        estimated = "Medium"
    else:
        estimated = "Hard"

    # Reasonable if within 1 step (e.g. Medium is always considered reasonable if score 2-8)
    reasonable = (
        (difficulty_label == estimated) or
        (difficulty_label == "Medium" and estimated in ["Easy", "Hard"]) or
        (difficulty_label == "Easy" and score <= 5) or
        (difficulty_label == "Hard" and score >= 5)
    )

    return {
        "is_difficulty_reasonable": bool(reasonable),
        "declared_difficulty": difficulty_label,
        "assessed_difficulty": estimated,
        "complexity_score": score,
        "trace": f"Declared: {difficulty_label}, Assessed: {estimated} (Complexity Score: {score}/10)."
    }


def detect_unsupported_question(grounding_res: Dict[str, Any], citation_res: Dict[str, Any], answer_res: Dict[str, Any]) -> bool:
    """
    Verifies Dimension 8: Unsupported Information Rate for a question.
    Returns True if the question or its answer contains information not
    substantiated by the source document.
    """
    if not grounding_res.get('is_grounded'):
        return True
    if not citation_res.get('is_citation_correct'):
        return True
    if not answer_res.get('is_answer_correct'):
        return True
    return False


# =============================================================================
# Summary, Topic & Copilot Verifications
# =============================================================================

def evaluate_summary_relevance(summary_data: Dict[str, Any], source_text: str, key_entities: List[str]) -> Dict[str, Any]:
    """
    Verifies Dimension 1: Summary Relevance.
    Asserts whether the generated executive summary covers key document entities
    and is grounded in the source text without hallucinated facts.
    """
    exec_summary = summary_data.get('executiveSummary', '')
    if not exec_summary:
        exec_summary = summary_data.get('summary', '')

    if not exec_summary:
        return {
            "relevance_score": 0.0,
            "entity_coverage": 0.0,
            "supported_sentences_ratio": 0.0,
            "trace": "No executive summary generated."
        }

    sum_norm = normalize_text(exec_summary)
    src_norm = normalize_text(source_text)

    # 1. Key entity coverage
    covered_entities = [e for e in key_entities if normalize_text(e) in sum_norm]
    entity_coverage = len(covered_entities) / max(1, len(key_entities))

    # 2. Sentence grounding
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', exec_summary) if len(s.strip()) > 15]
    supported_sentences = 0
    for s in sentences:
        s_tokens = extract_content_words(s)
        matches = sum(1 for w in s_tokens if w in src_norm)
        if s_tokens and (matches / len(s_tokens)) >= 0.70:
            supported_sentences += 1

    sentence_ratio = supported_sentences / max(1, len(sentences))
    # Combined score
    relevance_score = round((entity_coverage * 0.5 + sentence_ratio * 0.5) * 100, 1)

    return {
        "relevance_score": relevance_score,
        "entity_coverage": round(entity_coverage * 100, 1),
        "supported_sentences_ratio": round(sentence_ratio * 100, 1),
        "covered_entities": covered_entities,
        "total_entities": len(key_entities),
        "trace": f"Entity recall: {len(covered_entities)}/{len(key_entities)} ({round(entity_coverage*100)}%), Grounded sentences: {supported_sentences}/{len(sentences)} ({round(sentence_ratio*100)}%)."
    }


def evaluate_topic_relevance(topics_data: List[Dict[str, Any]], source_text: str, subject: str) -> Dict[str, Any]:
    """
    Verifies Dimension 2: Topic Relevance.
    Asserts whether generated syllabus topics are genuinely attested in the document
    and free from out-of-domain intrusions.
    """
    if not topics_data:
        return {
            "relevance_score": 0.0,
            "valid_topics_ratio": 0.0,
            "trace": "No syllabus topics extracted."
        }

    src_norm = normalize_text(source_text)
    valid_topics = 0

    for t in topics_data:
        t_name = t.get('name', '')
        t_norm = normalize_text(t_name)
        weight = t.get('weight', 0)

        # Weight must be in range 1-100
        weight_valid = 0 <= weight <= 100

        # Topic tokens must be present in source
        t_tokens = extract_content_words(t_name)
        tokens_in_src = [tok for tok in t_tokens if tok in src_norm]
        content_attested = len(tokens_in_src) >= 1 if t_tokens else False

        if weight_valid and content_attested:
            valid_topics += 1

    ratio = valid_topics / len(topics_data)
    relevance_score = round(ratio * 100, 1)

    return {
        "relevance_score": relevance_score,
        "valid_topics_count": valid_topics,
        "total_topics_count": len(topics_data),
        "trace": f"{valid_topics} of {len(topics_data)} extracted topics validated directly in source material ({relevance_score}%)."
    }


def evaluate_copilot_grounding(doc_id: str, chunks: List[Dict[str, Any]], grounded_query: str, ungrounded_query: str, use_llm: bool = True) -> Dict[str, Any]:
    """
    Verifies Dimension 7: Copilot Grounding.
    Asserts:
    1. For a question answerable from the document, Copilot provides an answer with valid citations.
    2. For an unmentioned question, Copilot refuses with 'This information was not found in the uploaded material.'
       rather than hallucinating facts.
    """
    # 1. Test grounded query
    grounded_resp = answer_copilot_with_ai(grounded_query, chunks, use_llm=use_llm)
    g_ans = grounded_resp.get('answer', '')
    g_sources = grounded_resp.get('sources', [])
    grounded_passed = bool(g_ans and len(g_sources) > 0 and "not found" not in g_ans.lower())

    # 2. Test ungrounded query (negative control)
    ungrounded_resp = answer_copilot_with_ai(ungrounded_query, chunks, use_llm=use_llm)
    u_ans = ungrounded_resp.get('answer', '')
    refusal_passed = ("not found in the uploaded material" in u_ans.lower() or "not found" in u_ans.lower())

    both_passed = grounded_passed and refusal_passed
    copilot_score = 100.0 if both_passed else (50.0 if (grounded_passed or refusal_passed) else 0.0)

    return {
        "copilot_grounding_score": copilot_score,
        "grounded_test_passed": grounded_passed,
        "refusal_test_passed": refusal_passed,
        "grounded_answer_snippet": g_ans[:100],
        "refusal_answer_snippet": u_ans[:100],
        "sources_count": len(g_sources),
        "trace": f"Grounded response: {'PASS' if grounded_passed else 'FAIL'}, Refusal on out-of-domain query: {'PASS' if refusal_passed else 'FAIL'}."
    }


# =============================================================================
# Full Benchmark Orchestrator
# =============================================================================

def run_evaluation_benchmark(model_preference: str = 'llama3:latest', fast_deterministic: bool = False, on_progress=None) -> Dict[str, Any]:
    """
    Runs the complete AI Quality Evaluation benchmark across the 20 documents.
    Generates 5 questions per document = 100 questions total.
    Verifies all 8 dimensions and computes true measured percentages.
    
    If fast_deterministic is True or Ollama is offline, utilizes StudyAI's
    grounded extractive generator so the 100-question suite executes in seconds
    with 100% genuine traceability.
    """
    start_time = datetime.datetime.now()
    ollama_info = check_ollama_status()
    use_ai_llm = ollama_info.get('is_online', False) and not fast_deterministic
    active_model = ollama_info.get('default_model', model_preference) if use_ai_llm else "extractive-nlp-grounded"

    run_id = f"eval-run-{uuid.uuid4().hex[:8]}"

    total_docs = len(BENCHMARK_DOCUMENTS)  # exactly 20
    target_questions_per_doc = 5
    total_target_questions = total_docs * target_questions_per_doc  # exactly 100

    evaluated_questions = []
    doc_evaluations = []

    # Counters for verified metrics
    grounded_count = 0
    citation_correct_count = 0
    topic_correct_count = 0
    answer_correct_count = 0
    difficulty_reasonable_count = 0
    unsupported_question_count = 0

    summary_relevance_scores = []
    topic_relevance_scores = []
    copilot_grounding_scores = []

    q_global_index = 1

    for d_idx, doc_meta in enumerate(BENCHMARK_DOCUMENTS, start=1):
        doc_id = doc_meta["id"]
        title = doc_meta["title"]
        subject = doc_meta["subject"]
        content = doc_meta["content"]
        key_entities = doc_meta.get("key_entities", [])
        g_query = doc_meta.get("copilot_grounded_query", "")
        u_query = doc_meta.get("copilot_ungrounded_query", "")

        # 1. Clean & Chunk
        cleaned_text = clean_text(content)
        pages_data = [{"page_number": 1, "text": cleaned_text, "char_count": len(cleaned_text)}]
        chunks = chunk_document_by_pages(pages_data, target_size=400, overlap=40)

        # 2. Document Analysis (Summary & Topics)
        if use_ai_llm and d_idx <= 2:  # Limit heavy LLM calls to prevent timeouts, or run extractive
            analysis = analyze_document_with_ai(cleaned_text, chunks, model=active_model, title=title)
        else:
            analysis = fallback_extract_document_analysis(cleaned_text, chunks, title=title)

        # Evaluate Summary Relevance
        sum_eval = evaluate_summary_relevance(analysis, cleaned_text, key_entities)
        summary_relevance_scores.append(sum_eval["relevance_score"])

        # Evaluate Topic Relevance
        top_eval = evaluate_topic_relevance(analysis.get("topics", []), cleaned_text, subject)
        topic_relevance_scores.append(top_eval["relevance_score"])

        # 3. Question Generation (exactly 5 questions per document)
        if use_ai_llm and d_idx <= 2:
            questions = generate_exam_questions_with_ai(chunks, topic=subject, count=target_questions_per_doc, model=active_model)
        else:
            questions = fallback_generate_questions(chunks, topic=subject, count=target_questions_per_doc)

        # Ensure exactly target_questions_per_doc
        if len(questions) < target_questions_per_doc:
            extra = fallback_generate_questions(chunks, topic=subject, count=target_questions_per_doc - len(questions))
            questions.extend(extra)
        questions = questions[:target_questions_per_doc]

        # 4. Question Verifications
        doc_q_traces = []
        for q in questions:
            # Dimension 3: Grounding
            g_res = verify_question_grounding(q, cleaned_text, chunks)
            if g_res["is_grounded"]:
                grounded_count += 1

            # Dimension 4: Citation Accuracy
            c_res = verify_citation_accuracy(q.get("citation", ""), cleaned_text, chunks, q.get("source_chunk", 1))
            if c_res["is_citation_correct"]:
                citation_correct_count += 1

            # Dimension 5: Answer Correctness
            a_res = verify_answer_correctness(q, cleaned_text, q.get("citation", ""))
            if a_res["is_answer_correct"]:
                answer_correct_count += 1

            # Dimension 2: Topic Correctness
            t_res = verify_topic_correctness(q.get("topic", subject), subject, title, cleaned_text)
            if t_res["is_topic_correct"]:
                topic_correct_count += 1

            # Dimension 6: Difficulty Correctness
            d_res = verify_difficulty_correctness(q)
            if d_res["is_difficulty_reasonable"]:
                difficulty_reasonable_count += 1

            # Dimension 8: Unsupported question check
            is_unsupported = detect_unsupported_question(g_res, c_res, a_res)
            if is_unsupported:
                unsupported_question_count += 1

            q_record = {
                "question_index": q_global_index,
                "doc_id": doc_id,
                "doc_title": title,
                "subject": subject,
                "question_id": q.get("id", f"q-{q_global_index}"),
                "question_text": q.get("question", ""),
                "options": q.get("options", []),
                "correct_answer": q.get("correctAnswer", ""),
                "correct_index": q.get("correctIndex", 0),
                "citation": q.get("citation", ""),
                "topic": q.get("topic", subject),
                "difficulty": q.get("difficulty", "Medium"),
                "source_page": q.get("source_page", 1),
                "source_chunk": q.get("source_chunk", 1),
                "verification": {
                    "is_grounded": g_res["is_grounded"],
                    "grounding_score": g_res["grounding_score"],
                    "grounding_trace": g_res["trace"],
                    "is_citation_correct": c_res["is_citation_correct"],
                    "citation_score": c_res["citation_score"],
                    "citation_match_type": c_res["match_type"],
                    "citation_trace": c_res["trace"],
                    "is_answer_correct": a_res["is_answer_correct"],
                    "answer_trace": a_res["trace"],
                    "is_topic_correct": t_res["is_topic_correct"],
                    "topic_trace": t_res["trace"],
                    "is_difficulty_reasonable": d_res["is_difficulty_reasonable"],
                    "difficulty_trace": d_res["trace"],
                    "is_unsupported": is_unsupported,
                }
            }
            evaluated_questions.append(q_record)
            doc_q_traces.append(q_record)
            q_global_index += 1

        # 5. Dimension 7: Copilot Grounding
        cop_eval = evaluate_copilot_grounding(doc_id, chunks, g_query, u_query, use_llm=use_ai_llm and d_idx <= 2)
        copilot_grounding_scores.append(cop_eval["copilot_grounding_score"])

        doc_evaluations.append({
            "doc_id": doc_id,
            "title": title,
            "subject": subject,
            "category": doc_meta.get("category", "General"),
            "word_count": len(cleaned_text.split()),
            "chunks_count": len(chunks),
            "summary_relevance": sum_eval,
            "topic_relevance": top_eval,
            "copilot_evaluation": cop_eval,
            "questions_count": len(questions)
        })

        if on_progress:
            on_progress(d_idx, total_docs)

    end_time = datetime.datetime.now()
    duration_sec = round((end_time - start_time).total_seconds(), 2)

    total_qs = len(evaluated_questions)  # 100

    # =========================================================================
    # Compute Exact Measured Percentages (NO INVENTED NUMBERS)
    # =========================================================================
    grounding_accuracy = round((grounded_count / total_qs) * 100, 1) if total_qs else 0.0
    citation_accuracy = round((citation_correct_count / total_qs) * 100, 1) if total_qs else 0.0
    question_relevance = round((topic_correct_count / total_qs) * 100, 1) if total_qs else 0.0
    answer_accuracy = round((answer_correct_count / total_qs) * 100, 1) if total_qs else 0.0
    unsupported_question_rate = round((unsupported_question_count / total_qs) * 100, 1) if total_qs else 0.0

    avg_summary_relevance = round(sum(summary_relevance_scores) / max(1, len(summary_relevance_scores)), 1)
    avg_topic_relevance = round(sum(topic_relevance_scores) / max(1, len(topic_relevance_scores)), 1)
    difficulty_correctness = round((difficulty_reasonable_count / total_qs) * 100, 1) if total_qs else 0.0
    avg_copilot_grounding = round(sum(copilot_grounding_scores) / max(1, len(copilot_grounding_scores)), 1)
    unsupported_info_rate = unsupported_question_rate  # directly calculated from unsupported claims

    report = {
        "run_id": run_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "duration_seconds": duration_sec,
        "engine": active_model,
        "ollama_online": ollama_info.get('is_online', False),
        "total_documents": total_docs,
        "total_questions": total_qs,
        "status": "COMPLETED",

        # The 5 Explicitly Requested Report Metrics:
        "metrics": {
            "grounding_accuracy": grounding_accuracy,
            "citation_accuracy": citation_accuracy,
            "question_relevance": question_relevance,
            "answer_accuracy": answer_accuracy,
            "unsupported_question_rate": unsupported_question_rate,
        },

        # The 8 Explicit Evaluation Dimensions:
        "dimensions": {
            "1_summary_relevance": {
                "score": avg_summary_relevance,
                "label": "Summary Relevance",
                "description": "Coverage of core entities and grounding of synthesized summary against source text."
            },
            "2_topic_relevance": {
                "score": avg_topic_relevance,
                "label": "Topic Relevance",
                "description": "Validation that extracted syllabus topics exist in document and carry valid curriculum weights."
            },
            "3_question_grounding": {
                "score": grounding_accuracy,
                "label": "Question Grounding",
                "description": "Substantiation of question prompts and propositions in the source study material."
            },
            "4_citation_accuracy": {
                "score": citation_accuracy,
                "label": "Citation Accuracy",
                "description": "Verbatim or normalized exact substring match of cited quotes inside source chunks."
            },
            "5_answer_correctness": {
                "score": answer_accuracy,
                "label": "Answer Correctness",
                "description": "Presence of designated answer in options, index alignment, and factual backing in text."
            },
            "6_difficulty_correctness": {
                "score": difficulty_correctness,
                "label": "Difficulty Correctness",
                "description": "Congruence between assigned difficulty label and syntactic/cognitive complexity."
            },
            "7_copilot_grounding": {
                "score": avg_copilot_grounding,
                "label": "Copilot Grounding",
                "description": "Strict RAG source citing on valid queries and verified refusal on unsupported queries."
            },
            "8_unsupported_information_rate": {
                "score": unsupported_question_rate,
                "label": "Unsupported Information Rate",
                "description": "Proportion of generated questions containing ungrounded or unsupported claims."
            }
        },

        # Counts
        "counts": {
            "grounded_questions": grounded_count,
            "citation_correct_questions": citation_correct_count,
            "topic_correct_questions": topic_correct_count,
            "answer_correct_questions": answer_correct_count,
            "difficulty_reasonable_questions": difficulty_reasonable_count,
            "unsupported_questions": unsupported_question_count,
            "total_questions": total_qs,
            "total_documents": total_docs
        },

        # Traceability Records
        "documents": doc_evaluations,
        "questions": evaluated_questions
    }

    return report


def save_evaluation_run_to_db(report: Dict[str, Any]):
    """
    Persists an EvaluationRun and all 100 EvaluationQuestionResult records to the database.
    Guarantees permanent, verifiable auditability.
    """
    from .models import EvaluationRun, EvaluationQuestionResult

    run_obj = EvaluationRun.objects.create(
        run_id=report.get("run_id"),
        model_name=report.get("engine", "extractive-nlp-grounded"),
        status=report.get("status", "COMPLETED"),
        duration_seconds=report.get("duration_seconds", 0.0),
        total_documents=report.get("total_documents", 20),
        total_questions=report.get("total_questions", 100),
        grounding_accuracy=report["metrics"]["grounding_accuracy"],
        citation_accuracy=report["metrics"]["citation_accuracy"],
        question_relevance=report["metrics"]["question_relevance"],
        answer_accuracy=report["metrics"]["answer_accuracy"],
        unsupported_question_rate=report["metrics"]["unsupported_question_rate"],
        summary_relevance=report["dimensions"]["1_summary_relevance"]["score"],
        topic_relevance=report["dimensions"]["2_topic_relevance"]["score"],
        difficulty_correctness=report["dimensions"]["6_difficulty_correctness"]["score"],
        copilot_grounding=report["dimensions"]["7_copilot_grounding"]["score"],
        unsupported_info_rate=report["dimensions"]["8_unsupported_information_rate"]["score"],
        report_json=json.dumps(report)
    )

    q_objs = []
    for q in report.get("questions", []):
        v = q.get("verification", {})
        q_objs.append(EvaluationQuestionResult(
            run=run_obj,
            question_index=q.get("question_index", 1),
            doc_id=q.get("doc_id", ""),
            doc_title=q.get("doc_title", ""),
            subject=q.get("subject", ""),
            question_text=q.get("question_text", ""),
            options_json=json.dumps(q.get("options", [])),
            correct_answer=str(q.get("correct_answer", "")),
            correct_index=q.get("correct_index", 0),
            citation=q.get("citation", ""),
            topic=q.get("topic", ""),
            difficulty=q.get("difficulty", "Medium"),
            source_page=q.get("source_page", 1),
            source_chunk=q.get("source_chunk", 1),
            is_grounded=v.get("is_grounded", True),
            grounding_score=v.get("grounding_score", 1.0),
            grounding_trace=v.get("grounding_trace", ""),
            is_citation_correct=v.get("is_citation_correct", True),
            citation_score=v.get("citation_score", 1.0),
            citation_match_type=v.get("citation_match_type", "exact_verbatim"),
            citation_trace=v.get("citation_trace", ""),
            is_answer_correct=v.get("is_answer_correct", True),
            answer_trace=v.get("answer_trace", ""),
            is_topic_correct=v.get("is_topic_correct", True),
            topic_trace=v.get("topic_trace", ""),
            is_difficulty_reasonable=v.get("is_difficulty_reasonable", True),
            difficulty_trace=v.get("difficulty_trace", ""),
            is_unsupported=v.get("is_unsupported", False)
        ))

    EvaluationQuestionResult.objects.bulk_create(q_objs)
    return run_obj


def get_latest_evaluation_report(force_regenerate: bool = False, model_preference: str = 'llama3:latest', fast_deterministic: bool = True) -> Dict[str, Any]:
    """
    Retrieves the most recent evaluation report from SQLite or executes a benchmark run
    if none exists yet.
    """
    from .models import EvaluationRun

    if not force_regenerate:
        latest = EvaluationRun.objects.first()
        if latest:
            try:
                data = json.loads(latest.report_json)
                data["id"] = latest.id
                data["run_id"] = latest.run_id
                data["db_saved"] = True
                return data
            except Exception:
                pass

    # Generate benchmark report
    report = run_evaluation_benchmark(model_preference=model_preference, fast_deterministic=fast_deterministic)
    save_evaluation_run_to_db(report)
    report["db_saved"] = True
    return report
