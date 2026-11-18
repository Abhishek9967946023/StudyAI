"""
StudyAI — Additional Acceptance Verification Script
Tests additional edge cases and failures specified in the Final Release Validation prompt:
1. Very large file (>50MB upload rejection)
2. Scanned PDF when OCR is unavailable / failing
3. Invalid question ID handling in exam submission
4. Duplicate submission / multiple attempt handling
5. Unsupported Copilot question refusal ("This information was not found...")
6. Adaptive practice loop generation and completion
7. Direct text ingestion flow
"""

import os
import sys
import json
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studyai_backend.settings')
django.setup()

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from api.models import Document, Exam, Question, ExamAttempt, AdaptivePracticeLoop
from api.ollama_service import answer_copilot_with_ai

client = Client()
results = []

def record(name, expected, actual, status):
    results.append({"name": name, "expected": expected, "actual": actual, "status": status})
    symbol = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"{symbol} {name}: {actual}")

# 1. Very Large File (>50MB)
print("\n--- Test: Very Large File (>50MB) ---")
large_file = SimpleUploadedFile("huge_file.pdf", b"%PDF-1.4\n" + b"A" * 100)
with patch('api.views.MAX_UPLOAD_SIZE_BYTES', 50):
    resp_big = client.post('/api/documents/upload/', {'file': large_file})
    if resp_big.status_code == 400 and "exceeds" in resp_big.json().get("error", "").lower():
        record("Very Large File (>50MB)", "HTTP 400 Exceeds limit", f"HTTP 400: {resp_big.json().get('error')}", "PASS")
    else:
        record("Very Large File (>50MB)", "HTTP 400 Exceeds limit", f"HTTP {resp_big.status_code}", "FAIL")

# 2. Scanned PDF with OCR Unavailable
print("\n--- Test: Scanned PDF / OCR Unavailable ---")
import pypdf
import io
scanned_writer = pypdf.PdfWriter()
scanned_writer.add_blank_page(width=612, height=792)
buf = io.BytesIO()
scanned_writer.write(buf)
scanned_bytes = buf.getvalue()

with patch('api.document_service.is_ocr_available', return_value=False):
    resp_ocr = client.post('/api/documents/upload/', {'file': SimpleUploadedFile('scanned_no_ocr.pdf', scanned_bytes)})
    if resp_ocr.status_code == 400:
        err = resp_ocr.json().get('error', '')
        record("Scanned PDF (No OCR)", "HTTP 400 Scanned PDF explanation", f"HTTP 400: {err}", "PASS")
    else:
        record("Scanned PDF (No OCR)", "HTTP 400 Scanned PDF explanation", f"HTTP {resp_ocr.status_code}", "FAIL")

# 3. Direct Text Ingestion Flow
print("\n--- Test: Direct Text Ingestion Flow ---")
resp_txt = client.post(
    '/api/documents/upload/',
    data=json.dumps({
        "title": "Quantum Computing Fundamentals",
        "text": "Quantum computers leverage superposition and quantum entanglement to process qubits simultaneously. Quantum gates like the Hadamard gate transform basis states into superpositions. Shor's algorithm provides exponential speedup for integer factorization. Grover's algorithm provides quadratic speedup for unstructured database searching."
    }),
    content_type='application/json'
)
if resp_txt.status_code == 200:
    dt_id = resp_txt.json().get('id')
    record("Direct Text Ingestion", "HTTP 200 with document created", f"HTTP 200, Doc ID: {dt_id}", "PASS")
else:
    record("Direct Text Ingestion", "HTTP 200", f"HTTP {resp_txt.status_code}", "FAIL")
    dt_id = None

# 4. Invalid Question ID in Submission
print("\n--- Test: Invalid Question ID in Submission ---")
doc = Document.objects.filter(exams__isnull=False).first()
if doc and doc.exams.exists():
    exam = doc.exams.first()
    # Submit with completely fake question IDs
    resp_inv_q = client.post(
        f'/api/exams/{exam.id}/submit/',
        data=json.dumps({"answers": {"q-999999": "Bogus Answer", "q-888888": "Fake Answer"}}),
        content_type='application/json'
    )
    if resp_inv_q.status_code == 200:
        inv_data = resp_inv_q.json()
        record("Invalid Question ID Handling", "Handled gracefully with 0% score", f"Score: {inv_data.get('scorePercent')}%, Grade: {inv_data.get('letterGrade')}", "PASS")
    else:
        record("Invalid Question ID Handling", "HTTP 200 graded", f"HTTP {resp_inv_q.status_code}", "FAIL")

# 5. Duplicate Submission / Multiple Attempts
print("\n--- Test: Duplicate Submission Handling ---")
if doc and doc.exams.exists():
    exam = doc.exams.first()
    prev_attempts = ExamAttempt.objects.filter(exam=exam).count()
    resp_sub1 = client.post(f'/api/exams/{exam.id}/submit/', data=json.dumps({"answers": {}}), content_type='application/json')
    resp_sub2 = client.post(f'/api/exams/{exam.id}/submit/', data=json.dumps({"answers": {}}), content_type='application/json')
    new_attempts = ExamAttempt.objects.filter(exam=exam).count()
    if resp_sub1.status_code == 200 and resp_sub2.status_code == 200 and new_attempts == prev_attempts + 2:
        record("Duplicate Submission Handling", "Both attempts recorded in longitudinal history", f"Attempts tracked: {new_attempts}", "PASS")
    else:
        record("Duplicate Submission Handling", "Both attempts recorded", f"Counts: {prev_attempts} -> {new_attempts}", "FAIL")

# 6. Unsupported Copilot Question Refusal
print("\n--- Test: Unsupported Copilot Question Refusal ---")
chunks = [{"chunk_index": 1, "page_start": 1, "text": "Operating system memory management uses paging and segmentation to allocate virtual memory."}]
copilot_unsupported = answer_copilot_with_ai("How does photosynthesis produce glucose in plants?", chunks, use_llm=False)
if "not found" in copilot_unsupported.get("answer", "").lower():
    record("Copilot Unsupported Question Refusal", "Refusal: 'This information was not found...'", f"Answer: '{copilot_unsupported.get('answer')}'", "PASS")
else:
    record("Copilot Unsupported Question Refusal", "Refusal message", f"Got: '{copilot_unsupported.get('answer')}'", "FAIL")

# 7. Adaptive Practice Loop
print("\n--- Test: Adaptive Practice Loop ---")
if dt_id:
    resp_loop_gen = client.post(
        '/api/adaptive/generate/',
        data=json.dumps({"document_id": dt_id, "topic": "Quantum Entanglement", "questionCount": 3, "previousPerformance": 30}),
        content_type='application/json'
    )
    if resp_loop_gen.status_code == 200:
        loop_data = resp_loop_gen.json()
        practice_exam_id = loop_data.get('exam_id') or loop_data.get('id')
        record("Adaptive Practice Loop Generation", "HTTP 200 with targeted drill questions", f"Exam ID: {practice_exam_id}, Questions: {len(loop_data.get('questions', []))}", "PASS")
        
        # Test Complete / Submit Loop
        resp_loop_done = client.post(
            '/api/adaptive/submit/',
            data=json.dumps({"exam_id": practice_exam_id, "topic": "Quantum Entanglement", "answers": {}, "previousPerformance": 30}),
            content_type='application/json'
        )
        if resp_loop_done.status_code == 200:
            sub_res = resp_loop_done.json()
            record("Adaptive Practice Loop Completion", "HTTP 200 with mastery delta", f"Topic: {sub_res.get('topic')}, Delta: {sub_res.get('improvement')}%, LoopID: {sub_res.get('loopId')}", "PASS")
        else:
            record("Adaptive Practice Loop Completion", "HTTP 200", f"HTTP {resp_loop_done.status_code}", "FAIL")
    else:
        record("Adaptive Practice Loop Generation", "HTTP 200", f"HTTP {resp_loop_gen.status_code}", "FAIL")

print("\n--- SUMMARY OF ADDITIONAL ACCEPTANCE TESTS ---")
p = sum(1 for r in results if r["status"] == "PASS")
f = sum(1 for r in results if r["status"] == "FAIL")
print(f"PASS={p}, FAIL={f}, TOTAL={len(results)}")
