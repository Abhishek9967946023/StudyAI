"""
=============================================================================
StudyAI — Complete Subject Understanding, Syllabus Discovery & Deep Teaching Engine
=============================================================================
Transforms StudyAI into an intelligent academic teacher:
1. Subject Understanding: Discovers subject domain, core purpose, real-world
   problems solved, practical applications, prerequisites, knowledge pillars,
   and logical learning progression with dynamic Mermaid knowledge maps.
2. Hierarchical Syllabus Discovery: Traverses 100% of document chunks to build
   a 6-level syllabus tree (Subject -> Knowledge Area -> Chapter -> Section -> Topic -> Concept).
   Aggressively filters running author headers (e.g. 'Srinivas Rao') and sentence fragments.
3. Deep Contextual Topic Teaching: Synthesizes comprehensive pedagogical explanations
   covering up to 26 dimensions: intuition, technical definitions, mechanics,
   numbered algorithms, frame formats, Mermaid diagrams, KaTeX math derivations,
   physical units tables, step-by-step solved numericals, trade-offs, pitfalls, and exam tips.
4. Document Coverage Engine: Verifies document coverage matrix across all pages,
   topics, formulas, and algorithms.
=============================================================================
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from django.db import transaction
from django.utils import timezone

from .models import Document, Chunk, Topic
from .content_cleaner import (
    clean_and_classify_document_content,
    is_malformed_sentence_fragment,
    is_malformed_concept_name,
    is_meaningful_math_or_technical,
    LineType
)
from .ai_provider_service import query_ai, check_ai_provider_status
from .ollama_service import parse_json_safely
from .prompt_templates import (
    ACADEMIC_NOTE_ANALYSIS_GUIDELINES,
    classify_document_genre,
    classify_topic_archetype,
    build_adaptive_topic_teaching_prompt,
    DOCUMENT_TYPE_STRUCTURES
)

logger = logging.getLogger(__name__)


# =============================================================================
# Noise & Header Filtering Constants
# =============================================================================

# Common author, instructor, university, and affiliation noise patterns
AUTHOR_NOISE_PATTERNS = [
    re.compile(r'^(?:wg\s*cdr|dr\.|prof\.|professor|lecturer|faculty|author|instructor|by:?)\b.*', re.IGNORECASE),
    re.compile(r'^(?:department\s+of|dept\.|school\s+of|college|university|institute|rgit|vtu|anna\s+univ|iit|nit)\b.*', re.IGNORECASE),
    re.compile(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}(?:,\s*(?:professor|asst|assoc|ph\.?d|m\.?tech|b\.?e|hod)).*', re.IGNORECASE),
    re.compile(r'^(?:prepared\s+by|compiled\s+by|notes\s+by|authored\s+by|edited\s+by)\b.*', re.IGNORECASE),
    re.compile(r'^(?:course\s+code|subject\s+code|semester|sem\s*\d|academic\s+year|bcs\d{3}|cs\d{3})\b.*', re.IGNORECASE),
]

# Patterns for sentence fragments mistakenly picked up as headings
SENTENCE_FRAGMENT_PATTERNS = [
    re.compile(r'^(?:if|when|where|because|since|whenever|suppose|assume|let|in\s+order\s+to|therefore|hence|thus|although)\b', re.IGNORECASE),
    re.compile(r'^(?:note\s+that|notice\s+that|it\s+is\s+important|recall\s+that|we\s+can\s+see|as\s+shown)\b', re.IGNORECASE),
    re.compile(r'(?:is\s+not\s+zero|packet\s+is\s+dropped|bits\s+are\s+corrupted|error\s+has\s+occurred|is\s+intended\s+for)$', re.IGNORECASE),
]


def is_author_or_institutional_noise(line: str) -> bool:
    """Detects author names, professor signatures, university credits, or course code headers."""
    s = line.strip()
    if not s or len(s) < 3:
        return True
    for pat in AUTHOR_NOISE_PATTERNS:
        if pat.search(s):
            return True
    # Specific known textbook author noise checks
    lower = s.lower()
    if any(k in lower for k in ['srinivas rao', 'wg cdr', 'department of cse', 'forouzan', 'tanenbaum', 'stallings']):
        if not any(k in lower for k in ['algorithm', 'theorem', 'protocol', 'layer', 'code', 'model']):
            return True
    return False


def is_invalid_heading_fragment(line: str) -> bool:
    """Detects if a string is a sentence fragment, clause, or non-heading text."""
    s = line.strip()
    if not s or len(s) < 3:
        return True
    # Pure acronym in parentheses e.g. '(FSM).' or '(CRC)'
    if re.match(r'^\(?[A-Za-z0-9]+\)?[\.\s]*$', s) and len(s) <= 6:
        return True
    # If it ends with period, colon, or semicolon followed by run-on text
    if len(s.split()) > 10 and not any(k in s.lower() for k in ['chapter', 'module', 'unit', 'section']):
        return True
    for pat in SENTENCE_FRAGMENT_PATTERNS:
        if pat.search(s):
            return True
    return False


def clean_heading_text(heading: str) -> str:
    """Normalizes and cleans heading titles, stripping prefixes and noise."""
    h = heading.strip()
    # Strip bullet points, arrows, markdown hashes
    h = re.sub(r'^[#*\-•\s➔→>]+', '', h).strip()
    # Strip trailing punctuation including period, colon, dash first
    h = re.sub(r'[\.:\-–—\s]+$', '', h).strip()
    # Strip enclosing parentheses if whole string is wrapped
    if h.startswith('(') and h.endswith(')'):
        h = h[1:-1].strip()
    # Strip trailing punctuation again if any remained inside parens
    h = re.sub(r'[\.:\-–—\s]+$', '', h).strip()
    # Remove artificial "Chapter X:" if followed by a run-on sentence
    h = re.sub(r'^(?:chapter|module|unit|section)\s*\d+\s*:\s*', '', h, flags=re.IGNORECASE).strip()
    return h


# =============================================================================
# MODULE A: Subject Understanding Engine
# =============================================================================

class SubjectUnderstandingEngine:
    """
    Analyzes the entire document to construct a deep, multi-dimensional subject model:
    - Subject Name & Academic Domain
    - Fundamental Purpose & Problems Solved
    - Real-World Production Applications
    - Core Prerequisites
    - Major Knowledge Pillars (Areas)
    - Optimal Pedagogical Progression
    - Verified Mermaid Knowledge Architecture Diagram
    - Cross-domain subject validation
    """

    @classmethod
    def analyze_subject(cls, doc: Document) -> Dict[str, Any]:
        """Performs subject understanding analysis grounded strictly in document text."""
        chunks = doc.chunks.all().order_by('chunk_index')
        total_chunks = chunks.count()
        if total_chunks == 0:
            return cls._fallback_subject_model(doc.title or "Academic Study Material", "")

        # Sample representative text across beginning, middle, and end of document
        sample_texts = []
        # Chunks 1-3 (Title, intro, table of contents)
        for c in chunks[:3]:
            sample_texts.append(f"--- Document Header / Early Section (Page {c.page_start}) ---\n{c.text[:1200]}")
        # Middle chunks
        if total_chunks > 6:
            mid = total_chunks // 2
            for c in chunks[mid:mid+2]:
                sample_texts.append(f"--- Document Core / Middle Section (Page {c.page_start}) ---\n{c.text[:1000]}")
        # Tail chunks
        if total_chunks > 4:
            for c in chunks[max(3, total_chunks-2):]:
                sample_texts.append(f"--- Document Summary / Later Section (Page {c.page_start}) ---\n{c.text[:800]}")

        combined_sample = "\n\n".join(sample_texts)

        # Attempt Ollama extraction
        subject_model = cls._query_ollama_for_subject(doc.title, combined_sample, doc.page_count)
        if not subject_model or not subject_model.get("subject_name"):
            subject_model = cls._extractive_subject_model(doc.title, combined_sample, doc.page_count)
            subject_model["analysis_source"] = "heuristic_fallback"
            subject_model["source_note"] = (
                "This overview uses heuristic general context and may include information "
                "not present in the uploaded document."
            )
        else:
            subject_model["analysis_source"] = "ai_generated"
            subject_model["source_note"] = (
                "AI-generated from sampled document text; claims have not been independently fact-checked."
            )

        # Detect document genre and structural blueprint
        genre = classify_document_genre(combined_sample, doc.title)
        subject_model["document_genre"] = genre
        subject_model["document_type"] = genre

        # Ensure valid Mermaid diagram
        mermaid_code = subject_model.get("mermaid_knowledge_map", "")
        if not mermaid_code or "flowchart" not in mermaid_code:
            subject_model["mermaid_knowledge_map"] = cls._generate_fallback_mermaid(subject_model)

        return subject_model

    @classmethod
    def analyze_and_persist_subject(cls, doc: Document) -> Dict[str, Any]:
        """Analyzes subject understanding and saves to Document model."""
        data = cls.analyze_subject(doc)
        doc.set_subject_understanding(data)
        if data.get("subject_name") and doc.subject in ['General Academic', 'General Education', '']:
            doc.subject = data["subject_name"]
            doc.save(update_fields=['subject', 'subject_understanding_json', 'updated_at'])
        else:
            doc.save(update_fields=['subject_understanding_json', 'updated_at'])
        return data

    @classmethod
    def _query_ollama_for_subject(cls, title: str, sample_text: str, total_pages: int) -> Optional[Dict[str, Any]]:
        """Invokes Ollama to discover subject parameters with strict JSON output."""
        status = check_ai_provider_status()
        if not status.get("can_generate"):
            return None

        prompt = f"""You are a distinguished University Professor and Curriculum Architect.
Analyze the following academic document sample (Title: "{title}", Total Pages: {total_pages}).

SAMPLE DOCUMENT TEXT:
\"\"\"
{sample_text[:5000]}
\"\"\"

CRITICAL INSTRUCTIONS:
1. Ground your analysis STRICTLY in this document. Do NOT introduce unrelated fields (e.g. if this is Computer Networks, do NOT include Operating Systems CPU scheduling or Biology).
2. Produce a valid, parseable JSON object matching this schema:
{{
  "subject_name": "Standard Academic Subject Name (e.g. Computer Networks)",
  "subject_domain": "Broader Academic Domain (e.g. Computer Science & Engineering)",
  "subject_description": "Comprehensive 2-3 paragraph academic overview of what this subject explores and why it is critical.",
  "purpose": "The core engineering or scientific purpose of this discipline.",
  "problems_solved": [
    "List of 4-6 specific fundamental problems this subject solves"
  ],
  "real_world_applications": [
    "List of 4-6 modern industrial, software, or hardware applications"
  ],
  "prerequisites": [
    "List of 3-5 foundational prerequisite subjects or concepts"
  ],
  "major_knowledge_areas": [
    {{
      "name": "Knowledge Pillar Name (e.g. Error Detection and Correction)",
      "description": "What this area covers",
      "core_focus": "Key theoretical focus"
    }}
  ],
  "logical_learning_order": [
    {{
      "step": 1,
      "topic": "First topic to learn",
      "rationale": "Why this must be understood first"
    }}
  ],
  "mermaid_knowledge_map": "flowchart TD\\n  A[Subject] --> B[Area 1]\\n  A --> C[Area 2]\\n  B --> D[Topic 1]"
}}

Respond ONLY with valid JSON.
"""
        response_text, success, _ = query_ai(prompt, format_json=True, timeout=60, temperature=0.1)
        if success and response_text:
            parsed = parse_json_safely(response_text)
            if isinstance(parsed, dict) and parsed.get("subject_name"):
                return parsed
        return None

    @classmethod
    def _extractive_subject_model(cls, title: str, sample_text: str, total_pages: int) -> Dict[str, Any]:
        """Grounded extractive fallback when Ollama is unavailable."""
        lower_text = (title + " " + sample_text).lower()

        # Subject heuristic detection grounded in keywords
        if any(k in lower_text for k in ['network', 'data link', 'packet', 'framing', 'crc', 'hdlc', 'csma', 'aloha', 'tcp', 'ip']):
            subject_name = "Computer Networks"
            domain = "Computer Science & Engineering"
            description = (
                "Computer Networks is the foundational discipline governing how independent computing systems "
                "interconnect, communicate, and transfer information reliably across physical and wireless media. "
                "This study material focuses primarily on Data Link Layer mechanisms, encompassing error detection "
                "and correction (block codes, CRC, checksum), data link control protocols (framing, flow control, HDLC), "
                "and media access control algorithms (ALOHA, CSMA/CD, CSMA/CA, CDMA)."
            )
            purpose = "To ensure reliable, error-free, and collision-managed communication over inherently noisy, shared transmission media."
            problems_solved = [
                "Node-to-node frame packaging and synchronization over raw bitstreams",
                "Detection and correction of single-bit and burst transmission errors",
                "Flow control to prevent fast senders from overwhelming slow receivers",
                "Medium access coordination and collision resolution across shared communication channels"
            ]
            applications = [
                "Ethernet (IEEE 802.3) local area networks and framing protocols",
                "Wi-Fi (IEEE 802.11) wireless communication and CSMA/CA collision avoidance",
                "Internet Protocol suite (TCP/IP) reliable end-to-end transport",
                "High-Level Data Link Control (HDLC) and Point-to-Point Protocol (PPP) serial links"
            ]
            prerequisites = [
                "Digital Logic & Binary Bitwise Operations",
                "Physical Layer Transmission Characteristics (Attenuation, Bandwidth)",
                "Basic Probability & Combinatorics (for error models)"
            ]
            knowledge_areas = [
                {
                    "name": "Error Detection and Correction",
                    "description": "Redundancy schemes, Hamming Distance, Parity Check, Linear Block Codes, and CRC.",
                    "core_focus": "Detecting and correcting bit corruption introduced by channel noise."
                },
                {
                    "name": "Data Link Control (DLC) Protocols",
                    "description": "Framing techniques (bit/byte stuffing), flow control, Stop-and-Wait, Go-Back-N, and Selective Repeat.",
                    "core_focus": "Reliable transmission and buffer management between adjacent nodes."
                },
                {
                    "name": "Media Access Control (MAC)",
                    "description": "Random access (ALOHA, CSMA, CSMA/CD, CSMA/CA), controlled access, and channelization (FDMA, TDMA, CDMA).",
                    "core_focus": "Coordinating shared channel access to minimize packet collisions."
                }
            ]
            learning_order = [
                {"step": 1, "topic": "Types of Errors & Redundancy", "rationale": "Establishes why error detection is required at the bit level."},
                {"step": 2, "topic": "Hamming Distance & Block Coding", "rationale": "Introduces geometric and linear bounds on error detection and correction."},
                {"step": 3, "topic": "Cyclic Redundancy Check (CRC) & Checksum", "rationale": "Covers high-speed polynomial and arithmetic verification algorithms used in hardware."},
                {"step": 4, "topic": "Framing & Data Link Protocols (HDLC)", "rationale": "Shows how bits are assembled into delineated frames with flow control."},
                {"step": 5, "topic": "Multiple Access Protocols (CSMA/CD & CSMA/CA)", "rationale": "Scales communication to shared multi-user transmission channels."}
            ]
        elif any(k in lower_text for k in ['automata', 'turing', 'context-free', 'grammar', 'cfg', 'pda', 'dfa', 'nfa']):
            subject_name = "Theory of Computation & Automata Theory"
            domain = "Theoretical Computer Science"
            description = (
                "Theory of Computation investigates the mathematical limits of computation, exploring what problems "
                "can be solved mechanically, how efficiently, and with what model of abstract computational machine. "
                "This material covers formal languages, grammars, finite automata, pushdown automata, and Turing machines."
            )
            purpose = "To formulate mathematical foundations of computing devices and classify computational problems by solvability and complexity."
            problems_solved = [
                "Formal specification and validation of programming language syntax",
                "State transition modeling for hardware and compiler design",
                "Rigorous classification of decidable and undecidable languages"
            ]
            applications = [
                "Compiler Lexical Analysis (Regular Expressions, Lex/Flex, DFA)",
                "Compiler Syntax Analysis (Context-Free Grammars, LL/LR Parsers)",
                "Hardware Finite State Machine (FSM) verification",
                "Regular expression pattern matching engines"
            ]
            prerequisites = ["Discrete Mathematics (Set Theory, Relations, Graph Theory)", "Mathematical Induction and Proof by Contradiction"]
            knowledge_areas = [
                {"name": "Regular Languages & Finite Automata", "description": "DFA, NFA, Regular Expressions, Pumping Lemma for Regular Languages.", "core_focus": "Memoryless state-based language recognition."},
                {"name": "Context-Free Languages & Pushdown Automata", "description": "CFGs, ambiguity, normal forms (CNF/GNF), and stack automata.", "core_focus": "Nested and balanced syntax recognition."},
                {"name": "Turing Machines & Decidability", "description": "Standard Turing machines, Universal Turing machines, Halting Problem.", "core_focus": "Universal computability and algorithmic limits."}
            ]
            learning_order = [
                {"step": 1, "topic": "Finite Automata (DFA / NFA)", "rationale": "Builds fundamental intuition of state transitions and regular language recognition."},
                {"step": 2, "topic": "Regular Expressions & Equivalence", "rationale": "Bridges algebraic expressions with state machine recognizers."},
                {"step": 3, "topic": "Context-Free Grammars & PDA", "rationale": "Adds stack memory to recognize recursive, nested syntactic constructs."},
                {"step": 4, "topic": "Turing Machines & Undecidability", "rationale": "Extends machines to infinite tape memory to determine theoretical solvability boundaries."}
            ]
        elif any(k in lower_text for k in ['process', 'thread', 'deadlock', 'scheduling', 'virtual memory', 'paging', 'semaphore']):
            subject_name = "Operating Systems"
            domain = "Computer Science & Engineering"
            description = (
                "Operating Systems is the core systems software discipline studying how computer hardware resources "
                "(CPU, memory, storage, I/O) are multiplexed, coordinated, and protected to provide a secure, efficient "
                "execution environment for multi-threaded application software."
            )
            purpose = "To manage computer hardware resources and provide a stable abstraction layer for concurrent processes."
            problems_solved = [
                "Fair and optimal CPU time allocation across concurrent threads",
                "Deadlock prevention, avoidance, and recovery in shared resource systems",
                "Memory isolation, protection, and virtual memory virtualization",
                "Synchronization and race condition elimination in shared-memory environments"
            ]
            applications = [
                "Linux and Windows Kernel Architecture",
                "Cloud hypervisors and container runtimes (Docker/Kubernetes)",
                "High-performance multi-threaded database servers",
                "Real-Time Operating Systems (RTOS) in embedded systems"
            ]
            prerequisites = ["Computer Architecture & Assembly Language", "C/C++ Systems Programming", "Data Structures (Queues, Trees, Hash Maps)"]
            knowledge_areas = [
                {"name": "Process & Thread Management", "description": "Process state lifecycle, PCB, context switching, CPU scheduling algorithms.", "core_focus": "Efficient CPU virtualization."},
                {"name": "Concurrency & Synchronization", "description": "Critical section problem, semaphores, mutexes, monitors, classical synchronization problems.", "core_focus": "Deterministic thread coordination."},
                {"name": "Deadlocks & Resource Allocation", "description": "Deadlock conditions, resource allocation graphs, Banker's Algorithm, detection.", "core_focus": "Preventing system starvation and lockup."},
                {"name": "Memory Management & Virtual Memory", "description": "Paging, segmentation, TLB, page replacement algorithms (FIFO, LRU, Optimal).", "core_focus": "Safe, efficient memory abstraction."}
            ]
            learning_order = [
                {"step": 1, "topic": "Process Concepts & Lifecycle", "rationale": "Understands fundamental unit of execution and state representation."},
                {"step": 2, "topic": "CPU Scheduling Algorithms", "rationale": "Explores how the OS optimizes throughput, latency, and fairness."},
                {"step": 3, "topic": "Process Synchronization", "rationale": "Prevents race conditions when concurrent processes share data."},
                {"step": 4, "topic": "Deadlock Handling & Banker's Algorithm", "rationale": "Ensures systems do not enter circular wait states."},
                {"step": 5, "topic": "Virtual Memory & Paging", "rationale": "Enables processes to execute beyond physical RAM boundaries."}
            ]
        else:
            # Generic academic fallback grounded in document title
            clean_title = re.sub(r'^(?:notes\s+on|lecture\s+notes|study\s+guide\s+for|module\s*\d*\s*)\s*', '', title, flags=re.IGNORECASE).strip()
            subject_name = clean_title.title() if clean_title else "Academic Curriculum"
            domain = "Higher Education & Engineering"
            description = (
                f"{subject_name} provides comprehensive theoretical and practical knowledge within {domain}. "
                "This study material structures foundational concepts, mathematical models, operational methods, "
                "and analytical frameworks essential for academic mastery and professional engineering problem solving."
            )
            purpose = f"To systematically master the core tenets, mechanisms, and analytical methods of {subject_name}."
            problems_solved = [
                "Understanding primary terminology and domain models",
                "Applying systematic analytical methods to solve standard problems",
                "Evaluating structural invariants, performance bounds, and trade-offs"
            ]
            applications = [
                f"Engineering design and practical implementation in {subject_name}",
                "University examinations and competitive entrance tests",
                "Advanced research and technical problem solving"
            ]
            prerequisites = ["Fundamental analytical reasoning", "Domain prerequisite fundamentals"]
            knowledge_areas = [
                {"name": "Core Principles & Fundamentals", "description": "Introductory definitions and governing laws.", "core_focus": "Conceptual grounding."},
                {"name": "Operational Mechanisms & Methods", "description": "Detailed workflows and algorithms.", "core_focus": "Execution procedures."},
                {"name": "Advanced Analysis & Applications", "description": "Optimization, trade-offs, and design patterns.", "core_focus": "Mastery and synthesis."}
            ]
            learning_order = [
                {"step": 1, "topic": "Foundations & Terminology", "rationale": "Establishes baseline vocabulary and axioms."},
                {"step": 2, "topic": "Core Mechanisms", "rationale": "Investigates operational algorithms and behaviors."},
                {"step": 3, "topic": "Systematic Analysis", "rationale": "Applies mathematical analysis and evaluates performance bounds."}
            ]

        model = {
            "subject_name": subject_name,
            "subject_domain": domain,
            "subject_description": description,
            "purpose": purpose,
            "problems_solved": problems_solved,
            "real_world_applications": applications,
            "prerequisites": prerequisites,
            "major_knowledge_areas": knowledge_areas,
            "logical_learning_order": learning_order,
            "mermaid_knowledge_map": ""
        }
        model["mermaid_knowledge_map"] = cls._generate_fallback_mermaid(model)
        return model

    @classmethod
    def _fallback_subject_model(cls, title: str, text: str) -> Dict[str, Any]:
        model = cls._extractive_subject_model(title, text, 1)
        model["analysis_source"] = "heuristic_fallback"
        model["source_note"] = (
            "This overview uses heuristic general context and may include information "
            "not present in the uploaded document."
        )
        return model

    @classmethod
    def _generate_fallback_mermaid(cls, model: Dict[str, Any]) -> str:
        """Constructs a clean, syntactically valid Mermaid diagram representing the knowledge areas."""
        subj = re.sub(r'[^a-zA-Z0-9\s]', '', model.get("subject_name", "Subject"))
        areas = model.get("major_knowledge_areas", [])
        lines = [
            "flowchart TD",
            f"  SUBJ[\"{subj}\"]"
        ]
        for i, a in enumerate(areas):
            aid = f"KA{i+1}"
            aname = re.sub(r'[^a-zA-Z0-9\s\-]', '', a.get("name", f"Area {i+1}"))
            lines.append(f"  {aid}[\"{aname}\"]")
            lines.append(f"  SUBJ --> {aid}")

        # Add logical progression if available
        prog = model.get("logical_learning_order", [])
        if len(prog) >= 2:
            lines.append("  %% Learning Progression Path")
            prev_id = None
            for i, p in enumerate(prog[:4]):
                pid = f"ST{i+1}"
                pname = re.sub(r'[^a-zA-Z0-9\s\-]', '', p.get("topic", f"Step {i+1}"))
                lines.append(f"  {pid}[\"{pname}\"]")
                if prev_id:
                    lines.append(f"  {prev_id} -.-> {pid}")
                prev_id = pid

        return "\n".join(lines)

    @classmethod
    def validate_concept_against_subject(cls, concept_name: str, subject_name: str, doc_chunks: list) -> bool:
        """
        Validates if a concept belongs to the document subject or text chunks,
        preventing cross-subject contamination (e.g. CPU scheduling in Computer Networks).
        """
        c_lower = concept_name.lower().strip()
        s_lower = subject_name.lower().strip()

        # Check if concept text appears directly in any chunk
        for chunk in doc_chunks:
            if c_lower in chunk.text.lower():
                return True

        # Blacklist checks for known cross-domain collisions
        if "network" in s_lower:
            disallowed = ['cpu scheduling', 'deadlock', 'demand paging', 'virtual memory', 'process synchronization', 'semaphore', 'banker\'s algorithm', 'photosynthesis', 'mitosis']
            for d in disallowed:
                if d in c_lower:
                    return False
        elif "operating system" in s_lower:
            disallowed = ['csma/cd', 'csma/ca', 'crc-32', 'aloha protocol', 'photosynthesis', 'cellular respiration']
            for d in disallowed:
                if d in c_lower:
                    return False

        return True


# =============================================================================
# MODULE B: Hierarchical Syllabus Discovery Engine
# =============================================================================

class HierarchicalSyllabusDiscoveryEngine:
    """
    Discovers the complete, multi-tiered syllabus hierarchy across 100% of document chunks.
    Filters out author noise ('Wg Cdr Dr. K Srinivas Rao'), sentence fragments,
    and constructs clean parent-child topic trees.
    """

    # Regex patterns for detecting explicit hierarchy markers
    RE_MODULE_CHAPTER = re.compile(
        r'^(?:module|unit|chapter)\s*(\d+)[:\s\-–—]+([A-Z0-9][a-zA-Z0-9\s\-,:?&/()]+)',
        re.IGNORECASE
    )
    RE_NUMBERED_SECTION = re.compile(
        r'^(\d+\.\d+(?:\.\d+)*)[:\s\-–—]+([A-Z0-9][a-zA-Z0-9\s\-,:?&/()]+)'
    )
    RE_NUMBERED_ITEM = re.compile(
        r'^(\d+)\.\s+([A-Z][a-zA-Z0-9\s\-,:?&/()]{2,60})$'
    )
    RE_ALL_CAPS_HEADING = re.compile(
        r'^([A-Z][A-Z0-9\s\-,:?&/()]{3,60})$'
    )
    RE_TITLE_CASE_HEADING = re.compile(
        r'^([A-Z][a-zA-Z0-9/()]+(?:\s+[A-Z0-9][a-zA-Z0-9/()]+){0,4})$'
    )
    RE_IMPLICIT_FORMULA = re.compile(
        r'(?:hamming\s+distance|generator\s+polynomial|cyclic\s+redundancy\s+check|crc|checksum|efficiency|throughput|frame\s+size|sliding\s+window|go-back-n|selective\s+repeat|csma/cd|csma/ca|aloha|cdma|chip\s+sequence)',
        re.IGNORECASE
    )

    @classmethod
    def discover_and_persist_syllabus(cls, doc: Document) -> List[Topic]:
        """
        Discovers the hierarchical syllabus across all chunks and persists
        Topic models into the database with parent-child links.
        """
        chunks = list(doc.chunks.all().order_by('chunk_index'))
        if not chunks:
            logger.warning(f"[SyllabusDiscovery] Document {doc.id} has no chunks.")
            return []

        # 1. Discover Candidate Nodes
        raw_nodes = cls._extract_candidate_nodes(doc, chunks)

        # 2. Filter Noise and Deduplicate
        clean_nodes = cls._filter_and_deduplicate_nodes(raw_nodes, chunks)

        # 3. Build Multi-Tier Tree Structure
        tree_roots = cls._build_hierarchy_tree(clean_nodes, doc)

        # 4. Transactionally Persist into DB
        with transaction.atomic():
            doc.topics.all().delete()
            saved_topics = cls._persist_tree(tree_roots, doc, parent=None, path_prefix="")

        logger.info(f"[SyllabusDiscovery] Saved {len(saved_topics)} hierarchical topics for Document {doc.id}.")
        return saved_topics

    @classmethod
    def _extract_candidate_nodes(cls, doc: Document, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """Scans all chunks line-by-line to extract candidate syllabus headings and concepts."""
        candidates = []
        seen_names = set()

        for chunk in chunks:
            page = chunk.page_start
            lines = chunk.text.split('\n')

            for line in lines:
                s = line.strip()
                if not s or len(s) < 3:
                    continue

                # Filter running headers, author signatures, institution credits
                if is_author_or_institutional_noise(s):
                    continue

                # Check for explicit Module/Unit/Chapter
                m_chap = cls.RE_MODULE_CHAPTER.match(s)
                if m_chap:
                    mod_num = m_chap.group(1)
                    title = clean_heading_text(m_chap.group(2))
                    if not is_invalid_heading_fragment(title) and title.lower() not in seen_names:
                        seen_names.add(title.lower())
                        candidates.append({
                            "name": f"Module {mod_num}: {title}",
                            "raw_text": s,
                            "node_type": "knowledge_area" if int(mod_num) <= 5 else "chapter",
                            "explicit_level": 1,
                            "page": page,
                            "importance": "High",
                            "weight": 95,
                            "is_implicit": False
                        })
                    continue

                # Check for numbered section (e.g. "1.1 Types of Errors" or "2.3.1 HDLC Frames")
                m_sec = cls.RE_NUMBERED_SECTION.match(s)
                if m_sec:
                    num_str = m_sec.group(1)
                    title = clean_heading_text(m_sec.group(2))
                    if not is_invalid_heading_fragment(title) and title.lower() not in seen_names:
                        seen_names.add(title.lower())
                        dots = num_str.count('.')
                        node_type = "section" if dots == 1 else ("topic" if dots == 2 else "subtopic")
                        candidates.append({
                            "name": f"{num_str} {title}",
                            "raw_text": s,
                            "node_type": node_type,
                            "explicit_level": dots + 2,
                            "page": page,
                            "importance": "High" if dots <= 1 else "Medium",
                            "weight": max(70, 90 - dots * 10),
                            "is_implicit": False
                        })
                    continue

                # Check for numbered items (e.g. "1. ALOHA" or "2. Polling")
                m_num_item = cls.RE_NUMBERED_ITEM.match(s)
                if m_num_item:
                    item_num = m_num_item.group(1)
                    title = clean_heading_text(m_num_item.group(2))
                    if not is_author_or_institutional_noise(title) and not is_invalid_heading_fragment(title):
                        if title.lower() not in seen_names:
                            seen_names.add(title.lower())
                            candidates.append({
                                "name": title.title(),
                                "raw_text": s,
                                "node_type": "topic",
                                "explicit_level": 4,
                                "page": page,
                                "importance": "High",
                                "weight": 85,
                                "is_implicit": False
                            })
                    continue

                # Check for ALL CAPS structural headings (e.g. "ERROR DETECTION AND CORRECTION", "HAMMING DISTANCE")
                if len(s.split()) <= 6 and s.isupper() and len(s) >= 4:
                    title = clean_heading_text(s)
                    if not is_author_or_institutional_noise(title) and not is_invalid_heading_fragment(title):
                        title_formatted = title.title()
                        if title_formatted.lower() not in seen_names:
                            seen_names.add(title_formatted.lower())
                            candidates.append({
                                "name": title_formatted,
                                "raw_text": s,
                                "node_type": "section",
                                "explicit_level": 3,
                                "page": page,
                                "importance": "High",
                                "weight": 85,
                                "is_implicit": False
                            })
                    continue

                # Check for standalone Title-Case headings (e.g. "Carrier Sense Multiple Access", "Controlled Access")
                m_title_case = cls.RE_TITLE_CASE_HEADING.match(s)
                if m_title_case and not s.endswith(('.', ':', ';', ',')):
                    title = clean_heading_text(m_title_case.group(1))
                    if not is_author_or_institutional_noise(title) and not is_invalid_heading_fragment(title):
                        # Verify it has significant words and is not just a common sentence opener
                        words = title.split()
                        if 1 <= len(words) <= 5 and title.lower() not in seen_names:
                            # Avoid standalone generic words
                            if title.lower() not in ['figure', 'table', 'example', 'solution', 'problem', 'step', 'note', 'index']:
                                seen_names.add(title.lower())
                                candidates.append({
                                    "name": title.title(),
                                    "raw_text": s,
                                    "node_type": "topic" if len(words) >= 2 else "concept",
                                    "explicit_level": 4,
                                    "page": page,
                                    "importance": "Medium",
                                    "weight": 80,
                                    "is_implicit": False
                                })
                    continue

                # Check for high-yield implicit formula/protocol concepts in paragraph text
                if cls.RE_IMPLICIT_FORMULA.search(s) and any(kw in s.lower() for kw in ['formula', 'algorithm', 'equation', 'protocol', 'defined as', 'calculate']):
                    # Extract the concept name
                    concept_match = cls.RE_IMPLICIT_FORMULA.search(s)
                    if concept_match:
                        c_name = concept_match.group(0).title()
                        if c_name.lower() not in seen_names and len(c_name) > 3:
                            seen_names.add(c_name.lower())
                            candidates.append({
                                "name": c_name,
                                "raw_text": s[:200],
                                "node_type": "concept",
                                "explicit_level": 5,
                                "page": page,
                                "importance": "High",
                                "weight": 85,
                                "is_implicit": True
                            })

        # Ensure we have a sensible fallback if document had minimal explicit formatting
        if len(candidates) < 3:
            candidates.extend(cls._fallback_heuristic_candidates(doc, chunks))

        return candidates

    @classmethod
    def _fallback_heuristic_candidates(cls, doc: Document, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """Provides heuristic academic nodes if formatting lacked explicit heading tags."""
        subj = doc.subject or "Academic Subject"
        fallbacks = [
            {"name": f"{subj} Core Fundamentals", "raw_text": "", "node_type": "knowledge_area", "explicit_level": 1, "page": 1, "importance": "Foundational", "weight": 90, "is_implicit": False},
            {"name": "Operational Mechanisms & Protocols", "raw_text": "", "node_type": "chapter", "explicit_level": 2, "page": max(1, doc.page_count // 3), "importance": "High", "weight": 85, "is_implicit": False},
            {"name": "Mathematical Formulation & Performance Bounds", "raw_text": "", "node_type": "chapter", "explicit_level": 2, "page": max(1, (doc.page_count * 2) // 3), "importance": "High", "weight": 85, "is_implicit": False},
            {"name": "Comparative Analysis & Solved Numerical Problems", "raw_text": "", "node_type": "section", "explicit_level": 3, "page": doc.page_count, "importance": "Medium", "weight": 80, "is_implicit": False}
        ]
        return fallbacks

    @classmethod
    def _filter_and_deduplicate_nodes(cls, raw_nodes: List[Dict[str, Any]], chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """Filters out noise, short fragments, duplicate headings, and sorts by page."""
        filtered = []
        seen = set()

        for node in raw_nodes:
            name = node["name"].strip()
            # Basic validation
            if len(name) < 3 or is_author_or_institutional_noise(name) or is_invalid_heading_fragment(name):
                continue

            # Normalized key for deduplication
            norm_key = re.sub(r'^(?:module\s*\d+:|chapter\s*\d+:|\d+(?:\.\d+)*)\s*', '', name, flags=re.IGNORECASE).strip().lower()
            if norm_key in seen:
                continue
            seen.add(norm_key)

            # Assign description from nearest chunk text
            nearest_chunk = None
            for c in chunks:
                if c.page_start <= node["page"] <= c.page_end:
                    nearest_chunk = c
                    break
            if not nearest_chunk and chunks:
                nearest_chunk = chunks[0]

            desc = ""
            if nearest_chunk:
                # Find sentence containing the topic
                for sentence in nearest_chunk.text.split('.'):
                    if norm_key in sentence.lower():
                        desc = sentence.strip() + "."
                        break
                if not desc:
                    desc = nearest_chunk.text[:200].strip() + "..."

            node["description"] = desc[:250]
            filtered.append(node)

        # Sort by page order
        filtered.sort(key=lambda x: (x["page"], x["explicit_level"]))
        return filtered

    @classmethod
    def _build_hierarchy_tree(cls, nodes: List[Dict[str, Any]], doc: Document) -> List[Dict[str, Any]]:
        """
        Organizes flat nodes into a nested tree structure:
        Knowledge Area -> Chapter -> Section -> Topic -> Concept
        """
        if not nodes:
            return []

        roots = []
        current_area = None
        current_chapter = None
        current_section = None

        for node in nodes:
            level = node.get("explicit_level", 3)
            node_copy = dict(node)
            node_copy["children"] = []

            if level == 1 or node["node_type"] == "knowledge_area":
                roots.append(node_copy)
                current_area = node_copy
                current_chapter = None
                current_section = None
            elif level == 2 or node["node_type"] == "chapter":
                if current_area is not None:
                    current_area["children"].append(node_copy)
                else:
                    roots.append(node_copy)
                current_chapter = node_copy
                current_section = None
            elif level == 3 or node["node_type"] == "section":
                if current_chapter is not None:
                    current_chapter["children"].append(node_copy)
                elif current_area is not None:
                    current_area["children"].append(node_copy)
                else:
                    roots.append(node_copy)
                current_section = node_copy
            else: # Topic, Subtopic, Concept
                if current_section is not None:
                    current_section["children"].append(node_copy)
                elif current_chapter is not None:
                    current_chapter["children"].append(node_copy)
                elif current_area is not None:
                    current_area["children"].append(node_copy)
                else:
                    roots.append(node_copy)

        # If no root was created, create a top-level Knowledge Area wrapper
        if not roots:
            wrapper = {
                "name": doc.subject or "Main Curriculum",
                "node_type": "knowledge_area",
                "page": 1,
                "importance": "High",
                "weight": 90,
                "description": f"Curriculum overview for {doc.title}",
                "children": nodes,
                "is_implicit": False
            }
            roots = [wrapper]

        return roots

    @classmethod
    def _persist_tree(
        cls,
        nodes: List[Dict[str, Any]],
        doc: Document,
        parent: Optional[Topic] = None,
        path_prefix: str = ""
    ) -> List[Topic]:
        """Recursively persists tree nodes as Topic database records with hierarchy_path and parent links."""
        saved = []
        total_siblings = len(nodes)
        doc_max_page = doc.page_count or doc.chunks.count() or 1

        for i, node_dict in enumerate(nodes, 1):
            h_path = f"{path_prefix}.{i}" if path_prefix else str(i)
            page_start = node_dict.get("page", 1)

            # Determine page_end from next sibling's start page
            if i < total_siblings:
                next_start = nodes[i].get("page", page_start)
                page_end = max(page_start, next_start - 1) if next_start > page_start else page_start
            else:
                # Last sibling covers until parent end or document end
                parent_end = parent.page_end if (parent and parent.page_end > page_start) else doc_max_page
                page_end = max(page_start, parent_end)

            # Calculate page_end from children if children extend further
            children = node_dict.get("children", [])
            if children:
                child_pages = [c.get("page", page_start) for c in children]
                page_end = max(page_end, max(child_pages))

            topic = Topic.objects.create(
                document=doc,
                parent=parent,
                name=node_dict["name"][:255],
                node_type=node_dict.get("node_type", "topic"),
                hierarchy_path=h_path,
                order_index=i,
                description=node_dict.get("description", "")[:500],
                importance=node_dict.get("importance", "Medium"),
                weight=node_dict.get("weight", 80),
                source_page=page_start,
                page_start=page_start,
                page_end=page_end,
                coverage_status="DISCOVERED",
                is_implicit=node_dict.get("is_implicit", False),
                metadata_json=json.dumps({
                    "raw_text": node_dict.get("raw_text", ""),
                    "explicit_level": node_dict.get("explicit_level", 3)
                })
            )
            saved.append(topic)

            # Recurse for children
            if children:
                child_saved = cls._persist_tree(children, doc, parent=topic, path_prefix=h_path)
                saved.extend(child_saved)
                # Expand parent's page_end if children span beyond
                max_child_end = max([c.page_end for c in child_saved], default=page_end)
                if max_child_end > topic.page_end:
                    topic.page_end = max_child_end
                    topic.save(update_fields=['page_end'])

        return saved


# =============================================================================
# MODULE C: Deep Topic Teaching Engine
# =============================================================================

class DeepTopicTeachingEngine:
    """
    Synthesizes deep, academic teaching content for an individual Topic.
    Dynamic pedagogical dimensions rendered:
    1. Intuitive Foundation & Analogy
    2. Formal Academic Definition & Standards
    3. Why We Need It: Failure Mode Analysis
    4. Operational Mechanics & Internal Process Flow
    5. Step-by-Step Procedural Algorithm
    6. Architectural Breakdown & Field Layout
    7. Process / State Diagram (Mermaid)
    8. Mathematical Formulation & LaTeX Derivations ($...$ and $$...$$)
    9. Variables, Notation & Physical Units Table
    10. Verified Solved Numerical Examples (Step-by-Step Arithmetic)
    11. Real-World Systems & Industrial Implementation
    12. Comparative Analysis & Engineering Trade-offs
    13. Boundary Conditions & Critical Corner Cases
    14. Common Student Misconceptions & High-Frequency Traps
    15. GATE & University Exam Observations
    16. Rapid Review & Key Takeaway Checklist
    """

    ENGINE_VERSION = 4

    @classmethod
    def teach_topic(cls, topic: Topic, force_regenerate: bool = False) -> Dict[str, Any]:
        """Generates deep teaching content for a topic if not already cached."""
        metadata = topic.get_metadata()
        if (
            not force_regenerate
            and topic.coverage_status in ['TEACHING_READY', 'VERIFIED']
            and topic.teaching_content
            and metadata.get("teaching_engine_version") == cls.ENGINE_VERSION
        ):
            return {
                "topic_id": topic.id,
                "name": topic.name,
                "hierarchy_path": topic.hierarchy_path,
                "coverage_status": topic.coverage_status,
                "teaching_content": topic.teaching_content,
                "diagram_mermaid": topic.diagram_mermaid,
                "metadata": topic.get_metadata(),
                "cached": True
            }

        doc = topic.document
        chunks = doc.chunks.filter(
            page_start__lte=topic.page_end,
            page_end__gte=topic.page_start
        ).order_by('chunk_index')

        # If no page-exact chunks found, search chunks containing the topic name
        if not chunks.exists():
            topic_clean = re.sub(r'^(?:module\s*\d+:|chapter\s*\d+:|\d+(?:\.\d+)*)\s*', '', topic.name, flags=re.IGNORECASE).strip()
            chunks = doc.chunks.filter(text__icontains=topic_clean)[:4]
        context_text = "\n\n".join([f"[Page {c.page_start}-{c.page_end}]:\n{c.text}" for c in chunks])

        teaching_data = cls._query_ollama_teaching(
            topic,
            doc.subject,
            context_text,
            language=doc.output_language or "en"
        ) if context_text.strip() else None
        is_model_generated = bool(teaching_data and teaching_data.get("teaching_content"))
        if not is_model_generated:
            teaching_data = cls._source_excerpt_teaching(topic, context_text)

        # Update Topic record
        archetype = teaching_data.get("archetype") or classify_topic_archetype(topic.name, context_text)
        topic.teaching_content = teaching_data.get("teaching_content", "")
        topic.diagram_mermaid = teaching_data.get("diagram_mermaid", "")
        topic.coverage_status = "TEACHING_READY" if is_model_generated else "EXTRACTED"
        meta = topic.get_metadata()
        meta.update({
            "archetype": archetype,
            "teaching_engine_version": cls.ENGINE_VERSION,
            "formulas": teaching_data.get("formulas", []),
            "solved_examples": teaching_data.get("solved_examples", []),
            "misconceptions": teaching_data.get("misconceptions", []),
            "applications": teaching_data.get("applications", []),
            "teaching_generated_at": timezone.now().isoformat()
        })
        topic.set_metadata(meta)
        topic.save(update_fields=['teaching_content', 'diagram_mermaid', 'coverage_status', 'metadata_json'])

        return {
            "topic_id": topic.id,
            "name": topic.name,
            "hierarchy_path": topic.hierarchy_path,
            "coverage_status": topic.coverage_status,
            "teaching_content": topic.teaching_content,
            "diagram_mermaid": topic.diagram_mermaid,
            "metadata": meta,
            "cached": False
        }

    @classmethod
    def batch_teach_document(cls, doc: Document, max_topics: int = 15, heartbeat_cb: Optional[Any] = None) -> int:
        """Progressively generates teaching material for top-priority topics in a document."""
        topics = list(doc.topics.filter(coverage_status__in=['DISCOVERED', 'EXTRACTED']).order_by('order_index', 'id')[:max_topics])
        count = 0
        total_cnt = len(topics)
        for i, t in enumerate(topics, 1):
            try:
                if heartbeat_cb:
                    try:
                        heartbeat_cb(t, i, total_cnt)
                    except Exception:
                        pass
                cls.teach_topic(t, force_regenerate=False)
                count += 1
            except Exception as e:
                logger.warning(f"Error teaching topic {t.id} ({t.name}): {e}")
        return count

    @classmethod
    def _source_excerpt_teaching(cls, topic: Topic, context_text: str) -> Dict[str, Any]:
        """Return source excerpts instead of fabricating a lesson when the model is unavailable."""
        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", context_text)
            if len(paragraph.strip()) > 30
        ]
        topic_terms = [
            term.lower() for term in re.findall(r"\b[\w-]{3,}\b", topic.name)
            if term.lower() not in {"chapter", "section", "topic", "module"}
        ]
        relevant = [
            paragraph for paragraph in paragraphs
            if any(term in paragraph.lower() for term in topic_terms)
        ]
        selected = relevant or paragraphs
        formulas = re.findall(r"\$\$(.+?)\$\$|\$([^$\n]+)\$", context_text, re.S)
        examples = [
            paragraph for paragraph in selected
            if re.search(r"\b(example|for instance|calculate|problem|solution|e\.g\.)\b", paragraph, re.I)
        ]

        content = [f"# {topic.name}", ""]
        if selected:
            content.extend([
                "> Offline notes show extracted source material only. They are not a verified explanation.",
                "",
                "## Relevant source text",
                "",
                "\n\n".join(selected[:8])
            ])
        else:
            content.extend([
                "> No source text was mapped to this topic, so an explanation was not generated.",
                "",
                "Add or reprocess source material that covers this topic, then try again."
            ])

        content.extend(["", "## Formulas in the source", ""])
        if formulas:
            content.extend(f"- `${(display or inline).strip()}$`" for display, inline in formulas[:8])
        else:
            content.append("No formula was identified in the mapped text.")

        content.extend(["", "## Examples in the source", ""])
        content.append(
            "\n\n".join(examples[:3])
            if examples else "No worked example was identified in the mapped text."
        )
        content.extend([
            "",
            "## Next step",
            "",
            "Use an available language model or provide more source material for a plain-language explanation, worked method, and diagram."
        ])

        return {
            "teaching_content": "\n".join(content),
            "diagram_mermaid": "",
            "formulas": [(display or inline).strip() for display, inline in formulas[:8]],
            "solved_examples": [],
            "misconceptions": [],
            "applications": []
        }

    @classmethod
    def _query_ollama_teaching(
        cls,
        topic: Topic,
        subject: str,
        context_text: str,
        language: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """Invokes AI with the adaptive archetype prompt to generate deep, topic-specific pedagogical content."""
        if not check_ai_provider_status().get("can_generate") or not context_text.strip():
            return None

        archetype = classify_topic_archetype(topic.name, context_text)
        prompt = build_adaptive_topic_teaching_prompt(
            topic_name=topic.name,
            topic_path=topic.hierarchy_path or "1",
            pages=f"{topic.page_start}-{topic.page_end}",
            subject=subject,
            archetype=archetype,
            source_context=context_text[:7500],
            language=language
        )

        response_text, success, _ = query_ai(prompt, format_json=True, timeout=90, temperature=0.15)
        if success and response_text:
            parsed = parse_json_safely(response_text)
            if isinstance(parsed, dict) and parsed.get("teaching_content"):
                parsed["archetype"] = archetype
                return parsed
        return None



# =============================================================================
# MODULE D: Document Coverage Engine
# =============================================================================

class DocumentCoverageEngine:
    """
    Computes a comprehensive audit and verification matrix for a document:
    - Total pages discovered vs. covered by topics
    - Discovered vs. Extracted vs. Teaching-Ready vs. Verified topics
    - Mathematical formulas indexed
    - Algorithms and protocols cataloged
    - Uncovered gap analysis
    """

    @classmethod
    def calculate_coverage(cls, doc: Document) -> Dict[str, Any]:
        """Calculates the full coverage matrix for the specified document."""
        total_pages = doc.page_count or doc.chunks.count() or 1
        topics = doc.topics.all()

        total_topics = topics.count()
        if total_topics == 0:
            return {
                "document_id": doc.id,
                "title": doc.title,
                "total_pages": total_pages,
                "covered_pages_count": 0,
                "coverage_percentage": 0.0,
                "total_topics": 0,
                "by_status": {"DISCOVERED": 0, "EXTRACTED": 0, "TEACHING_READY": 0, "VERIFIED": 0},
                "by_node_type": {},
                "formulas_count": 0,
                "algorithms_count": 0,
                "gaps": [{"start": 1, "end": total_pages}],
                "is_complete": False
            }

        # Calculate covered pages
        covered_pages: Set[int] = set()
        by_status = {"DISCOVERED": 0, "EXTRACTED": 0, "TEACHING_READY": 0, "VERIFIED": 0}
        by_node_type: Dict[str, int] = {}
        formulas_count = 0
        algorithms_count = 0

        for t in topics:
            by_status[t.coverage_status] = by_status.get(t.coverage_status, 0) + 1
            by_node_type[t.node_type] = by_node_type.get(t.node_type, 0) + 1

            p_start = t.page_start or t.source_page or 1
            p_end = t.page_end or p_start
            for p in range(p_start, p_end + 1):
                if 1 <= p <= total_pages:
                    covered_pages.add(p)

            meta = t.get_metadata()
            formulas_count += len(meta.get("formulas", []))
            if any(k in t.name.lower() for k in ['algorithm', 'protocol', 'procedure', 'method']):
                algorithms_count += 1

        covered_pages_count = len(covered_pages)
        coverage_pct = round((covered_pages_count / total_pages) * 100.0, 1) if total_pages > 0 else 100.0
        coverage_pct = min(100.0, coverage_pct)

        # Detect gaps
        all_pages = set(range(1, total_pages + 1))
        uncovered = sorted(list(all_pages - covered_pages))
        gaps = []
        if uncovered:
            gap_start = uncovered[0]
            gap_prev = uncovered[0]
            for p in uncovered[1:]:
                if p == gap_prev + 1:
                    gap_prev = p
                else:
                    gaps.append({"start": gap_start, "end": gap_prev})
                    gap_start = p
                    gap_prev = p
            gaps.append({"start": gap_start, "end": gap_prev})

        return {
            "document_id": doc.id,
            "title": doc.title,
            "total_pages": total_pages,
            "covered_pages_count": covered_pages_count,
            "coverage_percentage": coverage_pct,
            "total_topics": total_topics,
            "by_status": by_status,
            "by_node_type": by_node_type,
            "formulas_count": formulas_count,
            "algorithms_count": algorithms_count,
            "gaps": gaps,
            "is_complete": coverage_pct >= 90.0 and by_status["TEACHING_READY"] > 0
        }
