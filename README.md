# 🎓 StudyAI — AI Study Analyzer & Personalized Exam Generator

> **Turn lecture slides, PDFs, Word documents, notes, and textbooks into grounded study guides, interactive visual diagrams, personalized practice exams, weak-topic diagnostics, and spaced repetition revision plans.**

Built with 
*React 19 + Vite** (Frontend) + **Django REST Framework** (Backend) + **Ollama or configured OpenAI/Gemini/Anthropic-compatible AI providers** + **Automated Acceptance & Quality Suite** (Testing).

---

## 🏛️ System Architecture

```
                                    ┌────────────────────────────────────────────────────────┐
                                    │                     STUDYAI PLATFORM                   │
                                    └────────────────────────────────────────────────────────┘

    Client Layer                    Frontend Layer                       Backend Layer                    AI & Storage Layer
 ┌─────────────────┐             ┌────────────────────┐              ┌───────────────────┐             ┌─────────────────────┐
 │ Web Browser     │ ──────────> │ React 19 + Vite    │ ───────────> │ Django 6 REST API │ ──────────> │ SQLite / PostgreSQL │
 │ (Desktop/Mobile)│             │ Port: 5173         │ (Proxy/CORS) │ Port: 8000        │             │ (backend/db.sqlite3)│
 └─────────────────┘             └────────────────────┘              └───────────────────┘             └─────────────────────┘
                                                                               │                                  │
                                                                               ├─────────────────────────┐        │
                                                                               ▼                         ▼        ▼
                                                                     ┌───────────────────┐     ┌─────────────────────┐
                                                                     │ Local Ollama LLM  │     │ Persistent Storage  │
                                                                     │ Port: 11434       │     │ (backend/media/)    │
                                                                     │ llama3:latest     │     └─────────────────────┘
                                                                     └───────────────────┘
```

---

## 💻 Supported Environments

| Environment | Support Status | Notes |
| :--- | :--- | :--- |
| **Windows 10 / 11** | ✅ First-Class Native | Automated via `setup_studyai.bat` and `start_studyai.bat` |
| **Linux (Ubuntu / Debian / Fedora)** | ✅ First-Class Native | Automated via `setup_studyai.sh` and `start_studyai.sh` |
| **macOS (Intel & Apple Silicon)** | ✅ First-Class Native | Automated via `setup_studyai.sh` and `start_studyai.sh` |
| **Docker (Any OS with Docker Engine)** | ✅ Containerized | Automated via `docker compose up --build` |

---

## 📋 Prerequisites

Before running StudyAI, ensure the following tools are installed on your machine:

1. **Python 3.10 – 3.12** *(Python 3.12 recommended)*
   - Download: [python.org/downloads](https://www.python.org/downloads/)
   - *Windows note:* Ensure **"Add Python to PATH"** is checked during installation.
2. **Node.js 20+ (LTS)** and **npm 10+**
   - Download: [nodejs.org](https://nodejs.org/)
3. **Ollama** *(Optional but recommended for full local AI generation)*
   - Download: [ollama.com](https://ollama.com/)
   - Without Ollama, document extraction still works, but generated topic notes fall back to source excerpts rather than a full AI explanation.
4. **Tesseract OCR Engine** *(Required for scanned & image-based PDFs)*
   - **Windows:** `winget install UB-Mannheim.TesseractOCR` (or download the official UB-Mannheim installer)
   - **Ubuntu / Debian:** `sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils`
   - **macOS:** `brew install tesseract poppler`
   - **Docker:** Pre-installed automatically in the backend container!
   - *Note:* Text-based PDFs, Word (.docx), and plain text files work immediately without Tesseract. If an unconfigured system encounters a scanned PDF, StudyAI diagnoses the missing binary with actionable remedy instructions.

---

## ⚡ Quick Start (First-Time Setup)

### Windows (1-Click Automated Setup)
1. Open PowerShell or Command Prompt in the project folder.
2. Run:
   ```cmd
   setup_studyai.bat
   ```
3. Start the application:
   ```cmd
   start_studyai.bat
   ```
   *Your default web browser will open automatically at `http://127.0.0.1:5173/`.*

### Linux / macOS (1-Click Automated Setup)
1. Open your terminal in the project directory.
2. Make scripts executable and run setup:
   ```bash
   chmod +x setup_studyai.sh start_studyai.sh
   ./setup_studyai.sh
   ```
3. Start the application:
   ```bash
   ./start_studyai.sh
   ```
   *Open your browser at `http://localhost:5173/`.*

---

## 🛠️ Manual Step-by-Step Installation

If you prefer to configure the environment manually without batch/shell scripts:

### Step 1: Clone or Copy the Repository
```bash
git clone https://github.com/Abhishek9967946023/StudyAI-AI-Study-Analyzer-Personalized-Exam-Generator.git
cd StudyAI-AI-Study-Analyzer-Personalized-Exam-Generator
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```
*(The default configuration in `.env.example` works out-of-the-box for local development!)*

### Step 3: Backend Setup (Python Virtual Environment)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r backend/requirements.txt

# Run initial migrations
cd backend
python manage.py migrate

# Validate configuration
python manage.py check_configuration
cd ..
```

### Step 4: Frontend Setup (React 19 + Vite)
```bash
# Navigate to frontend and install cleanly from lockfile
cd frontend
npm ci
cd ..
```

### Step 5: Start StudyAI
You can run the unified runner from the project root:
```bash
node start_all.js
```
Or start each service in separate terminals:
- **Terminal 1 (Backend):**
  ```bash
  # Inside backend/ with virtualenv active
  python manage.py runserver 127.0.0.1:8000
  ```
- **Terminal 2 (Frontend):**
  ```bash
  # Inside frontend/
  npm run dev
  ```

---

## 🤖 Ollama AI Setup & Model Pull

StudyAI uses local LLMs through Ollama for zero-cost, private academic document analysis:

1. **Start the Ollama daemon:**
   ```bash
   ollama serve
   ```
2. **Pull the recommended model:**
   ```bash
   ollama pull llama3:latest
   ```
   *(Alternative lightweight models: `mistral:latest`, `phi3:latest`, `gemma:latest`)*
3. **Verify Ollama connectivity in StudyAI:**
   ```bash
   python backend/manage.py check_configuration
   ```

> **Offline behavior:** Document extraction and page-to-topic mapping remain available. Topic teaching falls back to excerpts from mapped source text and does not invent examples or diagrams. Coverage scores measure heuristic overlap with detected headings, concepts, and formulas; they are not factual-accuracy scores. Review generated content against the original document.

### Optional cloud AI providers

The backend can also use `openai`, `openai_compatible`, `gemini`, or `anthropic`. Configure `AI_PROVIDER`, the provider's API key, and its model in the server `.env`; optionally set `AI_FALLBACK_PROVIDER` to one provider for a single retry after a failed request. `OPENAI_BASE_URL` supports OpenAI-compatible endpoints, including local endpoints that do not require a key. The Settings page reports provider configuration but never exposes keys.

Cloud providers receive the prompt and relevant excerpts from the uploaded study document. Use a provider only if that data sharing is acceptable for your material and applicable policies. Keep keys out of frontend variables, source control, and logs. Provider status confirms configuration, not remote availability; requests report actual provider failures. Usage/cost telemetry is not implemented yet.

---

## 🔍 Document Processing & Optical Character Recognition (OCR)

StudyAI features a resilient, production-grade document extraction subsystem capable of handling:
1. **Digital / Text-Based PDFs:** Fast native vector text extraction via `pypdf` / `pymupdf` (zero OCR overhead).
2. **Scanned / Image-Based PDFs:** High-DPI rasterization via `pymupdf` (no Poppler executable dependency on Windows) followed by adaptive contrast enhancement and Tesseract OCR.
3. **Mixed PDFs (Hybrid):** Page-level classification preserving high-speed vector text for digital pages while running OCR only on scanned image pages.
4. **Office Documents & Text:** Native `.docx` (with decompression bomb defense) and `.txt` ingestion.

### ⚙️ Multi-Stage Tesseract Discovery
StudyAI automatically detects your Tesseract installation using a 4-tier discovery pipeline:
1. `TESSERACT_CMD` environment variable or `.env` configuration.
2. System `PATH` executable lookup (`tesseract`).
3. **Windows Registry:** Automatic inspection of `HKLM` and `HKCU` uninstall registry keys for UB-Mannheim / Tesseract installations.
4. **Standard OS Fallbacks:** `C:\Program Files\Tesseract-OCR\tesseract.exe`, `/usr/bin/tesseract`, `/usr/local/bin/tesseract`, `/opt/homebrew/bin/tesseract`.

### 🩺 OCR Health Check & Diagnostics
Verify your machine's OCR readiness anytime with the built-in management command:
```bash
# Check OCR status, binary path, version, and language packs
python backend/manage.py check_ocr

# Machine-readable JSON output for CI/CD or health scripts
python backend/manage.py check_ocr --json
```

If Tesseract is not installed or missing language packs, run:
```bash
python backend/manage.py setup_ocr
```
This prints tailored installation commands for Windows (`winget`), Ubuntu/Debian (`apt-get`), and macOS (`brew`).

### 🔄 Document Reprocessing Without Re-Upload
If a document was uploaded before Tesseract was installed or experienced a partial OCR failure, you can reprocess it directly without re-uploading:
- **API Endpoint:** `POST /api/documents/<document_id>/reprocess_ocr/` (or `/api/v1/materials/<document_id>/reprocess_ocr`)
- **Frontend:** Click the **Reprocess OCR** button directly in the document summary view.

---

## 🐳 Docker Deployment (Multi-Container)

StudyAI provides production-grade containerization with persistent volumes for media and database storage:

1. **Build and start containers:**
   ```bash
   docker compose up --build
   ```
2. **Access services:**
   - Frontend UI: `http://localhost:5173`
   - Backend API: `http://localhost:8000/api/`
   - API Health Check: `http://localhost:8000/api/health/`
3. **Stop containers (preserving data):**
   ```bash
   docker compose down
   ```

*Host Communication:* Docker automatically maps your host's local Ollama instance via `host.docker.internal:11434`.

---

## 🔒 Configuration & Environment Variables

| Variable | Default (Dev) | Description |
| :--- | :--- | :--- |
| `DJANGO_DEBUG` | `True` | Set to `False` in production. |
| `DJANGO_SECRET_KEY` | *(Ephemeral in dev)* | Secret key. Mandatory (min 32 chars) when `DJANGO_DEBUG=False`. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hostnames. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,...` | Comma-separated origins permitted to call API. |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Target URL for backend API. Dynamically adapts across LAN. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Target URL for Ollama daemon. |
| `OLLAMA_MODEL` | `llama3:latest` | Target LLM model name. |
| `AI_PROVIDER` | `ollama` | Primary provider: `ollama`, `openai`, `openai_compatible`, `gemini`, or `anthropic`. |
| `AI_FALLBACK_PROVIDER` | *(Empty)* | Optional single provider retry after primary request failure. |
| `OPENAI_API_KEY` / `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` | *(Empty)* | Server-side credentials for the selected cloud provider. |
| `OPENAI_MODEL` / `GEMINI_MODEL` / `ANTHROPIC_MODEL` | Provider default | Provider model name. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI or compatible API base URL. |
| `AI_MAX_TOKENS` | `3000` | Maximum output token request for cloud providers. |
| `EMAIL_BACKEND` | `console.EmailBackend` *(in dev)* | Console backend prints OTP codes to server terminal. Use SMTP for production. |
| `USE_POSTGRES` | `False` | Set `True` when using PostgreSQL instead of SQLite. |
| `DATABASE_URL` | *(Empty)* | Optional complete database URI (`postgres://...`). |
| `MEDIA_ROOT` | `backend/media` | Storage directory for uploaded lecture documents. |
| `TESSERACT_CMD` | *(Auto-detected)* | Path to Tesseract binary if outside standard system PATH. |
| `OCR_LANGUAGES` | `eng` | Language models for Tesseract (e.g. `eng` or `eng+fra`). |
| `OCR_DPI` | `200` | Rendering DPI for page rasterization (150-300 recommended). |
| `OCR_TIMEOUT_PER_PAGE` | `25` | Per-page OCR execution timeout in seconds. |
| `OCR_TOTAL_TIMEOUT` | `300` | Total document OCR extraction timeout in seconds. |
| `MAX_OCR_PAGES` | `100` | Safety ceiling on number of pages to OCR per document. |
| `OCR_QUALITY_MODE` | `BALANCED` | Preprocessing quality tier: `FAST`, `BALANCED`, or `BEST`. |
| `OCR_MIN_CONFIDENCE` | `50.0` | Minimum word confidence threshold to avoid retry heuristics. |

---

## 💾 Database & Media Data Portability

### Database Portability
- **Development:** Uses SQLite at `backend/db.sqlite3`. This file is preserved across reboots and git updates.
- **Exporting Data (to transfer to another device):**
  ```bash
  python backend/manage.py dumpdata api auth.user --indent 2 > studyai_backup.json
  ```
- **Importing Data on a new device:**
  ```bash
  python backend/manage.py loaddata studyai_backup.json
  ```
- **Seeding Test Data (safe, non-destructive):**
  ```bash
  python backend/manage.py seed_data --sample-data
  ```

### Media Storage
Uploaded PDF, Word, and text files are saved to `backend/media/documents/`. When transferring environments, copy the `backend/media/` folder to retain uploaded study files.

---

## 🧪 Testing & Verification Suite

StudyAI includes an end-to-end testing and quality assurance suite:

```bash
# Run unit, OCR, and security tests
python testing/run_tests.py --unit --ocr --security

# Run dedicated OCR subsystem tests (includes live Tesseract integration test)
python testing/run_tests.py --ocr

# Run AI evaluation benchmarks
python testing/run_tests.py --ai

# Run full test suite
python testing/run_tests.py --all

# Frontend build verification
cd frontend && npm run build
```

---

## 🛡️ Security Architecture

StudyAI enforces strict security controls:
1. **Zero Secret Leakage:** No passwords, tokens, or private paths in version control or error responses.
2. **Argon2id & PBKDF2 Password Hashing:** Cryptographically secure authentication.
3. **Email OTP Verification:** Registration and password resets require time-limited, rate-limited OTP validation.
4. **Tenant Isolation (IDOR Protection):** Documents and exams are strictly isolated per authenticated student.
5. **Path Traversal Protection:** All uploads and file downloads are validated to remain strictly inside `MEDIA_ROOT`.
6. **Decompression Bomb Defense:** DOCX uploads enforce strict uncompressed byte ceilings.
7. **Production Hardening:** When `DJANGO_DEBUG=False`, secure cookie flags (`HttpOnly`, `SameSite=Lax`, `Secure`), HSTS, and strict origin checks are enforced.

---

## ❓ Troubleshooting

For common questions, port conflicts, CORS resolution, and cross-device connectivity, please refer to:
👉 **[`TROUBLESHOOTING.md`](file:///TROUBLESHOOTING.md)**
