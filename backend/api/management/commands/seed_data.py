"""
=============================================================================
StudyAI — Safe System Seed Mechanism
=============================================================================
Usage:
    python manage.py seed_data [--sample-data]
=============================================================================
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from api.models import Document, Topic, Chunk


class Command(BaseCommand):
    help = "Safely initializes default system data without altering existing student records."

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample-data',
            action='store_true',
            help='Seeds a demo study document for verification in fresh environments.'
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("  StudyAI — Safe Seed Data Provisioning")
        self.stdout.write("=" * 70)

        with_sample = options.get('sample_data', False)

        if not with_sample:
            self.stdout.write(self.style.SUCCESS(
                "  [OK] System initialized. No fake student accounts or records created.\n"
                "  To seed a sample academic document for testing, run:\n"
                "    python manage.py seed_data --sample-data"
            ))
            self.stdout.write("=" * 70 + "\n")
            return

        # Create or retrieve sample document
        sample_title = "Computer Networks & Distributed Architecture (Sample)"
        existing_doc = Document.objects.filter(title=sample_title).first()
        if existing_doc:
            self.stdout.write(self.style.SUCCESS(f"  [OK] Sample document already exists (ID: {existing_doc.id})."))
        else:
            doc = Document.objects.create(
                title=sample_title,
                subject="Computer Networks",
                file_type="txt",
                raw_text=(
                    "The Open Systems Interconnection (OSI) model characterizes and standardizes the "
                    "communication functions of a telecommunication or computing system without regard "
                    "to its underlying internal structure and technology. Its goal is the interoperability "
                    "of diverse communication systems with standard communication protocols.\n\n"
                    "The model partitions a communication system into seven abstraction layers: Physical, "
                    "Data Link, Network, Transport, Session, Presentation, and Application layers."
                ),
                status="processed",
                page_count=1
            )
            Chunk.objects.create(
                document=doc,
                chunk_index=0,
                text=doc.raw_text,
                page_start=1,
                page_end=1,
                language="en"
            )
            Topic.objects.create(
                document=doc,
                name="OSI Reference Model",
                importance=9,
                relevance_score=0.95
            )
            Topic.objects.create(
                document=doc,
                name="Seven Abstraction Layers",
                importance=8,
                relevance_score=0.88
            )
            self.stdout.write(self.style.SUCCESS(f"  [OK] Created sample document '{sample_title}' (ID: {doc.id})."))

        self.stdout.write("=" * 70 + "\n")
