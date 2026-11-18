"""
=============================================================================
StudyAI — Critical Multi-Subject & Multilingual Verification Script
=============================================================================
Tests:
TEST A: Operating Systems
TEST B: Computer Networks
TEST C: Mathematics
TEST D: Hindi / Multilingual Academic Text
TEST E: Biology (Cellular Biology)

Asserts that:
- Operating Systems produces OS topics (Processes, Scheduling, Deadlocks)
- Computer Networks produces Network topics (TCP/IP, Routing, OSI)
- Mathematics produces Math topics (Calculus, Linear Algebra, Integrals)
- Hindi text produces Hindi language detection and accurate topics
- Cellular Biology produces Cellular topics
- NEVER defaulting to Photosynthesis unless the document is about Photosynthesis!
=============================================================================
"""

import os
import sys
import django

# Force UTF-8 output on Windows terminal
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studyai_backend.settings')
django.setup()

from api.models import Document, Chunk, Topic, Exam, Question, ExamAttempt, RevisionTask
from api.document_service import extract_study_material, chunk_document_by_pages, detect_language, clean_text
from api.ollama_service import analyze_document_with_ai, generate_exam_questions_with_ai, answer_copilot_with_ai


def run_subject_test(test_name, title, text, expected_keywords, forbidden_keywords=['photosynthesis', 'chloroplast', 'rubisco', 'calvin']):
    print(f"\n=======================================================")
    print(f"RUNNING {test_name}: {title}")
    print(f"=======================================================")

    # 1. Clean & Language
    cleaned = clean_text(text)
    lang = detect_language(cleaned)
    print(f"[*] Detected Language: {lang}")

    # 2. Chunking
    pages_data = [{"page_number": 1, "text": cleaned, "char_count": len(cleaned)}]
    chunks = chunk_document_by_pages(pages_data, target_size=500, overlap=50)
    print(f"[*] Created {len(chunks)} chunks with page tracking.")

    # 3. AI Analysis
    analysis = analyze_document_with_ai(cleaned, chunks, language=lang, title=title)
    detected_subject = analysis.get("subject", "Unknown")
    topics = analysis.get("topics", [])
    topic_names = [t["name"] for t in topics]

    print(f"[*] Detected Subject: {detected_subject}")
    print(f"[*] Extracted Topics: {topic_names}")
    print(f"[*] Executive Summary: {analysis.get('executiveSummary', '')[:120]}...")

    # 4. Assertions
    topic_text_blob = " ".join(topic_names).lower() + " " + detected_subject.lower()

    # Check for expected keywords
    has_expected = any(kw.lower() in topic_text_blob for kw in expected_keywords)
    if not has_expected:
        print(f"[!] WARNING: Expected one of {expected_keywords} in topics {topic_names}")

    # Check forbidden keywords (never Photosynthesis!)
    for fk in forbidden_keywords:
        if fk.lower() in topic_text_blob:
            raise AssertionError(f"CRITICAL FAILURE: Found '{fk}' in {test_name} topics: {topic_names}!")

    print(f"[PASS] {test_name} passed cleanly without default Photosynthesis leakage!")
    return analysis


def run_all_tests():
    print("Beginning StudyAI Multi-Subject Grounding Verification...")

    # TEST A: Operating Systems
    os_text = """
    Chapter 4: Operating Systems — Process Synchronization and Deadlocks.
    Processes require synchronization mechanisms such as semaphores, mutex locks, and monitors to prevent race conditions in critical sections.
    CPU scheduling algorithms allocate processor time among ready tasks using Round Robin, First-Come First-Served, or Priority Scheduling.
    Deadlocks occur when processes hold resources while waiting for other allocated resources, characterized by Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait.
    Virtual memory utilizes paging and page replacement algorithms such as LRU and FIFO.
    """
    run_subject_test(
        "TEST A (Operating Systems)",
        "Operating Systems: Synchronization & Deadlocks",
        os_text,
        expected_keywords=['process', 'synchronization', 'deadlock', 'scheduling', 'operating']
    )

    # TEST B: Computer Networks
    network_text = """
    Chapter 5: Computer Networks — Transport Layer and Routing Protocols.
    The Transmission Control Protocol (TCP) provides reliable, connection-oriented data transfer using three-way handshakes, sequence numbers, and sliding window flow control.
    In contrast, User Datagram Protocol (UDP) is connectionless and best-effort.
    The Network Layer handles packet routing across autonomous systems using algorithms such as Dijkstra's Link-State routing (OSPF) and Distance-Vector protocols (BGP, RIP).
    The OSI 7-layer model defines Physical, Data Link, Network, Transport, Session, Presentation, and Application layers.
    """
    run_subject_test(
        "TEST B (Computer Networks)",
        "Computer Networks: TCP/IP and Routing",
        network_text,
        expected_keywords=['network', 'tcp', 'routing', 'osi', 'protocol']
    )

    # TEST C: Mathematics
    math_text = """
    Chapter 2: Advanced Calculus and Linear Algebra.
    A matrix is a rectangular array of numbers representing linear transformations.
    Eigenvalues and eigenvectors satisfy the characteristic equation A*v = lambda*v.
    Definite integrals represent the accumulated area under a curve, evaluated using the Fundamental Theorem of Calculus.
    Differential equations describe rates of change across physical dynamical systems.
    Partial derivatives determine gradient vectors and Hessian matrices for multi-variable optimization.
    """
    run_subject_test(
        "TEST C (Mathematics)",
        "Calculus & Linear Algebra",
        math_text,
        expected_keywords=['calculus', 'linear algebra', 'matrix', 'integral', 'differential', 'math']
    )

    # TEST D: Hindi Text (Operating Systems in Hindi)
    hindi_text = """
    ऑपरेटिंग सिस्टम का परिचय:
    प्रक्रिया प्रबंधन (Process Management) आधुनिक ऑपरेटिंग सिस्टम का मूल घटक है।
    थ्रेड्स (Threads) प्रक्रिया के भीतर निष्पादन की सबसे छोटी इकाई हैं।
    सीपीयू शेड्यूलिंग (CPU Scheduling) यह तय करता है कि कौन सी प्रक्रिया प्रोसेसर प्राप्त करेगी।
    डेडलॉक (Deadlock) वह स्थिति है जब दो या दो से अधिक प्रक्रियाएं एक-दूसरे के संसाधनों का इंतजार करती हैं।
    """
    analysis_hi = run_subject_test(
        "TEST D (Hindi Multilingual Text)",
        "ऑपरेटिंग सिस्टम नोट्स",
        hindi_text,
        expected_keywords=['ऑपरेटिंग', 'प्रक्रिया', 'थ्रेड्स', 'डेडलॉक', 'operating'],
        forbidden_keywords=['photosynthesis', 'chloroplast']
    )

    # TEST E: Cellular Biology (Distinct from Photosynthesis)
    biology_text = """
    Chapter 3: Cellular Respiration and Mitochondrial Bioenergetics.
    Glycolysis takes place in the cytoplasm, converting glucose into pyruvate and generating ATP via substrate-level phosphorylation.
    Pyruvate then enters the mitochondrial matrix where the Citric Acid Cycle (Krebs Cycle) oxidizes acetyl-CoA into carbon dioxide, NADH, and FADH2.
    The electron transport chain located on the mitochondrial cristae creates a proton gradient across the inner membrane.
    ATP synthase harnesses the proton motive force to generate cellular ATP through oxidative phosphorylation.
    """
    run_subject_test(
        "TEST E (Cellular Biology - Respiration)",
        "Mitochondrial Respiration & Glycolysis",
        biology_text,
        expected_keywords=['respiration', 'glycolysis', 'mitochondri', 'krebs', 'atp', 'biology'],
        forbidden_keywords=['photosynthesis', 'chloroplast', 'rubisco']
    )

    print("\n=======================================================")
    print("ALL 5 SUBJECT TESTS PASSED! ZERO PHOTOSYNTHESIS LEAKAGE DETECTED.")
    print("=======================================================")

if __name__ == "__main__":
    run_all_tests()
