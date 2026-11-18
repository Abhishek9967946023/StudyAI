# 🛠️ StudyAI — Cross-Device Troubleshooting Guide

This guide provides targeted diagnoses and exact solutions for issues that can arise when setting up, cloning, or migrating StudyAI across different developer or student computers.

---

## 📑 Quick Navigation

1. [Works on one computer but not another](#1-works-on-one-computer-but-not-another)
2. [Python package installation fails](#2-python-package-installation-fails)
3. [`manage.py` not found](#3-managepy-not-found)
4. [`npm ci` or `npm install` fails](#4-npm-ci-or-npm-install-fails)
5. [`npm run dev` fails](#5-npm-run-dev-fails)
6. [Port already in use (8000 or 5173)](#6-port-already-in-use-8000-or-5173)
7. [API connection refused / Network Error](#7-api-connection-refused--network-error)
8. [CORS error (Cross-Origin Resource Sharing)](#8-cors-error)
9. [CSRF error (403 Forbidden on POST/PUT)](#9-csrf-error)
10. [Ollama connection refused](#10-ollama-connection-refused)
11. [Ollama model not found / wrong model](#11-ollama-model-not-found)
12. [PDF extraction fails](#12-pdf-extraction-fails)
13. [OCR unavailable / Scanned PDF error](#13-ocr-unavailable--scanned-pdf-error)
14. [Database migration error](#14-database-migration-error)
15. [Static files missing (Admin styling broken)](#15-static-files-missing)
16. [Media files missing after transferring project](#16-media-files-missing)
17. [Frontend works but backend doesn't](#17-frontend-works-but-backend-doesnt)
18. [Backend works but frontend doesn't](#18-backend-works-but-frontend-doesnt)
19. [Email / OTP verification delivery issues](#19-email--otp-verification-delivery-issues)

---

### 1. Works on one computer but not another
- **Symptom:** The project runs on the author's primary development machine, but crashes or throws missing module / connection errors on a new computer.
- **Root Causes:**
  1. Dependencies installed globally on Computer A were not installed in Computer B's virtual environment.
  2. Missing `.env` configuration file on Computer B (since `.env` is gitignored).
  3. Database `backend/db.sqlite3` is empty or unmigrated on Computer B.
  4. Ollama or the configured model is not installed on Computer B.
- **Solution:**
  1. On the new machine, run the automated setup script:
     - Windows: `setup_studyai.bat`
     - Linux/macOS: `./setup_studyai.sh`
  2. Run the diagnostic command to check what's missing:
     ```bash
     python backend/manage.py check_configuration
     ```

---

### 2. Python package installation fails
- **Symptom:** `pip install -r backend/requirements.txt` fails with compiler errors or wheel build errors (e.g., PyMuPDF, argon2-cffi).
- **Root Cause:** Incompatible Python version (e.g. Python 3.14 alpha/pre-release) lacking precompiled binary wheels for C-extensions.
- **Solution:**
  1. Ensure you are using **Python 3.12** or **Python 3.10–3.11**. Check with:
     ```bash
     python --version
     ```
  2. Upgrade pip and build tools before installing:
     ```bash
     python -m pip install --upgrade pip setuptools wheel
     pip install -r backend/requirements.txt
     ```

---

### 3. `manage.py` not found
- **Symptom:** `python: can't open file 'manage.py': [Errno 2] No such file or directory`
- **Root Cause:** Running `manage.py` from the project root instead of inside the `backend` directory.
- **Solution:**
  Either navigate to `backend/`:
  ```bash
  cd backend
  python manage.py runserver
  ```
  Or run with path from the repository root:
  ```bash
  python backend/manage.py runserver
  ```

---

### 4. `npm ci` or `npm install` fails
- **Symptom:** `npm error code EPERM` or `npm ERR! missing script: dev` when run at the workspace root.
- **Root Cause:**
  1. Frontend files and dependencies reside in `frontend/`, not at root.
  2. Another process (e.g. active Vite dev server) has locked files in `frontend/node_modules/`.
- **Solution:**
  1. Close any running dev servers or terminals.
  2. Navigate into `frontend/` and install:
     ```bash
     cd frontend
     npm ci
     ```
  3. If permissions are locked on Windows, delete `frontend/node_modules` and run `npm install`.

---

### 5. `npm run dev` fails
- **Symptom:** `vite: command not found` or module resolution errors.
- **Root Cause:** `frontend/node_modules` was not installed or command executed from the wrong directory.
- **Solution:**
  ```bash
  cd frontend
  npm ci
  npm run dev
  ```

---

### 6. Port already in use (8000 or 5173)
- **Symptom:** `Error: That port is already in use` or Vite switches to port `5174`.
- **Root Cause:** An earlier instance of Django (`8000`) or Vite (`5173`) was not stopped.
- **Solution:**
  - **Windows:** Find and terminate the blocking process:
    ```cmd
    netstat -ano | findstr :8000
    taskkill /F /PID <PID_NUMBER>
    netstat -ano | findstr :5173
    taskkill /F /PID <PID_NUMBER>
    ```
  - **Linux / macOS:**
    ```bash
    fuser -k 8000/tcp
    fuser -k 5173/tcp
    ```
  - **Alternative:** Configure custom ports in `.env`:
    ```env
    BACKEND_PORT=8001
    FRONTEND_PORT=5174
    VITE_API_BASE_URL=http://127.0.0.1:8001
    ```

---

### 7. API connection refused / Network Error
- **Symptom:** React frontend displays "Could not connect to StudyAI backend server (Failed to fetch)".
- **Root Cause:**
  1. Django backend is not running.
  2. The frontend is opened on Computer B, but `VITE_API_BASE_URL` is set to `http://localhost:8000` (which resolves to Computer B instead of Computer A hosting the backend).
- **Solution:**
  1. Verify the backend is online by visiting `http://127.0.0.1:8000/api/health/` in your browser.
  2. If connecting across a local WiFi / LAN network:
     - On the hosting machine, find your local IP (e.g. `192.168.1.100` via `ipconfig` or `ifconfig`).
     - In `.env`, set:
       ```env
       VITE_API_BASE_URL=http://192.168.1.100:8000
       DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100
       CORS_ALLOWED_ORIGINS=http://localhost:5173,http://192.168.1.100:5173
       ```
     - Start backend with `python backend/manage.py runserver 0.0.0.0:8000`.

---

### 8. CORS error
- **Symptom:** Browser console shows `Access to fetch has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present`.
- **Root Cause:** The frontend origin (protocol, host, port) is not in `CORS_ALLOWED_ORIGINS`.
- **Solution:**
  Add your frontend address to `CORS_ALLOWED_ORIGINS` in `.env`:
  ```env
  CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.100:5173
  ```
  Restart the Django backend for settings to take effect.

---

### 9. CSRF error
- **Symptom:** State-changing requests (POST, PUT, DELETE) fail with `403 Forbidden: CSRF verification failed`.
- **Root Cause:** The request origin is not in `CSRF_TRUSTED_ORIGINS`.
- **Solution:**
  In `.env`, configure:
  ```env
  CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.100:5173
  ```

---

### 10. Ollama connection refused
- **Symptom:** Backend diagnostic reports `Ollama is unavailable at http://localhost:11434`.
- **Root Cause:** The Ollama background daemon is not running.
- **Solution:**
  1. Open a new terminal and run:
     ```bash
     ollama serve
     ```
  2. Verify it is running by checking `http://localhost:11434/api/tags` in your browser.

---

### 11. Ollama model not found
- **Symptom:** Ollama is online, but model `llama3:latest` is missing.
- **Root Cause:** Ollama was installed, but no LLM weights have been downloaded yet.
- **Solution:**
  Pull the model explicitly:
  ```bash
  ollama pull llama3:latest
  ```
  *(Or set `OLLAMA_MODEL=mistral:latest` in `.env` if you prefer Mistral).*

---

### 12. PDF extraction fails
- **Symptom:** Uploading a PDF returns `400: Malformed PDF` or extraction error.
- **Root Cause:**
  1. File is password-protected or encrypted.
  2. File is corrupt or truncated.
  3. File is a scanned image without a native text layer, and OCR is not installed.
- **Solution:**
  Verify the PDF opens and text can be highlighted in a standard PDF viewer. If the PDF contains only images, see [OCR Unavailable](#13-ocr-unavailable--scanned-pdf-error).

---

### 13. OCR unavailable / Scanned PDF error
- **Symptom:** `This PDF appears to be scanned, but OCR is not available on this system.`
- **Root Cause:** Tesseract OCR binary is not installed or not discovered in system PATH.
- **Solution:**
  1. Install Tesseract OCR:
     - **Windows:** Download from UB-Mannheim (`C:\Program Files\Tesseract-OCR`)
     - **Ubuntu:** `sudo apt-get install tesseract-ocr poppler-utils`
     - **macOS:** `brew install tesseract poppler`
  2. If installed in a non-standard path, add to `.env`:
     ```env
     TESSERACT_CMD=C:\CustomPath\Tesseract-OCR\tesseract.exe
     ```
  3. Test with: `python backend/manage.py check_configuration`

---

### 14. Database migration error
- **Symptom:** `sqlite3.OperationalError: no such table: api_document`
- **Root Cause:** Migrations have not been applied to the local database file.
- **Solution:**
  Run:
  ```bash
  python backend/manage.py migrate
  ```

---

### 15. Static files missing
- **Symptom:** Django Admin (`http://127.0.0.1:8000/admin/`) appears unstyled without CSS.
- **Root Cause:** Static files have not been collected in production mode (`DJANGO_DEBUG=False`).
- **Solution:**
  Run:
  ```bash
  python backend/manage.py collectstatic --noinput
  ```

---

### 16. Media files missing
- **Symptom:** Clicking "Download Original Material" returns `404: Physical document file is missing from storage`.
- **Root Cause:** Database records (`backend/db.sqlite3`) were copied or transferred, but the actual files in `backend/media/` were not copied.
- **Solution:**
  Copy the `backend/media/` folder from the source computer to the target computer alongside `db.sqlite3`.

---

### 17. Frontend works but backend doesn't
- **Symptom:** Vite UI loads at `http://localhost:5173`, but login, upload, and exams show network errors.
- **Root Cause:** Django backend process is stopped or failed on startup.
- **Solution:**
  Start the backend explicitly to view error output:
  ```bash
  cd backend
  python manage.py runserver 127.0.0.1:8000
  ```

---

### 18. Backend works but frontend doesn't
- **Symptom:** `http://127.0.0.1:8000/api/health/` returns `{"status": "online"}`, but `http://127.0.0.1:5173/` refuses connection.
- **Root Cause:** Vite frontend process is not running.
- **Solution:**
  ```bash
  cd frontend
  npm run dev
  ```

---

### 19. Email / OTP verification delivery issues
- **Symptom:** Student registration OTP code is not arriving via email.
- **Root Cause:** In local development without real SMTP credentials, StudyAI uses the console backend.
- **Solution:**
  - **In Development:** Look at the terminal running the Django backend. The 6-digit verification code is printed directly to the console output:
    ```
    ------------------------------------------------------------
    StudyAI Verification Code: 123456
    ------------------------------------------------------------
    ```
  - **In Production:** Configure valid SMTP credentials in `.env`:
    ```env
    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_USE_TLS=True
    EMAIL_HOST_USER=your_email@gmail.com
    EMAIL_HOST_PASSWORD=your_16_char_google_app_password
    ```
