"""
=============================================================================
StudyAI — Hardened Authentication & OTP Security Service
=============================================================================
Provides:
- Cryptographic OTP generation and PBKDF2/Argon2 password hashing
- Fast, non-locking in-memory rate limiting with database audit trail
- Single-use verification tokens and replay protection
- SHA-256 digested bearer authentication token management (no raw token in DB)
- Trustworthy client IP resolution based on trusted proxy configuration
=============================================================================
"""

import secrets
import hashlib
import logging
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import EmailVerificationOTP, AuthToken, RateLimitRecord

logger = logging.getLogger(__name__)


class AuthSecurityError(Exception):
    """Raised on security violation (rate limit, expired OTP, invalid token)."""
    def __init__(self, message, code="SECURITY_ERROR", status=400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


def sanitize_email(email):
    """Normalizes and validates email address."""
    if not email or not isinstance(email, str):
        raise AuthSecurityError("Email address is required.", code="EMAIL_REQUIRED")
    email = email.strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        raise AuthSecurityError("Please enter a valid email address.", code="INVALID_EMAIL")
    return email


def generate_secure_otp():
    """
    Generates a cryptographically strong 6-digit numeric OTP.
    Guaranteed range: 100000 to 999999. Never fixed or predictable.
    """
    return f"{secrets.randbelow(900000) + 100000}"


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 cryptographic hex digest of a bearer authentication token."""
    if not raw_token:
        return ""
    return hashlib.sha256(raw_token.strip().encode('utf-8')).hexdigest()


def get_client_ip(request):
    """
    Safely resolves client IP address:
    Only trusts HTTP_X_FORWARDED_FOR if REMOTE_ADDR matches configured TRUSTED_PROXIES.
    Otherwise strictly defaults to REMOTE_ADDR to prevent header-spoofing bypasses.
    """
    if not request:
        return ""
    remote_addr = request.META.get('REMOTE_ADDR', '').strip()
    trusted_proxies = getattr(settings, 'TRUSTED_PROXIES', {'127.0.0.1', '::1'})

    if remote_addr in trusted_proxies:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            parts = [p.strip() for p in x_forwarded_for.split(',') if p.strip()]
            if parts:
                return parts[0]

    return remote_addr


# ----------------- Rate Limiting Safeguards -----------------

def check_otp_request_rate_limit(email, ip_address=""):
    """
    Enforces cooldown and frequency bounds on OTP requests:
    - Minimum 60s cooldown between requests for the same email
    - Max 5 requests per hour for the same email
    - Max 20 requests per hour for the same IP
    Uses atomic in-memory cache checks to prevent DB locking under flood attacks.
    """
    now = timezone.now()
    cooldown_seconds = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)

    # 1. Cooldown check (Cache fast-path)
    cooldown_cache_key = f"rl:otp_cooldown:{email}"
    try:
        if cache.get(cooldown_cache_key):
            raise AuthSecurityError(
                f"Please wait {cooldown_seconds} seconds before requesting another verification code.",
                code="OTP_COOLDOWN",
                status=429
            )
    except AuthSecurityError:
        raise
    except Exception:
        pass

    # Cooldown check (Database verification fallback)
    recent_otp = EmailVerificationOTP.objects.filter(
        email=email
    ).order_by('-created_at').first()

    if recent_otp:
        elapsed = (now - recent_otp.created_at).total_seconds()
        if elapsed < cooldown_seconds:
            wait_sec = int(cooldown_seconds - elapsed)
            raise AuthSecurityError(
                f"Please wait {wait_sec} seconds before requesting another verification code.",
                code="OTP_COOLDOWN",
                status=429
            )

    # 2. Hourly email limit
    email_cache_key = f"rl:otp_email:{email}"
    try:
        count = cache.get(email_cache_key, 0)
        if count >= 5:
            raise AuthSecurityError(
                "Too many verification requests for this email address. Please wait an hour before trying again.",
                code="RATE_LIMIT_EMAIL_EXCEEDED",
                status=429
            )
    except AuthSecurityError:
        raise
    except Exception:
        pass

    one_hour_ago = now - timedelta(hours=1)
    email_requests_count = RateLimitRecord.objects.filter(
        action='otp_request',
        identifier=email,
        timestamp__gte=one_hour_ago
    ).count()

    if email_requests_count >= 5:
        raise AuthSecurityError(
            "Too many verification requests for this email address. Please wait an hour before trying again.",
            code="RATE_LIMIT_EMAIL_EXCEEDED",
            status=429
        )

    # 3. Hourly IP limit
    if ip_address:
        ip_cache_key = f"rl:otp_ip:{ip_address}"
        try:
            count = cache.get(ip_cache_key, 0)
            if count >= 20:
                raise AuthSecurityError(
                    "Too many verification requests from your network. Please wait an hour before trying again.",
                    code="RATE_LIMIT_IP_EXCEEDED",
                    status=429
                )
        except AuthSecurityError:
            raise
        except Exception:
            pass

        ip_requests_count = RateLimitRecord.objects.filter(
            action='otp_request',
            ip_address=ip_address,
            timestamp__gte=one_hour_ago
        ).count()

        if ip_requests_count >= 20:
            raise AuthSecurityError(
                "Too many verification requests from your network. Please wait an hour before trying again.",
                code="RATE_LIMIT_IP_EXCEEDED",
                status=429
            )


def check_login_rate_limit(email, ip_address=""):
    """
    Protects login endpoints against brute-force attacks:
    - Maximum 5 failed login attempts per 5 minutes per email
    - Maximum 10 failed login attempts per 5 minutes per IP
    """
    email_key = f"rl:failed_login:email:{email}"
    try:
        if cache.get(email_key, 0) >= 5:
            raise AuthSecurityError(
                "Too many failed login attempts for this account. Please wait 5 minutes before trying again.",
                code="LOGIN_LOCKED_OUT",
                status=429
            )
    except AuthSecurityError:
        raise
    except Exception:
        pass

    now = timezone.now()
    five_min_ago = now - timedelta(minutes=5)

    failed_email_count = RateLimitRecord.objects.filter(
        action='login',
        identifier=email,
        success=False,
        timestamp__gte=five_min_ago
    ).count()

    if failed_email_count >= 5:
        raise AuthSecurityError(
            "Too many failed login attempts for this account. Please wait 5 minutes before trying again.",
            code="LOGIN_LOCKED_OUT",
            status=429
        )

    if ip_address:
        ip_key = f"rl:failed_login:ip:{ip_address}"
        try:
            if cache.get(ip_key, 0) >= 10:
                raise AuthSecurityError(
                    "Too many failed login attempts from your network. Please wait 5 minutes before trying again.",
                    code="LOGIN_IP_LOCKED_OUT",
                    status=429
                )
        except AuthSecurityError:
            raise
        except Exception:
            pass

        failed_ip_count = RateLimitRecord.objects.filter(
            action='login',
            ip_address=ip_address,
            success=False,
            timestamp__gte=five_min_ago
        ).count()

        if failed_ip_count >= 10:
            raise AuthSecurityError(
                "Too many failed login attempts from your network. Please wait 5 minutes before trying again.",
                code="LOGIN_IP_LOCKED_OUT",
                status=429
            )


def record_security_event(action, identifier, success=True, ip_address=""):
    """Records security audit events and updates cache counters."""
    # Update cache counters
    try:
        if action == 'otp_request' and success:
            cooldown_sec = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)
            cache.set(f"rl:otp_cooldown:{identifier}", True, timeout=cooldown_sec)
            
            cur_email = cache.get(f"rl:otp_email:{identifier}", 0)
            cache.set(f"rl:otp_email:{identifier}", cur_email + 1, timeout=3600)

            if ip_address:
                cur_ip = cache.get(f"rl:otp_ip:{ip_address}", 0)
                cache.set(f"rl:otp_ip:{ip_address}", cur_ip + 1, timeout=3600)

        elif action == 'login':
            if not success:
                cur = cache.get(f"rl:failed_login:email:{identifier}", 0)
                cache.set(f"rl:failed_login:email:{identifier}", cur + 1, timeout=300)
                if ip_address:
                    cur_ip = cache.get(f"rl:failed_login:ip:{ip_address}", 0)
                    cache.set(f"rl:failed_login:ip:{ip_address}", cur_ip + 1, timeout=300)
            else:
                # Clear failed login counter on successful login
                cache.delete(f"rl:failed_login:email:{identifier}")
    except Exception as cache_err:
        logger.debug("Cache update non-fatal error: %s", cache_err)

    # Persist in DB for permanent audit trail
    try:
        RateLimitRecord.objects.create(
            action=action,
            identifier=identifier[:255],
            success=success,
            ip_address=ip_address[:64]
        )
    except Exception as exc:
        logger.warning("Could not record security event to database: %s", exc)


# ----------------- OTP Lifecycle Management -----------------

def create_email_otp(email, purpose="REGISTRATION", ip_address=""):
    """
    Generates a secure 6-digit OTP, hashes it, and persists the record.
    Returns (raw_otp, expires_in_minutes, cooldown_seconds).
    Raw OTP is NEVER persisted in plaintext and NEVER returned to the browser.
    """
    email = sanitize_email(email)
    check_otp_request_rate_limit(email, ip_address)

    raw_otp = generate_secure_otp()
    otp_hash = make_password(raw_otp)

    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
    max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)

    # Invalidate any previous unverified OTPs for this email and purpose
    EmailVerificationOTP.objects.filter(
        email=email,
        purpose=purpose,
        is_used=False
    ).update(is_used=True)

    EmailVerificationOTP.objects.create(
        email=email,
        otp_hash=otp_hash,
        purpose=purpose,
        attempts=0,
        max_attempts=max_attempts,
        is_used=False,
        expires_at=expires_at,
        ip_address=ip_address
    )

    record_security_event('otp_request', email, success=True, ip_address=ip_address)
    cooldown = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)
    return raw_otp, expiry_minutes, cooldown


def verify_email_otp(email, submitted_otp, purpose="REGISTRATION", ip_address=""):
    """
    Validates a submitted 6-digit OTP against the active record:
    - Verifies server-side expiry
    - Verifies single-use
    - Limits incorrect attempts
    - Marks OTP as used upon match
    - Issues a 15-minute verification token for subsequent password creation
    """
    email = sanitize_email(email)
    submitted_otp = str(submitted_otp).strip()

    if not submitted_otp or len(submitted_otp) != 6 or not submitted_otp.isdigit():
        raise AuthSecurityError("Please enter a valid 6-digit verification code.", code="INVALID_FORMAT")

    otp_record = EmailVerificationOTP.objects.filter(
        email=email,
        purpose=purpose
    ).order_by('-created_at').first()

    if not otp_record:
        record_security_event('otp_verify', email, success=False, ip_address=ip_address)
        raise AuthSecurityError("No active verification code found. Please request a new code.", code="OTP_NOT_FOUND")

    if otp_record.is_used:
        record_security_event('otp_verify', email, success=False, ip_address=ip_address)
        raise AuthSecurityError("This verification code has already been used. Please request a new code.", code="OTP_ALREADY_USED")

    if otp_record.is_expired():
        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])
        record_security_event('otp_verify', email, success=False, ip_address=ip_address)
        raise AuthSecurityError("Verification code has expired. Please request a new code.", code="OTP_EXPIRED")

    if otp_record.attempts >= otp_record.max_attempts:
        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])
        record_security_event('otp_verify', email, success=False, ip_address=ip_address)
        raise AuthSecurityError(
            "Maximum verification attempts exceeded. For your security, this code has been invalidated. Please request a new code.",
            code="MAX_ATTEMPTS_EXCEEDED"
        )

    # Check the hash
    if not check_password(submitted_otp, otp_record.otp_hash):
        otp_record.attempts += 1
        otp_record.save(update_fields=['attempts'])
        remaining = max(0, otp_record.max_attempts - otp_record.attempts)
        record_security_event('otp_verify', email, success=False, ip_address=ip_address)
        if remaining == 0:
            otp_record.is_used = True
            otp_record.save(update_fields=['is_used'])
            raise AuthSecurityError(
                "Incorrect code. Maximum attempts exceeded. This code has been invalidated. Please request a new code.",
                code="MAX_ATTEMPTS_EXCEEDED"
            )
        raise AuthSecurityError(
            f"Incorrect verification code. ({remaining} attempt{'s' if remaining != 1 else ''} remaining)",
            code="INCORRECT_OTP"
        )

    # Success: mark OTP used and issue single-use verification token
    verification_token = secrets.token_urlsafe(32)
    otp_record.is_used = True
    otp_record.verification_token = verification_token
    otp_record.verification_token_expires_at = timezone.now() + timedelta(minutes=15)
    otp_record.save(update_fields=['is_used', 'verification_token', 'verification_token_expires_at'])

    record_security_event('otp_verify', email, success=True, ip_address=ip_address)
    return verification_token


def consume_verification_token(email, verification_token, purpose="REGISTRATION"):
    """
    Validates and immediately consumes a single-use verification token.
    Prevents token reuse or replay attacks when setting passwords.
    """
    email = sanitize_email(email)
    if not verification_token:
        raise AuthSecurityError("Verification token is missing. Please verify your email first.", code="TOKEN_MISSING")

    otp_record = EmailVerificationOTP.objects.filter(
        email=email,
        purpose=purpose,
        verification_token=verification_token
    ).order_by('-created_at').first()

    if not otp_record:
        raise AuthSecurityError("Invalid verification session. Please verify your email again.", code="TOKEN_INVALID")

    now = timezone.now()
    if not otp_record.verification_token_expires_at or now > otp_record.verification_token_expires_at:
        raise AuthSecurityError("Verification session has expired. Please verify your email again.", code="TOKEN_EXPIRED")

    # Consume immediately so it cannot be replayed
    otp_record.verification_token = ""
    otp_record.verification_token_expires_at = None
    otp_record.save(update_fields=['verification_token', 'verification_token_expires_at'])
    return True


# ----------------- Auth Token Management -----------------

def create_auth_token(user, ip_address="", user_agent=""):
    """
    Generates and stores a new bearer authentication token for the user.
    The database only ever stores the SHA-256 cryptographic digest of the token.
    The raw token string is attached as .raw_token so the caller can return it once to the client.
    """
    raw_token_string = secrets.token_urlsafe(48)
    token_digest = hash_token(raw_token_string)
    expiry_days = getattr(settings, 'AUTH_TOKEN_EXPIRY_DAYS', 7)
    expires_at = timezone.now() + timedelta(days=expiry_days)

    auth_token = AuthToken.objects.create(
        user=user,
        token=token_digest,
        expires_at=expires_at,
        is_active=True,
        ip_address=ip_address,
        user_agent=user_agent
    )
    auth_token.raw_token = raw_token_string
    return auth_token


def authenticate_bearer_token(token_string):
    """
    Authenticates an incoming Bearer token:
    Computes SHA-256 digest and queries AuthToken.
    Returns User if token is active and unexpired, else None.
    Transparently upgrades legacy unhashed tokens to SHA-256 digests.
    """
    if not token_string:
        return None

    clean_token = token_string.strip()
    token_digest = hash_token(clean_token)

    auth_token = AuthToken.objects.filter(
        token=token_digest,
        is_active=True,
        expires_at__gt=timezone.now()
    ).select_related('user').first()

    # Backward compatibility: check if token was stored in legacy unhashed format
    if not auth_token:
        legacy_token = AuthToken.objects.filter(
            token=clean_token,
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('user').first()
        if legacy_token:
            # Upgrade legacy plaintext token to SHA-256 digest in place
            legacy_token.token = token_digest
            legacy_token.save(update_fields=['token'])
            auth_token = legacy_token

    if auth_token and auth_token.user.is_active:
        return auth_token.user
    return None


def revoke_token(token_string):
    """Revokes a specific bearer token on logout."""
    if token_string:
        clean_token = token_string.strip()
        token_digest = hash_token(clean_token)
        AuthToken.objects.filter(token__in=[token_digest, clean_token]).update(is_active=False)


def revoke_all_user_tokens(user):
    """Revokes all active tokens for a user (e.g. after password reset)."""
    AuthToken.objects.filter(user=user).update(is_active=False)
