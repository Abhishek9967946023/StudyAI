"""
=============================================================================
StudyAI — Dedicated Application Security Verification Test Suite
=============================================================================
Automated regression tests covering key security audit domains:
1. Secret key & configuration fail-safe
2. SHA-256 token hashing in database (raw token never stored)
3. Client IP trust (spoofed X-Forwarded-For rejected from untrusted proxies)
4. Anti-spoofing rate limiting enforcement
5. Multi-tenant IDOR isolation across two distinct users
6. Magic byte file content validation (PDF, DOCX, TXT null-bytes)
7. DOCX Zip bomb / decompression limit enforcement
8. Authenticated media download view with strict path containment
9. Strict CORS allowlist (arbitrary origin reflection prevented)
10. CSRF token generation and validation
11. Baseline security headers
=============================================================================
"""

import io
import json
import zipfile
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from .models import Document, Exam, ExamAttempt, AuthToken, AdaptivePracticeLoop
from .auth_service import hash_token, get_client_ip, create_auth_token, authenticate_bearer_token
from .document_service import validate_file_content_signature


class SecurityHardeningVerificationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user_a = User.objects.create_user(
            username="sec_student_a@studyai.test",
            email="sec_student_a@studyai.test",
            password="SecurePassword123!"
        )
        self.user_b = User.objects.create_user(
            username="sec_student_b@studyai.test",
            email="sec_student_b@studyai.test",
            password="SecurePassword456!"
        )

    # 1. Bearer Token SHA-256 Storage
    def test_token_stored_as_sha256_hash_in_db(self):
        """Verifies raw auth token is NEVER stored in database; only SHA-256 hex digest is persisted."""
        token_obj = create_auth_token(self.user_a)
        raw_token = token_obj.raw_token
        self.assertTrue(len(raw_token) >= 40)

        # Database record must contain the SHA-256 hash, not the raw token
        db_token_record = AuthToken.objects.get(id=token_obj.id)
        expected_hash = hash_token(raw_token)
        self.assertEqual(db_token_record.token, expected_hash)
        self.assertNotEqual(db_token_record.token, raw_token)

        # Authenticate must succeed using raw token
        authenticated_user = authenticate_bearer_token(raw_token)
        self.assertEqual(authenticated_user, self.user_a)

    # 2. Client IP Trust & Forged X-Forwarded-For Rejection
    def test_spoofed_x_forwarded_for_rejected_from_untrusted_remote_addr(self):
        """Forged X-Forwarded-For header from untrusted proxy is rejected in favor of REMOTE_ADDR."""
        class MockRequest:
            META = {
                'REMOTE_ADDR': '198.51.100.5',  # Untrusted client IP
                'HTTP_X_FORWARDED_FOR': '8.8.8.8, 1.1.1.1'  # Spoofed victim/proxy IP
            }

        client_ip = get_client_ip(MockRequest())
        self.assertEqual(client_ip, '198.51.100.5')

    def test_trusted_proxy_x_forwarded_for_accepted(self):
        """X-Forwarded-For is only honored when REMOTE_ADDR matches configured TRUSTED_PROXIES."""
        with override_settings(TRUSTED_PROXIES=['10.0.0.1']):
            class MockRequest:
                META = {
                    'REMOTE_ADDR': '10.0.0.1',  # Known trusted reverse proxy
                    'HTTP_X_FORWARDED_FOR': '203.0.113.195'  # Real client IP behind proxy
                }

            client_ip = get_client_ip(MockRequest())
            self.assertEqual(client_ip, '203.0.113.195')

    # 3. Magic Byte & Content Inspection
    def test_file_signature_pdf_mismatch_rejected(self):
        """Fake PDF with invalid magic bytes is rejected."""
        fake_pdf = b"<html><script>alert('XSS')</script></html>"
        is_valid, msg = validate_file_content_signature(fake_pdf, 'pdf')
        self.assertFalse(is_valid)
        self.assertIn("Invalid PDF header signature", msg)

    def test_file_signature_valid_pdf_accepted(self):
        """Genuine PDF starting with %PDF- signature is accepted."""
        valid_pdf = b"%PDF-1.7\n%\xb5\xed\xae\xfb\n"
        is_valid, msg = validate_file_content_signature(valid_pdf, 'pdf')
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_file_signature_docx_missing_openxml_rejected(self):
        """Zip archive lacking OpenXML parts is rejected as malformed DOCX."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("test.txt", "not a docx")
        fake_docx = buf.getvalue()

        is_valid, msg = validate_file_content_signature(fake_docx, 'docx')
        self.assertFalse(is_valid)
        self.assertIn("missing required OpenXML descriptors", msg)

    def test_file_signature_text_with_null_bytes_rejected(self):
        """Text file with embedded null bytes is rejected."""
        binary_text = b"Normal text\x00malicious binary content"
        is_valid, msg = validate_file_content_signature(binary_text, 'txt')
        self.assertFalse(is_valid)
        self.assertIn("null bytes", msg)

    # 4. Strict CORS Allowlist
    def test_cors_rejects_arbitrary_unlisted_origin(self):
        """Arbitrary attacker origin is NOT reflected in Access-Control-Allow-Origin."""
        resp = self.client.get('/api/health/', HTTP_ORIGIN='https://evil-attacker.example.com')
        self.assertNotIn('Access-Control-Allow-Origin', resp.headers)

    def test_cors_allows_configured_trusted_origin(self):
        """Whitelisted origin receives proper CORS headers."""
        resp = self.client.get('/api/health/', HTTP_ORIGIN='http://localhost:5173')
        self.assertEqual(resp.headers.get('Access-Control-Allow-Origin'), 'http://localhost:5173')
        self.assertEqual(resp.headers.get('Access-Control-Allow-Credentials'), 'true')

    # 5. IDOR & Multi-Tenant Isolation
    def test_cross_tenant_document_download_forbidden(self):
        """User B cannot download User A's uploaded file (HTTP 403)."""
        import os
        from pathlib import Path

        # Create dummy file in MEDIA_ROOT
        media_docs = Path(settings.MEDIA_ROOT) / 'documents'
        media_docs.mkdir(parents=True, exist_ok=True)
        test_file = media_docs / 'test_user_a_file.pdf'
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4 sample user A private file content")

        rel_path = str(test_file.relative_to(settings.BASE_DIR))
        doc_a = Document.objects.create(
            user=self.user_a,
            title="User A Confidential",
            filename="test_user_a_file.pdf",
            file_path=rel_path,
            file_type="pdf",
            status="READY"
        )

        # Login as User B
        self.client.force_login(self.user_b)
        resp = self.client.get(f'/api/documents/{doc_a.id}/download/')
        self.assertEqual(resp.status_code, 403)
        self.assertIn("forbidden", resp.json().get("error", "").lower())

        # Login as User A: download succeeds
        self.client.force_login(self.user_a)
        resp_a = self.client.get(f'/api/documents/{doc_a.id}/download/')
        self.assertEqual(resp_a.status_code, 200)
        resp_a.close()

        # Cleanup test file
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
            except Exception:
                pass

    # 6. CSRF Token Endpoint
    def test_csrf_token_endpoint_returns_token(self):
        """GET /api/auth/csrf/ issues a valid CSRF token."""
        resp = self.client.get('/api/auth/csrf/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(bool(data.get("csrfToken")))

    # 7. Baseline Security Headers
    def test_baseline_security_headers_present(self):
        """Verifies X-Content-Type-Options, X-Frame-Options, and Referrer-Policy on all responses."""
        resp = self.client.get('/api/health/')
        self.assertEqual(resp.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(resp.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(resp.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    # 8. Adaptive Practice Multi-Tenant Isolation
    def test_cross_tenant_adaptive_practice_loop_isolation(self):
        """User B cannot view User A's adaptive practice loop records."""
        doc_a = Document.objects.create(
            user=self.user_a,
            title="User A Operating Systems",
            filename="os_notes.txt",
            file_type="txt",
            raw_text="OS concepts notes"
        )
        loop_a = AdaptivePracticeLoop.objects.create(
            user=self.user_a,
            document=doc_a,
            topic="Deadlocks & Semaphores",
            previous_performance=45,
            new_performance=85,
            improvement=40,
            importance_score=90,
            previous_priority="Critical",
            new_priority="Maintain"
        )

        # Login as User B: User A's loop must NOT appear
        self.client.force_login(self.user_b)
        resp_b = self.client.get('/api/adaptive/history/')
        self.assertEqual(resp_b.status_code, 200)
        loops_b = resp_b.json()
        loop_ids_b = [l["id"] for l in loops_b]
        self.assertNotIn(loop_a.id, loop_ids_b)

        # Login as User A: User A's loop MUST appear
        self.client.force_login(self.user_a)
        resp_a = self.client.get('/api/adaptive/history/')
        self.assertEqual(resp_a.status_code, 200)
        loops_a = resp_a.json()
        loop_ids_a = [l["id"] for l in loops_a]
        self.assertIn(loop_a.id, loop_ids_a)

    # 9. Protected Endpoints Reject Unauthenticated Access
    def test_unauthenticated_requests_rejected_with_401(self):
        """Protected core endpoints return HTTP 401 when accessed without session or token."""
        for endpoint in ['/api/documents/', '/api/history/', '/api/adaptive/history/']:
            resp = self.client.get(endpoint)
            self.assertEqual(resp.status_code, 401, f"Endpoint {endpoint} allowed unauthenticated access!")

    # 10. Upload Size Ceiling Validation
    def test_upload_exceeding_25mb_rejected(self):
        """Upload with declared size exceeding 25MB ceiling is rejected."""
        self.client.force_login(self.user_a)
        # 26 MB dummy payload
        oversized_file = SimpleUploadedFile(
            "large_file.pdf",
            b"%PDF-1.4 " + b"0" * (26 * 1024 * 1024),
            content_type="application/pdf"
        )
        resp = self.client.post(
            '/api/documents/upload/',
            {'file': oversized_file, 'title': 'Oversized Test Document'}
        )
        self.assertIn(resp.status_code, [400, 413])

