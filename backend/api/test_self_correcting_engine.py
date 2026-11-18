import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Document, Chunk
from .academic_ir import (
    AcademicDocumentIR,
    AcademicSectionIR,
    AcademicElementIR,
    AcademicElementType,
    GroundingType
)
from .typography_system import DocumentTypography
from .self_correcting_engine import (
    TopicInventorySpec,
    TopicCompletenessEngine,
    InformationDensityController,
    SemanticCompressionEngine,
    RepetitionAndConflictDetector,
    TechnicalExplanationVerifier,
    NumericalSolutionAuditor,
    StructureConsistencyEngine,
    DocumentConsistencyAuditor,
    SelfRepairEngine,
    HonestQualityDashboard
)


class TestAcademicElementIRBlockIdentity(TestCase):
    """
    Validates Requirement 1: Source-Aware Content Block Tracking,
    canonical 17 block types, and accidental content loss detection.
    """

    def test_canonical_17_block_types_and_aliases(self):
        # All 17 canonical types
        types_to_verify = [
            "TITLE", "HEADING", "SUBHEADING", "PARAGRAPH", "DEFINITION",
            "EXPLANATION", "EXAMPLE", "LIST", "LIST_ITEM", "TABLE",
            "FORMULA", "NUMERICAL_SOLUTION", "ALGORITHM", "DIAGRAM",
            "CAPTION", "NOTE", "CONCLUSION"
        ]
        for t_name in types_to_verify:
            elem_type = AcademicElementType.from_str(t_name)
            self.assertEqual(elem_type.value, t_name)

        # Aliases
        self.assertEqual(AcademicElementType.from_str("DOCUMENT_TITLE"), AcademicElementType.DOCUMENT_TITLE)
        self.assertEqual(AcademicElementType.from_str("BODY"), AcademicElementType.BODY_PARAGRAPH)
        self.assertEqual(AcademicElementType.from_str("CALLOUT"), AcademicElementType.CALLOUT)

    def test_source_aware_element_tracking_and_loss_detection(self):
        orig_text = "Virtual memory uses demand paging provided that page tables are resident in RAM."
        # Case A: Preserved reconstructed text
        elem_preserved = AcademicElementIR(
            element_id="elem_loss_1",
            element_type=AcademicElementType.DEFINITION,
            text_content="Virtual memory implements demand paging provided that page tables are resident in RAM.",
            original_text=orig_text,
            doc_id="doc_101",
            original_sequence=1,
            parent_heading="Virtual Memory"
        )
        self.assertFalse(elem_preserved.is_content_loss_detected())
        self.assertGreaterEqual(elem_preserved.compute_content_preservation_ratio(), 0.8)

        # Case B: Accidental content loss (critical conditions dropped)
        elem_dropped = AcademicElementIR(
            element_id="elem_loss_2",
            element_type=AcademicElementType.DEFINITION,
            text_content="Virtual memory is useful for computers.",
            original_text=orig_text,
            doc_id="doc_101",
            original_sequence=2
        )
        self.assertTrue(elem_dropped.is_content_loss_detected())
        self.assertLess(elem_dropped.compute_content_preservation_ratio(), 0.5)

    def test_dictionary_serialization_round_trip(self):
        elem = AcademicElementIR(
            element_id="elem_rt_1",
            element_type=AcademicElementType.ALGORITHM,
            text_content="Step 1: Check cache. Step 2: On miss, query memory.",
            original_text="Step 1: Check cache. Step 2: Query memory on miss.",
            doc_id="doc_rt",
            original_sequence=4,
            parent_heading="Cache Hierarchy",
            related_block_ids=["elem_rt_2", "elem_rt_3"],
            content_confidence=0.96,
            extraction_confidence=0.98,
            was_reconstructed=True,
            validation_status="PASS"
        )
        d = elem.to_dict()
        self.assertEqual(d["element_type"], "ALGORITHM")
        self.assertEqual(d["doc_id"], "doc_rt")
        self.assertEqual(d["original_sequence"], 4)
        self.assertTrue(d["was_reconstructed"])

        rebuilt = AcademicElementIR.from_dict(d)
        self.assertEqual(rebuilt.element_type, AcademicElementType.ALGORITHM)
        self.assertEqual(rebuilt.related_block_ids, ["elem_rt_2", "elem_rt_3"])
        self.assertEqual(rebuilt.content_confidence, 0.96)


class TestTopicCompletenessEngine(TestCase):
    """
    Validates Requirement 2: Topic Inventory Extraction & Deep Completeness Verification.
    """

    def test_build_topic_inventory_from_text(self):
        sample_source = (
            "# Module 1: Process Synchronization\n\n"
            "A critical section is defined as a piece of code that accesses shared variables.\n\n"
            "### Peterson's Algorithm\n\n"
            "Peterson's algorithm is a concurrent programming algorithm for mutual exclusion.\n"
            "Step 1: Process sets flag[i] = True.\n"
            "Step 2: Process sets turn = j.\n\n"
            "Formula: $$WaitTime = T_{entry} - T_{request}$$\n\n"
            "For example, two threads updating a shared bank balance illustrate race conditions.\n"
        )
        inventory = TopicCompletenessEngine.build_topic_inventory(sample_source, "Operating Systems", "Computer Science")
        self.assertGreaterEqual(len(inventory), 1)

        spec = inventory[0]
        self.assertIn("Process Synchronization", spec.name)
        self.assertTrue(len(spec.required_definitions) >= 1 or len(spec.procedures_or_steps) >= 1)
        self.assertIn(spec.complexity_level, ("LOW", "MEDIUM", "HIGH"))

    def test_verify_topic_completeness_missing_vs_covered(self):
        spec1 = TopicInventorySpec(
            topic_id="top_1",
            name="Virtual Memory Architecture",
            required_definitions=["Virtual memory"],
            formulas=["EAT = (1-p)*m + p*S"],
            procedures_or_steps=["Page table walk on miss"]
        )
        spec2 = TopicInventorySpec(
            topic_id="top_2",
            name="Deadlock Detection Algorithms",
            required_definitions=["Deadlock"],
            formulas=["Allocation + Need <= Available"],
            procedures_or_steps=["Banker's safety check"]
        )
        inventory = [spec1, spec2]

        # Generated notes cover topic 1 but omit topic 2
        generated_notes = (
            "# Operating Systems Notes\n\n"
            "## 1. Virtual Memory Architecture\n\n"
            "Virtual memory is a memory management scheme that decouples physical memory from logical address space.\n"
            "The effective access time formula is $$EAT = (1-p)*m + p*S$$.\n"
            "When a TLB miss occurs, the CPU performs a page table walk on miss to locate the physical frame.\n"
        )

        audit = TopicCompletenessEngine.verify_topic_completeness(inventory, generated_notes)
        self.assertEqual(audit["total_source_topics"], 2)
        self.assertEqual(audit["covered_topics_count"], 1)
        self.assertEqual(audit["missing_topics_count"], 1)
        self.assertIn("Deadlock Detection Algorithms", audit["missing_topics"])
        self.assertIn(audit["status"], ("WARNING", "FAIL"))


class TestInformationDensityController(TestCase):
    """
    Validates Requirement 3: Topic-Level Complexity Classification & Adaptive Depth.
    """

    def test_complexity_classification(self):
        low_text = "A process is a program in execution."
        med_text = (
            "A process control block (PCB) contains process state, program counter, CPU registers, "
            "CPU scheduling information, memory-management information, accounting information, "
            "and I/O status information. For example, in Linux the task_struct represents the PCB."
        )
        high_text = (
            "The Banker's Algorithm avoids deadlocks by testing for safety before granting resources. "
            "Given matrices Allocation, Max, and Available, the algorithm executes:\n"
            "Step 1: Let Work = Available and Finish[i] = False for all i.\n"
            "Step 2: Find index i such that Finish[i] == False and Need_i <= Work.\n"
            "Step 3: Work = Work + Allocation_i, Finish[i] = True.\n"
            "Formula: $$Need[i][j] = Max[i][j] - Allocation[i][j]$$\n"
            "Trade-off: High computational overhead O(m * n^2) but guarantees safe state."
        )

        self.assertEqual(InformationDensityController.classify_topic_complexity(low_text), "LOW")
        self.assertEqual(InformationDensityController.classify_topic_complexity(med_text), "MEDIUM")
        self.assertEqual(InformationDensityController.classify_topic_complexity(high_text), "HIGH")

    def test_density_validation_compressed_high_complexity(self):
        # A high complexity topic compressed into 25 words should flag an issue
        short_high_text = "The Banker's Algorithm avoids deadlocks in multi-threaded operating systems."
        result = InformationDensityController.validate_information_density(
            section_title="Banker's Algorithm",
            section_text=short_high_text,
            source_complexity="HIGH"
        )
        self.assertFalse(result["is_density_balanced"])
        self.assertEqual(result["status"], "WARNING")
        self.assertIn("compressed excessively", result["defect"])


class TestSemanticCompressionEngine(TestCase):
    """
    Validates Requirement 4: Condition Preservation and Loss Restoration.
    """

    def test_audit_compression_loss_and_restoration(self):
        source = (
            "In non-preemptive Shortest Job First scheduling, the CPU is allocated to the process "
            "with the smallest burst time. Assuming non-preemptive scheduling, once a process is given "
            "the CPU it cannot be interrupted until burst completion. "
            "Formula: $$Turnaround = Completion - Arrival$$"
        )
        # Summary accidentally dropped the non-preemptive assumption and formula
        bad_compressed = "Shortest Job First schedules processes by smallest burst time to minimize wait."

        loss_audit = SemanticCompressionEngine.audit_compression_loss(source, bad_compressed)
        self.assertTrue(loss_audit["has_accidental_content_loss"])
        self.assertGreater(loss_audit["lost_conditions_count"], 0)

        # Restore lost conditions
        repaired = SemanticCompressionEngine.restore_lost_conditions(bad_compressed, loss_audit["lost_conditions"])
        self.assertIn("Important Conditions & Constraints", repaired)
        self.assertIn("Assuming non-preemptive", repaired)


class TestRepetitionAndConflictDetector(TestCase):
    """
    Validates Requirement 5: Duplicate Detection, Cross-Referencing & Contradiction Flagging.
    """

    def test_detect_duplicate_definitions(self):
        md = (
            "# Operating Systems Notes\n\n"
            "## 1. Process Management\n\n"
            "A process is defined as an instance of a computer program in execution.\n\n"
            "## 2. Process Synchronization\n\n"
            "A process is defined as an instance of a computer program in execution.\n"
        )
        report = RepetitionAndConflictDetector.detect_repetition_and_conflicts(md)
        self.assertGreaterEqual(report["duplicate_definitions_count"], 1)
        self.assertEqual(report["duplicate_definitions"][0]["term"], "a process")

    def test_detect_direct_contradiction(self):
        # Section claiming FCFS is both preemptive and strictly non-preemptive
        md = (
            "# Scheduling Algorithms\n\n"
            "## 1. First-Come First-Served\n\n"
            "FCFS is preemptive when high-priority tasks arrive. However, FCFS is strictly non-preemptive in standard operating systems.\n"
        )
        report = RepetitionAndConflictDetector.detect_repetition_and_conflicts(md)
        self.assertGreaterEqual(report["conflicts_count"], 1)
        self.assertEqual(report["conflicts"][0]["type"], "DIRECT_CONTRADICTION")
        self.assertEqual(report["status"], "FAIL")


class TestTechnicalExplanationVerifier(TestCase):
    """
    Validates Requirement 6: 10-Point Technical Explanation Verification Checklist.
    """

    def test_complete_technical_explanation_passes(self):
        explanation = (
            "Virtual memory is defined as a memory management capability of an operating system. "
            "It operates by mapping virtual addresses into physical memory frames. "
            "Key components include the Page Table, Translation Lookaside Buffer (TLB), and Secondary Storage. "
            "The memory management unit communicates with the page table to translate logical pages. "
            "Step 1: CPU generates virtual address. Step 2: MMU checks TLB cache. Step 3: On TLB miss, page table walk occurs. "
            "For example, demand paging in modern Linux loads memory pages only when referenced. "
            "A key trade-off is flexible address space expansion versus potential page fault latency overhead."
        )
        result = TechnicalExplanationVerifier.verify_explanation(
            topic_title="Virtual Memory",
            explanation_text=explanation,
            source_evidence="Virtual memory maps virtual addresses into physical frames via page tables.",
            subject="Computer Science"
        )
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(result["points_passed"], 8)
        self.assertTrue(result["checklist"]["1_definition_present"])
        self.assertTrue(result["checklist"]["4_mechanism_explained"])
        self.assertTrue(result["checklist"]["7_step_order_present"])


class TestNumericalSolutionAuditor(TestCase):
    """
    Validates Requirement 7: 4-Stage Numerical Solution Validation Pass.
    """

    def test_audit_valid_numerical_solution(self):
        problem_spec = {
            "statement": "Calculate the effective access time (EAT) given a 90% TLB hit ratio, 20 ns lookup time, and 100 ns memory access time.",
            "given": {"Hit Ratio (alpha)": "0.90", "Lookup Time (c)": "20 ns", "Memory Access (m)": "100 ns"},
            "required": "Effective Access Time (EAT)",
            "formula": "EAT = alpha * (c + m) + (1 - alpha) * (c + 2m)",
            "substitution": "EAT = 0.90 * (20 + 100) + (1 - 0.90) * (20 + 2 * 100)",
            "calculation_steps": [
                {"lhs": "Hit Time", "rhs": "0.90 * 120 = 108 ns"},
                {"lhs": "Miss Time", "rhs": "0.10 * 220 = 22 ns"},
                {"lhs": "Total EAT", "rhs": "108 + 22 = 130 ns"}
            ],
            "final_answer": "130 ns",
            "units": "nanoseconds"
        }
        report = NumericalSolutionAuditor.audit_numerical_content(problem_spec)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["stages"]["1_extraction_check"]["status"], "PASS")
        self.assertEqual(report["stages"]["2_method_check"]["status"], "PASS")
        self.assertEqual(report["stages"]["4_presentation_check"]["status"], "PASS")


class TestStructureConsistencyEngine(TestCase):
    """
    Validates Requirement 8 & 9: Structure Hierarchy and Line Alignment Repairs.
    """

    def test_repair_skipped_heading_hierarchy_and_isolated_number(self):
        broken_md = (
            "# Main Title\n\n"
            "### Skipped to H3 Directly\n\n"
            "This heading skips level 2.\n\n"
            "1.\n"
            "First isolated step.\n\n"
            "2.\n"
            "Second isolated step.\n"
        )
        repaired, report = StructureConsistencyEngine.audit_and_repair_structure(broken_md)
        self.assertTrue(report["was_structure_repaired"])
        self.assertIn("## Skipped to H3 Directly", repaired)
        self.assertIn("1. First isolated step.", repaired)
        self.assertNotIn("1.\n", repaired)


class TestCentralStyleTokens(TestCase):
    """
    Validates Requirement 10: Central Style Token System in DocumentTypography.
    """

    def test_style_tokens_defined(self):
        required_tokens = [
            "DOCUMENT_TITLE", "MODULE_TITLE", "H1", "H2", "H3",
            "BODY", "BODY_COMPACT", "DEFINITION", "EXAMPLE", "NOTE",
            "FORMULA", "NUMERICAL_STEP", "TABLE_HEADER", "TABLE_BODY",
            "CAPTION", "HEADER", "FOOTER"
        ]
        for token in required_tokens:
            style = DocumentTypography.get_semantic_style(token)
            self.assertIsNotNone(style)
            self.assertIn("font_size", style)
            self.assertIn("leading", style)
            self.assertIn("color_hex", style)


class TestSelfRepairPipelineAndDashboard(TestCase):
    """
    Validates Requirement 11, 13 & 14: Multi-Stage Self-Repair Loop & Honest Dashboard.
    """

    def test_self_repair_pipeline_execution(self):
        source = (
            "# Process Scheduling\n\n"
            "A process is defined as an instance of a computer program in execution.\n"
            "Assuming non-preemptive execution, CPU burst cannot be interrupted.\n"
            "Formula: $$Wait = Turnaround - Burst$$\n"
        )
        initial_generated = (
            "# Process Scheduling\n\n"
            "### Process Basics\n\n"
            "1.\n"
            "Process definition.\n"
        )

        pipeline_res = SelfRepairEngine.execute_self_repair_pipeline(
            raw_source_or_chunks=source,
            generated_markdown=initial_generated,
            document_title="Process Scheduling",
            subject="Computer Science"
        )

        self.assertTrue(pipeline_res["success"])
        self.assertIn("repaired_markdown", pipeline_res)
        self.assertIn("dashboard", pipeline_res)

        db = pipeline_res["dashboard"]
        self.assertIn("content_coverage", db)
        self.assertIn("content_quality", db)
        self.assertIn("structure_quality", db)
        self.assertIn("mathematical_quality", db)
        self.assertIn("document_quality", db)
        self.assertIn(db["master_certification"], ("READY", "NEEDS_CORRECTION"))


class TestSelfRepairAPI(TestCase):
    """
    Validates Phase 8 REST API:
    GET & POST /api/documents/<doc_id>/self-repair-audit/
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="prof_knuth", password="algo_pass_123")
        self.client.login(username="prof_knuth", password="algo_pass_123")
        self.session = self.client.session
        self.session["user_id"] = self.user.id
        self.session.save()

        summary_data = {
            "response": (
                "# Algorithm Analysis\n\n"
                "## 1. Asymptotic Notation\n\n"
                "Big-O notation defines the upper bound of an algorithm's execution time.\n"
            )
        }

        self.doc = Document.objects.create(
            user=self.user,
            title="Algorithm Analysis Notes",
            subject="Computer Science",
            raw_text="Big-O notation is defined as the asymptotic upper bound.",
            summary_json=json.dumps(summary_data)
        )

        Chunk.objects.create(
            document=self.doc,
            chunk_index=0,
            text="# Asymptotic Notation\nBig-O notation defines upper bound.",
            page_start=1,
            page_end=1
        )

    def test_get_self_repair_audit(self):
        response = self.client.get(f"/api/documents/{self.doc.id}/self-repair-audit/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("dashboard", data)
        self.assertIn("content_coverage", data["dashboard"])
        self.assertIn("document_quality", data["dashboard"])

    def test_post_self_repair_execution(self):
        # Update document with text containing isolated numbering
        broken = (
            "# Algorithm Analysis\n\n"
            "## 1. Asymptotic Notation\n\n"
            "1.\n"
            "Big-O represents worst-case bound.\n"
        )
        self.doc.set_summary({"response": broken})
        self.doc.save()

        response = self.client.post(f"/api/documents/{self.doc.id}/self-repair/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Check DB update
        self.doc.refresh_from_db()
        repaired = self.doc.get_summary().get("response")
        self.assertIn("1. Big-O represents worst-case bound.", repaired)
        self.assertNotIn("1.\n", repaired)
