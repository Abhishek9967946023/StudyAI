import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Document, Chunk, Topic, Exam
from .auth_views import create_auth_token

class DeleteMaterialAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        token_obj = create_auth_token(self.user)
        raw_token = getattr(token_obj, 'raw_token', token_obj.token)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {raw_token}"}
        self.client.force_login(self.user)

        # Create test documents
        self.doc1 = Document.objects.create(
            user=self.user,
            title="Calculus Fundamentals",
            subject="Mathematics",
            raw_text="Derivatives and integrals...",
            status="READY"
        )
        self.chunk1 = Chunk.objects.create(
            document=self.doc1,
            chunk_index=0,
            text="Derivative of x^2 is 2x"
        )
        self.topic1 = Topic.objects.create(
            document=self.doc1,
            name="Differentiation",
            description="Rules of differentiation"
        )

        self.doc2 = Document.objects.create(
            user=self.user,
            title="Quantum Mechanics Primer",
            subject="Physics",
            raw_text="Wave-particle duality...",
            status="READY"
        )

    def test_delete_single_material(self):
        # Delete doc1 via /api/v1/materials/<id>
        resp = self.client.delete(f"/api/v1/materials/{self.doc1.id}", **self.auth_headers)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data.get("success"))

        # Verify document and related chunks/topics are deleted
        self.assertFalse(Document.objects.filter(id=self.doc1.id).exists())
        self.assertFalse(Chunk.objects.filter(id=self.chunk1.id).exists())
        self.assertFalse(Topic.objects.filter(id=self.topic1.id).exists())

    def test_delete_via_canonical_path(self):
        # Delete via /api/documents/<id>/
        resp = self.client.delete(f"/api/documents/{self.doc2.id}/", **self.auth_headers)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Document.objects.filter(id=self.doc2.id).exists())

    def test_bulk_delete_materials(self):
        # Create doc3
        doc3 = Document.objects.create(
            user=self.user,
            title="World History 101",
            subject="History",
            raw_text="The industrial revolution...",
            status="READY"
        )
        ids = [self.doc1.id, doc3.id]
        resp = self.client.delete(
            "/api/v1/materials",
            data=json.dumps({"ids": ids}),
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("deleted_count"), 2)

        self.assertFalse(Document.objects.filter(id=self.doc1.id).exists())
        self.assertFalse(Document.objects.filter(id=doc3.id).exists())
        self.assertTrue(Document.objects.filter(id=self.doc2.id).exists())

    def test_delete_unauthorized_forbidden(self):
        other_user = User.objects.create_user(username="otheruser", email="other@example.com", password="password123")
        other_token_obj = create_auth_token(other_user)
        other_raw = getattr(other_token_obj, 'raw_token', other_token_obj.token)
        other_client = Client()
        other_client.force_login(other_user)
        other_headers = {"HTTP_AUTHORIZATION": f"Bearer {other_raw}"}

        # other user attempts to delete testuser's doc1
        resp = other_client.delete(f"/api/v1/materials/{self.doc1.id}", **other_headers)
        self.assertIn(resp.status_code, [403, 404])
        self.assertTrue(Document.objects.filter(id=self.doc1.id).exists())
