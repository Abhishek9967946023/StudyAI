import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Document, Chunk
from .academic_ir import (
    AcademicDocumentIR,
    AcademicSectionIR,
    AcademicElementIR,
    AcademicElementType,
    GroundingType,
)
from .deep_content_intelligence import (
    DeepContentIntelligenceEngine,
    DeepContentAuditor,
    SUBJECT_PEDAGOGICAL_PROFILES,
)
from .precision_layout_engine import (
    PrecisionLayoutEngine,
)


class TestAcademicIR(TestCase):
    """
    Validates Structured Intermediate Representation (IR) parsing,
    bidirectional markdown conversion, and element taxonomy.
    """

    def test_ir_element_and_section_creation(self):
        elem1 = AcademicElementIR(
            element_id="elem_1",
            element_type=AcademicElementType.DEFINITION,
            text_content="A process is an instance of a computer program in execution.",
            grounding_type=GroundingType.SOURCE_DERIVED,
            source_page_start=2,
            confidence=0.98,
        )
        elem2 = AcademicElementIR(
            element_id="elem_2",
            element_type=AcademicElementType.FORMULA,
            text_content="$$T_{turnaround} = T_{completion} - T_{arrival}$$",
            grounding_type=GroundingType.SOURCE_DERIVED,
            source_page_start=2,
            confidence=0.99,
        )

        section = AcademicSectionIR(
            section_id="sec_1",
            title="Process Scheduling",
            order_index=1,
            elements=[elem1, elem2],
        )

        doc_ir = AcademicDocumentIR(
            doc_id="doc_test_1",
            title="Operating Systems Notes",
            subject="Computer Science",
            sections=[section],
        )

        # Validate dictionary round-trip
        data = doc_ir.to_dict()
        self.assertEqual(data["title"], "Operating Systems Notes")
        self.assertEqual(len(data["sections"]), 1)
        self.assertEqual(len(data["sections"][0]["elements"]), 2)

        reconstructed = AcademicDocumentIR.from_dict(data)
        self.assertEqual(reconstructed.doc_id, "doc_test_1")
        self.assertEqual(reconstructed.sections[0].elements[0].element_type, AcademicElementType.DEFINITION)
        self.assertEqual(reconstructed.sections[0].elements[1].grounding_type, GroundingType.SOURCE_DERIVED)

    def test_markdown_to_ir_and_back(self):
        markdown = (
            "# Operating Systems\n\n"
            "## Module 1: Process Management\n\n"
            "A process is a program in execution.\n\n"
            "### Process States\n\n"
            "A process moves through New, Ready, Running, Waiting, and Terminated states.\n\n"
            "## Module 2: Memory Management\n\n"
            "Virtual memory decouples logical address space from physical memory.\n"
        )

        doc_ir = AcademicDocumentIR.from_markdown(markdown, doc_title="Operating Systems", subject="Computer Science")
        self.assertEqual(len(doc_ir.sections), 2)

        md_out = doc_ir.to_markdown()
        self.assertIn("# Operating Systems", md_out)
        self.assertIn("Module 1: Process Management", md_out)
        self.assertIn("Process States", md_out)
        self.assertIn("Module 2: Memory Management", md_out)


class TestDeepContentIntelligenceEngine(TestCase):
    """
    Validates Subject Pedagogical Profiles, 12-Dimensional synthesis,
    semantic de-duplication with cross-referencing, and source grounding.
    """

    def test_subject_pedagogical_detection(self):
        cat_cs, cs_profile = DeepContentIntelligenceEngine.detect_subject_profile("Computer Science: Data Structures & Algorithms")
        self.assertEqual(cat_cs, "COMPUTER_SCIENCE")
        self.assertTrue(cs_profile["emphasize_code"])
        self.assertIn("MECHANISM", cs_profile["primary_dimensions"])

        cat_math, math_profile = DeepContentIntelligenceEngine.detect_subject_profile("Engineering Mathematics - Calculus")
        self.assertEqual(cat_math, "MATHEMATICS")
        self.assertTrue(math_profile["emphasize_derivations"])
        self.assertIn("MECHANISM", math_profile["primary_dimensions"])

        cat_phys, phys_profile = DeepContentIntelligenceEngine.detect_subject_profile("Quantum Physics & Electrodynamics")
        self.assertEqual(cat_phys, "PHYSICS")

    def test_synthesize_deep_topic_explanation(self):
        source_excerpts = [
            {
                "text": (
                    "Virtual memory is a memory management capability of an operating system. "
                    "It maps virtual addresses into physical addresses via page tables and TLB. "
                    "Mathematical model: $$EAT = (1 - p) \\times m + p \\times S$$. "
                    "In Linux demand paging, pages are loaded on demand into available frames. "
                    "Trade-off: Increased memory capacity vs potential page fault overhead."
                ),
                "page_start": 5,
                "page_end": 6,
            }
        ]

        section = DeepContentIntelligenceEngine.synthesize_deep_topic_explanation(
            topic_title="Virtual Memory Architecture",
            source_excerpts=source_excerpts,
            subject="Computer Science",
            depth="conceptual",
        )

        self.assertEqual(section.title, "Virtual Memory Architecture")
        self.assertGreater(len(section.elements), 2)
        texts = [e.text_content for e in section.elements]
        self.assertTrue(any("Virtual memory" in t for t in texts))

    def test_eliminate_semantic_repetition_with_cross_referencing(self):
        sec1 = AcademicSectionIR(
            section_id="sec_1",
            title="Introduction to Paging",
            order_index=1,
            elements=[
                AcademicElementIR(
                    element_id="e1",
                    element_type=AcademicElementType.DEFINITION,
                    text_content="Paging is a memory management scheme that eliminates the need for contiguous allocation of physical memory.",
                    grounding_type=GroundingType.SOURCE_DERIVED,
                )
            ],
        )
        sec2 = AcademicSectionIR(
            section_id="sec_2",
            title="Page Replacement Algorithms",
            order_index=2,
            elements=[
                AcademicElementIR(
                    element_id="e2",
                    element_type=AcademicElementType.DEFINITION,
                    text_content="Paging is a memory management scheme that eliminates the need for contiguous allocation of physical memory.",
                    grounding_type=GroundingType.SOURCE_DERIVED,
                ),
                AcademicElementIR(
                    element_id="e3",
                    element_type=AcademicElementType.BODY_PARAGRAPH,
                    text_content="When a page fault occurs, the OS must choose a page to evict using FIFO, LRU, or Optimal replacement.",
                    grounding_type=GroundingType.SOURCE_DERIVED,
                ),
            ],
        )

        doc_ir = AcademicDocumentIR(
            doc_id="doc_dup_1",
            title="OS Paging Guide",
            subject="Computer Science",
            sections=[sec1, sec2],
        )

        # Run de-duplication
        cleaned_doc, dup_count = DeepContentIntelligenceEngine.eliminate_semantic_repetition(doc_ir, similarity_threshold=0.85)
        self.assertEqual(dup_count, 1)

        # The duplicate in sec2 should now reference sec1
        sec2_elem = cleaned_doc.sections[1].elements[0]
        self.assertIn("Refer to Section", sec2_elem.text_content)
        self.assertIn("Introduction to Paging", sec2_elem.text_content)


class TestPrecisionLayoutEngine(TestCase):
    """
    Validates Precision Paragraph Stitching, Hyphen Repair,
    List Item Alignment, Step-by-Step Calculation, and LaTeX Multiline Alignment.
    """

    def test_paragraph_reconstruction_and_hyphen_repair(self):
        raw_text = (
            "The memory management unit uses dynamic ad-\n"
            "dress translation to map virtual addresses into physical\n"
            "frames in RAM.\n\n"
            "Next line starts a new concept.\n"
        )
        reconstructed = PrecisionLayoutEngine.reconstruct_logical_paragraphs(raw_text)
        self.assertIn("address translation", reconstructed)
        self.assertNotIn("ad-\ndress", reconstructed)

    def test_list_item_alignment_and_isolated_number_repair(self):
        malformed_list = (
            "1.\n"
            "First process state is New.\n"
            "2.\n"
            "Second process state is Ready.\n"
            "3.\n"
            "Third process state is Running.\n"
        )
        aligned = PrecisionLayoutEngine.align_list_items(malformed_list)
        self.assertIn("1. First process state is New.", aligned)
        self.assertIn("2. Second process state is Ready.", aligned)
        self.assertNotIn("1.\n", aligned)

    def test_format_step_by_step_numerical_solution(self):
        problem_spec = {
            "problem": "Calculate the Effective Access Time (EAT) for a system with 80% TLB hit ratio, 20 ns TLB lookup time, and 100 ns main memory access time.",
            "given": {
                "TLB Hit Ratio (alpha)": "0.80",
                "TLB Lookup Time (c)": "20 ns",
                "Memory Access Time (m)": "100 ns",
            },
            "required": "Effective Access Time (EAT)",
            "formula": "EAT = alpha * (c + m) + (1 - alpha) * (c + 2m)",
            "symbols": {
                "alpha": "TLB Hit Ratio",
                "c": "TLB search time",
                "m": "Main memory cycle time",
            },
            "substitution": "EAT = 0.80 * (20 + 100) + (1 - 0.80) * (20 + 2 * 100)",
            "calculation_steps": [
                "Hit Time = 20 + 100 = 120 ns",
                "Weighted Hit = 0.80 * 120 = 96 ns",
                "Miss Time = 20 + 200 = 220 ns",
                "Weighted Miss = 0.20 * 220 = 44 ns",
                "Total EAT = 96 + 44 = 140 ns",
            ],
            "intermediates": {
                "Hit Contribution": "96 ns",
                "Miss Contribution": "44 ns",
            },
            "final_answer": "140 ns",
            "units": "nanoseconds (ns)",
            "verification": "140 ns is within expected bound [120 ns, 220 ns].",
        }

        output = PrecisionLayoutEngine.format_step_by_step_numerical_solution(problem_spec)
        self.assertIn("Problem Statement", output)
        self.assertIn("Given Data", output)
        self.assertIn("Governing Formula", output)
        self.assertIn("Final Result", output)
        self.assertIn("140 ns", output)

    def test_align_multiline_equations(self):
        raw_eq = (
            "$$\n"
            "EAT = \\alpha (c + m) + (1 - \\alpha)(c + 2m)\n"
            "= 0.80(120) + 0.20(220)\n"
            "= 96 + 44\n"
            "= 140\n"
            "$$\n"
        )
        aligned = PrecisionLayoutEngine.align_multiline_equations(raw_eq)
        self.assertIn(r"\begin{aligned}", aligned)
        self.assertIn(r"\end{aligned}", aligned)
        self.assertIn("&=", aligned)

    def test_calculate_table_column_widths(self):
        headers = ["Algorithm", "Hit Ratio", "Description"]
        rows = [
            ["FIFO", "0.72", "First-in first-out page replacement strategy."],
            ["LRU", "0.85", "Least recently used page replacement strategy tracking chronological access."],
            ["OPT", "0.91", "Optimal page replacement replacing page not needed for longest period."],
        ]
        table_data = [headers] + rows
        widths = PrecisionLayoutEngine.calculate_table_column_widths(table_data, total_printable_width=468.0)
        self.assertEqual(len(widths), 3)
        self.assertAlmostEqual(sum(widths), 468.0, places=1)
        # The description column is longer, so it should receive more width
        self.assertGreater(widths[2], widths[0])


class TestDeepContentAuditor(TestCase):
    """
    Validates unpolluted 3-category metrics (Content, Structure, Layout)
    and master certification logic.
    """

    def test_auditor_pass_conditions(self):
        markdown = (
            "# Advanced Operating Systems\n\n"
            "## Process Synchronization\n\n"
            "A critical section is a piece of code that accesses shared resources.\n\n"
            "### Race Conditions\n\n"
            "A race condition occurs when multiple processes access and manipulate the same data concurrently.\n\n"
            "| Algorithm | Mutual Exclusion | Progress |\n"
            "|---|---|---|\n"
            "| Peterson's | Yes | Yes |\n"
            "| Test-and-Set | Yes | Yes |\n\n"
            "$$\n"
            "\\begin{aligned}\n"
            "S &= S - 1 \\\\\n"
            "W &= W + 1\n"
            "\\end{aligned}\n"
            "$$\n"
        )

        topics = [
            {"name": "Process Synchronization"},
            {"name": "Race Conditions"},
        ]

        audit = DeepContentAuditor.audit_document(
            doc_ir_or_md=markdown,
            doc_title="Advanced Operating Systems",
            subject="Computer Science",
            source_topics=topics,
        )

        self.assertTrue(audit["certified"])
        self.assertEqual(audit["final_document_status"], "READY")
        self.assertEqual(audit["content_metrics"]["status"], "PASS")
        self.assertEqual(audit["structure_metrics"]["status"], "PASS")
        self.assertEqual(audit["layout_metrics"]["status"], "PASS")
        self.assertEqual(audit["content_metrics"]["coverage_percentage"], 100.0)

    def test_auditor_skipped_heading_levels(self):
        # Skipped heading level from H1 directly to H3
        markdown = (
            "# Operating Systems\n\n"
            "### Skip to Subheading\n\n"
            "Skipped heading level should be detected.\n"
        )
        audit = DeepContentAuditor.audit_document(markdown)
        self.assertEqual(audit["structure_metrics"]["status"], "FAIL")
        self.assertFalse(audit["structure_metrics"]["heading_hierarchy_valid"])
        self.assertGreater(audit["structure_metrics"]["skipped_heading_levels_count"], 0)
        self.assertEqual(audit["final_document_status"], "NEEDS_CORRECTION")


class TestDeepContentAuditAPI(TestCase):
    """
    Validates the Phase 7 REST API endpoint:
    GET & POST /api/documents/<doc_id>/deep-content-audit/
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="prof_turing", password="secure_pass_123")
        self.client.login(username="prof_turing", password="secure_pass_123")
        self.session = self.client.session
        self.session["user_id"] = self.user.id
        self.session.save()

        summary_content = {
            "response": (
                "# Distributed Systems Consensus\n\n"
                "## Module 1: Raft Protocol\n\n"
                "Raft is a consensus algorithm that achieves fault tolerance through leader election, log replication, and safety.\n\n"
                "### Leader Election\n\n"
                "When a leader fails, follower nodes time out and transition to candidate state to start a new term election.\n"
            )
        }

        self.doc = Document.objects.create(
            user=self.user,
            title="Distributed Systems Consensus",
            subject="Computer Science",
            raw_text="Raft is a consensus algorithm designed as an alternative to Paxos.",
            summary_json=json.dumps(summary_content),
        )

        Chunk.objects.create(
            document=self.doc,
            chunk_index=0,
            text="# Module 1: Raft Protocol\nConsensus algorithm details.",
            page_start=1,
            page_end=1,
        )

    def test_get_deep_content_audit(self):
        response = self.client.get(f"/api/documents/{self.doc.id}/deep-content-audit/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("audit", data)
        self.assertIn("content_metrics", data["audit"])
        self.assertIn("structure_metrics", data["audit"])
        self.assertIn("layout_metrics", data["audit"])
        self.assertEqual(data["audit"]["final_document_status"], "READY")

    def test_post_deep_content_audit_repair(self):
        # Introduce broken text with unaligned lists into document summary
        broken_text = (
            "# Distributed Systems Consensus\n\n"
            "## Module 1: Raft Protocol\n\n"
            "1.\n"
            "Follower state.\n"
            "2.\n"
            "Candidate state.\n"
        )
        self.doc.set_summary({"response": broken_text})
        self.doc.save()

        response = self.client.post(f"/api/documents/{self.doc.id}/deep-content-audit/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Reload document from DB and verify repaired markdown
        self.doc.refresh_from_db()
        repaired = self.doc.get_summary().get("response")
        self.assertIn("1. Follower state.", repaired)
        self.assertNotIn("1.\n", repaired)
