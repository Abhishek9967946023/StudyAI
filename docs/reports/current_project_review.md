# StudyAI: Current Engineering Review

## Executive assessment

StudyAI has useful foundations: document extraction and chunking, page-linked source material, a syllabus tree, topic teaching, asynchronous notes, and exam/revision features. The main weakness was trust: some deterministic fallbacks presented generic or subject-specific textbook material as if it came from the uploaded file. The project also has several overlapping representations of study content, making it harder to know which output is authoritative.

This is a focused review of the document-summary, notes, syllabus, and topic-teaching paths and their related UI. It is not a security certification, production deployment review, or guarantee of model factual accuracy.

## Findings and changes in this pass

### Reliability

- Summary coverage was presented too confidently: the score had an artificial floor and missing measurements could appear complete. It now reports a heuristic source-feature overlap, with unavailable measurements left unavailable. This is not a fact-check or hallucination score.
- Summary enrichment previously inserted canned comparisons, worked examples, algorithms, exam traps, and exam-frequency advice for particular subjects. The active synthesis now uses extracted source elements and omits unsupported exam advice. The unused canned helper functions were removed.
- Concept cards previously generated hardcoded definitions, examples, misconceptions, and exam claims when the source did not contain them. Missing evidence is now described explicitly instead.
- Subject-specific “big picture” paragraphs could list curriculum content absent from the document. The summary overview now reports detected sections rather than inferring an unseen curriculum.
- A diagram could be selected from a section number or title alone and then show a hardcoded workflow. Diagrams are now emitted only from explicit numbered source steps.
- Formula metadata could infer a formula name and explanation from subject keywords. It now uses the containing source sentence.
- The theorem parser could claim proof invariants were verified when no proof was found. It now reports that proof details were not identified.
- Offline topic teaching and notes use mapped source excerpts or say when evidence is missing; they do not fill gaps with generic lessons. Syllabus topics without a matching source chunk no longer borrow the first unrelated chunk.
- Offline note excerpts and formulas now carry their mapped source page/range inline; missing page metadata is labeled unavailable rather than being presented as page 1.
- Native PDF table rows are now appended to page text when PyMuPDF table detection is available. Extraction results record per-page table status, preserve it through OCR processing, and warn students when tables could not be structurally extracted or need review.
- DOCX tables now retain row and column boundaries in extracted text and remain in document order. DOCX physical page locations are still not reliable because this parser does not perform layout rendering.
- PDF image and vector-graphic counts are recorded as visual elements that still need human interpretation; the system does not yet understand their semantic content.
- OCR pages containing recognizable mathematical notation are flagged for manual review when page confidence is low or unavailable; this is a review signal, not equation recognition or validation.
- Notes generation now preserves the document’s main summary, normalizes UI/API depth aliases, and includes the requested output language in the model prompt.
- The requested academic-analysis rubric is now a shared prompt used by both selected-topic teaching and full syllabus notes. It covers simple/technical definitions, subject context, mechanisms, formulas, calculations, examples, diagrams, applications, trade-offs, misconceptions, conclusions, source citations, and clearly labeled additional context.
- The notes UI recognizes the backend’s actual job states and presents coverage/verification checks as limited checks rather than factual certification.
- The upload page’s document chat now uses the existing Copilot service and reports request failures as service errors rather than implying the material lacked evidence. Its mount-time health check called undefined functions and updated state that was never rendered; that dead path and unused sample/language helpers were removed.
- When detailed pipeline steps are not yet available, the upload progress list now derives its active/completed fallback from the backend processing stage instead of remaining stuck on the initial upload step.

### Product experience

The clearest learning journey for the product is:

1. **Understand the subject** — show a short overview and clearly distinguish general subject context from material extracted from the upload.
2. **Inspect the syllabus map** — show detected chapters/topics, page references, and gaps; let the student choose one small topic.
3. **Learn one topic deeply** — organize the answer as definition, prerequisites, mechanism, formulas and units, worked example, diagram, applications, trade-offs, misconceptions, and recap. Attach page/source references to claims; display “not found in source” instead of fabricating missing examples or calculations.

Keep the quick-summary and exam-prep modes available, but make the selected topic and source evidence visible. A high “coverage” number must never imply that every generated claim is accurate.

## Architecture and maintainability observations

- The same document is represented in the summary JSON, document chunks, a `Topic` hierarchy/teaching cache, and `NotesGenerationJob`/`SyllabusSection` records. These are valid for different workflows, but the project should define ownership and synchronization rules for each rather than letting one flow overwrite another.
- `summary_engine.py`, `subject_engine.py`, and `notes_engine.py` have distinct but overlapping responsibilities. Keep extraction and evidence mapping reusable; keep per-topic teaching, whole-document summaries, and exportable notes as separate products with explicit source references.
- Subject overviews have an offline heuristic fallback containing broad domain material. Treat that material as general context, not as content proven to appear in the upload; expose its origin in the UI/API before relying on it as a source-grounded syllabus.
- The notes verifier checks structural properties and minimum content, not whether claims are true. Generated study documents and status labels now describe this as an automated structure/math check, not factual verification; DOCX/PDF exports include the same limitation.
- The generated front-end bundle still reports a chunk above 500 kB. Dynamic Mermaid loading helps defer diagram code, but the production build still needs route/vendor splitting and a follow-up size measurement.

## Updated development work list

The following work list combines the requested capabilities with what is already present. “Partial” means a foundation exists but the acceptance criteria below are not yet met; it does not mean the feature is release-ready.

| Area | Current status | Remaining work |
|---|---|---|
| **A. Document understanding** | Partial; extraction warnings added | Scanned-PDF uploads now fail early with actionable OCR setup guidance when OCR is unavailable. Extraction reports persist page gaps, failed/low-confidence pages, scan/OCR state, measured Tesseract confidence, per-page native PDF table status, and a manual-review signal for low-confidence OCR math pages. Native PDF tables and DOCX tables now preserve row/column structure in extracted source text; PDF tables have per-page statuses, while DOCX physical page locations remain unavailable without layout rendering. Image and vector-graphic counts are recorded but explicitly not interpreted. The upload UI flags unavailable/incomplete PDF table extraction and visual elements that need review. Offline note excerpts and formulas cite mapped page ranges, and missing page metadata is explicitly unavailable rather than defaulted to page 1. Still improve scanned table extraction, semantic figure/graph understanding, hierarchy and long-document coverage; deduplicate repeated material without losing distinctions; preserve terminology and cite pages consistently. |
| **B. Advanced notes** | Core prompt shared; partial outputs | The shared prompt now requests calibrated 2/5/10-mark answer outlines without padding or inventing exam expectations. Still add distinct persisted answer sheets, definition and formula sheets, diagrams-to-practice, comparison tables, memory aids, revision sheets, and source-based priority rankings. |
| **C. Summary accuracy** | Source-grounding improved; not fact-verified | Add evidence-linked claim checking, explicit missing-topic reports, long-document completeness measures, and targeted section regeneration. Keep extraction coverage separate from factual accuracy. |
| **D. Mathematics and technical content** | Partial | Notes and numeric-question validation now independently check simple arithmetic equalities with a bounded evaluator. Improve OCR for math, tables, graphs, units, and pseudocode; extend calculation verification to supported domain formulas; flag ambiguous or unreadable notation rather than guessing. |
| **E. Reference-document intelligence** | Style-only profile foundation implemented; partial | Users can analyze a separate uploaded document into presentation metrics/guidance and select that profile for notes. Reference facts are not persisted in the profile or sent in note prompts. Still add an output quality comparison rubric and validate coverage/structure against it. |
| **F. Questions and exams** | Core formats implemented; broader validation remains | Long-answer, fill-in-the-blank, and multiple-select questions preserve their types and answer contracts through generation, persistence, exam UI, grading, and review. Answer keys are withheld from exam-taking responses until submission. Exams support configurable 2/5/10 marks per question and weighted scoring. Still add other requested question formats and stronger ambiguity, explanation, and unsupported-premise validation. |
| **G. Document/AI platform** | Multiple provider adapters and privacy-safe usage telemetry; partial | OpenAI-compatible, Gemini, Anthropic, and Ollama adapters support server-side credentials and one optional fallback. Provider attempts record latency, success/failure category, fallback usage, and reported token counts without prompts or credentials; costs are estimated only with configured per-model rates. Strengthen OCR, multilingual handling, retrieval, and durable queue reliability. |
| **H. UI/UX** | Existing workspace; partial redesign | The public landing page now explains the subject → syllabus → focused-topic learning path and avoids synthetic exam scores and absolute accuracy/cost claims. Dashboard loading and partial API failures are now visible, with affected sections marked unavailable and a retry action rather than misleading empty states. Upload extraction warnings now include incomplete table/visual extraction, its document chat uses the existing Copilot service, its fallback progress reflects backend stages, and the dead undefined health-check path is removed. The login page no longer displays hard-coded demo-admin credentials. Settings identifies the server-configured provider without exposing credentials. Exam setup exposes mark tiers; exam UI supports long, fill-in-the-blank, and keyboard-operable multi-select answers, and result review reports weighted marks. Finish responsive auth, dashboard, workspace, notes, analytics, loading/error/empty states, and verify all navigation/actions. |
| **I. Backend and release quality** | Partial | Route-level lazy loading reduced the main browser entry bundle. Define data ownership, improve multi-user/performance behavior, use durable background jobs, run comprehensive tests on representative subjects, and complete security/deployment/documentation review. |

The cited “approximately 70% accuracy” is not a validated baseline in the evidence reviewed here. Define a representative, labeled evaluation set and measure claim support, extraction coverage, and math correctness separately before setting a target.

### Suggested delivery phases and acceptance gates

1. **Core learning workflow (current foundation):** Upload → subject context → detected syllabus with pages → choose one topic → detailed notes. Required: source claims link to pages or are marked as additional context; missing evidence is explicit; formulas/examples/diagrams are not forced; full-syllabus notes remain a separate action. The shared prompt and notes UI now support this direction.
2. **Document fidelity:** OCR availability failures and page-level extraction uncertainty now have explicit reporting, and the UI flags pages that need review. Still test math-heavy pages, tables, diagrams, and long documents; improve extraction coverage and ensure generated explanations do not silently invent or drop unreadable content.
3. **Reference quality:** Style-only reference profiles now guide note presentation without passing reference facts to the generator. Remaining: compare generated notes with a transparent presentation/coverage rubric, without treating reference text as source evidence.
4. **Assessment and revision:** Single choice, true/false, short/long, fill-in-the-blank, multiple-select, and configurable weighted marks are implemented across generation/persistence/UI/grading. Remaining: other requested formats, stronger answer/explanation validation, and revision-sheet improvements. Required: every answer has source support or an explicit additional-context label; numerical results are code-checked; duplicate/ambiguous questions are rejected.
5. **Provider and scale:** Provider adapters, failure fallback, and usage telemetry are implemented. Remaining: a durable worker queue and deeper provider/queue failure-recovery tests. Required: failures must not lose jobs or change source attribution.
6. **Release readiness:** Complete responsive visual review, accessibility/error states, full test CI, clean migrations, secret and permission review, deployment configuration, license, contribution guide, and user-facing limitations.

Across phases, the acceptance rule is: **no claim is presented as uploaded-source content without source evidence; no quality metric is called factual accuracy unless it actually checks facts.**

## Release priorities

### Before a hackathon demo

- Demonstrate the subject → syllabus → selected-topic flow with a short, text-based sample and a scanned/OCR sample.
- Show page references and the “evidence unavailable” state for an unmatched topic.
- Test online-model and offline behavior separately; do not demo a fallback as an AI-generated explanation.
- Review the large initial bundle for slow-device behavior and validate the topic flow on mobile.

### Before an open-source release

- Run the complete backend and frontend test suites in CI, not only the focused engines.
- Verify migrations from a clean database, upload limits, OCR dependencies, export generation, and restart/recovery behavior for background notes jobs.
- Replace or explicitly constrain in-process background execution before multi-worker deployment; use a durable job queue if jobs must survive restarts or scale across workers.
- Review production server/container configuration, secret handling, CORS/CSRF, logging, and database configuration against the intended deployment target.
- Add a license, contribution guide, environment-variable reference, supported-file/size limits, and a small redistributable test document.

## Cleanup guidance

The current worktree already contains many tracked deletions and untracked files. They were present before this review and may represent active work or user data, so they were not mass-deleted. Review those changes individually before deciding what is obsolete. Remove duplicate/unused code only after checking imports, routes, scripts, tests, and deployment references; do not use filename age or visual similarity alone as evidence.

The Taste skill installer previously reported a critical-risk assessment; its scripts were not executed. Treat the installed skill as untrusted until its contents are reviewed.

## Validation status

The frontend production build succeeds. Route-level lazy loading reduced the main entry from **1,007.71 kB (268.60 kB gzip)** to **338.24 kB (102.62 kB gzip)**. Vite still warns about deferred chunks above 500 kB; the largest is the 1.46 MB Mermaid ELK renderer. Targeted ESLint on the landing page, dashboard, and route table passes. The production preview rendered the lazy-loaded landing route and did not request the Vite development port.

The focused summary, notes, and subject backend suites pass: **45 tests**, including checks that both notes workflows use the shared analysis rubric. Python syntax checks found no syntax errors in the changed engines. A repository-wide `git diff --check` also reports pre-existing trailing whitespace and extra EOF blank lines outside the new changes; those unrelated lines were left unchanged. Repeat the full suite in CI before release.

Latest focused checks pass: **17 notes-engine tests** (including exported verification-scope and page-reference cases), OCR/document-fidelity tests (including native PDF and DOCX table extraction, visual-element metadata, low-confidence math review, and OCR metadata preservation), **5 focused arithmetic/notes tests**, **6 mocked provider-adapter tests**, five exam-format/MSQ/weighted-mark regression tests, migration consistency, the frontend production build, and targeted Upload ESLint with no remaining findings. The landing page was visually checked in a browser and had no horizontal overflow at the tested viewport; the login page renders without the demo credential hint. The build still flags deferred large diagram chunks.

The last full backend suite run passed **188 tests**, with **2 skipped**; it preceded the latest notes page-reference and PDF extraction changes. The affected notes and OCR/document-fidelity suites passed focused reruns afterward. The previously failing document-status tests now call the dedicated status route, and the long-document summary test checks for the distinct source-backed exam cue rather than counting repeated boilerplate as multiple points. Measured OCR confidence now reaches page-level extraction reports without being replaced by a fixed estimate. The project still has the broader document fidelity, UX, deployment, and release-readiness work listed above.
