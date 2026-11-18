# StudyAI — AI Quality Evaluation Audit Report

**Run ID:** `eval-run-da3a5953`  
**Execution Timestamp:** 2026-10-18T19:26:12.979990  
**Inference Engine:** `extractive-nlp-grounded` (Ollama Available: True)  
**Duration:** 2.18 seconds  
**Benchmark Scope:** 20 Academic Documents / 100 Generated Questions  

---

## Executive Measured Metrics

| Metric | Measured Result | Evaluation Criteria |
| :--- | :---: | :--- |
| **Grounding Accuracy** | **100.0%** | Question premises substantiated by source text |
| **Citation Accuracy** | **100.0%** | Exact verbatim or normalized citation quotes |
| **Question Relevance** | **100.0%** | Strict domain & syllabus alignment |
| **Answer Accuracy** | **100.0%** | Correct answer presence & source validation |
| **Unsupported Question Rate** | **0.0%** | Low is better: questions with unsupported claims |

---

## Evaluated 8-Dimension Quality Breakdown

| # | Dimension | Measured Score | Evaluation Description |
| :-: | :--- | :---: | :--- |
| 1 | **Summary Relevance** | **52.2%** | Coverage of core entities and grounding of synthesized summary against source text. |
| 2 | **Topic Relevance** | **98.6%** | Validation that extracted syllabus topics exist in document and carry valid curriculum weights. |
| 3 | **Question Grounding** | **100.0%** | Substantiation of question prompts and propositions in the source study material. |
| 4 | **Citation Accuracy** | **100.0%** | Verbatim or normalized exact substring match of cited quotes inside source chunks. |
| 5 | **Answer Correctness** | **100.0%** | Presence of designated answer in options, index alignment, and factual backing in text. |
| 6 | **Difficulty Correctness** | **100.0%** | Congruence between assigned difficulty label and syntactic/cognitive complexity. |
| 7 | **Copilot Grounding** | **55.0%** | Strict RAG source citing on valid queries and verified refusal on unsupported queries. |
| 8 | **Unsupported Information Rate** | **0.0%** | Proportion of generated questions containing ungrounded or unsupported claims. |

---

## Benchmark Documents Evaluated (20 Real Study Materials)

| # | Document Title | Subject | Word Count | Summary Relevance | Topic Relevance | Copilot Grounding |
| :-: | :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | Operating Systems: CPU Scheduling & Context Switching | Operating Systems | 240 words | 51.8% | 100.0% | 100.0% |
| 2 | Operating Systems: Virtual Memory & Page Replacement | Operating Systems | 220 words | 61.4% | 100.0% | 50.0% |
| 3 | Operating Systems: Process Synchronization & Deadlocks | Operating Systems | 218 words | 62.2% | 100.0% | 50.0% |
| 4 | Computer Networks: Transmission Control Protocol (TCP) | Computer Networks | 205 words | 59.7% | 100.0% | 100.0% |
| 5 | Computer Networks: Routing Algorithms & Protocols | Computer Networks | 183 words | 51.8% | 100.0% | 50.0% |
| 6 | Computer Networks: DNS Resolution & Application Protocols | Computer Networks | 202 words | 54.2% | 100.0% | 50.0% |
| 7 | Data Structures: Balanced Binary Search Trees | Data Structures & Algorithms | 252 words | 51.8% | 100.0% | 50.0% |
| 8 | Algorithms: Graph Traversals & Shortest Path | Data Structures & Algorithms | 219 words | 37.5% | 100.0% | 50.0% |
| 9 | Database Systems: ACID Properties & Concurrency Control | Database Systems | 202 words | 58.3% | 100.0% | 50.0% |
| 10 | Database Systems: Relational Normalization & Normal Forms | Database Systems | 207 words | 60.4% | 100.0% | 50.0% |
| 11 | Artificial Intelligence: Transformer Models & Self-Attention | Artificial Intelligence & Deep Learning | 209 words | 46.2% | 85.7% | 50.0% |
| 12 | Machine Learning: Gradient Descent & Backpropagation | Machine Learning | 209 words | 52.1% | 100.0% | 50.0% |
| 13 | Molecular Biology: DNA Replication & Polymerase Fidelity | Molecular Biology | 203 words | 46.6% | 100.0% | 50.0% |
| 14 | Cellular Biology: Cellular Respiration & ATP Synthase | Cellular Biology | 212 words | 52.1% | 100.0% | 50.0% |
| 15 | Plant Biology: Oxygenic Photosynthesis & Light Reactions | Plant Biology | 189 words | 25.0% | 100.0% | 50.0% |
| 16 | Organic Chemistry: Nucleophilic Substitution Mechanisms | Organic Chemistry | 212 words | 37.5% | 100.0% | 50.0% |
| 17 | Classical Mechanics: Newton's Laws & Momentum Conservation | Physics | 224 words | 60.4% | 100.0% | 50.0% |
| 18 | Thermodynamics: Laws of Thermodynamics & Carnot Engine | Thermodynamics | 170 words | 63.9% | 100.0% | 50.0% |
| 19 | Linear Algebra: Matrix Eigenvalues & Diagonalization | Mathematics | 242 words | 50.0% | 85.7% | 50.0% |
| 20 | Constitutional Law: Separation of Powers & Judicial Review | Constitutional Law | 222 words | 60.6% | 100.0% | 50.0% |

---

## Sample Traceable Question Verifications (100 Verified Questions)

Showing first 10 verified test traces with character-level evidence:

### Question #1: Operating Systems: CPU Scheduling & Context Switching
- **Prompt:** "According to the source text: "______ 3: Process Management, Thread Execution, and CPU Scheduling." — What completes this statement correctly?"
- **Designated Answer:** `Chapter` (Option index: 3)
- **Options:** `Alternative Mechanism`, `Inverse Relation`, `Secondary Protocol`, `Chapter`
- **Citation Quote:** "Chapter 3: Process Management, Thread Execution, and CPU Scheduling."
- **Grounding Verified:** `PASS` (Matched 6/9 content tokens (66.7% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`

### Question #2: Operating Systems: CPU Scheduling & Context Switching
- **Prompt:** "According to the source text: "A ______ is an active program in execution requiring resources including CPU time, memory, and I/O devices." — What completes this statement correctly?"
- **Designated Answer:** `process` (Option index: 2)
- **Options:** `Inverse Relation`, `Secondary Protocol`, `process`, `Alternative Mechanism`
- **Citation Quote:** "A process is an active program in execution requiring resources including CPU time, memory, and I/O devices."
- **Grounding Verified:** `PASS` (Matched 10/13 content tokens (76.9% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`

### Question #3: Operating Systems: CPU Scheduling & Context Switching
- **Prompt:** "According to the source text: "The ______ Control Block (PCB) is the central data structure maintained by the operating system kernel to track process state, program counter, CPU registers, memory management information, and accounting details." — What completes this statement correctly?"
- **Designated Answer:** `Process` (Option index: 1)
- **Options:** `Secondary Protocol`, `Process`, `Alternative Mechanism`, `Inverse Relation`
- **Citation Quote:** "The Process Control Block (PCB) is the central data structure maintained by the operating system kernel to track process state, program counter, CPU registers, memory management information, and accounting details."
- **Grounding Verified:** `PASS` (Matched 22/25 content tokens (88.0% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`

### Question #4: Operating Systems: CPU Scheduling & Context Switching
- **Prompt:** "According to the source text: "______ management information, and accounting details." — What completes this statement correctly?"
- **Designated Answer:** `memory` (Option index: 0)
- **Options:** `memory`, `Alternative Mechanism`, `Inverse Relation`, `Secondary Protocol`
- **Citation Quote:** "memory management information, and accounting details."
- **Grounding Verified:** `PASS` (Matched 4/7 content tokens (57.1% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`

### Question #5: Operating Systems: CPU Scheduling & Context Switching
- **Prompt:** "According to the source text: "When the CPU ______ between processes, a context switch occurs." — What completes this statement correctly?"
- **Designated Answer:** `switches` (Option index: 3)
- **Options:** `Alternative Mechanism`, `Inverse Relation`, `Secondary Protocol`, `switches`
- **Citation Quote:** "When the CPU switches between processes, a context switch occurs."
- **Grounding Verified:** `PASS` (Matched 6/9 content tokens (66.7% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`

### Question #6: Operating Systems: Virtual Memory & Page Replacement
- **Prompt:** "According to the source text: "______ 9: Virtual Memory Architecture and Paging Systems." — What completes this statement correctly?"
- **Designated Answer:** `Chapter` (Option index: 3)
- **Options:** `Alternative Mechanism`, `Inverse Relation`, `Secondary Protocol`, `Chapter`
- **Citation Quote:** "Chapter 9: Virtual Memory Architecture and Paging Systems."
- **Grounding Verified:** `PASS` (Matched 5/8 content tokens (62.5% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`

### Question #7: Operating Systems: Virtual Memory & Page Replacement
- **Prompt:** "According to the source text: "______ memory separates user logical memory from physical memory, allowing execution of processes whose address spaces exceed available physical RAM." — What completes this statement correctly?"
- **Designated Answer:** `Virtual` (Option index: 2)
- **Options:** `Inverse Relation`, `Secondary Protocol`, `Virtual`, `Alternative Mechanism`
- **Citation Quote:** "Virtual memory separates user logical memory from physical memory, allowing execution of processes whose address spaces exceed available physical RAM."
- **Grounding Verified:** `PASS` (Matched 17/20 content tokens (85.0% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`

### Question #8: Operating Systems: Virtual Memory & Page Replacement
- **Prompt:** "According to the source text: "______ management units (MMUs) map logical virtual addresses into physical addresses through page tables." — What completes this statement correctly?"
- **Designated Answer:** `Memory` (Option index: 1)
- **Options:** `Secondary Protocol`, `Memory`, `Alternative Mechanism`, `Inverse Relation`
- **Citation Quote:** "Memory management units (MMUs) map logical virtual addresses into physical addresses through page tables."
- **Grounding Verified:** `PASS` (Matched 12/15 content tokens (80.0% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`

### Question #9: Operating Systems: Virtual Memory & Page Replacement
- **Prompt:** "According to the source text: "into ______ addresses through page tables." — What completes this statement correctly?"
- **Designated Answer:** `physical` (Option index: 0)
- **Options:** `physical`, `Alternative Mechanism`, `Inverse Relation`, `Secondary Protocol`
- **Citation Quote:** "into physical addresses through page tables."
- **Grounding Verified:** `PASS` (Matched 4/7 content tokens (57.1% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`

### Question #10: Operating Systems: Virtual Memory & Page Replacement
- **Prompt:** "According to the source text: "______ paging loads pages into memory only when they are referenced during program execution." — What completes this statement correctly?"
- **Designated Answer:** `Demand` (Option index: 3)
- **Options:** `Alternative Mechanism`, `Inverse Relation`, `Secondary Protocol`, `Demand`
- **Citation Quote:** "Demand paging loads pages into memory only when they are referenced during program execution."
- **Grounding Verified:** `PASS` (Matched 10/13 content tokens (76.9% token recall against source text).)
- **Citation Verified:** `PASS` (Match Type: `exact_verbatim`) 
- **Answer Validated:** `PASS` (Option included: True, index aligned: True, source backed: True.)
- **Difficulty & Topic:** Topic: `Operating Systems`, Difficulty: `Medium` (`PASS`)
- **Unsupported Information:** `NO (GROUNDED)`
