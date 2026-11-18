"""
=============================================================================
StudyAI — Master Document Intelligence & Teaching System Prompts
=============================================================================
Defines the strict pedagogical guidelines, document-type structural blueprints,
concept interrogation rules, and few-shot formatting contracts.
=============================================================================
"""

import re
from typing import Dict, Any, List, Optional

# =============================================================================
# 1. Master System Prompt & 15 Strict Grounding Rules
# =============================================================================

MASTER_DOCUMENT_INTELLIGENCE_PROMPT = """You are an expert document-intelligence and teaching system.

Your task is NOT to shorten the document mechanically.
Your task is to understand the document and reconstruct its knowledge in a way that another human can learn from.

STRICT GROUNDING RULES:
1. Use ONLY information grounded in the supplied document representation.
2. Do not invent facts, examples, statistics, formulas, citations, or conclusions.
3. Do not merely rewrite the original paragraphs.
4. Do not produce generic statements such as "this document discusses..."
5. Preserve important technical terminology.
6. Explain difficult terminology in simple language.
7. Preserve important relationships between concepts.
8. Preserve important numbers, formulas, conditions, constraints and exceptions.
9. Do not remove information merely because it is difficult.
10. Distinguish facts stated by the source from interpretations.
11. If information is unavailable, explicitly state that it is not provided.
12. Do not repeat the same concept in multiple sections unless repetition improves understanding.
13. Do not create artificial sections that have no supporting content.
14. Prioritize concepts according to their importance in the source.
15. Preserve source/page references for important claims (e.g. *(Source: Page X)*).

FOR EVERY MAJOR CONCEPT, DETERMINE:
- What is it?
- What does it mean?
- Why is it important?
- How does it work?
- What are its components?
- What are its relationships with other concepts?
- Is there an example?
- Are there limitations or exceptions?
- Where is it supported in the source?

QUALITY REQUIREMENT:
The final answer must allow a reader to understand the document without repeatedly returning to the original document.
Do not optimize for minimum length.
Optimize for: UNDERSTANDING + ACCURACY + COVERAGE + CLARITY.
"""

# Backward compatibility and academic notes guidelines
ACADEMIC_NOTE_ANALYSIS_GUIDELINES = f"""{MASTER_DOCUMENT_INTELLIGENCE_PROMPT}

ACADEMIC NOTE ANALYSIS INSTRUCTIONS:
- If supplementary contextual knowledge is needed to clarify an ambiguous concept, label it as additional context clearly so the student knows it extends beyond the source text.
- Address advantages, disadvantages, limitations, trade-offs, and edge cases for all key mechanisms.
- Automated checks assess structure, length, math formatting; factual accuracy is not independently verified, so ensure claims are grounded in source text.
- MANDATORY CALCULATION STRUCTURE (Every numerical problem must follow this 10-part structure):
  1. Problem Statement
  2. Given Information (with symbols and SI units)
  3. Required Quantity / To Find
  4. Applicable Formula
  5. Explanation of Symbols
  6. Substitution of Values
  7. Step-by-Step Calculation (every mathematical transformation on a separate line in an aligned environment \\[ \\begin{{aligned}} ... \\end{{aligned}} \\])
  8. Intermediate Results
  9. Final Answer (highlighted in bold with units)
  10. Verification and Units (dimensional analysis / boundary check)
- MATHEMATICAL DERIVATION FORMATTING:
  * Every significant mathematical transformation must appear on a separate line.
  * Use LaTeX aligned equation environments \\[ \\begin{{aligned}} LHS &= RHS \\\\ ... \\end{{aligned}} \\].
  * Never use manual spaces to align equations. Never combine an entire derivation into one paragraph.
- CLASSIFICATION COMPLETENESS:
  * When a classification, categorization, or typology is introduced, you MUST explain every individual category in detail with its definition, characteristics, and examples. Never list categories without explaining each one.
- ADAPTIVE TOPIC STRUCTURE:
  * Adapt your structure to the topic type: Conceptual, Classification, Process, Comparison, Formula, Algorithm, or Proof.
- FACTUAL GROUNDING:
  * Use only the uploaded study document for factual claims. Do not invent facts or numbers.
"""

# =============================================================================
# 2. Document Type Structural Blueprints
# =============================================================================

DOCUMENT_TYPE_STRUCTURES = {
    "ACADEMIC": {
        "name": "Academic",
        "description": "Textbooks, course modules, lecture notes, syllabus materials",
        "sections": [
            ("Big Picture", "High-level intellectual context, problem domain, and real-world significance."),
            ("Core Concepts", "Fundamental concepts, principles, and conceptual architecture."),
            ("Definitions & Terminology", "Key terms defined both with formal precision and intuitive plain language."),
            ("Principles & Theorems", "Governing laws, axioms, invariances, and theoretical foundations."),
            ("Formulas & Derivations", "Clean LaTeX equations ($...$ and $$...$$), variables, units, and mathematical conditions."),
            ("Worked Examples", "Concrete source-grounded step-by-step examples with calculations and walkthroughs."),
            ("Common Confusions & Traps", "Subtle pitfalls, boundary edge cases, and frequent misconceptions."),
            ("Key Takeaways", "Consolidated, high-yield summary of indispensable insights.")
        ]
    },
    "RESEARCH": {
        "name": "Research",
        "description": "Peer-reviewed scientific papers, conference proceedings, preprints",
        "sections": [
            ("Research Problem", "The central scientific question, knowledge gap, and thesis."),
            ("Objectives & Hypothesis", "Primary hypotheses and intended research outcomes."),
            ("Methodology & Design", "Experimental design, theoretical frameworks, protocols, and workflows."),
            ("Data & Materials", "Datasets, baselines, benchmarks, hardware/software setup, and samples."),
            ("Experiments & Evaluation", "Step-by-step empirical tests, ablation studies, and comparisons."),
            ("Results", "Quantitative outcomes, metrics, statistical significance, and tables."),
            ("Key Findings & Contributions", "Novel insights, breakthrough discoveries, and domain advancements."),
            ("Limitations & Uncertainties", "Scope constraints, potential biases, unaddressed conditions, and future work."),
            ("Conclusion", "Final verdict on the hypothesis and overarching scientific implications.")
        ]
    },
    "BUSINESS": {
        "name": "Business",
        "description": "Executive briefs, quarterly reports, business plans, financial filings",
        "sections": [
            ("Executive Summary", "Strategic snapshot, critical results, and strategic imperative."),
            ("Business Context & Market Dynamics", "Market environment, industry backdrop, and problem statement."),
            ("Key Metrics & Financials", "Revenue, margins, growth, ROI, CAC, LTV, and performance indicators."),
            ("Operational Findings", "Internal performance, departmental achievements, and operational data."),
            ("Market Trends & Shifts", "Customer behavior, competitor moves, and macro trends."),
            ("Strategic Risks & Vulnerabilities", "Operational, financial, regulatory, and market risks with impact analysis."),
            ("Growth Opportunities", "Untapped market segments, efficiencies, and strategic initiatives."),
            ("Actionable Recommendations", "Concrete next steps, prioritized initiatives, and resource allocations.")
        ]
    },
    "TECHNICAL": {
        "name": "Technical",
        "description": "System architecture, API documentation, engineering manuals, runbooks",
        "sections": [
            ("Purpose & Scope", "System purpose, problem addressed, and operational scope."),
            ("Architecture Overview", "High-level design, components, interfaces, and architectural patterns."),
            ("Components & Specifications", "Hardware/software components, data models, schemas, and specs."),
            ("Operation & Workflow", "Runtime mechanics, lifecycle, state machines, and data flow."),
            ("Procedures & Execution Steps", "Step-by-step implementation, installation, or procedural instructions."),
            ("Configuration & Parameters", "Settings, flags, environment variables, and constraints."),
            ("Concrete Examples", "Code snippets, configuration samples, or CLI command walkthroughs."),
            ("Limitations & Constraints", "Performance ceilings, rate limits, latency bounds, and unsupported features."),
            ("Troubleshooting & Edge Cases", "Common failure modes, diagnostic steps, error codes, and fixes.")
        ]
    },
    "LEGAL": {
        "name": "Legal",
        "description": "Contracts, agreements, terms of service, compliance policies, regulations",
        "sections": [
            ("Purpose & Scope", "Legal objective, instrument type, and governing framework."),
            ("Parties Involved", "Defined entities, roles, agents, and effective dates."),
            ("Obligations & Covenants", "Binding duties, deliverables, and performance commitments."),
            ("Rights & Entitlements", "Privileges, licenses granted, remedies, and protections."),
            ("Restrictions & Prohibitions", "Negative covenants, non-disclosure, exclusivity, and use constraints."),
            ("Important Clauses & Terms", "Core provisions, warranties, representations, and indemnities."),
            ("Exceptions & Exclusions", "Carve-outs, force majeure, liability limits, and non-applicable scenarios."),
            ("Risks & Liabilities", "Default penalties, damages, exposure, and breach consequences."),
            ("Deadlines & Milestones", "Timelines, notice periods, renewal triggers, and termination schedule."),
            ("Plain-English Explanation", "Accessible breakdown translating dense legalese into clear lay terms.")
        ]
    },
    "GENERAL": {
        "name": "General",
        "description": "Articles, historical accounts, policy guides, reports, books",
        "sections": [
            ("Executive Overview", "Essential thesis, scope, and significance."),
            ("Main Ideas & Arguments", "Primary thematic points and logical structure."),
            ("Important Concepts", "Core conceptual building blocks and definitions."),
            ("Detailed Explanation", "Comprehensive section-by-section breakdown with evidence."),
            ("Relationships & Connections", "How concepts, events, or entities interact and depend on each other."),
            ("Concrete Examples", "Real-world cases, historical evidence, or illustrative applications."),
            ("Important Data & Facts", "Preserved figures, dates, statistics, and verifiable findings."),
            ("Risks, Nuances & Limitations", "Caveats, counterarguments, uncertainties, and constraints."),
            ("Key Takeaways", "Indispensable conclusions and actionable knowledge.")
        ]
    }
}

# =============================================================================
# 3. Document Genre Classifier
# =============================================================================

def classify_document_genre(text: str, title: str = "") -> str:
    """
    Classifies a document into one of 6 primary genres:
    ACADEMIC, RESEARCH, BUSINESS, TECHNICAL, LEGAL, or GENERAL.
    Uses multi-signal keyword density, structural markers, and heading patterns.
    """
    if not text:
        return "GENERAL"

    sample = (title + "\n" + text[:25000]).lower()

    scores = {
        "LEGAL": 0,
        "RESEARCH": 0,
        "BUSINESS": 0,
        "TECHNICAL": 0,
        "ACADEMIC": 0,
        "GENERAL": 1  # Base score
    }

    # 1. LEGAL Signals
    legal_terms = [
        r'\bherein\b', r'\bwhereas\b', r'\bparties\b', r'\bindemnif\w+',
        r'\bliability\b', r'\bgoverning law\b', r'\bjurisdiction\b', r'\barbitration\b',
        r'\bconfidentiality agreement\b', r'\bnon-disclosure\b', r'\bterms of service\b',
        r'\bcontract\b', r'\bseverability\b', r'\bwarranties\b', r'\bbreach of\b',
        r'\bintellectual property rights\b', r'\bin witness whereof\b'
    ]
    for pat in legal_terms:
        matches = len(re.findall(pat, sample))
        scores["LEGAL"] += matches * 2

    # 2. RESEARCH Signals
    research_terms = [
        r'\babstract\b', r'\bmethodology\b', r'\bliterature review\b', r'\brelated work\b',
        r'\bexperiments?\b', r'\bdataset\b', r'\bbaseline\b', r'\bstate-of-the-art\b',
        r'\bdoi:\b', r'\barxiv:\b', r'\bproceedings of\b', r'\bstatistical significance\b',
        r'\bp-value\b', r'\bconfidence interval\b', r'\bempirical results?\b', r'\bablation study\b'
    ]
    for pat in research_terms:
        matches = len(re.findall(pat, sample))
        scores["RESEARCH"] += matches * 2

    # 3. BUSINESS Signals
    business_terms = [
        r'\bexecutive summary\b', r'\brevenue\b', r'\bprofit margin\b', r'\bebitda\b',
        r'\bfiscal year\b', r'\bquarterly report\b', r'\broi\b', r'\bkpis?\b',
        r'\bmarket share\b', r'\bcash flow\b', r'\bswot analysis\b', r'\bshareholders?\b',
        r'\bbalance sheet\b', r'\bforecast\b', r'\bfinancial results\b', r'\boperating costs?\b'
    ]
    for pat in business_terms:
        matches = len(re.findall(pat, sample))
        scores["BUSINESS"] += matches * 2

    # 4. TECHNICAL Signals
    technical_terms = [
        r'\barchitecture\b', r'\bapi\b', r'\bsdk\b', r'\bcli\b', r'\bendpoints?\b',
        r'\bdeployment\b', r'\binstallation\b', r'\bconfiguration\b', r'\brunbook\b',
        r'\btroubleshooting\b', r'\bparameters?\b', r'\bprerequisites?\b', r'\bprotocol\b',
        r'\bjson\b', r'\byaml\b', r'\bhardware\b', r'\bfirmware\b', r'\blatency\b', r'\bthroughput\b'
    ]
    for pat in technical_terms:
        matches = len(re.findall(pat, sample))
        scores["TECHNICAL"] += matches * 2

    # 5. ACADEMIC Signals
    academic_terms = [
        r'\bchapter\b', r'\bsyllabus\b', r'\blecture\b', r'\btextbook\b',
        r'\btheorems?\b', r'\blemma\b', r'\bproof\b', r'\bcorollary\b',
        r'\bworked examples?\b', r'\bexercise\b', r'\bproblem set\b', r'\bderivation\b',
        r'\bdefinition\s+\d', r'\bmodule\s+\d', r'\bunit\s+\d', r'\bexam\b'
    ]
    for pat in academic_terms:
        matches = len(re.findall(pat, sample))
        scores["ACADEMIC"] += matches * 2

    # Heading Pattern Boosts
    if re.search(r'^\s*(?:abstract|methodology|experimental results)\b', sample, re.M):
        scores["RESEARCH"] += 10
    if re.search(r'^\s*(?:executive summary|financial highlights|market overview)\b', sample, re.M):
        scores["BUSINESS"] += 10
    if re.search(r'^\s*(?:system architecture|api reference|configuration guide)\b', sample, re.M):
        scores["TECHNICAL"] += 10
    if re.search(r'^\s*(?:this agreement|in witness whereof|governing law)\b', sample, re.M):
        scores["LEGAL"] += 15
    if re.search(r'^\s*(?:chapter\s+\d|unit\s+\d|lecture\s+\d)\b', sample, re.M):
        scores["ACADEMIC"] += 10

    # Pick highest scoring genre
    sorted_genres = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_genre, top_score = sorted_genres[0]

    # If top score is weak, default to GENERAL
    if top_score < 6:
        return "GENERAL"
    return top_genre


# =============================================================================
# 4. Master Prompt Assembly Function
# =============================================================================

def build_document_intelligence_prompt(
    doc_title: str,
    doc_genre: str,
    source_context: str,
    mode: str = "detailed",
    target_language: str = "en",
    depth: str = "detailed",
    output_style: str = "standard"
) -> str:
    """
    Constructs a comprehensive AI prompt that enforces strict grounding,
    concept interrogation, depth calibration, output style adaptation,
    and the specific structural blueprint of the document genre.
    """
    genre_info = DOCUMENT_TYPE_STRUCTURES.get(doc_genre, DOCUMENT_TYPE_STRUCTURES["GENERAL"])
    genre_name = genre_info["name"]

    sections_outline = "\n".join(
        f"- {sec_title}: {sec_desc}"
        for sec_title, sec_desc in genre_info["sections"]
    )

    lang_instruction = f"Output language: {target_language}." if target_language and target_language != 'en' else ""

    # Depth calibration
    depth_instructions = {
        "concise": "DEPTH: CONCISE. Provide direct, highly focused summaries preserving key facts, formulas, and conclusions without tangential elaboration.",
        "brief": "DEPTH: CONCISE. Provide direct, highly focused summaries preserving key facts, formulas, and conclusions without tangential elaboration.",
        "detailed": "DEPTH: DETAILED. Provide a comprehensive explanation covering all major sections, mechanisms, definitions, and examples in full depth.",
        "comprehensive": "DEPTH: EXHAUSTIVE / VERY DETAILED. Provide complete, deep coverage explaining every concept, subtopic, proof step, formula, and nuance with maximal pedagogical clarity.",
        "very_detailed": "DEPTH: EXHAUSTIVE / VERY DETAILED. Provide complete, deep coverage explaining every concept, subtopic, proof step, formula, and nuance with maximal pedagogical clarity.",
        "exhaustive": "DEPTH: EXHAUSTIVE / VERY DETAILED. Provide complete, deep coverage explaining every concept, subtopic, proof step, formula, and nuance with maximal pedagogical clarity."
    }
    depth_guide = depth_instructions.get(str(depth).lower(), depth_instructions["detailed"])

    # Output style adaptation
    style_instructions = {
        "academic": "STYLE: ACADEMIC & RIGOROUS. Use precise scholarly language, formal definitions, theoretical foundations, and mathematical rigor.",
        "technical": "STYLE: TECHNICAL & SYSTEMIC. Focus on architectures, specifications, operation procedures, parameters, and concrete mechanisms.",
        "business": "STYLE: EXECUTIVE & STRATEGIC. Emphasize operational context, quantitative metrics, risks, strategic trade-offs, and actionable decisions.",
        "simple": "STYLE: SIMPLE & ACCESSIBLE. Translate dense jargon into intuitive plain-English explanations using clear analogies while strictly preserving technical precision.",
        "standard": "STYLE: BALANCED & CLEAR. Deliver balanced, authoritative explanations accessible to students and professionals alike."
    }
    style_guide = style_instructions.get(str(output_style).lower(), style_instructions["standard"])

    return f"""{MASTER_DOCUMENT_INTELLIGENCE_PROMPT}

TARGET DOCUMENT TYPE: {genre_name.upper()} ({genre_info['description']})
{lang_instruction}
{depth_guide}
{style_guide}

REQUIRED ADAPTIVE STRUCTURE FOR THIS {genre_name.upper()} DOCUMENT:
{sections_outline}

CONCEPT INTERROGATION REQUIREMENT:
For every major concept discovered in the text, you must address:
1. What is it?
2. What does it mean?
3. Why is it important?
4. How does it work?
5. What are its components?
6. What are its relationships with other concepts?
7. Is there a concrete example?
8. Are there limitations or exceptions?
9. Where is it supported in the source? (e.g. Page X)

INTERNAL VERIFICATION CHECKLIST (Verify before finalizing):
- Did every major section receive thorough coverage?
- Did I preserve all important facts, numbers, and formulas?
- Did I explain important concepts rather than merely mention them?
- Did I avoid hallucinations?
- Did I remove unnecessary repetition?
- Did I preserve source references?
- Does the output strictly match the {genre_name} blueprint without forcing irrelevant academic/exam cards?

DOCUMENT TITLE: "{doc_title}"

GROUNDED SOURCE CONTENT:
\"\"\"
{source_context}
\"\"\"

Produce the comprehensive, structured, natural Markdown explanation:
"""


# =============================================================================
# 5. Adaptive Topic Archetype Classifier & Teaching Framework
# =============================================================================

TOPIC_ARCHETYPES = {
    "THEORETICAL": {
        "name": "Theoretical Foundation",
        "description": "Core concepts, principles, definitions, laws, theorems, properties",
        "emphasis": "Clear definitions, intuitive analogies, first-principles mechanisms, and source examples."
    },
    "NUMERICAL": {
        "name": "Numerical & Calculation Solver",
        "description": "Mathematical problems, quantitative calculations, formulas, numerical data",
        "emphasis": "Given info, required target, formula breakdown, step-by-step substitution without skipping steps, units, and verification."
    },
    "ALGORITHM": {
        "name": "Algorithm & Computational Logic",
        "description": "Procedural logic, pseudocode, state transitions, complexity analysis",
        "emphasis": "High-level intuition, operational steps, Mermaid flowchart, and time/space complexity."
    },
    "ARCHITECTURE": {
        "name": "System Architecture & Structure",
        "description": "Component layouts, block diagrams, structural layers, hardware/software modules",
        "emphasis": "Component hierarchy, Mermaid block diagram, interface interactions, and data flow."
    },
    "COMPARISON": {
        "name": "Comparative Analysis & Trade-Offs",
        "description": "Distinctions between technologies, protocols, algorithms, or approaches",
        "emphasis": "Structured comparison table, distinction criteria, advantages/disadvantages, and decision rules."
    },
    "PROCESS": {
        "name": "Sequential Workflow & Protocol",
        "description": "Multi-stage workflows, lifecycles, handshakes, procedures, state machines",
        "emphasis": "Preconditions, ordered numbered stages, Mermaid sequence/state diagram, and exception handling."
    },
    "CASE_STUDY": {
        "name": "Applied Case Study & Scenario",
        "description": "Real-world implementations, enterprise scenarios, empirical studies",
        "emphasis": "Operational context, problem statement, diagnostic analysis, intervention, and measurable outcomes."
    }
}


def classify_topic_archetype(topic_name: str, topic_text: str = "") -> str:
    """
    Classifies a topic/subtopic into one of 7 adaptive pedagogical archetypes:
    NUMERICAL, ALGORITHM, ARCHITECTURE, COMPARISON, PROCESS, CASE_STUDY, THEORETICAL.
    """
    t_name_lower = (topic_name or "").lower()
    combined = f"{t_name_lower}\n{(topic_text or '')[:4000]}".lower()

    # 1. COMPARISON (High Priority on explicit 'vs' or 'comparison')
    if re.search(r'\b(vs\.?|versus|compare|comparison|difference\s+between|distinction\s+between|trade-?offs?)\b', t_name_lower) or \
       re.search(r'\b(comparison\s+table|key\s+distinctions?|compared\s+to|advantages?\s+and\s+disadvantages?)\b', combined):
        return "COMPARISON"

    # 2. NUMERICAL / CALCULATION
    numerical_keywords = [
        r'\bcalculate\b', r'\bcomputation\b', r'\bnumerical\b', r'\bsolve\b',
        r'\bfind\s+the\b', r'\bhamming\s+distance\b', r'\bcrc\b', r'\bcyclic\s+redundancy\b',
        r'\bchecksum\b', r'\befficiency\b', r'\bthroughput\b', r'\bbandwidth-delay\b',
        r'\bsubnet\s+mask\b', r'\baddressing\b', r'\bformula\b', r'\bequation\b',
        r'\bprobability\b', r'\bvariance\b', r'\bstandard\s+deviation\b', r'\bcost\b', r'\bmargins?\b'
    ]
    has_math_symbols = bool(re.search(r'(?:\$\$|\\frac|\b[0-9]+\s*(?:ms|kbps|mbps|gbps|hz|khz|mhz|ghz|%|\$)\b)', combined))
    if any(re.search(p, t_name_lower) for p in numerical_keywords) or (has_math_symbols and any(re.search(p, combined) for p in numerical_keywords)):
        return "NUMERICAL"

    # 3. ALGORITHM
    algo_keywords = [
        r'\balgorithm\b', r'\bpseudocode\b', r'\bdijkstra\b', r'\bbellman\b',
        r'\btraversal\b', r'\bsorting\b', r'\bsearching\b', r'\bstate\s+elimination\b',
        r'\bminimization\b', r'\bcomplexity\b', r'\btime\s+complexity\b', r'\bspace\s+complexity\b',
        r'\bo\([n0-9log\s]+\)', r'\bheuristic\b', r'\bdynamic\s+programming\b'
    ]
    if any(re.search(p, combined) for p in algo_keywords):
        return "ALGORITHM"

    # 4. ARCHITECTURE
    arch_keywords = [
        r'\barchitecture\b', r'\bblock\s+diagram\b', r'\blayered\s+architecture\b',
        r'\bosi\s+model\b', r'\btcp/ip\b', r'\bclient-server\b', r'\bmicroservices\b',
        r'\bcomponent\s+hierarchy\b', r'\bframe\s+format\b', r'\bpacket\s+format\b',
        r'\bheader\s+format\b', r'\bpipeline\s+architecture\b', r'\bhardware\s+organization\b'
    ]
    if any(re.search(p, combined) for p in arch_keywords):
        return "ARCHITECTURE"

    # 5. PROCESS / WORKFLOW
    process_keywords = [
        r'\bprocess\b', r'\bprocedure\b', r'\bworkflow\b', r'\blifecycle\b',
        r'\bhandshake\b', r'\bthree-way\s+handshake\b', r'\bconnection\s+establishment\b',
        r'\bstate\s+machine\b', r'\bstate\s+diagram\b', r'\btransition\s+diagram\b',
        r'\bprotocol\s+execution\b', r'\bstep-by-step\s+procedure\b'
    ]
    if any(re.search(p, combined) for p in process_keywords):
        return "PROCESS"

    # 6. CASE STUDY
    case_keywords = [
        r'\bcase\s+study\b', r'\breal-world\s+scenario\b', r'\bincident\b',
        r'\bempirical\s+study\b', r'\bfield\s+study\b', r'\bpost-mortem\b'
    ]
    if any(re.search(p, combined) for p in case_keywords):
        return "CASE_STUDY"

    # 7. Default to THEORETICAL
    return "THEORETICAL"


def build_adaptive_topic_teaching_prompt(
    topic_name: str,
    topic_path: str,
    pages: str,
    subject: str,
    archetype: str,
    source_context: str,
    language: str = "en"
) -> str:
    """
    Constructs an adaptive pedagogical teaching prompt tailored specifically to the
    topic archetype (Numerical, Algorithm, Architecture, Comparison, Process, Case Study, Theoretical).
    Strictly enforces grounded explanations, human teacher tone, and clear visual structures.
    """
    archetype_info = TOPIC_ARCHETYPES.get(archetype, TOPIC_ARCHETYPES["THEORETICAL"])
    lang_inst = f"Output language: {language}." if language and language != "en" else ""

    archetype_directives = {
        "NUMERICAL": """
TEACHING ARCHETYPE: NUMERICAL / CALCULATION SOLVER
Whenever presenting a calculation or numerical problem:
1. State the original problem statement accurately from the source.
2. Given Information: List all given variables with symbols and units ($Given: \dots$).
3. Required Target: Explicitly state what must be found ($To\ Find: \dots$).
4. Concept Explanation: Explain the underlying physical/systemic concept in beginner-friendly language.
5. Formula & Variables: Write the formula in display LaTeX ($$Formula$$) and explain each variable.
6. Step-by-Step Substitution: Substitute values clearly. Solve EVERY intermediate step without skipping arithmetic. Explain why each step is performed.
7. Final Answer: Highlight the final value with units ($Answer: \dots$).
8. Verification / Sanity Check: Verify the answer (e.g. dimensional analysis, boundary check).
9. Visual: Include a Markdown table or diagram if it clarifies the numbers.
Never invent values or alter the problem. If data is missing in source, explicitly note it.
""",
        "ALGORITHM": """
TEACHING ARCHETYPE: ALGORITHM & COMPUTATIONAL LOGIC
1. Intuitive Purpose: Explain what problem the algorithm solves and why it is needed.
2. Step-by-Step Logic: Provide clean, numbered procedural steps or pseudocode.
3. Visual Flowchart: Provide a Mermaid flowchart (`flowchart TD`) showing decisions, loops, and terminal states.
4. Worked Trace / Example: Walk through an execution example step-by-step.
5. Complexity Analysis: State Best, Worst, and Average Time Complexity ($O(\dots)$) and Space Complexity with clear mathematical justification.
""",
        "ARCHITECTURE": """
TEACHING ARCHETYPE: SYSTEM ARCHITECTURE & COMPONENTS
1. Architectural Purpose: High-level purpose and the systemic role this architecture plays.
2. Component Breakdown: Describe each hardware/software component, register, or layer with its exact responsibility.
3. Visual Diagram: Provide a clean, properly labelled Mermaid block diagram or architecture map (`graph TD` or `classDiagram`).
4. Data & Control Flow: Explain how signals, packets, or data travel across interfaces.
5. Structural Constraints & Trade-Offs: Performance bounds, failure modes, and architectural trade-offs.
""",
        "COMPARISON": """
TEACHING ARCHETYPE: COMPARATIVE ANALYSIS & TRADE-OFFS
1. Conceptual Background: Introduce the concepts/technologies being compared.
2. Structured Comparison Table: Provide a Markdown comparison table with clear criteria columns:
   | Evaluation Dimension | Concept A | Concept B | Practical Impact |
3. Deep Analysis: Explain the underlying architectural or theoretical reasons for these differences.
4. Engineering Decision Rules: Practical guidelines on when to choose Option A vs Option B.
""",
        "PROCESS": """
TEACHING ARCHETYPE: SEQUENTIAL WORKFLOW & PROTOCOL
1. Preconditions & Inputs: Required state before the process begins.
2. Ordered Sequential Stages: Numbered, chronological breakdown of every phase.
3. Visual Workflow: Provide a Mermaid sequence diagram (`sequenceDiagram`) or state machine (`stateDiagram-v2`).
4. Invariants & Postconditions: Expected outcomes, guarantees, and recovery steps on failure.
""",
        "CASE_STUDY": """
TEACHING ARCHETYPE: APPLIED CASE STUDY & SCENARIO
1. Context & Background: Real-world operational setting.
2. Problem Statement: Core challenge, bottleneck, or failure that occurred.
3. Diagnostic Analysis: How the problem was investigated using first principles.
4. Solution & Intervention: Architecture or procedure implemented to solve it.
5. Measurable Outcomes & Lessons Learned: Concrete metrics, results, and generalizable takeaways.
""",
        "THEORETICAL": """
TEACHING ARCHETYPE: THEORETICAL FOUNDATION
1. Accurate Definition: Formal precision paired with a plain-English translation.
2. Intuitive Analogy: Everyday technology or physical analogy to build intuition.
3. First-Principles Explanation: How and why it works at the fundamental level.
4. Source Examples: Concrete examples drawn directly from the text.
5. Supplementary Real-World Application: Clearly labelled as `[Supplementary Practical Application]` showing how it is used in software, engineering, or business today.
6. Common Misconceptions & Exam Traps: Subtle pitfalls students frequently stumble on.
"""
    }

    directive = archetype_directives.get(archetype, archetype_directives["THEORETICAL"])

    return f"""You are an experienced, patient human teacher and domain specialist teaching {subject}.
Your mission is to teach this specific topic deeply, clearly, and engagingly as a human master instructor would.
Assume the reader may be a beginner: explain unfamiliar terminology before using it, prefer simple sentences, and break difficult concepts into smaller steps.

TOPIC: "{topic_name}"
HIERARCHY PATH: {topic_path}
SOURCE LOCATION: Pages {pages}
PRIMARY PEDAGOGICAL ARCHETYPE: {archetype_info['name']}
{lang_inst}

{directive}

STRICT GROUNDING & TEACHING RULES:
1. Teach using ONLY the supplied source context as ground truth for all facts, formulas, and data.
2. Do NOT invent missing formulas, numbers, or problem values.
3. If supplementary contextual knowledge or real-world examples are needed, label it as additional context clearly so the student knows it extends beyond the source text.
4. Address advantages, disadvantages, limitations, trade-offs, and edge cases for key mechanisms.
5. Ensure all formulas use inline LaTeX ($...$) and standalone display LaTeX ($$...$$).
6. Never force an identical cookie-cutter template: use headings that genuinely match the content.

SOURCE CONTEXT:
\"\"\"
{source_context}
\"\"\"

Format your output as a JSON object:
{{
  "archetype": "{archetype}",
  "teaching_content": "# Comprehensive topic masterclass in human-friendly Markdown...",
  "diagram_mermaid": "Valid Mermaid diagram code (or empty string if not applicable)",
  "formulas": ["LaTeX formula 1", "LaTeX formula 2"],
  "solved_examples": [
    {{"problem": "...", "given": "...", "formula": "...", "solution": "...", "units": "...", "verification": "..."}}
  ],
  "misconceptions": ["Misconception 1", "Misconception 2"],
  "applications": ["Application 1", "Application 2"]
}}
"""

