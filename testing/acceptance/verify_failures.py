import os
import sys
import json
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studyai_backend.settings')
django.setup()

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from run_comprehensive_acceptance import test_results, record
from api.ollama_service import analyze_document_with_ai, generate_exam_questions_with_ai

client = Client()
test_results.clear()

print("Running all 10 Failure Resilience Tests...")

# Failure 1: Empty file upload (0 bytes)
empty_file = SimpleUploadedFile("empty.txt", b"")
resp_f1 = client.post('/api/documents/upload/', {'file': empty_file})
if resp_f1.status_code == 400:
    record("Failure 1: Empty File Upload", "HTTP 400 error", f"HTTP 400: {resp_f1.json().get('error')}", "PASS")
else:
    record("Failure 1: Empty File Upload", "HTTP 400 error", f"HTTP {resp_f1.status_code}", "FAIL")

# Failure 2: Empty text input ("   ")
resp_f2 = client.post(
    '/api/documents/upload/',
    data=json.dumps({"title": "Blank", "text": "   "}),
    content_type='application/json'
)
if resp_f2.status_code == 400:
    record("Failure 2: Blank Text Input", "HTTP 400 error", f"HTTP 400: {resp_f2.json().get('error')}", "PASS")
else:
    record("Failure 2: Blank Text Input", "HTTP 400 error", f"HTTP {resp_f2.status_code}", "FAIL")

# Failure 3: Unsupported file extension (.exe)
unsupported_file = SimpleUploadedFile("malicious.exe", b"MZ\x90\x00\x03\x00")
resp_f3 = client.post('/api/documents/upload/', {'file': unsupported_file})
if resp_f3.status_code == 400 and "unsupported" in resp_f3.json().get("error", "").lower():
    record("Failure 3: Unsupported Extension (.exe)", "HTTP 400 Unsupported format error", f"HTTP 400: {resp_f3.json().get('error')}", "PASS")
else:
    record("Failure 3: Unsupported Extension (.exe)", "HTTP 400 Unsupported format error", f"HTTP {resp_f3.status_code}", "FAIL")

# Failure 4: Corrupted PDF file
corrupt_pdf = SimpleUploadedFile("corrupt.pdf", b"%PDF-1.4\ncorrupted binary garbage data %%%EOF")
resp_f4 = client.post('/api/documents/upload/', {'file': corrupt_pdf})
if resp_f4.status_code == 400:
    record("Failure 4: Corrupted PDF Handling", "HTTP 400 with extraction error details", f"HTTP 400: {resp_f4.json().get('error')}", "PASS")
else:
    record("Failure 4: Corrupted PDF Handling", "HTTP 400 error", f"HTTP {resp_f4.status_code}", "FAIL")

# Failure 5: Requesting Nonexistent Document ID (404 / handled)
resp_f5 = client.get('/api/documents/999999/')
if resp_f5.status_code == 404:
    record("Failure 5: Missing Document ID (999999)", "HTTP 404 Not Found", f"HTTP 404: {resp_f5.json().get('error')}", "PASS")
else:
    record("Failure 5: Missing Document ID (999999)", "HTTP 404 Not Found", f"HTTP {resp_f5.status_code}", "FAIL")

# Failure 6: Requesting Nonexistent Exam ID
resp_f6 = client.get('/api/exams/exam-999999/')
if resp_f6.status_code == 404:
    record("Failure 6: Missing Exam ID", "HTTP 404 Not Found", f"HTTP 404: {resp_f6.json().get('error')}", "PASS")
else:
    record("Failure 6: Missing Exam ID", "HTTP 404 Not Found", f"HTTP {resp_f6.status_code}", "FAIL")

# Failure 7: Submitting Exam with Nonexistent Exam ID
resp_f7 = client.post('/api/exams/exam-999999/submit/', data=json.dumps({"answers": {}}), content_type='application/json')
if resp_f7.status_code == 404:
    record("Failure 7: Submit Nonexistent Exam", "HTTP 404 Not Found", f"HTTP 404: {resp_f7.json().get('error')}", "PASS")
else:
    record("Failure 7: Submit Nonexistent Exam", "HTTP 404 Not Found", f"HTTP {resp_f7.status_code}", "FAIL")

# Failure 8: Ollama Unavailable Simulation
with patch('api.ollama_service.query_ollama', return_value=(None, False, "Connection refused")):
    fb_analysis = analyze_document_with_ai("Sample OS text with process control block and scheduling.", [{"chunk_index": 1, "page_start": 1, "text": "Process scheduling and memory"}], title="OS Fallback Test")
    if fb_analysis and "topics" in fb_analysis and len(fb_analysis["topics"]) > 0:
        record("Failure 8: Ollama Offline Fallback", "Grounded fallback analysis succeeds", f"Extracted {len(fb_analysis['topics'])} topics: {[t['name'] for t in fb_analysis['topics']]}", "PASS")
    else:
        record("Failure 8: Ollama Offline Fallback", "Grounded fallback analysis succeeds", "Failed to extract fallback", "FAIL")

# Failure 9: Ollama Model Unavailable Simulation
with patch('api.ollama_service.query_ollama', return_value=(None, False, "model 'nonexistent-model' not found")):
    fb_questions = generate_exam_questions_with_ai([{"chunk_index": 1, "page_start": 1, "text": "TCP operates at transport layer with sequence numbers."}], topic="All", count=2, model="nonexistent-model")
    if fb_questions and len(fb_questions) >= 1 and fb_questions[0].get("citation"):
        record("Failure 9: Ollama Missing Model Fallback", "Extractive question generation with citations", f"{len(fb_questions)} questions with citations: '{fb_questions[0]['citation'][:40]}...'", "PASS")
    else:
        record("Failure 9: Ollama Missing Model Fallback", "Extractive question generation with citations", "Failed", "FAIL")

# Failure 10: Malformed AI JSON Response Handling
malformed_raw_ai = "Here is your response:\n```json\n{\ninvalid json format without closing bracket"
with patch('api.ollama_service.query_ollama', return_value=(malformed_raw_ai, True, None)):
    analysis_malformed = analyze_document_with_ai("Database normalization 1NF 2NF 3NF BCNF dependencies.", [{"chunk_index": 1, "page_start": 1, "text": "Database normalization and relations"}])
    if analysis_malformed and "topics" in analysis_malformed:
        record("Failure 10: Malformed AI JSON Parsing", "Graceful recovery to extractive NLP", f"Recovered with subject: '{analysis_malformed.get('subject')}' and {len(analysis_malformed.get('topics', []))} topics", "PASS")
    else:
        record("Failure 10: Malformed AI JSON Parsing", "Graceful recovery", "Crashed on malformed JSON", "FAIL")

# Summary
pass_count = sum(1 for r in test_results if r["status"] == "PASS")
fail_count = sum(1 for r in test_results if r["status"] == "FAIL")
print(f"\nFAILURE TESTS SUMMARY: PASS={pass_count}, FAIL={fail_count}, TOTAL={len(test_results)}")
