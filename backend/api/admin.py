"""
=============================================================================
StudyAI — Django Admin Dashboard Registration
=============================================================================
Registers Document, Chunk, Topic, Exam, Question, and ExamAttempt models
with the Django Admin interface for easy visual database inspection.
=============================================================================
"""

from django.contrib import admin
from .models import Document, Chunk, Topic, Exam, Question, ExamAttempt, AIUsageEvent

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'word_count', 'total_chunks', 'created_at')
    search_fields = ('title', 'raw_text')
    list_filter = ('file_type', 'created_at')

@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'chunk_index', 'char_count', 'estimated_tokens')
    list_filter = ('document',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'document', 'importance', 'weight')
    list_filter = ('importance', 'document')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'total_questions', 'selected_topic', 'created_at')
    list_filter = ('difficulty', 'created_at')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_number', 'exam', 'question_type', 'topic', 'difficulty')
    list_filter = ('question_type', 'difficulty', 'topic')

@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam', 'score_percent', 'letter_grade', 'correct_count', 'incorrect_count', 'created_at')
    list_filter = ('letter_grade', 'created_at')

@admin.register(AIUsageEvent)
class AIUsageEventAdmin(admin.ModelAdmin):
    list_display = (
        'provider',
        'model',
        'success',
        'fallback_used',
        'prompt_tokens',
        'completion_tokens',
        'latency_ms',
        'estimated_cost_usd',
        'created_at',
    )
    list_filter = ('provider', 'success', 'fallback_used', 'created_at')
    search_fields = ('model', 'failure_code')
    readonly_fields = (
        'provider',
        'model',
        'prompt_tokens',
        'completion_tokens',
        'latency_ms',
        'success',
        'fallback_used',
        'failure_code',
        'estimated_cost_usd',
        'created_at',
    )
