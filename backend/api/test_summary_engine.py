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
    destack_vertical_text,
    normalize_academic_math_and_ocr,
    _is_valid_mathematical_formula,
    derive_formula_metadata,
    _synthesize_grounded_markdown_explanation,
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

    def test_pedagogical_card_does_not_invent_missing_evidence(self):
        card = format_pedagogical_concept(
            "Pumping Lemma",
            "The source describes CPU scheduling and ready queues.",
            subject="Operating Systems"
        )
        self.assertIn("No explanation", card["intuition"])
        self.assertEqual(card["level_3_formal"], "Not stated in the provided source.")
        self.assertIn("No worked example", card["example"])
        self.assertIn("No misconception", card["common_mistake"])
        self.assertIn("not assessed", card["exam_point"])

    def test_grounded_mermaid_diagram_generation(self):
        diagram = generate_grounded_mermaid_diagram("CPU Scheduling Execution Flow", SAMPLE_OS_TEXT, "flowchart")
        self.assertIsNotNone(diagram)
        self.assertIn("flowchart", diagram["code"])
        self.assertEqual(diagram["type"], "flowchart")
        self.assertTrue("-->" in diagram["code"])

    def test_diagram_generation_requires_explicit_source_steps(self):
        self.assertIsNone(
            generate_grounded_mermaid_diagram(
                "Section 4.4",
                "This passage describes a concept but contains no numbered workflow."
            )
        )

    def test_formula_metadata_does_not_infer_domain_facts(self):
        sentence = "The source gives CPU Utilization = (Busy Time / Total Time) * 100%."
        name, explanation = derive_formula_metadata(
            "CPU Utilization = (Busy Time / Total Time) * 100%",
            sentence,
            "Computer Networks"
        )
        self.assertEqual(name, "Formula from source")
        self.assertEqual(explanation, sentence)
        self.assertNotIn("Stop-and-Wait", explanation)

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
            self.assertIn("Detected section order", guide["big_picture"])
            self.assertNotIn("OSI and TCP/IP", guide["big_picture"])
            self.assertFalse(any(
                "Transmission Delay" in example.get("title", "")
                for example in guide["examples"]
            ))
            self.assertEqual(guide["exam_insights"], [])

    def test_quality_validation_audit(self):
        struct = detect_document_structure(SAMPLE_OS_TEXT)
        guide = synthesize_study_guide(SAMPLE_OS_TEXT, title="OS CPU Scheduling", total_pages=3, mode="standard")
        report = validate_summary_quality(SAMPLE_OS_TEXT, guide, struct)
        self.assertIn("coverage_score", report)
        self.assertIn("concept_coverage", report)
        self.assertIn("formula_coverage", report)
        self.assertIn("quality_level", report)
        self.assertGreaterEqual(report["coverage_score"], 0.80)
        self.assertEqual(report["metric_scope"], "heuristic_source_feature_overlap_not_fact_check")

        low_coverage = validate_summary_quality(SAMPLE_OS_TEXT, {"response": "unrelated text"}, struct)
        self.assertLess(low_coverage["coverage_score"], 0.85)

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

    def test_api_recalculates_legacy_cached_coverage_score(self):
        doc = Document.objects.create(
            user=self.user,
            title="CPU Scheduling Notes",
            subject="Computer Science",
            page_count=2,
            raw_text=SAMPLE_OS_TEXT,
            status="READY"
        )
        doc.set_summary({
            "modes": {
                "standard": {
                    "response": "Unrelated cached text.",
                    "sections": [{"id": "legacy", "title": "Unrelated", "pages": [], "narrative": "No source coverage."}],
                    "quality_report": {"coverage_score": 0.95}
                }
            }
        })
        doc.save(update_fields=["summary_json"])

        response = self.client.get(f"/api/documents/{doc.id}/summary/?mode=standard")

        self.assertEqual(response.status_code, 200)
        quality = response.json()["quality_report"]
        self.assertLess(quality["coverage_score"], 0.85)
        self.assertEqual(quality["metric_scope"], "heuristic_source_feature_overlap_not_fact_check")

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

    def test_destack_vertical_text(self):
        stacked = "T\nh\ne\n \nr\ne\nv\ne\nr\ns\na\nl\n \no\nf\n \na\n \nl\na\nn\ng\nu\na\ng\ne\n \nL"
        destacked = destack_vertical_text(stacked)
        self.assertIn("The reversal of a language L", destacked)

        # Single characters without spaces
        single_chars = "T\nh\ne\nr\ne\nv\ne\nr\ns\na\nl"
        destacked_single = destack_vertical_text(single_chars)
        self.assertEqual(destacked_single, "Thereversal")

    def test_normalize_academic_math_and_ocr(self):
        # OCR asterisk variable wraps
        raw_ocr = "*h*(*a*)=01*andh*(*b*)=10"
        normalized = normalize_academic_math_and_ocr(raw_ocr)
        self.assertEqual(normalized, "h(a)=01 and h(b)=10")

        # Corrupted sequence notation
        corrupted_seq = "w=aja2---dn and a;a2--+d@"
        norm_seq = normalize_academic_math_and_ocr(corrupted_seq)
        self.assertIn("a_1 a_2 \\dots a_n", norm_seq)

    def test_is_valid_mathematical_formula(self):
        # Valid mathematical formulas
        self.assertTrue(_is_valid_mathematical_formula("CPU Utilization = (Busy Time / Total Time) * 100%"))
        self.assertTrue(_is_valid_mathematical_formula("R* = \\cup R^i"))
        self.assertTrue(_is_valid_mathematical_formula("L(R+S) = L(R) \\cup L(S)"))

        # Invalid OCR noise / corrupted text
        self.assertFalse(_is_valid_mathematical_formula("w=aja2---dn"))
        self.assertFalse(_is_valid_mathematical_formula("a;a2--+d@"))
        self.assertFalse(_is_valid_mathematical_formula("The reversal of a regular language L is regular."))
        self.assertFalse(_is_valid_mathematical_formula(""))

    def test_no_synthetic_formula_intro_in_markdown(self):
        struct = detect_document_structure(SAMPLE_OS_TEXT)
        guide = synthesize_study_guide(SAMPLE_OS_TEXT, title="CPU Scheduling", total_pages=2, mode="standard")
        markdown = _synthesize_grounded_markdown_explanation(struct, guide, mode="standard")
        
        # Verify no synthetic introductory phrases exist
        self.assertNotIn("The mathematical formulation for mathematical formulation", markdown)
        self.assertNotIn("The mathematical formulation for", markdown)

        # Verify no legacy category cards exist
        legacy_cards = [
            "Core Theoretical Concepts & Architecture",
            "Document Definitions & Terminology",
            "High-Yield Formulas",
            "Exam Traps & Critical Takeaways",
            "Quick Revision Checklist"
        ]
        for card in legacy_cards:
            self.assertNotIn(card, markdown)

    def test_algorithms_and_worked_examples_integrated_in_markdown(self):
        """Verifies that algorithms with operational breakdowns and worked examples with step-by-step derivations appear in the markdown."""
        text = """
CHAPTER 3: AUTOMATA AND REGULAR EXPRESSIONS

Section 3.1: Thompson's Construction Algorithm
Thompson's construction algorithm converts any regular expression into an equivalent non-deterministic finite automaton with epsilon transitions.
Step 1: For the base cases, construct primitive automata for empty set, epsilon, and single alphabet symbols.
Step 2: For regular expression union R + S, create a new start state with epsilon transitions to the start states of R and S.
Step 3: For concatenation RS, connect the accepting state of R to the start state of S.
Step 4: For Kleene closure R*, add epsilon loops allowing repetition and zero occurrences.
Result: An equivalent NFA with at most 2 * |R| states and O(|R|) transitions.

Section 3.2: Pumping Lemma for Regular Languages
Theorem 3.1: The Pumping Lemma states that for any regular language L, there exists a constant p such that any string w in L with length at least p can be divided into three parts w = xyz satisfying |y| > 0, |xy| <= p, and xy^i z is in L for all i >= 0.
Proof: By the pigeonhole principle, any DFA with p states processing a string of length at least p must visit at least one state twice.

Worked Example 3.1: Proving that L = {0^n 1^n | n >= 0} is not regular.
Problem: Show that the language of balanced zeros and ones cannot be recognized by any finite automaton.
Step 1: Assume for contradiction that L is regular. Let p be the pumping length.
Step 2: Select the string w = 0^p 1^p in L with |w| = 2p >= p.
Step 3: Decompose w = xyz. Since |xy| <= p, y must consist solely of zeros (y = 0^k, k >= 1).
Step 4: Pump with i = 2: w' = xy^2 z = 0^(p+k) 1^p.
Result: The pumped string contains strictly more zeros than ones, so w' is not in L, contradicting the pumping lemma.
"""
        struct = detect_document_structure(text)
        guide = synthesize_study_guide(text, title="Automata and Regular Expressions", total_pages=5, mode="detailed")
        md = guide.get("markdown_content") or guide.get("response") or ""

        # Assert Algorithm is rendered
        self.assertIn("Algorithm: Thompson's Construction", md)
        self.assertIn("Operational Breakdown:", md)
        self.assertIn("Step 1:", md)

        # Assert Theorem is rendered with proof
        self.assertIn("Theorem:", md)
        self.assertIn("Formal Statement:", md)
        self.assertIn("Proof Reasoning & Conditions:", md)

        # Assert Worked Example is rendered with step-by-step derivation
        self.assertIn("Worked Example:", md)
        self.assertIn("Step-by-Step Derivation:", md)
        self.assertIn("Result:", md)

    def test_summary_mode_normalization(self):
        """Verifies natural language query intent normalization to canonical modes."""
        from .summary_engine import normalize_summary_mode
        self.assertEqual(normalize_summary_mode("summarize this pdf"), "standard")
        self.assertEqual(normalize_summary_mode("give me complete notes"), "deep_study")
        self.assertEqual(normalize_summary_mode("explain this pdf"), "detailed")
        self.assertEqual(normalize_summary_mode("quick revision"), "quick_revision")
        self.assertEqual(normalize_summary_mode("explain for gate"), "exam_prep")
        self.assertEqual(normalize_summary_mode("explain simply"), "beginner")

    def test_audit_markdown_cleanliness(self):
        """Verifies that audit_markdown_for_corruption passes on properly formatted study notes."""
        from .diagnostics import audit_markdown_for_corruption
        clean_markdown = """
# Regular Expressions and Languages

Regular expressions provide a formal algebraic foundation for defining regular languages.

## Regular Expressions
A **regular expression** is a declarative notation for describing token patterns.

$$
L(R^*) = (L(R))^*
$$

### Algorithm: Thompson's Construction
**Operational Breakdown:**
1. Base cases for epsilon and symbols.
2. Union construction.
"""
        result = audit_markdown_for_corruption(clean_markdown)
        self.assertTrue(result["is_clean"])
        self.assertEqual(result["issues_count"], 0)


