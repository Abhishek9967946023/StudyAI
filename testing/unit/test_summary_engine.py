"""
=============================================================================
StudyAI — Comprehensive Test Suite for AI Summary & Study Notes Engine
=============================================================================
Tests:
1. Document Structure Detection (Headings, Formulas, Definitions, Comparisons, Workflows)
2. Structure-Aware Semantic Chunking with Metadata Grounding
3. Pedagogical Concept Formatting (6 Fields)
4. Content-Aware Grounded Mermaid Diagram Generation
5. 5-Mode Multi-Stage Hierarchical Synthesis
6. Quality Coverage Validation Audit
7. Targeted Single-Section Re-Synthesis
8. API Endpoints (GET summary with mode, POST regenerate, GET status/visuals/sections)
=============================================================================
"""

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Document, Chunk
from .summary_engine import (
    detect_document_structure,
    chunk_document_semantically,
    format_pedagogical_concept,
    generate_grounded_mermaid_diagram,
    synthesize_study_guide,
    validate_summary_quality,
    regenerate_single_section,
    SUMMARY_MODES
)

SAMPLE_OS_TEXT = """
CHAPTER 1: CPU SCHEDULING ALGORITHMS

Section 1.1: Foundations of Multiprogramming
CPU scheduling is the basis of multiprogrammed operating systems. By switching the CPU among processes, the operating system can make the computer more productive.
A process is defined as an instance of a program in execution containing the program counter, stack, and data section.
The CPU scheduler selects from among the processes in ready queue and allocates a CPU core to one of them.

Turnaround time is defined as the interval from the time of submission of a process to the time of completion.
Waiting time is the sum of periods spent waiting in the ready queue.
CPU Utilization = (Busy Time / Total Time) * 100%
Average Waiting Time = (Total Waiting Time / Total Processes)

Section 1.2: First-Come First-Served Scheduling
In FCFS scheduling, the process that requests the CPU first is allocated the CPU first.
Step 1: Process enters the ready queue and is linked to the tail.
Step 2: CPU scheduler picks the process from the head of the queue.
Step 3: Process executes until completion or I/O request.
Result: Simple implementation using a FIFO queue, but suffers from the Convoy Effect.
For example, consider processes P1 (burst 24ms), P2 (burst 3ms), and P3 (burst 3ms). If they arrive in order P1, P2, P3, the average waiting time is 17ms.

Section 1.3: Shortest-Job-First versus Round-Robin Scheduling
Unlike Shortest-Job-First which minimizes average waiting time but requires predicting future CPU bursts, Round-Robin uses a fixed time quantum to provide fair interactive response times.
Shortest-Job-First is optimal because it gives the minimum average waiting time for a given set of processes.
Round-Robin scheduling is designed especially for timesharing systems.
"""

class SummaryEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='summary_tester', password='TestPassword123!', email='tester@studyai.io')
        self.client = Client()
        self.client.login(username='summary_tester', password='TestPassword123!')

    def test_summary_modes_defined(self):
        self.assertEqual(len(SUMMARY_MODES), 5)
        self.assertIn('quick_revision', SUMMARY_MODES)
        self.assertIn('standard', SUMMARY_MODES)
        self.assertIn('detailed', SUMMARY_MODES)
        self.assertIn('deep_study', SUMMARY_MODES)
        self.assertIn('exam_prep', SUMMARY_MODES)

    def test_document_structure_detection(self):
        struct = detect_document_structure(SAMPLE_OS_TEXT)
        self.assertGreater(len(struct.sections), 0)
        self.assertTrue(any("CPU SCHEDULING" in s["title"].upper() or "FOUNDATIONS" in s["title"].upper() for s in struct.sections))
        self.assertGreater(len(struct.global_definitions), 0)
        self.assertGreater(len(struct.global_formulas), 0)
        self.assertTrue(any("Turnaround time" in d["term"] or "process" in d["term"].lower() for d in struct.global_definitions))
        self.assertTrue(any("CPU Utilization" in f["formula"] or "Waiting Time" in f["formula"] for f in struct.global_formulas))

    def test_semantic_chunking_metadata(self):
        struct = detect_document_structure(SAMPLE_OS_TEXT)
        chunks = chunk_document_semantically(struct, doc_id="test-doc-1", max_chunk_words=150, overlap_words=25)
        self.assertGreater(len(chunks), 0)
        first_chunk = chunks[0]
        self.assertIn("chunk_id", first_chunk)
        self.assertEqual(first_chunk["doc_id"], "test-doc-1")
        self.assertIn("heading", first_chunk)
        self.assertIn("page_start", first_chunk)
        self.assertIn("page_end", first_chunk)
        self.assertIn("text", first_chunk)

    def test_pedagogical_concept_card_formatting(self):
        card = format_pedagogical_concept("CPU Scheduling", SAMPLE_OS_TEXT, source_page=1, subject="Operating Systems")
        self.assertEqual(card["term"], "CPU Scheduling")
        self.assertTrue(len(card["intuition"]) > 0)
        self.assertTrue(len(card["in_depth"]) > 0)
        self.assertTrue(len(card["why_it_matters"]) > 0)
        self.assertTrue(len(card["common_mistake"]) > 0)
        self.assertTrue(len(card["exam_point"]) > 0)

    def test_grounded_mermaid_diagram_generation(self):
        diagram = generate_grounded_mermaid_diagram("CPU Scheduling Execution Flow", SAMPLE_OS_TEXT, "flowchart")
        self.assertIsNotNone(diagram)
        self.assertIn("flowchart", diagram["code"])
        self.assertEqual(diagram["type"], "flowchart")
        self.assertTrue("-->" in diagram["code"])

    def test_all_five_modes_synthesis(self):
        for mode in SUMMARY_MODES:
            guide = synthesize_study_guide(
                raw_text=SAMPLE_OS_TEXT,
                title="OS CPU Scheduling",
                total_pages=3,
                mode=mode
            )
            self.assertEqual(guide["mode"], mode)
            self.assertGreater(len(guide["sections"]), 0)
            self.assertIn("executiveSummary", guide)
            self.assertIn("quality_report", guide)
            self.assertGreaterEqual(guide["quality_report"]["coverage_score"], 0.70)

    def test_quality_validation_audit(self):
        struct = detect_document_structure(SAMPLE_OS_TEXT)
        guide = synthesize_study_guide(SAMPLE_OS_TEXT, title="OS CPU Scheduling", total_pages=3, mode="standard")
        report = validate_summary_quality(SAMPLE_OS_TEXT, guide, struct)
        self.assertIn("coverage_score", report)
        self.assertIn("concept_coverage", report)
        self.assertIn("formula_coverage", report)
        self.assertIn("quality_level", report)
        self.assertGreaterEqual(report["coverage_score"], 0.80)

    def test_targeted_single_section_regeneration(self):
        new_sec = regenerate_single_section(
            doc_id="test-doc-1",
            section_id="sec-1",
            section_title="First-Come First-Served Scheduling",
            source_text="FCFS scheduling is FIFO. It suffers from the convoy effect.",
            mode="detailed"
        )
        self.assertEqual(new_sec["id"], "sec-1")
        self.assertEqual(new_sec["title"], "First-Come First-Served Scheduling")
        self.assertTrue(len(new_sec["narrative"]) > 0)

    def test_api_summary_endpoints(self):
        # Create a document for user
        doc = Document.objects.create(
            user=self.user,
            title="CPU Scheduling Notes",
            subject="Computer Science",
            page_count=2,
            raw_text=SAMPLE_OS_TEXT,
            status='READY'
        )

        # 1. GET Summary default mode
        resp = self.client.get(f'/api/documents/{doc.id}/summary/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["active_mode"], "standard")
        self.assertIn("sections", data)
        self.assertIn("study_guide", data)
        self.assertIn("quality_report", data)

        # 2. GET Summary with specific mode
        resp_exam = self.client.get(f'/api/documents/{doc.id}/summary/?mode=exam_prep')
        self.assertEqual(resp_exam.status_code, 200)
        data_exam = resp_exam.json()
        self.assertEqual(data_exam["active_mode"], "exam_prep")

        # 3. GET Summary status
        resp_status = self.client.get(f'/api/documents/{doc.id}/summary/status/')
        self.assertEqual(resp_status.status_code, 200)
        status_data = resp_status.json()
        self.assertIn("coverage_score", status_data)
        self.assertIn("available_modes", status_data)

        # 4. GET Summary sections outline
        resp_sections = self.client.get(f'/api/documents/{doc.id}/summary/sections/')
        self.assertEqual(resp_sections.status_code, 200)
        sec_data = resp_sections.json()
        self.assertIn("sections", sec_data)

        # 5. GET Summary visuals
        resp_visuals = self.client.get(f'/api/documents/{doc.id}/summary/visuals/')
        self.assertEqual(resp_visuals.status_code, 200)

        # 6. POST Summary targeted section regeneration
        first_sec_id = data["study_guide"]["sections"][0]["id"]
        resp_regen = self.client.post(
            f'/api/documents/{doc.id}/summary/regenerate/',
            data=json.dumps({"mode": "standard", "section_id": first_sec_id}),
            content_type='application/json'
        )
        self.assertEqual(resp_regen.status_code, 200)
        regen_data = resp_regen.json()
        self.assertEqual(regen_data["status"], "success")
        self.assertEqual(regen_data["section"]["id"], first_sec_id)
