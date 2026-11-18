# ⚙️ Backend Subsystem (Member 1: Backend Developer)

Welcome to the **StudyAI Backend** module. This directory encapsulates the Django REST API, database architecture, authentication service, and document ingestion system.

---

## 👥 Module Ownership: Member 1 (Backend Developer)
- **Primary Responsibility**: Database models, migrations, authentication & security, document ingestion API endpoints, rate limiting, and CORS/CSRF middleware.
- **Key Files & Folders**:
  - `manage.py`: Django administrative CLI entrypoint.
  - `studyai_backend/`: Core project settings, security headers, middleware, and root URL routing.
  - `api/models.py`: Data models (`Document`, `Chunk`, `Topic`, `Question`, `Exam`, `ExamAttempt`, `RevisionTask`, `RateLimitRecord`).
  - `api/views.py`: REST API endpoints for document ingestion, study guides, exam generation, and progress tracking.
  - `api/auth_views.py`: Registration, login, logout, password resets, session tokens.
  - `api/auth_service.py`: Password hashing (Argon2id), rate limiting, and token management.
  - `api/document_service.py`: File ingestion, PDF/DOCX magic bytes verification, sanitization, and database chunking.
  - `db.sqlite3`: Local SQLite database.
  - `requirements.txt`: Python package dependencies.

---

## 🚀 Quick Setup for Member 1

### 1. Activate Environment
```powershell
# On Windows:
backend\venv\Scripts\activate
```

### 2. Run Database Migrations
```bash
python backend/manage.py migrate
```

### 3. Start the Backend Development Server
```bash
python backend/manage.py runserver 127.0.0.1:8000
```
- API Base: `http://127.0.0.1:8000/api/`
- Health Check: `http://127.0.0.1:8000/api/health/`
- Admin Panel: `http://127.0.0.1:8000/admin/`

---

## 📡 Core API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health/` | `GET` | Health status and Ollama availability |
| `/api/auth/register/` | `POST` | User registration |
| `/api/auth/login/` | `POST` | User login & session creation |
| `/api/auth/logout/` | `POST` | Invalidate session |
| `/api/auth/me/` | `GET` | Current authenticated user profile |
| `/api/documents/upload/` | `POST` | Upload and process study material |
| `/api/documents/` | `GET` | List user uploaded documents |
| `/api/documents/<id>/` | `GET` | Retrieve document details & chunks |
| `/api/generate-summary/` | `POST` | Generate hierarchical study notes |
| `/api/generate-exam/` | `POST` | Generate practice exam questions |
| `/api/submit-attempt/` | `POST` | Grade student exam submission |
| `/api/analytics/` | `GET` | Student mastery & revision radar data |

---

## 🧪 Testing Backend
```bash
python testing/run_tests.py --backend
```

## AI usage visibility

Provider attempts are recorded in the Django admin as `AI usage events`. Records include the provider/model, success or failure category, fallback usage, latency, and provider-reported token counts when available. Prompts, generated text, and API keys are not stored in these events. Estimated cost stays empty unless per-million input/output rates are configured for the exact model name:

```env
AI_MODEL_PRICING_USD_PER_1M_JSON={"gpt-4o-mini":{"input":"0.15","output":"0.6"}}
```

Keep rates current with the provider's published pricing; unconfigured or unavailable token usage is not guessed.
