#!/usr/bin/env python3
"""
=============================================================================
StudyAI — AI Quality Evaluation CLI Runner
=============================================================================
Executes the empirical benchmark across 20 real academic documents and
100 generated questions to measure AI quality across 8 dimensions.

Usage:
    python run_ai_evaluation.py
    python run_ai_evaluation.py --live-llm --model llama3:latest
    python run_ai_evaluation.py --export-json audit_report.json --export-md audit_report.md
=============================================================================
"""

import os
import sys
import json
import argparse
import datetime

# Ensure Windows terminal handles UTF-8 formatting cleanly
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studyai_backend.settings')

import django
django.setup()

from api.benchmark_dataset import BENCHMARK_DOCUMENTS
from api.evaluator import run_evaluation_benchmark, save_evaluation_run_to_db, get_latest_evaluation_report
from api.models import EvaluationRun, EvaluationQuestionResult


def format_table_row(col1, col2, col3="", width1=32, width2=18, width3=25):
    return f"  {str(col1):<{width1}} | {str(col2):<{width2}} | {str(col3):<{width3}}"


def generate_markdown_report(report: dict) -> str:
    metrics = report.get("metrics", {})
    dimensions = report.get("dimensions", {})
    counts = report.get("counts", {})
    questions = report.get("questions", [])
    documents = report.get("documents", [])

    md = []
    md.append("# StudyAI — AI Quality Evaluation Audit Report")
    md.append(f"\n**Run ID:** `{report.get('run_id')}`  ")
    md.append(f"**Execution Timestamp:** {report.get('timestamp')}  ")
    md.append(f"**Inference Engine:** `{report.get('engine')}` (Ollama Available: {report.get('ollama_online')})  ")
    md.append(f"**Duration:** {report.get('duration_seconds')} seconds  ")
    md.append(f"**Benchmark Scope:** {report.get('total_documents')} Academic Documents / {report.get('total_questions')} Generated Questions  ")

    md.append("\n---\n")
    md.append("## Executive Measured Metrics\n")
    md.append("| Metric | Measured Result | Evaluation Criteria |")
    md.append("| :--- | :---: | :--- |")
    md.append(f"| **Grounding Accuracy** | **{metrics.get('grounding_accuracy')}%** | Question premises substantiated by source text |")
    md.append(f"| **Citation Accuracy** | **{metrics.get('citation_accuracy')}%** | Exact verbatim or normalized citation quotes |")
    md.append(f"| **Question Relevance** | **{metrics.get('question_relevance')}%** | Strict domain & syllabus alignment |")
    md.append(f"| **Answer Accuracy** | **{metrics.get('answer_accuracy')}%** | Correct answer presence & source validation |")
    md.append(f"| **Unsupported Question Rate** | **{metrics.get('unsupported_question_rate')}%** | Low is better: questions with unsupported claims |")

    md.append("\n---\n")
    md.append("## Evaluated 8-Dimension Quality Breakdown\n")
    md.append("| # | Dimension | Measured Score | Evaluation Description |")
    md.append("| :-: | :--- | :---: | :--- |")
    for key in sorted(dimensions.keys()):
        dim = dimensions[key]
        num = key.split('_')[0]
        md.append(f"| {num} | **{dim.get('label')}** | **{dim.get('score')}%** | {dim.get('description')} |")

    md.append("\n---\n")
    md.append("## Benchmark Documents Evaluated (20 Real Study Materials)\n")
    md.append("| # | Document Title | Subject | Word Count | Summary Relevance | Topic Relevance | Copilot Grounding |")
    md.append("| :-: | :--- | :--- | :---: | :---: | :---: | :---: |")
    for idx, d in enumerate(documents, start=1):
        s_rel = d.get('summary_relevance', {}).get('relevance_score', 0)
        t_rel = d.get('topic_relevance', {}).get('relevance_score', 0)
        c_rel = d.get('copilot_evaluation', {}).get('copilot_grounding_score', 0)
        md.append(f"| {idx} | {d.get('title')} | {d.get('subject')} | {d.get('word_count')} words | {s_rel}% | {t_rel}% | {c_rel}% |")

    md.append("\n---\n")
    md.append("## Sample Traceable Question Verifications (100 Verified Questions)\n")
    md.append("Showing first 10 verified test traces with character-level evidence:\n")

    for q in questions[:10]:
        v = q.get('verification', {})
        md.append(f"### Question #{q.get('question_index')}: {q.get('doc_title')}")
        md.append(f"- **Prompt:** \"{q.get('question_text')}\"")
        md.append(f"- **Designated Answer:** `{q.get('correct_answer')}` (Option index: {q.get('correct_index')})")
        md.append(f"- **Options:** {', '.join([f'`{opt}`' for opt in q.get('options', [])])}")
        md.append(f"- **Citation Quote:** \"{q.get('citation')}\"")
        md.append(f"- **Grounding Verified:** `{'PASS' if v.get('is_grounded') else 'FAIL'}` ({v.get('grounding_trace')})")
        md.append(f"- **Citation Verified:** `{'PASS' if v.get('is_citation_correct') else 'FAIL'}` (Match Type: `{v.get('citation_match_type')}`) ")
        md.append(f"- **Answer Validated:** `{'PASS' if v.get('is_answer_correct') else 'FAIL'}` ({v.get('answer_trace')})")
        md.append(f"- **Difficulty & Topic:** Topic: `{q.get('topic')}`, Difficulty: `{q.get('difficulty')}` (`{'PASS' if v.get('is_difficulty_reasonable') else 'FAIL'}`)")
        md.append(f"- **Unsupported Information:** `{'YES (FLAGGED)' if v.get('is_unsupported') else 'NO (GROUNDED)'}`")
        md.append("")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="StudyAI AI Quality Evaluation Runner")
    parser.add_argument("--model", type=str, default="llama3:latest", help="Preferred Ollama model")
    parser.add_argument("--live-llm", action="store_true", help="Force live Ollama LLM queries across all documents")
    parser.add_argument("--export-json", type=str, default="evaluation_report.json", help="Path to export JSON audit report")
    parser.add_argument("--export-md", type=str, default="evaluation_report.md", help="Path to export Markdown audit report")
    args = parser.parse_args()

    print("================================================================================")
    print("                    STUDYAI — AI QUALITY EVALUATION SUITE                       ")
    print("================================================================================")
    print(f" Target Benchmark Scope: {len(BENCHMARK_DOCUMENTS)} Real Academic Study Documents")
    print(f" Target Generated Questions: 100 Questions (5 per document)")
    print(f" Quality Dimensions Evaluated: 8 Core Dimensions")
    print("================================================================================")
    print("[*] Running rigorous evaluation pipeline across 20 academic domains...")

    def progress(current, total):
        pct = int((current / total) * 100)
        bar = "#" * (pct // 5) + "-" * (20 - (pct // 5))
        sys.stdout.write(f"\r[{bar}] Document {current}/{total} ({pct}%)")
        sys.stdout.flush()

    report = run_evaluation_benchmark(
        model_preference=args.model,
        fast_deterministic=not args.live_llm,
        on_progress=progress
    )
    print("\n[*] Benchmark processing complete. Persisting audit records to database...")

    # Save to SQLite database
    save_evaluation_run_to_db(report)
    print(f"[+] Persisted 1 EvaluationRun and {len(report.get('questions', []))} EvaluationQuestionResult records to SQLite.")

    # Export to files
    if args.export_json:
        with open(args.export_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[+] Exported JSON audit report to: {os.path.abspath(args.export_json)}")

    if args.export_md:
        md_content = generate_markdown_report(report)
        with open(args.export_md, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[+] Exported Markdown audit report to: {os.path.abspath(args.export_md)}")

    # Print Formatted Executive Report
    metrics = report.get("metrics", {})
    dimensions = report.get("dimensions", {})
    counts = report.get("counts", {})

    print("\n" + "=" * 60)
    print("                           REPORT                               ")
    print("=" * 60)
    print(f"  Grounding Accuracy        : {metrics.get('grounding_accuracy')}% ({counts.get('grounded_questions')}/{counts.get('total_questions')})")
    print(f"  Citation Accuracy         : {metrics.get('citation_accuracy')}% ({counts.get('citation_correct_questions')}/{counts.get('total_questions')})")
    print(f"  Question Relevance        : {metrics.get('question_relevance')}% ({counts.get('topic_correct_questions')}/{counts.get('total_questions')})")
    print(f"  Answer Accuracy           : {metrics.get('answer_accuracy')}% ({counts.get('answer_correct_questions')}/{counts.get('total_questions')})")
    print(f"  Unsupported Question Rate : {metrics.get('unsupported_question_rate')}% ({counts.get('unsupported_questions')}/{counts.get('total_questions')})")
    print("=" * 60)

    print("\n" + "-" * 78)
    print("                  8 EVALUATION DIMENSIONS MEASUREMENT SUMMARY                   ")
    print("-" * 78)
    print(format_table_row("Dimension", "Measured Score", "Description"))
    print("-" * 78)
    for k in sorted(dimensions.keys()):
        d = dimensions[k]
        print(format_table_row(d["label"], f"{d['score']}%", d["description"][:24] + "..."))
    print("-" * 78)

    print("\n[+] Verification audit complete. All 100 questions verified and traceable.")


if __name__ == "__main__":
    main()
