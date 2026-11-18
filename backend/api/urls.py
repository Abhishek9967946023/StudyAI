"""
=============================================================================
StudyAI — API URL Routing
=============================================================================
Maps all endpoints for both clean REST conventions and v1 frontend adapters.
=============================================================================
"""

from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    # 0. Authentication & Security (Email OTP & Sessions)
    path('auth/register/request-otp/', auth_views.request_registration_otp_view, name='api_auth_register_request_otp'),
    path('auth/register/verify-otp/', auth_views.verify_registration_otp_view, name='api_auth_register_verify_otp'),
    path('auth/register/complete/', auth_views.complete_registration_view, name='api_auth_register_complete'),
    path('auth/login/', auth_views.login_view, name='api_auth_login'),
    path('auth/logout/', auth_views.logout_view, name='api_auth_logout'),
    path('auth/me/', auth_views.current_user_view, name='api_auth_me'),
    path('auth/password-reset/request-otp/', auth_views.request_password_reset_otp_view, name='api_auth_reset_request_otp'),
    path('auth/password-reset/verify-otp/', auth_views.verify_password_reset_otp_view, name='api_auth_reset_verify_otp'),
    path('auth/password-reset/confirm/', auth_views.confirm_password_reset_view, name='api_auth_reset_confirm'),
    path('auth/csrf/', auth_views.csrf_token_view, name='api_auth_csrf'),

    # v1 frontend aliases
    path('v1/auth/csrf', auth_views.csrf_token_view, name='api_v1_auth_csrf'),
    path('v1/auth/register/request-otp', auth_views.request_registration_otp_view, name='api_v1_auth_register_request_otp'),
    path('v1/auth/register/verify-otp', auth_views.verify_registration_otp_view, name='api_v1_auth_register_verify_otp'),
    path('v1/auth/register/complete', auth_views.complete_registration_view, name='api_v1_auth_register_complete'),
    path('v1/auth/login', auth_views.login_view, name='api_v1_auth_login'),
    path('v1/auth/logout', auth_views.logout_view, name='api_v1_auth_logout'),
    path('v1/auth/me', auth_views.current_user_view, name='api_v1_auth_me'),
    path('v1/auth/password-reset/request-otp', auth_views.request_password_reset_otp_view, name='api_v1_auth_reset_request_otp'),
    path('v1/auth/password-reset/verify-otp', auth_views.verify_password_reset_otp_view, name='api_v1_auth_reset_verify_otp'),
    path('v1/auth/password-reset/confirm', auth_views.confirm_password_reset_view, name='api_v1_auth_reset_confirm'),

    # 1. System Health, Ollama & OCR Diagnostics
    path('health/', views.health_check, name='api_health'),
    path('ocr/status/', views.ocr_status_view, name='api_ocr_status'),
    path('v1/ocr/status', views.ocr_status_view, name='api_v1_ocr_status'),
    path('ollama/status/', views.ollama_status_view, name='api_ollama_status'),
    path('ollama/models/', views.ollama_models_view, name='api_ollama_models'),

    # 2. Documents & Materials (Canonical REST)
    path('documents/upload/', views.upload_document_view, name='api_upload_document'),
    path('documents/', views.get_documents_list_view, name='api_documents_list'),
    path('documents/<str:doc_id>/', views.document_detail_view, name='api_document_detail'),
    path('documents/<str:doc_id>/delete/', views.delete_document_view, name='api_document_delete'),
    path('documents/<str:doc_id>/reprocess_ocr/', views.reprocess_document_ocr_view, name='api_document_reprocess_ocr'),
    path('documents/<str:doc_id>/status/', views.get_document_status_view, name='api_document_status'),
    path('documents/<str:doc_id>/retry/', views.retry_document_processing_view, name='api_document_retry'),
    path('documents/<str:doc_id>/cancel/', views.cancel_document_processing_view, name='api_document_cancel'),
    path('documents/<str:doc_id>/analyze/', views.analyze_document_detail_view, name='api_document_analyze'),
    path('documents/<str:doc_id>/analysis/', views.get_document_analysis_view, name='api_document_analysis'),
    path('documents/<str:doc_id>/summary/', views.get_document_summary_view, name='api_document_summary'),
    path('documents/<str:doc_id>/summary/status/', views.get_document_summary_status_view, name='api_document_summary_status'),
    path('documents/<str:doc_id>/summary/sections/', views.get_document_summary_sections_view, name='api_document_summary_sections'),
    path('documents/<str:doc_id>/summary/visuals/', views.get_document_summary_visuals_view, name='api_document_summary_visuals'),
    path('documents/<str:doc_id>/summary/regenerate/', views.regenerate_document_summary_view, name='api_document_summary_regenerate'),
    path('documents/<str:doc_id>/chat/', views.chat_document_view, name='api_document_chat'),
    path('documents/<str:doc_id>/topics/', views.get_document_topics_view, name='api_document_topics'),
    path('documents/<str:doc_id>/subject-overview/', views.get_document_subject_overview_view, name='api_document_subject_overview'),
    path('documents/<str:doc_id>/syllabus/', views.get_document_syllabus_view, name='api_document_syllabus'),
    path('documents/<str:doc_id>/topics/<str:topic_id>/teach/', views.get_or_generate_topic_teaching_view, name='api_document_topic_teach'),
    path('documents/<str:doc_id>/coverage/', views.get_document_coverage_view, name='api_document_coverage'),
    path('documents/<str:doc_id>/diagnostics/', views.get_document_pipeline_diagnostics_view, name='api_document_diagnostics'),
    path('documents/<str:doc_id>/visual-audit/', views.get_document_visual_audit_view, name='api_document_visual_audit'),
    path('documents/<str:doc_id>/zero-defect-audit/', views.get_document_zero_defect_audit_view, name='api_document_zero_defect_audit'),
    path('documents/<str:doc_id>/deep-content-audit/', views.get_document_deep_content_audit_view, name='api_document_deep_content_audit'),
    path('documents/<str:doc_id>/self-repair-audit/', views.get_document_self_repair_audit_view, name='api_document_self_repair_audit'),
    path('documents/<str:doc_id>/self-repair/', views.get_document_self_repair_audit_view, name='api_document_self_repair'),
    path('documents/<str:doc_id>/download/', views.download_document_file_view, name='api_document_download'),
    path('documents/<str:doc_id>/notes/start/', views.start_notes_generation_view, name='api_document_notes_start'),
    path('documents/<str:doc_id>/reference-styles/', views.document_reference_styles_view, name='api_document_reference_styles'),
    path('documents/<str:doc_id>/notes/job/<str:job_id>/', views.get_notes_job_status_view, name='api_document_notes_job_status'),
    path('documents/<str:doc_id>/notes/latest/', views.get_notes_job_status_view, name='api_document_notes_latest'),
    path('documents/<str:doc_id>/notes/job/<str:job_id>/retry-section/', views.retry_section_notes_view, name='api_document_notes_retry_section'),
    path('documents/<str:doc_id>/notes/job/<str:job_id>/resume/', views.resume_notes_job_view, name='api_document_notes_resume'),
    path('documents/<str:doc_id>/notes/export/docx/', views.export_notes_docx_view, name='api_document_notes_export_docx'),
    path('documents/<str:doc_id>/notes/export/pdf/', views.export_notes_pdf_view, name='api_document_notes_export_pdf'),

    # Legacy endpoint aliases
    path('document/process/', views.upload_document_view, name='api_legacy_process'),
    path('document/analyze/', views.upload_document_view, name='api_legacy_analyze'),

    # Frontend v1 materials contract aliases
    path('v1/materials', views.materials_collection_view, name='api_v1_materials_root'),
    path('v1/materials/', views.materials_collection_view, name='api_v1_materials_slash'),
    path('v1/materials/bulk-delete', views.bulk_delete_documents_view, name='api_v1_materials_bulk_delete'),
    path('v1/materials/bulk-delete/', views.bulk_delete_documents_view, name='api_v1_materials_bulk_delete_slash'),
    path('v1/materials/<str:doc_id>', views.document_detail_view, name='api_v1_material_detail'),
    path('v1/materials/<str:doc_id>/', views.document_detail_view, name='api_v1_material_detail_slash'),
    path('v1/materials/<str:doc_id>/delete', views.delete_document_view, name='api_v1_material_delete'),
    path('v1/materials/<str:doc_id>/delete/', views.delete_document_view, name='api_v1_material_delete_slash'),
    path('v1/materials/<str:doc_id>/reprocess_ocr', views.reprocess_document_ocr_view, name='api_v1_material_reprocess_ocr'),
    path('v1/materials/<str:doc_id>/reprocess_ocr/', views.reprocess_document_ocr_view, name='api_v1_material_reprocess_ocr_slash'),
    path('v1/materials/<str:doc_id>/status', views.get_document_status_view, name='api_v1_material_status'),
    path('v1/materials/<str:doc_id>/status/', views.get_document_status_view, name='api_v1_material_status_slash'),
    path('v1/materials/<str:doc_id>/retry', views.retry_document_processing_view, name='api_v1_material_retry'),
    path('v1/materials/<str:doc_id>/retry/', views.retry_document_processing_view, name='api_v1_material_retry_slash'),
    path('v1/materials/<str:doc_id>/cancel', views.cancel_document_processing_view, name='api_v1_material_cancel'),
    path('v1/materials/<str:doc_id>/cancel/', views.cancel_document_processing_view, name='api_v1_material_cancel_slash'),
    path('v1/materials/<str:doc_id>/analysis', views.get_document_analysis_view, name='api_v1_material_analysis'),
    path('v1/materials/<str:doc_id>/analysis/', views.get_document_analysis_view, name='api_v1_material_analysis_slash'),
    path('v1/materials/<str:doc_id>/summary', views.get_document_summary_view, name='api_v1_material_summary'),
    path('v1/materials/<str:doc_id>/summary/', views.get_document_summary_view, name='api_v1_material_summary_slash'),
    path('v1/materials/<str:doc_id>/summary/status', views.get_document_summary_status_view, name='api_v1_material_summary_status'),
    path('v1/materials/<str:doc_id>/summary/status/', views.get_document_summary_status_view, name='api_v1_material_summary_status_slash'),
    path('v1/materials/<str:doc_id>/summary/sections', views.get_document_summary_sections_view, name='api_v1_material_summary_sections'),
    path('v1/materials/<str:doc_id>/summary/sections/', views.get_document_summary_sections_view, name='api_v1_material_summary_sections_slash'),
    path('v1/materials/<str:doc_id>/summary/visuals', views.get_document_summary_visuals_view, name='api_v1_material_summary_visuals'),
    path('v1/materials/<str:doc_id>/summary/visuals/', views.get_document_summary_visuals_view, name='api_v1_material_summary_visuals_slash'),
    path('v1/materials/<str:doc_id>/summary/regenerate', views.regenerate_document_summary_view, name='api_v1_material_summary_regenerate'),
    path('v1/materials/<str:doc_id>/summary/regenerate/', views.regenerate_document_summary_view, name='api_v1_material_summary_regenerate_slash'),
    path('v1/materials/<str:doc_id>/chat', views.chat_document_view, name='api_v1_material_chat'),
    path('v1/materials/<str:doc_id>/chat/', views.chat_document_view, name='api_v1_material_chat_slash'),
    path('v1/materials/<str:doc_id>/subject-overview', views.get_document_subject_overview_view, name='api_v1_material_subject_overview'),
    path('v1/materials/<str:doc_id>/subject-overview/', views.get_document_subject_overview_view, name='api_v1_material_subject_overview_slash'),
    path('v1/materials/<str:doc_id>/syllabus', views.get_document_syllabus_view, name='api_v1_material_syllabus'),
    path('v1/materials/<str:doc_id>/syllabus/', views.get_document_syllabus_view, name='api_v1_material_syllabus_slash'),
    path('v1/materials/<str:doc_id>/topics/<str:topic_id>/teach', views.get_or_generate_topic_teaching_view, name='api_v1_material_topic_teach'),
    path('v1/materials/<str:doc_id>/topics/<str:topic_id>/teach/', views.get_or_generate_topic_teaching_view, name='api_v1_material_topic_teach_slash'),
    path('v1/materials/<str:doc_id>/coverage', views.get_document_coverage_view, name='api_v1_material_coverage'),
    path('v1/materials/<str:doc_id>/coverage/', views.get_document_coverage_view, name='api_v1_material_coverage_slash'),
    path('v1/materials/<str:doc_id>/diagnostics', views.get_document_pipeline_diagnostics_view, name='api_v1_material_diagnostics'),
    path('v1/materials/<str:doc_id>/diagnostics/', views.get_document_pipeline_diagnostics_view, name='api_v1_material_diagnostics_slash'),
    path('v1/materials/<str:doc_id>/visual-audit', views.get_document_visual_audit_view, name='api_v1_material_visual_audit'),
    path('v1/materials/<str:doc_id>/visual-audit/', views.get_document_visual_audit_view, name='api_v1_material_visual_audit_slash'),
    path('v1/materials/<str:doc_id>/zero-defect-audit', views.get_document_zero_defect_audit_view, name='api_v1_material_zero_defect_audit'),
    path('v1/materials/<str:doc_id>/zero-defect-audit/', views.get_document_zero_defect_audit_view, name='api_v1_material_zero_defect_audit_slash'),
    path('v1/materials/<str:doc_id>/deep-content-audit', views.get_document_deep_content_audit_view, name='api_v1_material_deep_content_audit'),
    path('v1/materials/<str:doc_id>/deep-content-audit/', views.get_document_deep_content_audit_view, name='api_v1_material_deep_content_audit_slash'),
    path('v1/materials/<str:doc_id>/self-repair-audit', views.get_document_self_repair_audit_view, name='api_v1_material_self_repair_audit'),
    path('v1/materials/<str:doc_id>/self-repair-audit/', views.get_document_self_repair_audit_view, name='api_v1_material_self_repair_audit_slash'),
    path('v1/materials/<str:doc_id>/self-repair', views.get_document_self_repair_audit_view, name='api_v1_material_self_repair'),
    path('v1/materials/<str:doc_id>/self-repair/', views.get_document_self_repair_audit_view, name='api_v1_material_self_repair_slash'),
    path('v1/materials/<str:doc_id>/download', views.download_document_file_view, name='api_v1_material_download'),
    path('v1/materials/<str:doc_id>/download/', views.download_document_file_view, name='api_v1_material_download_slash'),
    path('v1/materials/<str:doc_id>/notes/start', views.start_notes_generation_view, name='api_v1_material_notes_start'),
    path('v1/materials/<str:doc_id>/notes/start/', views.start_notes_generation_view, name='api_v1_material_notes_start_slash'),
    path('v1/materials/<str:doc_id>/reference-styles', views.document_reference_styles_view, name='api_v1_material_reference_styles'),
    path('v1/materials/<str:doc_id>/reference-styles/', views.document_reference_styles_view, name='api_v1_material_reference_styles_slash'),
    path('v1/materials/<str:doc_id>/notes/job/<str:job_id>', views.get_notes_job_status_view, name='api_v1_material_notes_job_status'),
    path('v1/materials/<str:doc_id>/notes/job/<str:job_id>/', views.get_notes_job_status_view, name='api_v1_material_notes_job_status_slash'),
    path('v1/materials/<str:doc_id>/notes/latest', views.get_notes_job_status_view, name='api_v1_material_notes_latest'),
    path('v1/materials/<str:doc_id>/notes/latest/', views.get_notes_job_status_view, name='api_v1_material_notes_latest_slash'),
    path('v1/materials/<str:doc_id>/notes/job/<str:job_id>/retry-section', views.retry_section_notes_view, name='api_v1_material_notes_retry_section'),
    path('v1/materials/<str:doc_id>/notes/job/<str:job_id>/retry-section/', views.retry_section_notes_view, name='api_v1_material_notes_retry_section_slash'),
    path('v1/materials/<str:doc_id>/notes/job/<str:job_id>/resume', views.resume_notes_job_view, name='api_v1_material_notes_resume'),
    path('v1/materials/<str:doc_id>/notes/job/<str:job_id>/resume/', views.resume_notes_job_view, name='api_v1_material_notes_resume_slash'),
    path('v1/materials/<str:doc_id>/notes/export/docx', views.export_notes_docx_view, name='api_v1_material_notes_export_docx'),
    path('v1/materials/<str:doc_id>/notes/export/docx/', views.export_notes_docx_view, name='api_v1_material_notes_export_docx_slash'),
    path('v1/materials/<str:doc_id>/notes/export/pdf', views.export_notes_pdf_view, name='api_v1_material_notes_export_pdf'),
    path('v1/materials/<str:doc_id>/notes/export/pdf/', views.export_notes_pdf_view, name='api_v1_material_notes_export_pdf_slash'),

    # 3. Exams (Canonical REST)
    path('exams/', views.generate_exam_view, name='api_exams_canonical'),
    path('exams/generate/', views.generate_exam_view, name='api_generate_exam'),
    path('exams/<str:exam_id>/', views.get_exam_detail_view, name='api_get_exam'),
    path('exams/<str:exam_id>/submit/', views.submit_exam_view, name='api_submit_exam'),

    # Legacy exam aliases
    path('exam/generate/', views.generate_exam_view, name='api_legacy_generate_exam'),
    path('exam/evaluate/', views.submit_exam_view, name='api_legacy_evaluate_exam'),

    # Frontend v1 exams contract aliases
    path('v1/exams', views.generate_exam_view, name='api_v1_exams_root'),
    path('v1/exams/', views.generate_exam_view, name='api_v1_exams_slash'),
    path('v1/exams/<str:exam_id>', views.get_exam_detail_view, name='api_v1_exam_detail'),
    path('v1/exams/<str:exam_id>/submit', views.submit_exam_view, name='api_v1_exam_submit'),

    # 4. Results
    path('results/<str:result_id>/', views.get_result_detail_view, name='api_get_result'),
    path('v1/results/<str:result_id>', views.get_result_detail_view, name='api_v1_get_result'),

    # 5. Topic Intelligence
    path('topics/', views.get_topic_intelligence_view, name='api_topics_root'),
    path('topics/<str:doc_id>/', views.get_topic_intelligence_view, name='api_topics_doc'),
    path('v1/topics/intelligence', views.get_topic_intelligence_view, name='api_v1_topics_intelligence'),

    # 6. Revision Plans
    path('revision/', views.get_revision_plan_view, name='api_revision_root'),
    path('revision/<str:doc_id>/', views.get_revision_plan_view, name='api_revision_doc'),
    path('revision/items/<str:item_id>/', views.mark_revision_item_view, name='api_revision_item'),
    path('v1/revision/plan', views.get_revision_plan_view, name='api_v1_revision_plan'),
    path('v1/revision/items/<str:item_id>', views.mark_revision_item_view, name='api_v1_revision_item'),

    # 7. Question Bank
    path('questions/', views.get_questions_bank_view, name='api_questions_root'),
    path('v1/questions', views.get_questions_bank_view, name='api_v1_questions'),

    # 8. Longitudinal History
    path('history/', views.get_history_list_view, name='api_history_root'),
    path('v1/history', views.get_history_list_view, name='api_v1_history'),
    path('exam/history/', views.get_history_list_view, name='api_legacy_history'),

    # 9. Grounded AI Copilot
    path('copilot/', views.ask_copilot_view, name='api_copilot_root'),
    path('v1/copilot/ask', views.ask_copilot_view, name='api_v1_copilot_ask'),

    # 10. Adaptive Learning Loop
    path('adaptive/generate/', views.generate_adaptive_practice_view, name='api_adaptive_generate'),
    path('adaptive/submit/', views.submit_adaptive_practice_view, name='api_adaptive_submit'),
    path('adaptive/history/', views.get_adaptive_history_view, name='api_adaptive_history'),
    path('v1/adaptive/generate', views.generate_adaptive_practice_view, name='api_v1_adaptive_generate'),
    path('v1/adaptive/submit', views.submit_adaptive_practice_view, name='api_v1_adaptive_submit'),
    path('v1/adaptive/history', views.get_adaptive_history_view, name='api_v1_adaptive_history'),

    # 11. AI Quality Evaluation System
    path('evaluation/benchmark/', views.get_evaluation_benchmark_view, name='api_evaluation_benchmark'),
    path('evaluation/latest/', views.get_latest_evaluation_report_view, name='api_evaluation_latest'),
    path('evaluation/run/', views.run_evaluation_view, name='api_evaluation_run'),
    path('evaluation/runs/', views.get_evaluation_runs_list_view, name='api_evaluation_runs'),
    path('evaluation/runs/<str:run_id>/', views.get_evaluation_run_detail_view, name='api_evaluation_detail'),
    path('v1/evaluation/benchmark', views.get_evaluation_benchmark_view, name='api_v1_eval_benchmark'),
    path('v1/evaluation/latest', views.get_latest_evaluation_report_view, name='api_v1_eval_latest'),
    path('v1/evaluation/run', views.run_evaluation_view, name='api_v1_eval_run'),
    path('v1/evaluation/runs', views.get_evaluation_runs_list_view, name='api_v1_eval_runs'),

    # 12. Project Bundles & Archive Downloads
    path('downloads/bundles/', views.list_download_bundles_view, name='api_list_download_bundles'),
    path('downloads/bundles/<str:bundle_name>', views.download_bundle_zip_view, name='api_download_bundle'),
    path('downloads/bundles/<str:bundle_name>/', views.download_bundle_zip_view, name='api_download_bundle_slash'),
]
