# 🧪 Testing & QA Subsystem (Member 4: Testing & QA Engineer)

Welcome to the **StudyAI Testing & Quality Assurance** module. This directory consolidates unit tests, end-to-end acceptance tests, security validations, and AI quality benchmarks.

---

## 👥 Module Ownership: Member 4 (Testing & QA Engineer)
- **Primary Responsibility**: Test automation, end-to-end verification pipelines, security and authentication vulnerability regression testing, edge case resilience, and AI output quality scoring.
- **Key Files & Folders**:
  - `run_tests.py`: Centralized test runner with options for all test suites.
  - `acceptance/`:
    - `run_comprehensive_acceptance.py`: End-to-end real material verification across 10 document types and 18 verification steps.
    - `acceptance_test.py`: Fast smoke acceptance tests for API workflows.
    - `test_additional_acceptance.py`: Edge cases, malformed uploads, and boundary scenarios.
    - `verify_pipeline.py`: Step-by-step pipeline validation.
    - `verify_failures.py`: Negative testing and graceful failure handling.
  - `unit/`:
    - `test_auth.py`: Authentication, Argon2id passwords, and token expiration tests.
    - `test_security.py`: Rate limiting, path traversal defenses, zip bomb protection, and SQL injection checks.
    - `test_summary_engine.py`: Chunking heuristics and summary validation tests.
    - `test_evaluation.py`: Mathematical consistency of evaluation metrics.
    - `test_api.py`: Core REST endpoint integration tests.
  - `ai_evaluation/`:
    - `run_ai_evaluation.py`: Automated benchmarking measuring factual grounding, hallucination rate, and question quality.
  - `reports/`: Test outputs, JSON metrics, and audit documentation.

---

## 🚀 Running Tests

### 1. Unified Test Runner
You can run the entire test suite or specific modules using `run_tests.py`:

```bash
# Run unit and security tests (fast default)
python testing/run_tests.py

# Run all test suites
python testing/run_tests.py --all

# Run specific suites
python testing/run_tests.py --unit
python testing/run_tests.py --security
python testing/run_tests.py --ai
python testing/run_tests.py --acceptance
```

### 2. Running Django Native Tests
```bash
python backend/manage.py test api.tests
python backend/manage.py test api.test_security
python backend/manage.py test api.test_auth
```

---

## 📊 Quality Standards & Criteria
- **Security**: Zero unhandled exceptions on malicious or oversized payloads.
- **Grounding**: AI questions must achieve >= 90% grounding ratio against uploaded source text.
- **Failures**: Any service outage (e.g. Ollama daemon offline) must gracefully fall back to local extractive NLP without throwing 500 errors.
