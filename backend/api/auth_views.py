"""
=============================================================================
StudyAI — Authentication API Views
=============================================================================
Handles:
1. Registration flow (Email -> OTP -> Password Creation -> Dashboard Session)
2. Returning-user Login & Logout
3. Current Authenticated User Profile
4. Forgot-Password & Secure Reset Flow
5. Request Authentication Resolution & Ownership Enforcement
=============================================================================
"""

import json
import logging
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .auth_service import (
    sanitize_email,
    create_email_otp,
    verify_email_otp,
    consume_verification_token,
    create_auth_token,
    authenticate_bearer_token,
    revoke_token,
    revoke_all_user_tokens,
    check_login_rate_limit,
    record_security_event,
    get_client_ip,
    AuthSecurityError
)
from .email_service import (
    send_verification_otp_email,
    EmailConfigurationError,
    EmailDeliveryError
)

logger = logging.getLogger(__name__)


def parse_json_payload(request):
    """Safely extracts JSON payload from request body."""
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        return {}


def get_authenticated_user(request):
    """
    Resolves the authenticated user from:
    1. HTTP header 'Authorization: Bearer <token>' or 'Token <token>'
    2. HTTP-only secure cookie 'studyai_auth_token'
    3. Django session 'request.user' if is_authenticated is True
    Returns User instance or None.
    """
    if not request:
        return None

    # 1. Bearer Token in Authorization header
    auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() in ('bearer', 'token'):
            token_string = parts[1]
            user = authenticate_bearer_token(token_string)
            if user:
                return user

    # 2. HTTP-Only Cookie Token
    cookie_token = request.COOKIES.get('studyai_auth_token')
    if cookie_token:
        user = authenticate_bearer_token(cookie_token)
        if user:
            return user

    # 3. Session authentication
    if hasattr(request, 'user') and request.user and request.user.is_authenticated:
        return request.user

    return None


def auth_required(view_func):
    """
    Decorator for views requiring authentication.
    Returns HTTP 401 if request is unauthenticated.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        user = get_authenticated_user(request)
        if not user or not user.is_authenticated:
            return JsonResponse({
                "error": "Authentication required. Please log in to access this resource.",
                "code": "UNAUTHENTICATED"
            }, status=401)
        request.user = user
        return view_func(request, *args, **kwargs)
    return wrapped_view


# ----------------- 1. Registration Flow -----------------

@csrf_exempt
@require_http_methods(["POST"])
def request_registration_otp_view(request):
    """
    Step 1 of Registration:
    - Validates email address format
    - Ensures user is not already registered
    - Enforces rate limits and cooldown
    - Generates 6-digit OTP and sends real email
    """
    data = parse_json_payload(request)
    email_raw = data.get('email', '')
    ip_addr = get_client_ip(request)

    try:
        email = sanitize_email(email_raw)

        # Check if already registered
        if User.objects.filter(email=email, is_active=True).exists():
            return JsonResponse({
                "error": "An account with this email address already exists. Please log in or reset your password.",
                "code": "ACCOUNT_ALREADY_EXISTS"
            }, status=400)

        # Generate and record OTP
        raw_otp, expiry_minutes, cooldown_sec = create_email_otp(
            email=email,
            purpose="REGISTRATION",
            ip_address=ip_addr
        )

        # Deliver email via real email backend
        send_verification_otp_email(email, raw_otp, purpose="REGISTRATION")

        resp_payload = {
            "success": True,
            "message": f"A six-digit verification code has been sent to {email}.",
            "email": email,
            "expires_in_minutes": expiry_minutes,
            "cooldown_seconds": cooldown_sec
        }
        is_console = "console" in getattr(settings, 'EMAIL_BACKEND', '').lower()
        if settings.DEBUG and is_console:
            resp_payload["dev_otp"] = raw_otp
            resp_payload["dev_note"] = f"Local development code: {raw_otp} (console email backend active)"

        return JsonResponse(resp_payload)

    except AuthSecurityError as sec_err:
        return JsonResponse({"error": sec_err.message, "code": sec_err.code}, status=sec_err.status)
    except EmailConfigurationError as cfg_err:
        return JsonResponse({
            "error": str(cfg_err),
            "code": "EMAIL_CONFIG_ERROR"
        }, status=503)
    except EmailDeliveryError as del_err:
        return JsonResponse({
            "error": str(del_err),
            "code": "EMAIL_DELIVERY_ERROR"
        }, status=503)
    except Exception as exc:
        logger.exception("Unexpected error in request_registration_otp_view: %s", exc)
        return JsonResponse({"error": f"An error occurred: {str(exc)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_registration_otp_view(request):
    """
    Step 2 of Registration:
    - Verifies 6-digit OTP code against server-side records
    - Checks expiration, single-use, and attempt limits
    - Issues a 15-minute single-use verification token
    """
    data = parse_json_payload(request)
    email_raw = data.get('email', '')
    otp_code = data.get('otp', '')
    ip_addr = get_client_ip(request)

    try:
        email = sanitize_email(email_raw)
        verification_token = verify_email_otp(
            email=email,
            submitted_otp=otp_code,
            purpose="REGISTRATION",
            ip_address=ip_addr
        )

        return JsonResponse({
            "success": True,
            "verified": True,
            "message": "Email verified successfully.",
            "email": email,
            "verification_token": verification_token
        })

    except AuthSecurityError as sec_err:
        return JsonResponse({"error": sec_err.message, "code": sec_err.code}, status=sec_err.status)
    except Exception as exc:
        logger.exception("Unexpected error in verify_registration_otp_view: %s", exc)
        return JsonResponse({"error": f"An error occurred: {str(exc)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def complete_registration_view(request):
    """
    Step 3 of Registration:
    - Requires single-use verification token from Step 2
    - Enforces password validation
    - Uses Django's PBKDF2 password hasher
    - Creates active User and issues bearer AuthToken
    """
    data = parse_json_payload(request)
    email_raw = data.get('email', '')
    verification_token = data.get('verification_token', '')
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    name = (data.get('name') or '').strip()
    ip_addr = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    try:
        email = sanitize_email(email_raw)

        # 1. Validate & consume verification token (prevent replay)
        consume_verification_token(email, verification_token, purpose="REGISTRATION")

        # 2. Password matching check
        if not password:
            return JsonResponse({"error": "Password cannot be empty.", "code": "PASSWORD_REQUIRED"}, status=400)
        if password != confirm_password:
            return JsonResponse({"error": "Passwords do not match.", "code": "PASSWORD_MISMATCH"}, status=400)

        # 3. Password complexity / strength check
        try:
            validate_password(password)
        except ValidationError as val_err:
            return JsonResponse({"error": " ".join(val_err.messages), "code": "WEAK_PASSWORD"}, status=400)

        # 4. Check concurrency uniqueness
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                "error": "An account with this email address already exists. Please log in.",
                "code": "ACCOUNT_EXISTS"
            }, status=400)

        # 5. Create user securely
        username = email
        user = User.objects.create(
            username=username,
            email=email,
            first_name=name or email.split('@')[0],
            is_active=True
        )
        user.set_password(password)
        user.save()

        # 6. Issue bearer AuthToken
        auth_token = create_auth_token(user, ip_address=ip_addr, user_agent=user_agent)
        raw_token = getattr(auth_token, 'raw_token', auth_token.token)

        # Optional session login for web cookies
        try:
            django_login(request, user)
        except Exception:
            pass

        record_security_event('registration_complete', email, success=True, ip_address=ip_addr)

        response = JsonResponse({
            "success": True,
            "message": "Account created successfully! Welcome to StudyAI.",
            "token": raw_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.first_name
            }
        }, status=201)

        expiry_days = getattr(settings, 'AUTH_TOKEN_EXPIRY_DAYS', 7)
        response.set_cookie(
            key='studyai_auth_token',
            value=raw_token,
            max_age=expiry_days * 86400,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        return response

    except AuthSecurityError as sec_err:
        return JsonResponse({"error": sec_err.message, "code": sec_err.code}, status=sec_err.status)
    except Exception as exc:
        logger.exception("Unexpected error in complete_registration_view: %s", exc)
        return JsonResponse({"error": f"Account creation failed: {str(exc)}"}, status=500)


# ----------------- 2. Login, Logout, Profile -----------------

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """
    Authenticates returning user via email and password:
    - Protects against brute-force attacks via rate limiting
    - Returns generic error message on invalid credentials to protect privacy
    - Issues active AuthToken on success
    """
    data = parse_json_payload(request)
    email_raw = data.get('email', '')
    password = data.get('password', '')
    ip_addr = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    try:
        identifier = str(email_raw).strip()
        if not identifier:
            return JsonResponse({"error": "Email address or username is required.", "code": "IDENTIFIER_REQUIRED"}, status=400)

        if not password:
            return JsonResponse({"error": "Password is required.", "code": "PASSWORD_REQUIRED"}, status=400)

        check_login_rate_limit(identifier.lower(), ip_addr)

        # Match user by email or username
        user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            user = User.objects.filter(username__iexact=identifier).first()

        # Constant-time / generic failure handling
        if not user or not user.check_password(password) or not user.is_active:
            record_security_event('login', identifier.lower(), success=False, ip_address=ip_addr)
            return JsonResponse({
                "error": "Invalid email address or password.",
                "code": "INVALID_CREDENTIALS"
            }, status=401)

        # Success: create token
        auth_token = create_auth_token(user, ip_address=ip_addr, user_agent=user_agent)
        raw_token = getattr(auth_token, 'raw_token', auth_token.token)
        record_security_event('login', identifier.lower(), success=True, ip_address=ip_addr)

        try:
            django_login(request, user)
        except Exception:
            pass

        response = JsonResponse({
            "success": True,
            "message": "Login successful.",
            "token": raw_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.first_name or user.email.split('@')[0]
            }
        })

        expiry_days = getattr(settings, 'AUTH_TOKEN_EXPIRY_DAYS', 7)
        response.set_cookie(
            key='studyai_auth_token',
            value=raw_token,
            max_age=expiry_days * 86400,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        return response

    except AuthSecurityError as sec_err:
        return JsonResponse({"error": sec_err.message, "code": sec_err.code}, status=sec_err.status)
    except Exception as exc:
        logger.exception("Unexpected error in login_view: %s", exc)
        return JsonResponse({"error": f"An error occurred: {str(exc)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """
    Invalidates current bearer token and clears session & cookie.
    """
    auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() in ('bearer', 'token'):
            revoke_token(parts[1])

    cookie_token = request.COOKIES.get('studyai_auth_token')
    if cookie_token:
        revoke_token(cookie_token)

    try:
        django_logout(request)
    except Exception:
        pass

    response = JsonResponse({
        "success": True,
        "message": "Logged out successfully."
    })
    response.delete_cookie('studyai_auth_token')
    return response


@require_http_methods(["GET"])
def current_user_view(request):
    """
    Returns profile information for currently authenticated user.
    """
    user = get_authenticated_user(request)
    if not user or not user.is_authenticated:
        return JsonResponse({
            "error": "Not authenticated.",
            "code": "UNAUTHENTICATED"
        }, status=401)

    return JsonResponse({
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.first_name or user.email.split('@')[0],
            "date_joined": user.date_joined.isoformat() if hasattr(user, 'date_joined') else None
        }
    })


# ----------------- 3. Forgot-Password Flow -----------------

@csrf_exempt
@require_http_methods(["POST"])
def request_password_reset_otp_view(request):
    """
    Step 1 of Forgot Password:
    - Requests OTP for password reset
    - To prevent account enumeration, returns generic success even if email is not found
    - Only sends email if active user exists
    """
    data = parse_json_payload(request)
    email_raw = data.get('email', '')
    ip_addr = get_client_ip(request)

    try:
        email = sanitize_email(email_raw)
        user = User.objects.filter(email=email, is_active=True).first()

        expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        cooldown_sec = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)

        if user:
            raw_otp, expiry_minutes, cooldown_sec = create_email_otp(
                email=email,
                purpose="PASSWORD_RESET",
                ip_address=ip_addr
            )
            send_verification_otp_email(email, raw_otp, purpose="PASSWORD_RESET")

        resp_payload = {
            "success": True,
            "message": "If an account exists with this email address, a password reset code has been sent.",
            "email": email,
            "expires_in_minutes": expiry_minutes,
            "cooldown_seconds": cooldown_sec
        }
        is_console = "console" in getattr(settings, 'EMAIL_BACKEND', '').lower()
        if settings.DEBUG and is_console:
            if user:
                resp_payload["dev_otp"] = raw_otp
                resp_payload["dev_note"] = f"Local development code: {raw_otp} (console email backend active)"
            else:
                resp_payload["dev_note"] = f"Note: No registered user found for '{email}'. Please create an account on the Register page first."

        return JsonResponse(resp_payload)

    except AuthSecurityError as sec_err:
        return JsonResponse({"error": sec_err.message, "code": sec_err.code}, status=sec_err.status)
    except EmailConfigurationError as cfg_err:
        return JsonResponse({
            "error": str(cfg_err),
            "code": "EMAIL_CONFIG_ERROR"
        }, status=503)
    except EmailDeliveryError as del_err:
        return JsonResponse({
            "error": str(del_err),
            "code": "EMAIL_DELIVERY_ERROR"
        }, status=503)
    except Exception as exc:
        logger.exception("Unexpected error in request_password_reset_otp_view: %s", exc)
        return JsonResponse({"error": f"An error occurred: {str(exc)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_password_reset_otp_view(request):
    """
    Step 2 of Forgot Password:
    - Verifies 6-digit reset OTP
    - Issues single-use reset token
    """
    data = parse_json_payload(request)
    email_raw = data.get('email', '')
    otp_code = data.get('otp', '')
    ip_addr = get_client_ip(request)

    try:
        email = sanitize_email(email_raw)
        reset_token = verify_email_otp(
            email=email,
            submitted_otp=otp_code,
            purpose="PASSWORD_RESET",
            ip_address=ip_addr
        )

        return JsonResponse({
            "success": True,
            "verified": True,
            "message": "Reset code verified successfully.",
            "email": email,
            "reset_token": reset_token,
            "verification_token": reset_token
        })

    except AuthSecurityError as sec_err:
        return JsonResponse({"error": sec_err.message, "code": sec_err.code}, status=sec_err.status)
    except Exception as exc:
        logger.exception("Unexpected error in verify_password_reset_otp_view: %s", exc)
        return JsonResponse({"error": f"An error occurred: {str(exc)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def confirm_password_reset_view(request):
    """
    Step 3 of Forgot Password:
    - Requires single-use reset token
    - Validates new password & confirmation
    - Updates user password securely
    - Revokes all prior auth tokens
    - Issues fresh auth token
    """
    data = parse_json_payload(request)
    email_raw = data.get('email', '')
    reset_token = data.get('reset_token') or data.get('verification_token') or data.get('token', '')
    new_password = data.get('new_password') or data.get('password', '')
    confirm_password = data.get('confirm_password') or data.get('confirmPassword', '')
    ip_addr = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    try:
        email = sanitize_email(email_raw)

        # 1. Validate & consume reset token
        consume_verification_token(email, reset_token, purpose="PASSWORD_RESET")

        # 2. Check password matching
        if not new_password:
            return JsonResponse({"error": "New password cannot be empty.", "code": "PASSWORD_REQUIRED"}, status=400)
        if new_password != confirm_password:
            return JsonResponse({"error": "Passwords do not match.", "code": "PASSWORD_MISMATCH"}, status=400)

        # 3. Complexity check
        try:
            validate_password(new_password)
        except ValidationError as val_err:
            return JsonResponse({"error": " ".join(val_err.messages), "code": "WEAK_PASSWORD"}, status=400)

        # 4. Lookup user — MUST NOT create new account
        user = User.objects.filter(email=email, is_active=True).first()
        if not user:
            return JsonResponse({
                "error": "No user account was found for this email address.",
                "code": "USER_NOT_FOUND"
            }, status=404)

        # 5. Save new password and revoke old tokens
        user.set_password(new_password)
        user.save()
        revoke_all_user_tokens(user)

        # 6. Issue fresh session token
        auth_token = create_auth_token(user, ip_address=ip_addr, user_agent=user_agent)
        raw_token = getattr(auth_token, 'raw_token', auth_token.token)
        record_security_event('password_reset_complete', email, success=True, ip_address=ip_addr)

        response = JsonResponse({
            "success": True,
            "message": "Password reset successfully. You can now log in with your new password.",
            "token": raw_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.first_name or user.email.split('@')[0]
            }
        })

        expiry_days = getattr(settings, 'AUTH_TOKEN_EXPIRY_DAYS', 7)
        response.set_cookie(
            key='studyai_auth_token',
            value=raw_token,
            max_age=expiry_days * 86400,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        return response

    except AuthSecurityError as sec_err:
        return JsonResponse({"error": sec_err.message, "code": sec_err.code}, status=sec_err.status)
    except Exception as exc:
        logger.exception("Unexpected error in confirm_password_reset_view: %s", exc)
        return JsonResponse({"error": f"An error occurred: {str(exc)}"}, status=500)


# ----------------- 5. CSRF Defense Endpoint -----------------

from django.middleware.csrf import get_token

@require_http_methods(["GET"])
def csrf_token_view(request):
    """
    Issues and sets a CSRF cookie for the client session.
    Allows frontend clients to retrieve and bind an anti-CSRF token.
    """
    token = get_token(request)
    return JsonResponse({"csrfToken": token})

