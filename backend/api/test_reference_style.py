import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase as DjangoTestCase

from .auth_views import create_auth_token
from .models import Document, ReferenceStyleProfile
from .notes_engine import generate_single_section_notes
from .reference_style_engine import analyze_reference_style


class ReferenceStyleAnalysisTests(TestCase):
    def test_profile_contains_style_metrics_not_reference_facts(self):
        private_fact = "Zorblax catalysts triple the reaction rate"
        profile = analyze_reference_style(
            "# Unit 1\n\n"
            f"{private_fact}. This is defined as a reference-only claim.\n\n"
            "- First point\n- Second point\n\n"
            "For example, the original reference demonstrates a method."
        )

        serialized = str(profile)
        self.assertNotIn(private_fact, serialized)
        self.assertEqual(profile["metrics"]["heading_count"], 1)
        self.assertEqual(profile["metrics"]["list_item_count"], 2)
        self.assertIn("do not reuse reference examples", " ".join(profile["guidance"]).lower())

    def test_notes_prompt_uses_style_guidance_without_reference_text(self):
        reference_fact = "Zorblax catalysts triple the reaction rate"
        profile = analyze_reference_style(
            f"# Reference\n\n{reference_fact}. For example, use the case described here."
        )
        section = SimpleNamespace(
            title="Catalyst basics",
            module="Chemistry",
            required_coverage="Explain the source-supported concept.",
        )
        generated = " ".join(["grounded"] * 160)

        with patch("api.notes_engine.check_ai_provider_status", return_value={
            "can_generate": True,
            "default_model": "test-model",
        }), patch("api.notes_engine.query_ai", return_value=(generated, True, None)) as query:
            generate_single_section_notes(
                section=section,
                source_chunks=[{
                    "text": "Study source: catalysts alter reaction pathways.",
                    "page_start": 1,
                    "page_end": 1,
                }],
                reference_style_profile=profile,
            )

        prompt = query.call_args.args[0]
        self.assertIn("Presentation guidance (style only; not a source of facts)", prompt)
        self.assertIn("Study source: catalysts alter reaction pathways.", prompt)
        self.assertNotIn(reference_fact, prompt)

    def test_empty_reference_text_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_reference_style("  \n ")


class ReferenceStyleAPITests(DjangoTestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="style-user", password="password123")
        token = create_auth_token(self.user)
        raw_token = getattr(token, "raw_token", token.token)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {raw_token}"}
        self.study_doc = Document.objects.create(
            user=self.user,
            title="Study material",
            raw_text="Study source content.",
            status="READY",
        )
        self.reference_doc = Document.objects.create(
            user=self.user,
            title="Reference material",
            raw_text="# Reference\n\nZorblax catalysts triple the reaction rate.",
            status="READY",
        )

    def test_reference_profile_api_stores_metrics_not_document_text(self):
        response = self.client.post(
            f"/api/v1/materials/{self.study_doc.id}/reference-styles",
            data=json.dumps({"reference_document_id": self.reference_doc.id}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 201)
        profile_data = json.loads(response.content)
        saved_profile = ReferenceStyleProfile.objects.get(id=profile_data["id"])
        self.assertNotIn("Zorblax", saved_profile.profile_json)

        listing = self.client.get(
            f"/api/v1/materials/{self.study_doc.id}/reference-styles",
            **self.auth_headers,
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(json.loads(listing.content)["profiles"]), 1)

    def test_notes_job_rejects_another_users_style_profile(self):
        other_user = User.objects.create_user(username="other-style-user", password="password123")
        other_doc = Document.objects.create(
            user=other_user,
            title="Private reference",
            raw_text="Private reference content.",
        )
        other_profile = ReferenceStyleProfile.objects.create(
            user=other_user,
            document=other_doc,
            label=other_doc.title,
            profile_json=json.dumps(analyze_reference_style(other_doc.raw_text)),
        )

        with patch("api.views.plan_syllabus_checklist") as planner:
            response = self.client.post(
                f"/api/v1/materials/{self.study_doc.id}/notes/start",
                data=json.dumps({"reference_style_profile_id": other_profile.id}),
                content_type="application/json",
                **self.auth_headers,
            )

        self.assertEqual(response.status_code, 404)
        planner.assert_not_called()
