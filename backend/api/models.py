"""
=============================================================================
StudyAI — Database Models (Django ORM)
=============================================================================
This file defines the relational database schema for StudyAI using Django's ORM.
Supports SQLite (local dev) and PostgreSQL (production).
=============================================================================
"""

import json
from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    """
    Represents an uploaded study material document or direct raw text entry.
    Fully agnostic to subject matter and language.
    """
    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('PROCESSING', 'Processing'),
        ('EXTRACTING', 'Extracting Text'),
        ('EXTRACTED', 'Extracted'),
        ('OCR_PROCESSING', 'OCR Processing'),
        ('CLEANING', 'Cleaning Content'),
        ('LANGUAGE_DETECTION', 'Detecting Language'),
        ('CHUNKING', 'Chunking Document'),
        ('CHUNKED', 'Chunked'),
        ('ANALYZING', 'Analyzing Content'),
        ('GENERATING_SUMMARY', 'Synthesizing Summary'),
        ('EXTRACTING_TOPICS', 'Extracting Syllabus Topics'),
        ('GENERATING_QUESTIONS', 'Preparing Question Bank'),
        ('READY', 'Ready'),
        ('COMPLETED', 'Completed'),
        ('PARTIAL', 'Completed with Partial Extractions'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('UPLOADED', 'Uploaded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents', null=True, blank=True, help_text="Authenticated owner of this document")
    title = models.CharField(max_length=255, help_text="Document or topic title")
    filename = models.CharField(max_length=255, blank=True, default='', help_text="Original uploaded filename")
    file_path = models.CharField(max_length=500, blank=True, default='', help_text="Relative path in storage")
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    file_type = models.CharField(
        max_length=20,
        choices=[
            ('pdf', 'PDF Document'),
            ('docx', 'Word Document'),
            ('txt', 'Text File'),
            ('raw', 'Direct Text Entry')
        ],
        default='raw',
        help_text="Format of the uploaded material"
    )
    page_count = models.IntegerField(default=1, help_text="Total detected pages")
    raw_text = models.TextField(blank=True, default='', help_text="Full extracted text content")
    word_count = models.IntegerField(default=0, help_text="Total number of words")
    total_chunks = models.IntegerField(default=0, help_text="Number of semantic chunks generated")
    original_language = models.CharField(max_length=50, default='en', help_text="Detected source language")
    output_language = models.CharField(max_length=50, default='en', help_text="Target output notes language")
    subject = models.CharField(max_length=255, default='General Education', help_text="Dynamically detected subject")
    is_scanned = models.BooleanField(default=False, help_text="Detected as image or scanned PDF")
    ocr_applied = models.BooleanField(default=False, help_text="OCR was applied to extract text")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='QUEUED', help_text="Pipeline processing stage")
    error_message = models.TextField(blank=True, default='', help_text="Processing error details if failed")
    summary_json = models.TextField(default='{}', help_text="Structured synthesis JSON (abstract, concepts, formulas)")
    subject_understanding_json = models.TextField(
        default='{}',
        help_text="Deep subject understanding representation: purpose, problems solved, applications, prerequisites, areas, knowledge map, coverage matrix"
    )

    # Comprehensive Document Processing Pipeline Tracking Fields
    processing_stage = models.CharField(max_length=64, default='QUEUED', help_text="Fine-grained processing stage")
    processing_progress = models.IntegerField(default=0, help_text="Real processing progress percentage (0-100)")
    processing_message = models.CharField(max_length=255, default='Document queued for processing', help_text="Human-readable progress status")
    processing_error_code = models.CharField(max_length=64, blank=True, default='', help_text="Standardized error code if processing failed")
    processing_error_message = models.TextField(blank=True, default='', help_text="Detailed error message or remedy guidance")
    processing_started_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when worker started processing")
    processing_updated_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last stage update")
    processing_heartbeat_at = models.DateTimeField(null=True, blank=True, help_text="Heartbeat timestamp for stale process detection")
    processing_attempts = models.IntegerField(default=0, help_text="Number of processing attempts")
    last_successful_stage = models.CharField(max_length=64, blank=True, default='', help_text="Last successfully completed stage for checkpoint resumption")
    checkpoint_data = models.TextField(default='{}', help_text="JSON payload containing intermediate checkpoint artifacts")
    extraction_report_json = models.TextField(default='{}', help_text="Page-level extraction and OCR fidelity metadata")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp of ingestion")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp of last update")

    def get_checkpoint_data(self) -> dict:
        try:
            return json.loads(self.checkpoint_data)
        except Exception:
            return {}

    def set_checkpoint_data(self, data: dict):
        self.checkpoint_data = json.dumps(data)

    def get_extraction_report(self) -> dict:
        try:
            report = json.loads(self.extraction_report_json)
        except (TypeError, ValueError):
            return {}
        return report if isinstance(report, dict) else {}

    def set_extraction_report(self, report: dict):
        self.extraction_report_json = json.dumps(report)

    def is_stale(self, timeout_seconds: int = None) -> bool:
        if self.status != 'PROCESSING':
            return False
        from django.conf import settings
        from django.utils import timezone
        effective_timeout = timeout_seconds if timeout_seconds is not None else getattr(settings, 'DOCUMENT_HEARTBEAT_TIMEOUT_SECONDS', 360)
        ref_time = self.processing_heartbeat_at or self.processing_updated_at or self.processing_started_at or self.updated_at
        if not ref_time:
            return False
        elapsed = (timezone.now() - ref_time).total_seconds()
        return elapsed > effective_timeout

    def update_progress(self, stage: str, progress: int, message: str, status: str = None, error_code: str = '', error_message: str = '', save: bool = True):
        from django.utils import timezone
        self.processing_stage = stage
        self.processing_progress = max(0, min(100, int(progress)))
        self.processing_message = message[:255]
        if status:
            self.status = status
        if error_code:
            self.processing_error_code = error_code
        if error_message:
            self.processing_error_message = error_message
            self.error_message = error_message
        now = timezone.now()
        self.processing_updated_at = now
        self.processing_heartbeat_at = now
        if not self.processing_started_at and self.status == 'PROCESSING':
            self.processing_started_at = now
        if save:
            update_fields = [
                'processing_stage', 'processing_progress', 'processing_message',
                'processing_updated_at', 'processing_heartbeat_at', 'updated_at'
            ]
            if status:
                update_fields.append('status')
            if error_code:
                update_fields.append('processing_error_code')
            if error_message:
                update_fields.extend(['processing_error_message', 'error_message'])
            if self.processing_started_at:
                update_fields.append('processing_started_at')
            self.save(update_fields=list(set(update_fields)))

    def get_summary(self):
        try:
            return json.loads(self.summary_json)
        except Exception:
            return {}

    def set_summary(self, data):
        self.summary_json = json.dumps(data)

    def get_subject_understanding(self) -> dict:
        try:
            return json.loads(self.subject_understanding_json)
        except Exception:
            return {}

    def set_subject_understanding(self, data: dict):
        self.subject_understanding_json = json.dumps(data)

    @property
    def summary(self):
        return self.get_summary()

    def __str__(self):
        return f"{self.title} ({self.subject} - {self.original_language}) [{self.status}]"


class Chunk(models.Model):
    """
    Represents an individual semantic chunk sliced from a Document.
    Maintains page boundaries and overlap for RAG grounding.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField(help_text="Sequential index of chunk (1-indexed)")
    page_start = models.IntegerField(default=1, help_text="Starting page in source document")
    page_end = models.IntegerField(default=1, help_text="Ending page in source document")
    section = models.CharField(max_length=255, blank=True, default='', help_text="Detected heading/section")
    text = models.TextField(help_text="Chunk text content")
    char_count = models.IntegerField(default=0, help_text="Character length")
    estimated_tokens = models.IntegerField(default=0, help_text="Estimated token count (~4 chars/token)")
    language = models.CharField(max_length=50, default='en')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['chunk_index']

    def __str__(self):
        return f"Doc {self.document_id} - Chunk {self.chunk_index} (p.{self.page_start}-{self.page_end})"


class ReferenceStyleProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reference_style_profiles')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='style_profiles')
    label = models.CharField(max_length=255)
    profile_json = models.TextField(default='{}')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'document'], name='unique_user_reference_style_profile')
        ]
        ordering = ['-updated_at']

    def get_profile(self) -> dict:
        try:
            profile = json.loads(self.profile_json)
        except (TypeError, ValueError):
            return {}
        return profile if isinstance(profile, dict) else {}

    def __str__(self):
        return f"{self.label} (style profile)"


class AIUsageEvent(models.Model):
    provider = models.CharField(max_length=32, db_index=True)
    model = models.CharField(max_length=255, blank=True, default='')
    prompt_tokens = models.PositiveIntegerField(null=True, blank=True)
    completion_tokens = models.PositiveIntegerField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField()
    success = models.BooleanField(default=False, db_index=True)
    fallback_used = models.BooleanField(default=False)
    failure_code = models.CharField(max_length=64, blank=True, default='')
    estimated_cost_usd = models.DecimalField(max_digits=16, decimal_places=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'created_at'], name='ai_usage_provider_created_idx')
        ]

    def __str__(self):
        state = "success" if self.success else "failed"
        return f"{self.provider}/{self.model or 'unknown'} {state}"


class Topic(models.Model):
    """
    Represents an academic syllabus topic, chapter, section, or concept in the document hierarchy.
    Maintains parent-child tree structure, deep contextual teaching content, coverage status,
    and verified mathematical/algorithmic metadata.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='topics')
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subtopics',
        help_text="Parent topic in the hierarchical syllabus tree"
    )
    name = models.CharField(max_length=255, help_text="Name of the topic or concept")
    node_type = models.CharField(
        max_length=50,
        choices=[
            ('knowledge_area', 'Knowledge Area'),
            ('chapter', 'Chapter / Module'),
            ('section', 'Section'),
            ('topic', 'Topic'),
            ('subtopic', 'Subtopic'),
            ('concept', 'Core Concept')
        ],
        default='topic',
        help_text="Granularity level in syllabus hierarchy"
    )
    hierarchy_path = models.CharField(max_length=100, default='1', help_text="Hierarchical numbering e.g. '1', '1.2', '1.2.3'")
    order_index = models.IntegerField(default=1, help_text="Display order within sibling nodes")
    description = models.TextField(blank=True, default='', help_text="Contextual summary from document")
    importance = models.CharField(
        max_length=50,
        choices=[('High', 'High Importance'), ('Medium', 'Medium Importance'), ('Foundational', 'Foundational')],
        default='Medium',
        help_text="Curriculum importance rating"
    )
    weight = models.IntegerField(default=80, help_text="Material Importance percentage (0-100)")
    source_reference = models.CharField(max_length=255, blank=True, default='', help_text="Source section reference")
    source_page = models.IntegerField(default=1, help_text="Source primary page number")
    page_start = models.IntegerField(default=1, help_text="Starting source page")
    page_end = models.IntegerField(default=1, help_text="Ending source page")
    coverage_status = models.CharField(
        max_length=50,
        choices=[
            ('DISCOVERED', 'Discovered in Source'),
            ('EXTRACTED', 'Extracted & Parsed'),
            ('TEACHING_READY', 'Teaching Material Ready'),
            ('VERIFIED', 'Pedagogically Verified')
        ],
        default='DISCOVERED',
        help_text="Document coverage and pedagogical teaching status"
    )
    teaching_content = models.TextField(blank=True, default='', help_text="Deep contextual teaching markdown (step-by-step working, architecture, formulas, calculations)")
    diagram_mermaid = models.TextField(blank=True, default='', help_text="Mermaid process/architecture diagram")
    metadata_json = models.TextField(default='{}', help_text="JSON payload: formulas, solved examples, misconceptions, prerequisites, applications")
    is_implicit = models.BooleanField(default=False, help_text="True if discovered from content rather than explicit heading")

    class Meta:
        ordering = ['order_index', 'id']

    def get_metadata(self) -> dict:
        try:
            return json.loads(self.metadata_json)
        except Exception:
            return {}

    def set_metadata(self, data: dict):
        self.metadata_json = json.dumps(data)

    def to_tree_dict(self, include_content: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "importance": self.importance,
            "weight": self.weight,
            "node_type": self.node_type,
            "hierarchy_path": self.hierarchy_path,
            "order_index": self.order_index,
            "source_page": self.source_page or self.page_start,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "coverage_status": self.coverage_status,
            "has_diagram": bool(self.diagram_mermaid),
            "is_implicit": self.is_implicit,
            "subtopics": [child.to_tree_dict(include_content=include_content) for child in self.subtopics.all().order_by('order_index', 'id')]
        }
        if include_content:
            data["teaching_content"] = self.teaching_content
            data["diagram_mermaid"] = self.diagram_mermaid
            data["metadata"] = self.get_metadata()
            data["archetype"] = (self.get_metadata() or {}).get("archetype")
        return data

    def __str__(self):
        return f"{self.hierarchy_path} {self.name} [{self.node_type}] ({self.coverage_status})"


class Exam(models.Model):
    """
    Represents an AI-generated exam created from a Document.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams', null=True, blank=True, help_text="Authenticated owner of this exam")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    title = models.CharField(max_length=255, default="StudyAI Practice Exam")
    difficulty = models.CharField(
        max_length=30,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard'), ('adaptive', 'Adaptive')],
        default='medium'
    )
    question_type = models.CharField(max_length=50, default='all', help_text="Format: all, mcq, tf, short, long, mixed")
    selected_topic = models.CharField(max_length=255, default='All', help_text="Topic focus filter")
    total_questions = models.IntegerField(default=10, help_text="Total questions in this exam")
    total_marks = models.PositiveIntegerField(default=0)
    time_limit_minutes = models.IntegerField(default=12, help_text="Time allowed in minutes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.difficulty}) - {self.total_questions} Qs"


class Question(models.Model):
    """
    Represents an individual grounded question inside an Exam or Question Bank.
    Guarantees citations, knowledge-unit grounding, independent validation status,
    and source chunk/page traceability.
    """
    STATUS_CHOICES = [
        ('GENERATED', 'Generated'),
        ('VALIDATING', 'Validating'),
        ('VERIFIED', 'Verified'),
        ('NEEDS_REPAIR', 'Needs Repair'),
        ('REJECTED', 'Rejected'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    question_number = models.IntegerField(default=1, help_text="Order in exam (1, 2, 3...)")
    question_type = models.CharField(
        max_length=30,
        choices=[
            ('mcq', 'Multiple Choice'),
            ('msq', 'Multiple Select'),
            ('tf', 'True / False'),
            ('fill_blank', 'Fill in the Blank'),
            ('short', 'Short Answer'),
            ('long', 'Long Answer'),
            ('numerical', 'Numerical / Problem Solving'),
        ],
        default='mcq'
    )
    question_text = models.TextField(help_text="The prompt or question asked")
    options_json = models.TextField(default='[]', help_text="JSON list of choices for MCQs/MSQs")
    correct_answer = models.TextField(help_text="Correct answer string or JSON array")
    correct_index = models.IntegerField(null=True, blank=True, help_text="Index of correct option (0-3)")
    correct_indices_json = models.TextField(default='[]', help_text="JSON list of correct option indexes for MSQs")
    marks = models.PositiveSmallIntegerField(default=1)
    explanation = models.TextField(help_text="In-depth pedagogical rationale grounded in text")
    citation = models.TextField(help_text="Direct quote from source chunk guaranteeing grounding")
    topic = models.CharField(max_length=255, help_text="Topic classification tag")
    difficulty = models.CharField(max_length=30, default='Medium')
    source_chunk = models.ForeignKey(Chunk, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    source_page = models.IntegerField(default=1, help_text="Page in original document")
    source_pages = models.CharField(max_length=50, default="1", help_text="Page range e.g. '24-25'")
    knowledge_unit_id = models.CharField(max_length=100, null=True, blank=True, help_text="ID of grounded Knowledge Unit")
    validation_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='GENERATED', help_text="Quality validation state")
    validation_score = models.FloatField(default=0.0, help_text="Composite quality score from 0.0 to 1.0")
    validation_errors = models.TextField(default='[]', help_text="JSON list of validation failure codes/reasons")
    generation_model = models.CharField(max_length=100, default='llama3:latest')
    validator_model = models.CharField(max_length=100, default='heuristic+llama3')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['question_number']

    def get_options(self):
        try:
            return json.loads(self.options_json)
        except Exception:
            return []

    def set_options(self, options_list):
        self.options_json = json.dumps(options_list)

    def get_correct_answer(self):
        if self.question_type != 'msq':
            return self.correct_answer
        try:
            answer = json.loads(self.correct_answer)
        except (TypeError, ValueError):
            return []
        return answer if isinstance(answer, list) else []

    def set_correct_answer(self, answer):
        self.correct_answer = json.dumps(answer) if isinstance(answer, list) else str(answer)

    def get_correct_indices(self):
        try:
            indices = json.loads(self.correct_indices_json)
        except (TypeError, ValueError):
            return []
        return indices if isinstance(indices, list) else []

    def set_correct_indices(self, indices):
        self.correct_indices_json = json.dumps(indices if isinstance(indices, list) else [])

    def get_validation_errors(self):
        try:
            return json.loads(self.validation_errors)
        except Exception:
            return []

    def set_validation_errors(self, err_list):
        self.validation_errors = json.dumps(err_list)

    def __str__(self):
        return f"Q{self.question_number} [{self.validation_status}]: {self.question_text[:50]}... [{self.topic}]"



class ExamAttempt(models.Model):
    """
    Represents a student's completion of an Exam.
    Stores user answers, total score, topic accuracy, and detected weak topics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts', null=True, blank=True, help_text="Authenticated student who completed this attempt")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    user_answers_json = models.TextField(default='{}', help_text="Student submitted answers in JSON")
    score_percent = models.IntegerField(default=0, help_text="Overall percentage score (0-100)")
    marks_scored = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    letter_grade = models.CharField(max_length=50, default='B (Competent)')
    correct_count = models.IntegerField(default=0)
    incorrect_count = models.IntegerField(default=0)
    time_spent = models.CharField(max_length=50, default='8m 30s', help_text="Formatted time spent")
    feedback_text = models.TextField(blank=True, default='', help_text="Dynamically generated cognitive diagnostic")
    topic_stats_json = models.TextField(default='[]', help_text="JSON breakdown of score per topic")
    weak_topics_json = models.TextField(default='[]', help_text="JSON array of topics scored < 60%")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Time of completion")

    def __str__(self):
        return f"Attempt #{self.id} on Exam {self.exam_id}: {self.score_percent}%"


class RevisionTask(models.Model):
    """
    Represents a personalized revision action item derived from the Priority Matrix:
    - High Material Importance + Low Performance = Critical
    - High Material Importance + High Performance = Maintain
    - Low Material Importance + Low Performance = Practice if time permits
    - Low Material Importance + High Performance = Low priority
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='revision_tasks', null=True, blank=True, help_text="Authenticated owner of this revision task")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='revision_tasks', null=True, blank=True)
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='revision_tasks', null=True, blank=True)
    topic = models.CharField(max_length=255)
    priority = models.CharField(max_length=50, default='Critical')
    importance_score = models.IntegerField(default=80)
    performance_score = models.IntegerField(default=40)
    reason = models.TextField(default='')
    recommended_action = models.TextField(default='')
    estimated_minutes = models.IntegerField(default=15)
    completed = models.BooleanField(default=False)
    question = models.TextField(default='', blank=True, help_text="Grounded revision question or prompt")
    answer = models.TextField(default='', blank=True, help_text="Grounded answer to revision question")
    explanation = models.TextField(default='', blank=True, help_text="Explanatory derivation or conceptual context")
    difficulty = models.CharField(max_length=30, default='medium', blank=True)
    source_info = models.TextField(default='', blank=True, help_text="Source citation e.g. Page X, Section Y")
    notes_json = models.TextField(default='[]', blank=True, help_text="JSON list of high-yield bullet points")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_notes(self):
        try:
            return json.loads(self.notes_json) if self.notes_json else []
        except (ValueError, TypeError):
            return []

    def __str__(self):
        return f"[{self.priority}] {self.topic} (Importance: {self.importance_score}%, Mastery: {self.performance_score}%)"


class AdaptivePracticeLoop(models.Model):
    """
    Represents an Adaptive Learning Loop iteration:
    Weak Topic -> Targeted Practice -> Mini-Test -> New Score -> Performance Comparison -> Priority Recalculation.
    Stores previous performance, new performance, practice attempt, topic, improvement, and timestamp.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='adaptive_loops', null=True, blank=True, help_text="Authenticated owner of this adaptive loop")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='adaptive_loops', null=True, blank=True)
    topic = models.CharField(max_length=255)
    previous_performance = models.IntegerField(default=0, help_text="Initial weak performance percentage (0-100)")
    new_performance = models.IntegerField(default=0, help_text="Post-practice performance percentage (0-100)")
    improvement = models.IntegerField(default=0, help_text="Performance delta (+/- %)")
    importance_score = models.IntegerField(default=80, help_text="Topic syllabus weight (0-100)")
    previous_priority = models.CharField(max_length=50, default='CRITICAL')
    new_priority = models.CharField(max_length=50, default='PRACTICE')
    practice_exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True, blank=True, related_name='adaptive_loops')
    practice_attempt = models.ForeignKey(ExamAttempt, on_delete=models.SET_NULL, null=True, blank=True, related_name='adaptive_loops')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.topic}: {self.previous_performance}% → {self.new_performance}% ({self.improvement:+d}%)"


class EvaluationRun(models.Model):
    """
    Represents an empirical AI Quality Evaluation benchmark run across 20 documents.
    Stores measured quality metrics, evaluated dimensions, and summary counts.
    """
    run_id = models.CharField(max_length=64, unique=True, help_text="Unique benchmark run identifier")
    model_name = models.CharField(max_length=128, default="extractive-nlp-grounded", help_text="AI model evaluated")
    status = models.CharField(max_length=32, default="COMPLETED")
    duration_seconds = models.FloatField(default=0.0)
    total_documents = models.IntegerField(default=20)
    total_questions = models.IntegerField(default=100)

    # 5 Explicitly Required Report Metrics
    grounding_accuracy = models.FloatField(default=0.0, help_text="Measured Grounding Accuracy %")
    citation_accuracy = models.FloatField(default=0.0, help_text="Measured Citation Accuracy %")
    question_relevance = models.FloatField(default=0.0, help_text="Measured Question Relevance %")
    answer_accuracy = models.FloatField(default=0.0, help_text="Measured Answer Accuracy %")
    unsupported_question_rate = models.FloatField(default=0.0, help_text="Measured Unsupported Question Rate %")

    # Supplementary Evaluated Dimensions
    summary_relevance = models.FloatField(default=0.0)
    topic_relevance = models.FloatField(default=0.0)
    difficulty_correctness = models.FloatField(default=0.0)
    copilot_grounding = models.FloatField(default=0.0)
    unsupported_info_rate = models.FloatField(default=0.0)

    report_json = models.TextField(default='{}', help_text="Complete JSON report artifact")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"EvaluationRun {self.run_id} ({self.grounding_accuracy}% Grounding, {self.citation_accuracy}% Citation)"


class EvaluationQuestionResult(models.Model):
    """
    Represents the complete verification audit of an individual test question.
    Guarantees 100% traceability to actual empirical tests.
    """
    run = models.ForeignKey(EvaluationRun, on_delete=models.CASCADE, related_name='question_results')
    question_index = models.IntegerField(help_text="1 to 100")
    doc_id = models.CharField(max_length=128)
    doc_title = models.CharField(max_length=255)
    subject = models.CharField(max_length=128)
    question_text = models.TextField()
    options_json = models.TextField(default='[]')
    correct_answer = models.TextField()
    correct_index = models.IntegerField(default=0)
    citation = models.TextField()
    topic = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=64, default="Medium")
    source_page = models.IntegerField(default=1)
    source_chunk = models.IntegerField(default=1)

    # Empirical verification outcomes
    is_grounded = models.BooleanField(default=True)
    grounding_score = models.FloatField(default=1.0)
    grounding_trace = models.TextField(default='')

    is_citation_correct = models.BooleanField(default=True)
    citation_score = models.FloatField(default=1.0)
    citation_match_type = models.CharField(max_length=64, default='exact_verbatim')
    citation_trace = models.TextField(default='')

    is_answer_correct = models.BooleanField(default=True)
    answer_trace = models.TextField(default='')

    is_topic_correct = models.BooleanField(default=True)
    topic_trace = models.TextField(default='')

    is_difficulty_reasonable = models.BooleanField(default=True)
    difficulty_trace = models.TextField(default='')

    is_unsupported = models.BooleanField(default=False)

    class Meta:
        ordering = ['question_index']

    def __str__(self):
        return f"Run {self.run.run_id} - Q{self.question_index}: {'PASS' if not self.is_unsupported else 'FLAG'}"


class EmailVerificationOTP(models.Model):
    """
    Stores 6-digit email OTPs for registration and password resets.
    Enforces server-side expiry, single-use, max attempts, and rate limiting.
    """
    PURPOSE_CHOICES = [
        ('REGISTRATION', 'Registration'),
        ('PASSWORD_RESET', 'Password Reset'),
    ]

    email = models.EmailField(db_index=True, help_text="Target recipient email address")
    otp_hash = models.CharField(max_length=255, help_text="Cryptographically hashed 6-digit OTP code")
    purpose = models.CharField(max_length=32, choices=PURPOSE_CHOICES, default='REGISTRATION')
    attempts = models.IntegerField(default=0, help_text="Failed verification attempts counter")
    max_attempts = models.IntegerField(default=5, help_text="Threshold before OTP is invalidated")
    is_used = models.BooleanField(default=False, help_text="True once successfully verified")
    verification_token = models.CharField(max_length=128, blank=True, default='', db_index=True, help_text="Single-use proof token for completing registration/reset")
    verification_token_expires_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True, help_text="Hard server-side expiry timestamp")
    ip_address = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.email} [{self.purpose}] (Used: {self.is_used})"


class AuthToken(models.Model):
    """
    Persistent bearer authentication token associated with a verified User.
    Supports secure API calls across web and mobile clients without cross-origin cookie issues.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_tokens')
    token = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    ip_address = models.CharField(max_length=64, blank=True, default='')
    user_agent = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Token for {self.user.email} (Expires: {self.expires_at})"


class RateLimitRecord(models.Model):
    """
    Tracks security audit events and rate-limiting counters (OTP requests, verification attempts, failed logins).
    """
    action = models.CharField(max_length=64, db_index=True)  # 'otp_request', 'otp_verify', 'login'
    identifier = models.CharField(max_length=255, db_index=True)  # email, IP address, or token
    ip_address = models.CharField(max_length=64, blank=True, default='')
    success = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.identifier} @ {self.timestamp}"


class NotesGenerationJob(models.Model):
    """
    Represents an asynchronous, resumable, section-by-section study notes generation job.
    Tracks overall progress, verification status, retry counters, and export paths.
    """
    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('PLANNING', 'Planning Syllabus Checklist'),
        ('GENERATING', 'Generating Sections'),
        ('VERIFYING', 'Verifying Completeness & Mathematics'),
        ('REPAIRING', 'Repairing Missing Content'),
        ('COMPLETED', 'Completed'),
        ('COMPLETED_WITH_WARNINGS', 'Completed with Warnings'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled')
    ]

    job_id = models.CharField(max_length=64, unique=True, db_index=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='notes_jobs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes_jobs', null=True, blank=True)
    mode = models.CharField(max_length=50, default='standard')
    depth = models.CharField(max_length=50, default='intermediate')
    language = models.CharField(max_length=50, default='en')
    syllabus_source = models.CharField(max_length=64, default='document_derived')
    reference_style_profile_json = models.TextField(default='{}')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='QUEUED')
    total_topics = models.IntegerField(default=0)
    completed_topics = models.IntegerField(default=0)
    verified_topics = models.IntegerField(default=0)
    failed_topics = models.IntegerField(default=0)
    progress_percent = models.IntegerField(default=0)
    current_step_label = models.CharField(max_length=255, default='Initializing generation job...')
    coverage_manifest_json = models.TextField(default='{}')
    final_document_markdown = models.TextField(blank=True, default='')
    docx_export_path = models.CharField(max_length=500, blank=True, default='')
    pdf_export_path = models.CharField(max_length=500, blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def get_manifest(self):
        try:
            return json.loads(self.coverage_manifest_json)
        except Exception:
            return {}

    def set_manifest(self, manifest_dict):
        self.coverage_manifest_json = json.dumps(manifest_dict)

    def get_reference_style_profile(self) -> dict:
        try:
            profile = json.loads(self.reference_style_profile_json)
        except (TypeError, ValueError):
            return {}
        return profile if isinstance(profile, dict) else {}

    def __str__(self):
        return f"Job {self.job_id} on Doc {self.document_id} [{self.status}] ({self.progress_percent}%)"


class SyllabusSection(models.Model):
    """
    Represents an individual syllabus section/topic within a NotesGenerationJob.
    Maintains independent generation, verification, and targeted repair status.
    """
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('GENERATED', 'Generated'),
        ('VERIFICATION_REQUIRED', 'Verification Required'),
        ('NEEDS_REPAIR', 'Needs Repair'),
        ('VERIFIED', 'Verified'),
        ('BLOCKED', 'Blocked')
    ]

    job = models.ForeignKey(NotesGenerationJob, on_delete=models.CASCADE, related_name='sections')
    topic_id = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255)
    parent_topic = models.CharField(max_length=255, blank=True, default='')
    module = models.CharField(max_length=255, default='Core Module')
    order_index = models.IntegerField(default=1)
    required_coverage = models.TextField(blank=True, default='')
    source_chunks_json = models.TextField(default='[]')
    source_pages_json = models.TextField(default='[]')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='NOT_STARTED')
    generated_notes = models.TextField(blank=True, default='')
    verification_score = models.FloatField(default=0.0)
    verification_report_json = models.TextField(default='{}')
    missing_content = models.TextField(blank=True, default='')
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_index']

    def get_source_chunks(self):
        try:
            return json.loads(self.source_chunks_json)
        except Exception:
            return []

    def set_source_chunks(self, chunks_list):
        self.source_chunks_json = json.dumps(chunks_list)

    def get_verification_report(self):
        try:
            return json.loads(self.verification_report_json)
        except Exception:
            return {}

    def set_verification_report(self, report_dict):
        self.verification_report_json = json.dumps(report_dict)

    def __str__(self):
        return f"{self.topic_id}: {self.title} [{self.status}]"


