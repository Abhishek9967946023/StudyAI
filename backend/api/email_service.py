"""
=============================================================================
StudyAI — Real Email Delivery Service
=============================================================================
Dispatches verification OTPs using Django's email framework and configured SMTP.
Enforces:
1. Clear configuration errors if SMTP credentials are missing.
2. Safe local development fallback if console/locmem backend is configured.
3. Branded HTML and accessible plain-text email templates.
4. Complete confidentiality — OTP codes are never logged to ordinary stdout.
=============================================================================
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

logger = logging.getLogger(__name__)


class EmailConfigurationError(Exception):
    """Raised when email delivery is attempted with missing or invalid credentials."""
    pass


class EmailDeliveryError(Exception):
    """Raised when email delivery fails due to SMTP network or provider errors."""
    pass


def is_email_backend_configured():
    """
    Checks if email delivery backend is properly configured.
    Console and locmem backends don't require SMTP passwords.
    SMTP backends require EMAIL_HOST_USER and EMAIL_HOST_PASSWORD.
    """
    backend = getattr(settings, 'EMAIL_BACKEND', '')
    if 'console' in backend or 'locmem' in backend or 'filebased' in backend:
        return True, "Configured for local development/testing."

    host_user = getattr(settings, 'EMAIL_HOST_USER', '')
    host_pwd = getattr(settings, 'EMAIL_HOST_PASSWORD', '')

    # Check if empty or obvious placeholder
    if not host_user or not host_pwd or 'placeholder' in host_pwd.lower():
        return False, (
            "SMTP email service is not configured. EMAIL_HOST_USER and EMAIL_HOST_PASSWORD "
            "must be set in your .env file to deliver verification codes. "
            "For local testing without real SMTP, set EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend in .env."
        )
    return True, "Configured with SMTP credentials."


def send_verification_otp_email(to_email, otp_code, purpose="REGISTRATION"):
    """
    Sends a 6-digit OTP to the recipient email using Django's EmailMultiAlternatives.

    Raises:
        EmailConfigurationError: if SMTP credentials are missing.
        EmailDeliveryError: if sending fails over the network.
    """
    to_email = to_email.strip().lower()
    try:
        validate_email(to_email)
    except ValidationError:
        raise ValueError(f"Invalid recipient email address: '{to_email}'")

    configured, msg = is_email_backend_configured()
    if not configured:
        logger.error("Email delivery failed: %s", msg)
        raise EmailConfigurationError(msg)

    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)

    if purpose == "PASSWORD_RESET":
        subject = f"StudyAI — Your Password Reset Code: {otp_code}"
        headline = "Reset Your StudyAI Password"
        instruction = "We received a request to reset your StudyAI account password. Use the verification code below to proceed:"
    else:
        subject = f"StudyAI — Your Verification Code: {otp_code}"
        headline = "Verify Your StudyAI Account"
        instruction = "Welcome to StudyAI! Enter the six-digit verification code below to confirm your email and complete registration:"

    # Plain-text body
    plain_text = f"""{headline}

{instruction}

Verification Code: {otp_code}

This code will expire in {expiry_minutes} minutes and can only be used once.
If you did not request this verification code, please ignore this email.

— The StudyAI Team
Educational Intelligence Platform
"""

    # HTML body matching StudyAI's modern visual design
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #f6f5fb;
      margin: 0;
      padding: 30px 15px;
      color: #17152b;
    }}
    .email-container {{
      max-width: 520px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 16px;
      padding: 36px 32px;
      box-shadow: 0 10px 30px rgba(79, 63, 240, 0.08);
      border: 1px solid #e6e3f3;
    }}
    .brand-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 24px;
    }}
    .logo-badge {{
      display: inline-block;
      width: 34px;
      height: 34px;
      line-height: 34px;
      background: linear-gradient(135deg, #4f3ff0, #8b5cf6);
      color: #ffffff;
      font-size: 18px;
      font-weight: bold;
      text-align: center;
      border-radius: 10px;
    }}
    .brand-title {{
      font-size: 20px;
      font-weight: 700;
      color: #17152b;
      margin: 0;
    }}
    .brand-subtitle {{
      font-size: 11px;
      color: #5e5a7a;
      letter-spacing: 0.5px;
      margin: 2px 0 0 0;
    }}
    h2 {{
      color: #17152b;
      font-size: 20px;
      margin-top: 16px;
      margin-bottom: 12px;
    }}
    p {{
      color: #5e5a7a;
      font-size: 14px;
      line-height: 1.6;
      margin: 0 0 20px 0;
    }}
    .code-container {{
      background: #eceaff;
      border: 1px dashed #4f3ff0;
      border-radius: 12px;
      padding: 20px;
      text-align: center;
      margin: 24px 0;
    }}
    .otp-code {{
      font-family: 'SF Mono', Monaco, Menlo, Consolas, monospace;
      font-size: 34px;
      font-weight: 800;
      letter-spacing: 10px;
      color: #4f3ff0;
      margin: 0;
    }}
    .expiry-note {{
      font-size: 12px;
      color: #5e5a7a;
      margin-top: 8px;
    }}
    .footer {{
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #e6e3f3;
      font-size: 11px;
      color: #8e8aa8;
      text-align: center;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="brand-header">
      <div class="logo-badge">✦</div>
      <div>
        <div class="brand-title">StudyAI</div>
        <div class="brand-subtitle">AI Study Analyzer & Exam Generator</div>
      </div>
    </div>
    <h2>{headline}</h2>
    <p>{instruction}</p>
    <div class="code-container">
      <div class="otp-code">{otp_code}</div>
      <div class="expiry-note">Expires in <strong>{expiry_minutes} minutes</strong> • Single use only</div>
    </div>
    <p style="font-size: 13px;">Never share this code with anyone. StudyAI support will never ask for your verification code.</p>
    <div class="footer">
      This is an automated security transmission sent to {to_email}.<br>
      © StudyAI Platform — Grounded Academic Intelligence.
    </div>
  </div>
</body>
</html>
"""

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'StudyAI <no-reply@studyai.edu>')

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_text,
        from_email=from_email,
        to=[to_email]
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        logger.info("Sent %s verification email to %s", purpose, to_email)
        return True
    except Exception as exc:
        logger.error("Failed to deliver email to %s: %s", to_email, str(exc))
        raise EmailDeliveryError(f"Could not deliver verification email via SMTP: {str(exc)}")
