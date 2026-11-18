"""
=============================================================================
StudyAI — Hardened Django Backend Settings
=============================================================================
Configures the Django backend for StudyAI with production security defenses:
- Cryptographic secret key enforcement (no static fallbacks)
- Safe fail-fast environment variable validation
- Strict CORS & CSRF origin controls
- In-memory cache for atomic rate-limiting
- Argon2id password hashing with legacy upgrade compatibility
- Baseline HTTP security headers & secure cookie defaults
=============================================================================
"""

from pathlib import Path
import json
import os
import sys

# Build paths inside the project: BASE_DIR is 'backend'
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe environment variables loader from .env
def _load_env_file(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        parts = line.split('=', 1)
                        k = parts[0].strip()
                        v = parts[1].strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception as e:
            sys.stderr.write(f"[WARNING] Error reading environment file {path}: {str(e)}\n")

env_file_custom = os.environ.get('ENV_FILE')
if env_file_custom:
    _load_env_file(Path(env_file_custom))
_load_env_file(BASE_DIR.parent / '.env')
_load_env_file(BASE_DIR / '.env')

# SECURITY: Debug toggle controlled via DJANGO_DEBUG (defaults safely to False)
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

# SECURITY: Secret key enforcement — never allow publicly known default keys
raw_secret = os.environ.get('DJANGO_SECRET_KEY')
if raw_secret and len(raw_secret.strip()) >= 32:
    SECRET_KEY = raw_secret.strip()
elif DEBUG:
    import secrets
    SECRET_KEY = secrets.token_urlsafe(64)
    sys.stderr.write("[SECURITY NOTICE] DJANGO_SECRET_KEY unset in development; using ephemeral session key.\n")
else:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        "CRITICAL: DJANGO_SECRET_KEY environment variable is mandatory in production! "
        "Generate a strong 64-character secret and set DJANGO_SECRET_KEY in your environment."
    )

# SECURITY: Allowed hosts list parsed from DJANGO_ALLOWED_HOSTS or ALLOWED_HOSTS env var
allowed_hosts_env = os.environ.get('DJANGO_ALLOWED_HOSTS') or os.environ.get('ALLOWED_HOSTS', '')
if allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver']

# SECURITY: CORS Allowed Origins configuration
cors_env = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000'
)
cors_origins_list = [origin.strip() for origin in cors_env.split(',') if origin.strip()]
frontend_url = os.environ.get('FRONTEND_URL')
if frontend_url and frontend_url.strip() not in cors_origins_list:
    cors_origins_list.append(frontend_url.strip())
CORS_ALLOWED_ORIGINS = cors_origins_list
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# SECURITY: CSRF Trusted Origins for state-changing requests
csrf_origins_env = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins_env.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [o for o in CORS_ALLOWED_ORIGINS if o.startswith(('http://', 'https://'))]

# Document Ingestion upload sizes (25MB standard safeguard)
MAX_UPLOAD_SIZE_BYTES = int(os.environ.get('MAX_UPLOAD_SIZE_BYTES', 25 * 1024 * 1024))
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_BYTES
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_BYTES

# HTTP Security Headers & Cookie Flags
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False  # Required so frontend JS can read and attach X-CSRFToken
CSRF_COOKIE_SAMESITE = 'Lax'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    if os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes'):
        SECURE_SSL_REDIRECT = True
        SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True

# Trusted reverse proxies for client IP extraction
TRUSTED_PROXIES = set(
    p.strip() for p in os.environ.get('DJANGO_TRUSTED_PROXIES', '127.0.0.1,::1').split(',') if p.strip()
)

# Cache configuration: supports Redis in production multi-worker environments with LocMemCache local fallback
redis_url = os.environ.get('REDIS_URL', '').strip()
if redis_url:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url,
            'TIMEOUT': 300,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'studyai-security-cache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 10000,
                'CULL_FREQUENCY': 3,
            }
        }
    }

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # StudyAI Educational Intelligence API App
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Custom CORS Middleware at the top to handle React frontend requests
    'studyai_backend.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'studyai_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'studyai_backend.wsgi.application'

# =============================================================================
# Database Configuration
# =============================================================================
database_url = os.environ.get('DATABASE_URL', '').strip()
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'False').lower() in ('true', '1')

if database_url.startswith(('postgres://', 'postgresql://')) or USE_POSTGRES:
    if database_url:
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': parsed.path.lstrip('/') or 'studyai_db',
                'USER': parsed.username or 'postgres',
                'PASSWORD': parsed.password or '',
                'HOST': parsed.hostname or 'localhost',
                'PORT': str(parsed.port or 5432),
            }
        }
    else:
        db_pass = os.environ.get('DB_PASSWORD')
        if not db_pass and not DEBUG:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured("CRITICAL: DB_PASSWORD must be configured for PostgreSQL in production.")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_NAME', 'studyai_db'),
                'USER': os.environ.get('DB_USER', 'postgres'),
                'PASSWORD': db_pass or 'postgres',
                'HOST': os.environ.get('DB_HOST', 'localhost'),
                'PORT': os.environ.get('DB_PORT', '5432'),
            }
        }
elif database_url.startswith('sqlite:///'):
    sqlite_rel = database_url.replace('sqlite:///', '')
    sqlite_path = Path(sqlite_rel)
    if not sqlite_path.is_absolute():
        sqlite_path = BASE_DIR / sqlite_path
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_path,
        }
    }
else:
    # SQLite Configuration (Default, portable, built-in)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password hashing with modern PBKDF2/Argon2 priority and legacy upgrade fallback
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]
try:
    import argon2  # noqa
    PASSWORD_HASHERS.insert(0, 'django.contrib.auth.hashers.Argon2PasswordHasher')
except ImportError:
    pass


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# Media files (for uploaded documents)
MEDIA_URL = 'media/'
media_root_env = os.environ.get('MEDIA_ROOT')
MEDIA_ROOT = Path(media_root_env).resolve() if media_root_env else (BASE_DIR / 'media')
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Ollama Host & Model URL (supports OLLAMA_BASE_URL and OLLAMA_HOST)
OLLAMA_HOST = (
    os.environ.get('OLLAMA_BASE_URL')
    or os.environ.get('OLLAMA_HOST')
    or 'http://localhost:11434'
    ).rstrip('/')
OLLAMA_BASE_URL = OLLAMA_HOST
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3:latest')
OLLAMA_TEMPERATURE = float(os.environ.get('OLLAMA_TEMPERATURE', '0.2'))
OLLAMA_CONTEXT_LENGTH = int(os.environ.get('OLLAMA_CONTEXT_LENGTH', '8192'))
OLLAMA_NUM_PREDICT = int(os.environ.get('OLLAMA_NUM_PREDICT', '3000'))
OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '120'))

# AI provider credentials and model selection remain server-side environment settings.
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'ollama').strip().lower()
AI_FALLBACK_PROVIDER = os.environ.get('AI_FALLBACK_PROVIDER', '').strip().lower()
AI_MAX_TOKENS = int(os.environ.get('AI_MAX_TOKENS', '3000'))
try:
    AI_MODEL_PRICING_USD_PER_1M = json.loads(
        os.environ.get('AI_MODEL_PRICING_USD_PER_1M_JSON', '{}')
    )
except json.JSONDecodeError as exc:
    raise ValueError("AI_MODEL_PRICING_USD_PER_1M_JSON must be valid JSON.") from exc
if not isinstance(AI_MODEL_PRICING_USD_PER_1M, dict):
    raise ValueError("AI_MODEL_PRICING_USD_PER_1M_JSON must be a JSON object.")
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '').strip()
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini').strip()
OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1').strip().rstrip('/')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash').strip()
GEMINI_BASE_URL = os.environ.get(
    'GEMINI_BASE_URL',
    'https://generativelanguage.googleapis.com/v1beta'
).strip().rstrip('/')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '').strip()
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-haiku-latest').strip()
ANTHROPIC_BASE_URL = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com/v1').strip().rstrip('/')

# =============================================================================
# Optical Character Recognition (OCR) Engine Configuration
# =============================================================================
TESSERACT_CMD = os.environ.get('TESSERACT_CMD', '').strip()
OCR_LANGUAGES = os.environ.get('OCR_LANGUAGES', 'eng').strip()
OCR_DPI = int(os.environ.get('OCR_DPI', '200'))
OCR_TIMEOUT_PER_PAGE = int(os.environ.get('OCR_TIMEOUT_PER_PAGE', '25'))
OCR_TOTAL_TIMEOUT = int(os.environ.get('OCR_TOTAL_TIMEOUT', '300'))
MAX_OCR_PAGES = int(os.environ.get('MAX_OCR_PAGES', '100'))
OCR_QUALITY_MODE = os.environ.get('OCR_QUALITY_MODE', 'BALANCED').strip().upper()
OCR_MIN_CONFIDENCE = float(os.environ.get('OCR_MIN_CONFIDENCE', '50.0'))


# =============================================================================
# Email Delivery Configuration (Real SMTP / Testing Console Backend)
# =============================================================================
# Smart development default: if in DEBUG and no SMTP user set, route to console
default_email_backend = 'django.core.mail.backends.smtp.EmailBackend'
if DEBUG and not os.environ.get('EMAIL_HOST_USER'):
    default_email_backend = 'django.core.mail.backends.console.EmailBackend'

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', default_email_backend)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    EMAIL_HOST_USER if EMAIL_HOST_USER else 'StudyAI Platform <no-reply@studyai.edu>'
)
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))

# =============================================================================
# Authentication & Security Safeguards
# =============================================================================
OTP_EXPIRY_MINUTES = int(os.environ.get('OTP_EXPIRY_MINUTES', '10'))
OTP_MAX_ATTEMPTS = int(os.environ.get('OTP_MAX_ATTEMPTS', '5'))
OTP_RESEND_COOLDOWN_SECONDS = int(os.environ.get('OTP_RESEND_COOLDOWN_SECONDS', '60'))
AUTH_TOKEN_EXPIRY_DAYS = int(os.environ.get('AUTH_TOKEN_EXPIRY_DAYS', '7'))

# =============================================================================
# Document Processing Pipeline & Heartbeat Configuration
# =============================================================================
DOCUMENT_PIPELINE_WORKERS = int(os.environ.get('DOCUMENT_PIPELINE_WORKERS', '2'))
DOCUMENT_HEARTBEAT_TIMEOUT_SECONDS = int(os.environ.get('DOCUMENT_HEARTBEAT_TIMEOUT_SECONDS', '360'))

