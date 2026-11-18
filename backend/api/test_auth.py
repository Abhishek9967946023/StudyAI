"""
=============================================================================
StudyAI — Comprehensive Email OTP Authentication & Data Isolation Test Suite
=============================================================================
Covers:
1. Registration OTP generation, rate limits, cooldown, and validation
2. Real email / console backend dispatch and unconfigured SMTP 503 handling
3. OTP verification: single-use, max attempts, expiry, and replay prevention
4. Account creation: PBKDF2 hashing, password strength validation, session/token issue
5. Returning-user login: brute-force lockout, generic error masking
6. Session and Bearer token lifecycle, logout, and token revocation
7. Forgot-password flow: reset OTP, verification, password update, token revocation
8. Multi-tenant data isolation: User A records are strictly 403 Forbidden to User B
=============================================================================
"""

import json
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core import mail
from .models import (
    Document, Exam, ExamAttempt, RevisionTask, AdaptivePracticeLoop,
    EmailVerificationOTP, AuthToken, RateLimitRecord
)
from .email_service import EmailConfigurationError


class EmailOTPAuthenticationTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = Client()
        self.reg_email = "student@studyai.test"
        self.password = "StudySecurePass123!"

    # ---------------- 1. Registration OTP Flow ----------------

    def test_request_registration_otp_success(self):
        resp = self.client.post(
            "/api/auth/register/request-otp/",
            data=json.dumps({"email": self.reg_email}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("verification code has been sent", data.get("message", "").lower())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.reg_email, mail.outbox[0].to)
        self.assertIn("Verification Code", mail.outbox[0].subject)

        # Check DB record
        otp_record = EmailVerificationOTP.objects.filter(email=self.reg_email, purpose="REGISTRATION").first()
        self.assertIsNotNone(otp_record)
        self.assertFalse(otp_record.is_used)

    def test_request_registration_otp_cooldown(self):
        # First request
        self.client.post(
            "/api/auth/register/request-otp/",
            data=json.dumps({"email": self.reg_email}),
            content_type="application/json"
        )
        # Immediate second request should be throttled (429)
        resp2 = self.client.post(
            "/api/auth/register/request-otp/",
            data=json.dumps({"email": self.reg_email}),
            content_type="application/json"
        )
        self.assertEqual(resp2.status_code, 429)
        self.assertIn("wait", resp2.json().get("error", "").lower())

    def test_request_registration_otp_invalid_email(self):
        resp = self.client.post(
            "/api/auth/register/request-otp/",
            data=json.dumps({"email": "not-a-valid-email"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("valid email", resp.json().get("error", "").lower())

    def test_request_registration_otp_already_registered(self):
        User.objects.create_user(username=self.reg_email, email=self.reg_email, password=self.password)
        resp = self.client.post(
            "/api/auth/register/request-otp/",
            data=json.dumps({"email": self.reg_email}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("already exists", resp.json().get("error", "").lower())

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_HOST_USER="",
        EMAIL_HOST_PASSWORD=""
    )
    def test_request_registration_otp_missing_smtp_config_returns_503(self):
        resp = self.client.post(
            "/api/auth/register/request-otp/",
            data=json.dumps({"email": "unconfigured@studyai.test"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 503)
        self.assertIn("email service is not configured", resp.json().get("error", "").lower())

    # ---------------- 2. Verify Registration OTP ----------------

    def test_verify_registration_otp_success(self):
        # Seed an OTP
        raw_code = "654321"
        EmailVerificationOTP.objects.create(
            email=self.reg_email,
            otp_hash=make_password(raw_code),
            purpose="REGISTRATION",
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        resp = self.client.post(
            "/api/auth/register/verify-otp/",
            data=json.dumps({"email": self.reg_email, "otp": raw_code}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("verified"))
        self.assertTrue(bool(data.get("verification_token")))

        # Check that OTP is now marked as used
        otp_rec = EmailVerificationOTP.objects.get(email=self.reg_email, purpose="REGISTRATION")
        self.assertTrue(otp_rec.is_used)

    def test_verify_registration_otp_wrong_code(self):
        EmailVerificationOTP.objects.create(
            email=self.reg_email,
            otp_hash=make_password("112233"),
            purpose="REGISTRATION",
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        resp = self.client.post(
            "/api/auth/register/verify-otp/",
            data=json.dumps({"email": self.reg_email, "otp": "999999"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("incorrect", resp.json().get("error", "").lower())

        # Check attempt count incremented
        otp_rec = EmailVerificationOTP.objects.get(email=self.reg_email, purpose="REGISTRATION")
        self.assertEqual(otp_rec.attempts, 1)

    def test_verify_registration_otp_max_attempts_exceeded(self):
        EmailVerificationOTP.objects.create(
            email=self.reg_email,
            otp_hash=make_password("112233"),
            purpose="REGISTRATION",
            attempts=5,
            max_attempts=5,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        resp = self.client.post(
            "/api/auth/register/verify-otp/",
            data=json.dumps({"email": self.reg_email, "otp": "112233"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("exceeded", resp.json().get("error", "").lower())

    def test_verify_registration_otp_expired(self):
        EmailVerificationOTP.objects.create(
            email=self.reg_email,
            otp_hash=make_password("112233"),
            purpose="REGISTRATION",
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        resp = self.client.post(
            "/api/auth/register/verify-otp/",
            data=json.dumps({"email": self.reg_email, "otp": "112233"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("expired", resp.json().get("error", "").lower())

    def test_verify_registration_otp_single_use(self):
        raw_code = "789123"
        otp_obj = EmailVerificationOTP.objects.create(
            email=self.reg_email,
            otp_hash=make_password(raw_code),
            purpose="REGISTRATION",
            is_used=True,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        resp = self.client.post(
            "/api/auth/register/verify-otp/",
            data=json.dumps({"email": self.reg_email, "otp": raw_code}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("already been used", resp.json().get("error", "").lower())

    # ---------------- 3. Complete Registration ----------------

    def test_complete_registration_success(self):
        token_str = "verif-token-12345"
        EmailVerificationOTP.objects.create(
            email=self.reg_email,
            otp_hash=make_password("123456"),
            purpose="REGISTRATION",
            is_used=True,
            verification_token=token_str,
            verification_token_expires_at=timezone.now() + timedelta(minutes=15),
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        resp = self.client.post(
            "/api/auth/register/complete/",
            data=json.dumps({
                "email": self.reg_email,
                "verification_token": token_str,
                "password": self.password,
                "confirm_password": self.password
            }),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertTrue(bool(data.get("token")))
        self.assertEqual(data.get("user", {}).get("email"), self.reg_email)

        # Verify password is not plaintext in DB and hashes properly
        user = User.objects.get(email=self.reg_email)
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))

        # Verification token must now be consumed
        consumed_otp = EmailVerificationOTP.objects.filter(email=self.reg_email, verification_token=token_str).first()
        self.assertIsNone(consumed_otp)

    def test_complete_registration_weak_password(self):
        token_str = "verif-token-weak-pass"
        EmailVerificationOTP.objects.create(
            email=self.reg_email,
            otp_hash=make_password("123456"),
            purpose="REGISTRATION",
            is_used=True,
            verification_token=token_str,
            verification_token_expires_at=timezone.now() + timedelta(minutes=15),
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        resp = self.client.post(
            "/api/auth/register/complete/",
            data=json.dumps({
                "email": self.reg_email,
                "verification_token": token_str,
                "password": "short",
                "confirm_password": "short"
            }),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("at least 8 characters", resp.json().get("error", "").lower())

    # ---------------- 4. Login, Current User & Logout ----------------

    def test_login_success_and_current_user_me(self):
        User.objects.create_user(username=self.reg_email, email=self.reg_email, password=self.password)

        resp = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"email": self.reg_email, "password": self.password}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        token = data.get("token")
        self.assertTrue(bool(token))

        # Check /api/auth/me/ with Bearer token
        me_resp = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json().get("user", {}).get("email"), self.reg_email)

    def test_login_invalid_password_returns_generic_error(self):
        User.objects.create_user(username=self.reg_email, email=self.reg_email, password=self.password)

        resp = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"email": self.reg_email, "password": "WrongPassword!"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json().get("error"), "Invalid email address or password.")

    def test_login_rate_limiting_lockout(self):
        User.objects.create_user(username=self.reg_email, email=self.reg_email, password=self.password)

        # Trigger 5 failed logins
        for _ in range(5):
            self.client.post(
                "/api/auth/login/",
                data=json.dumps({"email": self.reg_email, "password": "WrongPassword!"}),
                content_type="application/json"
            )

        # 6th attempt should be locked out with 429
        resp_locked = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"email": self.reg_email, "password": self.password}),
            content_type="application/json"
        )
        self.assertEqual(resp_locked.status_code, 429)
        self.assertIn("too many failed login attempts", resp_locked.json().get("error", "").lower())

    def test_logout_revokes_token(self):
        user = User.objects.create_user(username=self.reg_email, email=self.reg_email, password=self.password)
        resp = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"email": self.reg_email, "password": self.password}),
            content_type="application/json"
        )
        token = resp.json().get("token")

        # Logout
        logout_resp = self.client.post("/api/auth/logout/", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(logout_resp.status_code, 200)

        # Subsequent request with revoked token should fail (401)
        me_resp = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(me_resp.status_code, 401)

    # ---------------- 5. Forgot Password Flow ----------------

    def test_forgot_password_flow_complete(self):
        user = User.objects.create_user(username=self.reg_email, email=self.reg_email, password=self.password)
        old_user_count = User.objects.count()

        # Step 1: Request reset OTP
        resp_req = self.client.post(
            "/api/auth/password-reset/request-otp/",
            data=json.dumps({"email": self.reg_email}),
            content_type="application/json"
        )
        self.assertEqual(resp_req.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        # Extract code from DB
        otp_rec = EmailVerificationOTP.objects.get(email=self.reg_email, purpose="PASSWORD_RESET")
        raw_code = "889900"
        otp_rec.otp_hash = make_password(raw_code)
        otp_rec.save()

        # Step 2: Verify reset OTP
        resp_ver = self.client.post(
            "/api/auth/password-reset/verify-otp/",
            data=json.dumps({"email": self.reg_email, "otp": raw_code}),
            content_type="application/json"
        )
        self.assertEqual(resp_ver.status_code, 200)
        ver_token = resp_ver.json().get("verification_token")
        self.assertTrue(bool(ver_token))

        # Step 3: Confirm new password
        new_password = "BrandNewStrongPassword456!"
        resp_confirm = self.client.post(
            "/api/auth/password-reset/confirm/",
            data=json.dumps({
                "email": self.reg_email,
                "verification_token": ver_token,
                "password": new_password,
                "confirm_password": new_password
            }),
            content_type="application/json"
        )
        self.assertEqual(resp_confirm.status_code, 200)

        # Must NOT create a new user account
        self.assertEqual(User.objects.count(), old_user_count)

        # Step 4: Login with new password must succeed, old password must fail
        old_login = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"email": self.reg_email, "password": self.password}),
            content_type="application/json"
        )
        self.assertEqual(old_login.status_code, 401)

        new_login = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"email": self.reg_email, "password": new_password}),
            content_type="application/json"
        )
        self.assertEqual(new_login.status_code, 200)

    # ---------------- 6. Multi-Tenant Data Isolation (User A vs User B) ----------------

    def test_user_b_cannot_access_user_a_documents_or_results(self):
        user_a = User.objects.create_user(username="usera@studyai.test", email="usera@studyai.test", password=self.password)
        user_b = User.objects.create_user(username="userb@studyai.test", email="userb@studyai.test", password=self.password)

        doc_a = Document.objects.create(
            user=user_a,
            title="User A Private Research",
            filename="private_a.txt",
            file_type="txt",
            raw_text="Confidential findings owned by User A."
        )
        exam_a = Exam.objects.create(
            user=user_a,
            document=doc_a,
            title="User A Private Exam"
        )
        attempt_a = ExamAttempt.objects.create(
            user=user_a,
            exam=exam_a,
            score_percent=95,
            letter_grade="A",
            correct_count=10,
            incorrect_count=1
        )

        # Login as User B
        self.client.force_login(user_b)

        # User B attempts to access User A's document status
        resp_doc = self.client.get(f"/api/documents/{doc_a.id}/status/")
        self.assertEqual(resp_doc.status_code, 403)
        self.assertIn("forbidden", resp_doc.json().get("error", "").lower())

        # User B attempts to access User A's document analysis
        resp_analysis = self.client.get(f"/api/documents/{doc_a.id}/analysis/")
        self.assertEqual(resp_analysis.status_code, 403)

        # User B attempts to access User A's exam detail
        resp_exam = self.client.get(f"/api/exams/{exam_a.id}/")
        self.assertEqual(resp_exam.status_code, 403)

        # User B attempts to access User A's attempt result
        resp_res = self.client.get(f"/api/results/{attempt_a.id}/")
        self.assertEqual(resp_res.status_code, 403)

        # User B calls document listing: User A's document must NOT appear
        resp_list = self.client.get("/api/documents/")
        self.assertEqual(resp_list.status_code, 200)
        docs_data = resp_list.json()
        doc_ids = [d["id"] for d in (docs_data if isinstance(docs_data, list) else docs_data.get("documents", []))]
        self.assertNotIn(doc_a.id, doc_ids)

        # User B calls history listing: User A's attempt must NOT appear
        resp_hist = self.client.get("/api/history/")
        self.assertEqual(resp_hist.status_code, 200)
        res_ids = [h["id"] for h in resp_hist.json()]
        self.assertNotIn(f"res-{attempt_a.id}", res_ids)

        # User A logs in and CAN access their own records
        self.client.force_login(user_a)
        resp_a_doc = self.client.get(f"/api/documents/{doc_a.id}/status/")
        self.assertEqual(resp_a_doc.status_code, 200)
        resp_a_res = self.client.get(f"/api/results/{attempt_a.id}/")
        self.assertEqual(resp_a_res.status_code, 200)
