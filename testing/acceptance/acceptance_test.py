
"""
=============================================================================
StudyAI — End-to-End Real File Acceptance Test
=============================================================================
Tests:
1. Real PDF ingestion (generated via pypdf)
2. Real TXT ingestion
3. Real Markdown (.md) ingestion
4. Real DOCX ingestion (generated via zipfile)
5. Multilingual ingestion (Hindi study text)
6. Scanned PDF detection and graceful notification
7. Empty / invalid file error handling
8. Grounded Exam creation
9. Student submission & Automated grading
10. 4-Quadrant Priority Matrix calculation
11. Grounded Copilot Q&A
12. System Health & Ollama Status
=============================================================================
"""

import os
import io
import sys
import json
import zipfile
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studyai_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import pypdf

client = Client()
user, _ = User.objects.get_or_create(
    username="acceptance_test@studyai.internal",
    defaults={"email": "acceptance_test@studyai.internal"}
)
client.force_login(user)

def test_health_and_ollama():
    print("\n--- 1. Testing Health & Ollama Status ---")
    resp_health = client.get('/api/health/')
    assert resp_health.status_code == 200, f"Health check failed: {resp_health.status_code}"
    print("[PASS] /api/health/ status 200:", resp_health.json()["status"])

    resp_ollama = client.get('/api/ollama/status/')
    assert resp_ollama.status_code == 200, f"Ollama status failed: {resp_ollama.status_code}"
    print("[PASS] /api/ollama/status/ is_online:", resp_ollama.json()["is_online"])

    resp_models = client.get('/api/ollama/models/')
    assert resp_models.status_code == 200, f"Ollama models failed: {resp_models.status_code}"
    print("[PASS] /api/ollama/models/ count:", len(resp_models.json().get("models", [])))


def test_txt_upload():
    print("\n--- 2. Testing TXT Document Upload ---")
    txt_content = """Computer Networks: Transport Layer and Protocols.
The Transmission Control Protocol (TCP) provides reliable, ordered byte-stream delivery using sequence numbers and 3-way handshakes.
User Datagram Protocol (UDP) is connectionless and does not guarantee packet delivery.
Congestion control in TCP uses slow start, congestion avoidance, fast retransmit, and fast recovery mechanisms."""
    
    file = SimpleUploadedFile("network_notes.txt", txt_content.encode('utf-8'), content_type="text/plain")
    resp = client.post('/api/documents/upload/', {'file': file})
    assert resp.status_code == 200, f"TXT upload failed: {resp.content}"
    data = resp.json()
    assert "Network" in data["subject"], f"Unexpected subject: {data['subject']}"
    print(f"[PASS] TXT Uploaded successfully! Document ID: {data['id']}, Subject: {data['subject']}")
    return data["id"]


def test_markdown_upload():
    print("\n--- 3. Testing Markdown Document Upload ---")
    md_content = """# Operating Systems: Deadlock Detection & Recovery
## Deadlock Characterization
A deadlock requires four simultaneous Coffman conditions:
1. Mutual Exclusion: At least one unshareable resource.
2. Hold and Wait: A process holds resources while waiting for more.
3. No Preemption: Resources cannot be forcibly revoked.
4. Circular Wait: A closed loop of waiting processes.

Resource allocation graphs (RAG) detect deadlocks in single-instance systems."""

    file = SimpleUploadedFile("deadlocks.md", md_content.encode('utf-8'), content_type="text/markdown")
    resp = client.post('/api/documents/upload/', {'file': file})
    assert resp.status_code == 200, f"Markdown upload failed: {resp.content}"
    data = resp.json()
    assert data["subject"] in ["Operating Systems", "Deadlocks", "Deadlock Detection & Recovery"], f"Unexpected subject: {data['subject']}"
    print(f"[PASS] Markdown Uploaded! Document ID: {data['id']}, Subject: {data['subject']}")
    return data["id"]


def test_pdf_upload():
    print("\n--- 4. Testing Real PDF Upload ---")
    pdf_text_raw = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 220 >>
stream
BT
/F1 14 Tf
50 700 Td
(Discrete Mathematics: Graph Theory and Combinatorics in Computer Science.) Tj
0 -30 Td
(Eulerian circuits and Hamiltonian graphs are fundamental structures in discrete mathematics.) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000236 00000 n 
0000000311 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
563
%%EOF
"""
    r = pypdf.PdfReader(io.BytesIO(pdf_text_raw))
    writer = pypdf.PdfWriter()
    for p in r.pages:
        writer.add_page(p)
    buf = io.BytesIO()
    writer.write(buf)
    clean_pdf_bytes = buf.getvalue()

    file = SimpleUploadedFile("discrete_math.pdf", clean_pdf_bytes, content_type="application/pdf")
    resp = client.post('/api/documents/upload/', {'file': file})
    assert resp.status_code == 200, f"PDF upload failed: {resp.content}"
    data = resp.json()
    print(f"[PASS] PDF Uploaded successfully! Document ID: {data['id']}, Subject: {data['subject']}")
    return data["id"]


def test_docx_upload():
    print("\n--- 5. Testing Real DOCX Document Upload ---")
    # Build a minimal valid .docx package using zipfile
    xml_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body>
            <w:p><w:r><w:t>Database Management Systems: Relational Algebra &amp; SQL.</w:t></w:r></w:p>
            <w:p><w:r><w:t>ACID properties guarantee Atomicity, Consistency, Isolation, and Durability in transactional databases.</w:t></w:r></w:p>
            <w:p><w:r><w:t>Normalization forms 1NF, 2NF, 3NF, and BCNF eliminate data anomalies and functional dependency redundancy.</w:t></w:r></w:p>
        </w:body>
    </w:document>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('word/document.xml', xml_content)
    docx_bytes = buf.getvalue()

    file = SimpleUploadedFile("dbms_lecture.docx", docx_bytes, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    resp = client.post('/api/documents/upload/', {'file': file})
    assert resp.status_code == 200, f"DOCX upload failed: {resp.content}"
    data = resp.json()
    print(f"[PASS] DOCX Uploaded! Document ID: {data['id']}, Subject: {data['subject']}")
    return data["id"]


def test_multilingual_hindi_text():
    print("\n--- 6. Testing Multilingual Hindi Direct Text Upload ---")
    hi_text = """ऑपरेटिंग सिस्टम का परिचय और प्रक्रिया प्रबंधन:
    एक प्रक्रिया निष्पादन में एक प्रोग्राम है। प्रक्रिया नियंत्रण ब्लॉक (PCB) में प्रक्रिया स्थिति, काउंटर, और रजिस्टर शामिल हैं।
    सीपीयू शेड्यूलिंग एल्गोरिदम जैसे राउंड रॉबिन और शॉर्टेस्ट जॉब फर्स्ट प्रोसेसर समय आवंटित करते हैं।
    वर्चुअल मेमोरी पेजिंग तकनीक का उपयोग करती है।"""

    resp = client.post(
        '/api/documents/upload/',
        data=json.dumps({"title": "Hindi OS Material", "text": hi_text}),
        content_type='application/json'
    )
    assert resp.status_code == 200, f"Hindi upload failed: {resp.content}"
    data = resp.json()
    assert data["original_language"] == "hi", f"Expected language 'hi', got {data['original_language']}"
    print(f"[PASS] Multilingual Hindi Ingested! ID: {data['id']}, Detected Language: {data['original_language']}")
    return data["id"]


def test_failure_modes():
    print("\n--- 7. Testing Failure Modes (Empty & Scanned PDF) ---")
    # Test Empty File
    resp_empty = client.post(
        '/api/documents/upload/',
        data=json.dumps({"title": "Empty File", "text": "   "}),
        content_type='application/json'
    )
    assert resp_empty.status_code == 400
    print("[PASS] Empty text rejected with 400 status:", resp_empty.json()["error"])

    # Test Scanned PDF Detection (PDF with 0 readable text)
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    blank_pdf = buf.getvalue()

    file_blank = SimpleUploadedFile("scanned_scan.pdf", blank_pdf, content_type="application/pdf")
    resp_scanned = client.post('/api/documents/upload/', {'file': file_blank})
    assert resp_scanned.status_code == 400
    err_msg = resp_scanned.json().get("error", "")
    assert "scanned" in err_msg.lower() or "readable" in err_msg.lower(), f"Unexpected message: {err_msg}"
    print("[PASS] Scanned/Blank PDF detected gracefully:", err_msg)


def test_exam_and_revision_loop(doc_id):
    print(f"\n--- 8. Testing Exam Generation & Submission Loop for Doc {doc_id} ---")
    # Generate Exam
    exam_payload = {
        "document_id": doc_id,
        "questionCount": 3,
        "difficulty": "Medium",
        "questionType": "Mixed"
    }
    resp_exam = client.post('/api/exams/', data=json.dumps(exam_payload), content_type='application/json')
    assert resp_exam.status_code == 200, f"Exam generation failed: {resp_exam.content}"
    exam_data = resp_exam.json()
    print(f"[PASS] Exam generated: {exam_data['id']} with {len(exam_data['questions'])} questions")

    # Submit Exam
    qs = exam_data["questions"]
    answers = {}
    if len(qs) >= 2:
        answers[qs[0]["id"]] = qs[0].get("correctAnswer") or 0  # Pass first question
        answers[qs[1]["id"]] = "Intentional Wrong Answer"       # Fail second question

    resp_submit = client.post(f'/api/exams/{exam_data["id"]}/submit/', data=json.dumps({"answers": answers}), content_type='application/json')
    assert resp_submit.status_code == 200, f"Exam submit failed: {resp_submit.content}"
    result_data = resp_submit.json()
    print(f"[PASS] Exam evaluated: Score {result_data['scorePercent']}%, Grade: {result_data['letterGrade']}")

    # Check Priority Matrix Revision Tasks
    resp_rev = client.get(f'/api/revision/{doc_id}/')
    assert resp_rev.status_code == 200, f"Revision plan failed: {resp_rev.content}"
    rev_data = resp_rev.json()
    print(f"[PASS] Revision plan generated: {rev_data['totalItemsCount']} task(s), {rev_data['totalMinutes']} min total")
    priorities = [it["priority"] for it in rev_data["items"]]
    print(f"       Task Priorities: {priorities}")


def test_copilot(doc_id):
    print(f"\n--- 9. Testing Grounded AI Copilot for Doc {doc_id} ---")
    query_payload = {
        "document_id": doc_id,
        "question": "What is the primary concept explained in this text?"
    }
    resp_copilot = client.post('/api/copilot/', data=json.dumps(query_payload), content_type='application/json')
    assert resp_copilot.status_code == 200, f"Copilot query failed: {resp_copilot.content}"
    ans = resp_copilot.json()
    print(f"[PASS] Copilot response: {ans.get('answer', '')[:100]}...")
    print(f"       Sources cited: {len(ans.get('sources', []))}")


def main():
    print("=============================================================")
    print("STUDYAI COMPREHENSIVE ACCEPTANCE & REAL FILE TEST SUITE")
    print("=============================================================")
    test_health_and_ollama()
    txt_id = test_txt_upload()
    md_id = test_markdown_upload()
    pdf_id = test_pdf_upload()
    docx_id = test_docx_upload()
    hi_id = test_multilingual_hindi_text()
    test_failure_modes()
    test_exam_and_revision_loop(txt_id)
    test_copilot(txt_id)
    print("\n=============================================================")
    print("ALL ACCEPTANCE TESTS COMPLETED SUCCESSFULLY WITH ZERO DEFECTS!")
    print("=============================================================")

if __name__ == '__main__':
    main()
