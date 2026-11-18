import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  UploadCloud,
  CheckCircle2,
  Loader2,
  Sparkles,
  AlertCircle,
  FileText,
  Copy,
  Check,
  Send,
  BookOpen,
  GraduationCap,
  RotateCcw,
  Layers
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { StepGuide } from '../components/layout/StepGuide';
import {
  uploadMaterial,
  setActiveMaterialId,
  getMaterialSummary,
  getMaterialStatus,
  retryMaterialProcessing,
  cancelMaterialProcessing
} from '../services/materialsService';
import { StudyMarkdown } from '../components/common/StudyMarkdown';
import { askCopilot } from '../services/copilotService';

const DEFAULT_STEPS = [
  { key: 'uploaded', label: 'Material uploaded & secured', state: 'done' },
  { key: 'validating', label: 'Format signature validated', state: 'active' },
  { key: 'extracted', label: 'Extracting text & equations', state: 'pending' },
  { key: 'chunked', label: 'Creating semantic study chunks', state: 'pending' },
  { key: 'topics', label: 'Discovering syllabus & topics', state: 'pending' },
  { key: 'synthesizing', label: 'Synthesizing comprehensive study guide', state: 'pending' },
  { key: 'ready', label: 'Grounded AI exam engine ready', state: 'pending' }
];

let msgCounter = 0;
const generateMessageId = (prefix) => `${prefix}-${Date.now()}-${++msgCounter}`;
const formatCurrentTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export function Upload() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const docIdParam = searchParams.get('id');

  const [rawText, setRawText] = useState('');
  const [title, setTitle] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  // Customization Options
  const [summaryDepth, setSummaryDepth] = useState('detailed');
  const [outputStyle, setOutputStyle] = useState('standard');
  const [outputLanguage, setOutputLanguage] = useState('en');

  // 'idle' | 'processing' | 'summary' | 'failed'
  const [processingState, setProcessingPhase] = useState('idle');
  const [docName, setDocName] = useState('');
  const [errorReason, setErrorReason] = useState('');
  const [errorCode, setErrorCode] = useState('');
  const [errorAction, setErrorAction] = useState('');
  const [isRetryable, setIsRetryable] = useState(true);

  const [docMeta, setDocMeta] = useState(null);

  // Background pipeline status
  const [serverProgress, setServerProgress] = useState(0);
  const [serverStage, setServerStage] = useState('QUEUED');
  const [serverMessage, setServerMessage] = useState('Initializing upload...');
  const [pipelineSteps, setPipelineSteps] = useState(DEFAULT_STEPS);
  const [isCancelling, setIsCancelling] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Summary & Copilot Chat
  const [activeDocId, setActiveDocId] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [copied, setCopied] = useState(false);

  const lastPayloadRef = useRef(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const hasCompletedRef = useRef(false);

  // Resume or load document if ID passed in URL
  useEffect(() => {
    if (!docIdParam) return;

    let isMounted = true;
    async function loadParamDoc() {
      setActiveDocId(docIdParam);
      setActiveMaterialId(docIdParam);

      try {
        const statusRes = await getMaterialStatus(docIdParam);
        if (!isMounted) return;
        setDocName(statusRes?.title || 'Academic Study Material');

        if (statusRes.isComplete || statusRes.status === 'COMPLETED' || statusRes.status === 'READY') {
          const sum = await getMaterialSummary(docIdParam).catch(() => null);
          if (sum && isMounted) {
            setProcessingPhase('summary');
            setSummaryData(sum);
          } else if (isMounted) {
            setProcessingPhase('failed');
            setErrorReason('Failed to load generated summary. Please retry.');
          }
        } else if (statusRes.isFailed || statusRes.status === 'FAILED') {
          setProcessingPhase('failed');
          setErrorReason(statusRes.errorMessage || statusRes.message || 'Processing failed.');
          setErrorCode(statusRes.errorCode || 'PREVIOUS_FAILURE');
          setIsRetryable(true);
        } else {
          setServerProgress(statusRes.progress || 10);
          setServerStage(statusRes.stage || 'PROCESSING');
          setServerMessage(statusRes.message || 'Processing in background...');
          if (Array.isArray(statusRes.steps) && statusRes.steps.length > 0) {
            setPipelineSteps(statusRes.steps);
          }
          setProcessingPhase('processing');
        }
      } catch {
        const sum = await getMaterialSummary(docIdParam).catch(() => null);
        if (sum && isMounted) {
          setProcessingPhase('summary');
          setSummaryData(sum);
          setDocName(sum?.title || 'Academic Study Material');
        } else if (isMounted) {
          setProcessingPhase('failed');
          setErrorReason('Unable to load document details. Please check your network or try again.');
        }
      }
    }

    loadParamDoc();
    return () => { isMounted = false; };
  }, [docIdParam]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Status Polling Effect: Heartbeat check every 1.5s
  useEffect(() => {
    if (processingState !== 'processing' || !activeDocId) {
      return;
    }

    let isMounted = true;
    let pollTimer = null;
    let consecutiveErrors = 0;

    const pollStatus = async () => {
      try {
        const res = await getMaterialStatus(activeDocId);
        if (!isMounted) return;

        consecutiveErrors = 0;
        if (typeof res.progress === 'number') {
          setServerProgress(res.progress);
        }
        if (res.stage) setServerStage(res.stage);
        if (res.message) setServerMessage(res.message);
        if (Array.isArray(res.steps) && res.steps.length > 0) {
          setPipelineSteps(res.steps);
        }
        if (res.subject) {
          setDocMeta(prev => ({
            ...(prev || {}),
            subject: res.subject,
            pages: res.page_count,
            totalChunks: res.total_chunks,
            is_scanned: res.is_scanned,
            ocr_applied: res.ocr_applied,
            extraction_report: res.extraction_report,
            partial_success: Boolean(res.extraction_report?.partial_success || res.isPartial)
          }));
        }

        // Completion handler
        if (res.isComplete || res.status === 'COMPLETED' || res.status === 'READY') {
          if (hasCompletedRef.current) return;
          hasCompletedRef.current = true;
          if (pollTimer) clearTimeout(pollTimer);

          setServerProgress(100);
          setServerMessage('Complete AI study guide and notes ready.');

          const summary = await getMaterialSummary(activeDocId).catch(() => null);
          if (!isMounted) return;

          const finalData = summary ? {
            id: summary.id || activeDocId,
            title: summary.title || res.title || docName,
            subject: summary.subject || res.subject || 'Verified Material',
            pages: summary.pages || res.page_count || 1,
            wordCount: summary.wordCount || res.word_count,
            topics: summary.topics || [],
            markdown_content: summary.markdown_content || summary.summary || summary.response || '',
            executiveSummary: summary.executiveSummary || '',
            sections: summary.sections || [],
            grounding_notes: summary.grounding_notes || []
          } : {
            id: activeDocId,
            title: res.title || docName,
            subject: res.subject || 'Verified Material',
            pages: res.page_count || 1,
            wordCount: res.word_count,
            topics: [],
            response: res.message || '',
            markdown_content: res.message || ''
          };

          setSummaryData(finalData);
          setChatMessages([
            {
              id: 'welcome-chat',
              sender: 'assistant',
              text: `Your document "${res.title || docName}" has been indexed and summarized. You can read the summary above or ask me any questions below!`,
              time: 'Just now'
            }
          ]);
          setProcessingPhase('summary');
          return;
        }

        // Failure handler
        if (res.isFailed || res.status === 'FAILED') {
          if (pollTimer) clearTimeout(pollTimer);
          hasCompletedRef.current = true;
          setProcessingPhase('failed');
          setErrorReason(res.errorMessage || res.message || 'Processing failed.');
          setErrorCode(res.errorCode || 'PROCESSING_ERROR');
          setErrorAction(res.canRetry ? 'You can retry processing. The worker will safely resume from the last saved stage.' : 'Please review the document format and try again.');
          setIsRetryable(res.canRetry !== false);
          return;
        }

        // Cancellation handler
        if (res.isCancelled || res.status === 'CANCELLED') {
          if (pollTimer) clearTimeout(pollTimer);
          hasCompletedRef.current = true;
          setProcessingPhase('failed');
          setErrorReason('Document processing was cancelled.');
          setErrorCode('CANCELLED');
          setErrorAction('You can retry or upload a different file.');
          setIsRetryable(true);
          return;
        }

        pollTimer = setTimeout(pollStatus, 1500);

      } catch (err) {
        if (!isMounted) return;
        consecutiveErrors++;

        if (consecutiveErrors >= 6) {
          setProcessingPhase('failed');
          setErrorReason('Lost connection to processing worker.');
          setErrorCode('NETWORK_TIMEOUT');
          setErrorAction('Check server connectivity and click Retry to reconnect.');
          setIsRetryable(true);
        } else {
          pollTimer = setTimeout(pollStatus, 2500);
        }
      }
    };

    pollStatus();

    return () => {
      isMounted = false;
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [processingState, activeDocId, docName]);

  const startProcessing = async (dataPayload, displayName, fileObj = null) => {
    hasCompletedRef.current = false;
    lastPayloadRef.current = { dataPayload, displayName, fileObj };
    setDocName(displayName);
    setProcessingPhase('processing');
    setErrorReason('');
    setErrorCode('');
    setErrorAction('');
    setServerProgress(8);
    setServerStage('VALIDATING');
    setServerMessage('Validating document format and security signatures...');
    setPipelineSteps(DEFAULT_STEPS);
    setIsCancelling(false);

    try {
      if (fileObj) {
        if (fileObj.size > 50 * 1024 * 1024) {
          throw new Error('File size exceeds 50MB limit.');
        }
        const ext = fileObj.name.split('.').pop()?.toLowerCase();
        const allowedExts = ['pdf', 'docx', 'pptx', 'txt', 'md', 'png', 'jpg', 'jpeg', 'webp'];
        if (ext && !allowedExts.includes(ext)) {
          throw new Error(`Unsupported file format '.${ext}'. Supported formats: PDF, DOCX, PPTX, TXT, MD, PNG, JPG, WEBP.`);
        }
      }

      const response = await uploadMaterial(dataPayload);
      const materialId = response.id || response.document_id;
      if (!materialId) {
        throw new Error(response.error || 'Failed to create document record.');
      }

      setActiveDocId(materialId);
      setActiveMaterialId(materialId);
      setDocMeta({
        is_scanned: response.is_scanned,
        ocr_applied: response.ocr_applied,
        extraction_report: response.extraction_report,
      });
      setServerProgress(response.processing_progress || 8);
      setServerStage(response.processing_stage || 'QUEUED');
      setServerMessage(response.message || 'Queued for background processing...');
    } catch (err) {
      setProcessingPhase('failed');
      const apiErr = err.data || {};
      setErrorReason(err.message || apiErr.error || 'An unexpected error occurred during upload.');
      setErrorCode(apiErr.code || 'UPLOAD_FAILED');
      setErrorAction(apiErr.action || 'Please verify the document format and server connectivity.');
      setIsRetryable(true);
    }
  };

  const handleCancelProcessing = async () => {
    if (!activeDocId) {
      setProcessingPhase('idle');
      return;
    }
    setIsCancelling(true);
    try {
      await cancelMaterialProcessing(activeDocId);
    } catch (e) {
      console.warn('Cancel error:', e);
    } finally {
      setIsCancelling(false);
      setProcessingPhase('failed');
      setErrorCode('CANCELLED');
      setErrorReason('Document processing was cancelled by user.');
      setErrorAction('You can retry this document or choose a different file.');
      setIsRetryable(true);
    }
  };

  const handleRetryProcessing = async () => {
    hasCompletedRef.current = false;
    if (activeDocId) {
      setIsRetrying(true);
      setErrorReason('');
      setErrorCode('');
      setProcessingPhase('processing');
      setServerProgress(10);
      setServerStage('QUEUED');
      setServerMessage('Resuming background processing...');
      setPipelineSteps(DEFAULT_STEPS);
      try {
        await retryMaterialProcessing(activeDocId);
      } catch (e) {
        console.warn('Retry error:', e);
        if (lastPayloadRef.current?.dataPayload) {
          startProcessing(lastPayloadRef.current.dataPayload, docName);
        }
      } finally {
        setIsRetrying(false);
      }
    } else if (lastPayloadRef.current?.dataPayload) {
      startProcessing(lastPayloadRef.current.dataPayload, docName);
    }
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('summary_depth', summaryDepth);
      formData.append('output_style', outputStyle);
      formData.append('output_language', outputLanguage);
      startProcessing(formData, file.name, file);
    }
  };

  const handleManualUpload = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('summary_depth', summaryDepth);
      formData.append('output_style', outputStyle);
      formData.append('output_language', outputLanguage);
      startProcessing(formData, file.name, file);
      e.target.value = '';
    }
  };

  const handleTextSubmit = () => {
    if (!rawText.trim() || rawText.trim().length < 40) {
      setErrorReason('Please enter at least 40 characters of academic study material.');
      setProcessingPhase('failed');
      setDocName(title.trim() || 'Custom Study Notes');
      return;
    }
    const docTitle = title.trim() || 'Custom Study Notes';
    startProcessing({
      text: rawText,
      title: docTitle,
      summary_depth: summaryDepth,
      output_style: outputStyle,
      output_language: outputLanguage
    }, docTitle);
  };

  const handleSendChat = async (textToSend = null) => {
    const q = textToSend || chatInput;
    if (!q.trim() || isSendingChat || !activeDocId) return;

    const userMsg = {
      id: generateMessageId('usr'),
      sender: 'user',
      text: q.trim(),
      time: formatCurrentTime()
    };

    const next = [...chatMessages, userMsg];
    setChatMessages(next);
    if (!textToSend) setChatInput('');
    setIsSendingChat(true);

    try {
      const res = await askCopilot(q.trim(), activeDocId);
      const botMsg = {
        id: generateMessageId('bot'),
        sender: 'assistant',
        text: res.answer,
        sources: res.sources || [],
        time: formatCurrentTime()
      };
      setChatMessages([...next, botMsg]);
    } catch (error) {
      const failureText = Number.isInteger(error?.status)
        ? `Study Copilot returned an error (${error.status}). Please try again.`
        : 'Study Copilot could not reach the document service. Please try again.';
      const errMsg = {
        id: generateMessageId('err'),
        sender: 'assistant',
        text: failureText,
        sources: [],
        time: formatCurrentTime()
      };
      setChatMessages([...next, errMsg]);
    } finally {
      setIsSendingChat(false);
    }
  };

  const handleCopySummary = () => {
    if (!summaryData) return;
    const textToCopy = summaryData.markdown_content || summaryData.summary || summaryData.response || summaryData.executiveSummary || '';
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    hasCompletedRef.current = false;
    setProcessingPhase('idle');
    setErrorReason('');
    setDocName('');
    setActiveDocId(null);
    setSummaryData(null);
    setChatMessages([]);
    setPipelineSteps(DEFAULT_STEPS);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="fade-in" style={{ maxWidth: processingState === 'summary' ? '980px' : '820px', margin: '0 auto' }}>
      <StepGuide currentStep={1} nextUpText="Review study summary and generate your practice exam." />

      {/* 1. UPLOAD VIEW */}
      {processingState === 'idle' && (
        <>
          <div className="upload-heading" style={{ marginBottom: '20px' }}>
            <p className="eyebrow-upload">STEP 1 • INPUT MATERIAL</p>
            <h1 style={{ fontSize: '2.1rem', fontWeight: 700, margin: '8px 0' }}>
              Document Intelligence & Explanation
            </h1>
            <p style={{ color: 'var(--muted)', fontSize: '0.95rem', margin: 0 }}>
              Upload any PDF, Word, PowerPoint, Image, or Text file. StudyAI understands the material and produces a deep, structured explanation.
            </p>
          </div>

          {/* Customization Options Toolbar */}
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            padding: '14px 18px',
            marginBottom: '16px',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '14px',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Depth:
              </span>
              <select
                value={summaryDepth}
                onChange={(e) => setSummaryDepth(e.target.value)}
                style={{
                  padding: '6px 10px',
                  borderRadius: '8px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: 'var(--ink)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <option value="detailed">Detailed (Comprehensive & Structured)</option>
                <option value="comprehensive">Exhaustive (Deep Formulas & Nuances)</option>
                <option value="concise">Concise (High-Yield Essentials)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Output Style:
              </span>
              <select
                value={outputStyle}
                onChange={(e) => setOutputStyle(e.target.value)}
                style={{
                  padding: '6px 10px',
                  borderRadius: '8px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: 'var(--ink)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <option value="standard">Standard (Clear & Authoritative)</option>
                <option value="academic">Academic & Rigorous (Formal Foundations)</option>
                <option value="technical">Technical & Systemic (Architectures & Workflows)</option>
                <option value="simple">Simple & Plain-English (Accessible Analogies)</option>
                <option value="business">Executive & Strategic (Metrics & Decisions)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Language:
              </span>
              <select
                value={outputLanguage}
                onChange={(e) => setOutputLanguage(e.target.value)}
                style={{
                  padding: '6px 10px',
                  borderRadius: '8px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: 'var(--ink)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <option value="en">English (Default)</option>
                <option value="hi">Hindi (हिंदी)</option>
                <option value="es">Spanish (Español)</option>
                <option value="fr">French (Français)</option>
                <option value="de">German (Deutsch)</option>
                <option value="kn">Kannada (ಕನ್ನಡ)</option>
                <option value="ta">Tamil (தமிழ்)</option>
                <option value="te">Telugu (తెలుగు)</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div
              className="upload-card"
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }}
              onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); }}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                cursor: 'pointer',
                borderColor: isDragging ? 'var(--indigo)' : undefined,
                backgroundColor: isDragging ? 'var(--indigo-tint)' : undefined
              }}
            >
              <div className="upload-symbol" style={{ marginBottom: '8px' }}>📁</div>
              <h2>Upload Document, Slides, Images or Notes</h2>
              <p>Drag & drop PDF, Word (DOCX), PowerPoint (PPTX), Images (PNG, JPG, WEBP), or TXT here, or click to browse.</p>

              <button
                type="button"
                className="file-button"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', cursor: 'pointer', border: 'none' }}
              >
                <UploadCloud size={16} /> Choose Document or Image
              </button>
              <input
                type="file"
                ref={fileInputRef}
                accept=".pdf,.docx,.pptx,.txt,.md,.png,.jpg,.jpeg,.webp"
                onChange={handleManualUpload}
                style={{ display: 'none' }}
              />
            </div>

            <div className="or-divider">
              <span>OR</span>
            </div>

            <div className="text-card">
              <h2>Paste Lecture Notes or Syllabus Text</h2>
              <p>Type or paste any study text below to generate an instant synthesis.</p>

              <input
                type="text"
                placeholder="Optional Title (e.g., Chapter 4: Database Systems)"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: 'var(--ink)',
                  fontSize: '0.9rem',
                  marginTop: '12px',
                  boxSizing: 'border-box'
                }}
              />

              <textarea
                className="study-textarea"
                placeholder="Paste your notes or textbook content here (min. 40 characters)..."
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                style={{
                  backgroundColor: 'var(--surface)',
                  color: 'var(--ink)'
                }}
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                <span className="character-count" style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>
                  {rawText.length} characters &bull; {rawText.split(/\s+/).filter(Boolean).length} words
                </span>
                <Button
                  variant="primary"
                  size="md"
                  icon={<Sparkles size={16} />}
                  onClick={handleTextSubmit}
                  disabled={rawText.trim().length < 40}
                >
                  Generate AI Summary
                </Button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* 2. BACKGROUND PROCESSING VIEW */}
      {processingState === 'processing' && (
        <Card style={{ padding: '36px 32px' }}>
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, var(--indigo), #8B5CF6)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto',
              boxShadow: 'var(--shadow-glow)'
            }}>
              <Loader2 size={28} className="animate-spin" />
            </div>
            <h2 style={{ fontSize: '1.45rem', fontWeight: 700, margin: '0 0 6px 0', color: 'var(--ink)' }}>
              Processing Study Material...
            </h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.92rem', margin: 0 }}>
              Analyzing <strong style={{ color: 'var(--ink)' }}>{docName}</strong> using grounded AI & OCR
            </p>
          </div>

          <div style={{ maxWidth: '520px', margin: '0 auto 24px auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{
                fontSize: '0.78rem',
                fontWeight: 700,
                color: 'var(--indigo)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                background: 'var(--indigo-tint)',
                padding: '3px 8px',
                borderRadius: '6px'
              }}>
                Stage: {serverStage ? serverStage.replace('_', ' ') : 'PROCESSING'}
              </span>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--ink)' }}>
                {serverProgress}%
              </span>
            </div>
            <div style={{
              height: '8px',
              width: '100%',
              backgroundColor: 'var(--border)',
              borderRadius: '999px',
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                width: `${Math.max(5, Math.min(100, serverProgress))}%`,
                background: 'linear-gradient(90deg, var(--indigo), #8B5CF6)',
                borderRadius: '999px',
                transition: 'width 0.4s ease'
              }} />
            </div>
            {serverMessage && (
              <div style={{
                marginTop: '10px',
                fontSize: '0.86rem',
                color: 'var(--muted)',
                textAlign: 'center'
              }}>
                {serverMessage}
              </div>
            )}
          </div>

          <div style={{ maxWidth: '520px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {pipelineSteps.map((step) => {
              const isDone = step.state === 'done';
              const isActive = step.state === 'active';
              const isFailed = step.state === 'failed';

              return (
                <div
                  key={step.key}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '8px 12px',
                    borderRadius: '10px',
                    backgroundColor: isActive ? 'var(--indigo-tint)' : (isFailed ? 'rgba(239, 68, 68, 0.08)' : 'transparent'),
                    transition: 'all 0.2s ease'
                  }}
                >
                  {isDone ? (
                    <CheckCircle2 size={18} color="var(--teal)" style={{ flexShrink: 0 }} />
                  ) : isActive ? (
                    <Loader2 size={18} color="var(--indigo)" className="animate-spin" style={{ flexShrink: 0 }} />
                  ) : isFailed ? (
                    <AlertCircle size={18} color="var(--coral)" style={{ flexShrink: 0 }} />
                  ) : (
                    <div style={{ width: '18px', height: '18px', borderRadius: '50%', border: '2px solid var(--border)', flexShrink: 0 }} />
                  )}
                  <span style={{
                    fontSize: '0.88rem',
                    fontWeight: isActive || isDone ? 600 : 500,
                    color: isDone ? 'var(--ink)' : (isActive ? 'var(--indigo-text)' : (isFailed ? 'var(--coral)' : 'var(--muted)'))
                  }}>
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>

          <div style={{ textAlign: 'center', marginTop: '28px' }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleCancelProcessing}
              disabled={isCancelling}
              style={{ color: 'var(--muted)', fontSize: '0.84rem' }}
            >
              {isCancelling ? 'Cancelling...' : 'Cancel Processing'}
            </Button>
          </div>
        </Card>
      )}

      {/* 3. SUMMARY & COPILOT VIEW */}
      {processingState === 'summary' && !summaryData && (
        <Card style={{ padding: '48px 32px', textAlign: 'center' }}>
          <Loader2 size={36} className="animate-spin" style={{ margin: '0 auto 16px auto', color: 'var(--indigo)' }} />
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, margin: '0 0 8px 0', color: 'var(--ink)' }}>
            Loading AI Study Summary...
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.92rem', margin: 0 }}>
            Retrieving structured document summary and syllabus analysis.
          </p>
        </Card>
      )}

      {processingState === 'summary' && summaryData && (
        <div className="chatgpt-layout">
          <div className="chatgpt-header-card">
            <div className="chatgpt-header-left">
              <div className="chatgpt-doc-icon">
                <FileText size={24} />
              </div>
              <div>
                <h2 className="chatgpt-header-title">{docName || summaryData.title || 'Study Summary'}</h2>
                <div className="chatgpt-header-meta">
                  <Chip variant="teal">Summary Complete</Chip>
                  {docMeta?.ocr_applied && (
                    <span style={{
                      background: 'rgba(99, 102, 241, 0.12)',
                      color: '#4f46e5',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      fontSize: '0.74rem',
                      fontWeight: 600
                    }}>
                      ⚡ OCR Scanned
                    </span>
                  )}
                  {docMeta?.partial_success && (
                    <span style={{
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: '#b45309',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      fontSize: '0.74rem',
                      fontWeight: 600
                    }}>
                      ⚠ Partial OCR
                    </span>
                  )}
                  <span>•</span>
                  <span>{summaryData.subject || 'Verified Material'}</span>
                  <span>•</span>
                  <span>{summaryData.pages || 1} Pages</span>
                </div>
              </div>
            </div>

            <div className="chatgpt-actions-row">
              <Button
                variant="primary"
                size="sm"
                icon={<BookOpen size={14} />}
                onClick={() => navigate(`/summary?id=${activeDocId}&tab=guide`)}
              >
                Full Study Guide
              </Button>

              <Button
                variant="secondary"
                size="sm"
                icon={<GraduationCap size={15} />}
                onClick={() => navigate(`/generate-exam?id=${activeDocId}`)}
              >
                Generate Exam
              </Button>

              <Button
                variant="secondary"
                size="sm"
                icon={<Layers size={14} />}
                onClick={() => navigate(`/my-summaries?id=${activeDocId}`)}
              >
                My Summaries
              </Button>

              <Button
                variant="secondary"
                size="sm"
                icon={<RotateCcw size={14} />}
                onClick={() => navigate('/revision')}
              >
                Revision
              </Button>

              <button
                type="button"
                onClick={handleCopySummary}
                className="chatgpt-copy-btn"
                title="Copy formatted summary"
              >
                {copied ? <Check size={14} color="var(--teal)" /> : <Copy size={14} />}
                <span>{copied ? 'Copied!' : 'Copy'}</span>
              </button>

              <Button
                variant="ghost"
                size="sm"
                icon={<UploadCloud size={14} />}
                onClick={handleReset}
              >
                Upload Another
              </Button>
            </div>
          </div>

          {extractionWarnings.length > 0 && (
            <div style={{
              margin: '16px 0 10px 0',
              background: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              borderLeft: '4px solid #f59e0b',
              borderRadius: '12px',
              padding: '14px 16px',
              color: '#7c4d00'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: 700,
                marginBottom: '8px'
              }}>
                <AlertCircle size={16} />
                Document review notes
              </div>
              <ul style={{
                margin: 0,
                paddingLeft: '18px',
                lineHeight: 1.6,
                fontSize: '0.84rem'
              }}>
                {extractionWarnings.map((warning, index) => (
                  <li key={`${warning}-${index}`}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="chatgpt-msg-wrapper">
            <div className="chatgpt-avatar-ai">
              <Sparkles size={20} />
            </div>
            <div className="chatgpt-bubble-ai">
              <div className="chatgpt-bubble-header">
                <div className="chatgpt-author-label">
                  <span>StudyAI Assistant</span>
                  <Chip variant="indigo" style={{ fontSize: '0.68rem', padding: '2px 6px' }}>AI Summary</Chip>
                </div>
              </div>

              <div className="summary-prose">
                {summaryData.markdown_content || summaryData.summary || summaryData.response ? (
                  <StudyMarkdown content={summaryData.markdown_content || summaryData.summary || summaryData.response} />
                ) : (
                  <div>
                    {summaryData.executiveSummary && (
                      <p style={{ margin: '0 0 16px 0', fontSize: '0.95rem', lineHeight: 1.6, color: 'var(--ink)' }}>
                        {summaryData.executiveSummary}
                      </p>
                    )}
                    {summaryData.sections && summaryData.sections.map((section) => (
                      <div key={section.id || section.title} style={{ marginBottom: '24px' }}>
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ink)', marginBottom: '8px' }}>
                          {section.title}
                        </h3>
                        {section.content && (
                          <p style={{ margin: '0 0 10px 0', fontSize: '0.95rem', lineHeight: 1.6, color: 'var(--ink)' }}>
                            {section.content}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="chatgpt-thread">
            {chatMessages.map((msg) => (
              <div key={msg.id} className="chatgpt-msg-wrapper">
                {msg.sender === 'assistant' ? (
                  <div className="chatgpt-avatar-ai">
                    <Sparkles size={18} />
                  </div>
                ) : (
                  <div className="chatgpt-avatar-user">
                    You
                  </div>
                )}

                <div className={msg.sender === 'assistant' ? 'chatgpt-bubble-ai' : 'chatgpt-bubble-user'}>
                  <div className="chatgpt-bubble-header">
                    <div className="chatgpt-author-label">
                      <span>{msg.sender === 'assistant' ? 'StudyAI Tutor' : 'You'}</span>
                    </div>
                    <span style={{ fontSize: '0.72rem', color: msg.sender === 'assistant' ? 'var(--muted)' : 'rgba(79, 63, 240, 0.7)' }}>
                      {msg.time || ''}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.94rem', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                    {msg.text}
                  </div>

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="chatgpt-sources-row">
                      {msg.sources.map((s, idx) => (
                        <span key={idx} className="chatgpt-source-tag">
                          📖 {s.section || 'Source'} (Page {s.page || 1})
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="chatgpt-input-dock">
            <div className="chatgpt-suggestions-row">
              {[
                "Explain the 1st concept in simpler terms",
                "What are the most likely exam questions on this?",
                "Give me 2 real-world examples",
                "Summarize in 3 bullet points"
              ].map((chipText, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSendChat(chipText)}
                  className="chatgpt-suggestion-chip"
                >
                  {chipText}
                </button>
              ))}
            </div>

            <div className="chatgpt-input-row">
              <textarea
                rows={1}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendChat();
                  }
                }}
                placeholder="Ask a follow-up question about this summary..."
                className="chatgpt-input-field"
              />
              <button
                type="button"
                onClick={() => handleSendChat()}
                disabled={!chatInput.trim() || isSendingChat}
                className="chatgpt-send-btn"
                title="Send query"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4. ERROR & RETRY VIEW */}
      {processingState === 'failed' && (
        <Card style={{ padding: '36px 32px', textAlign: 'center' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'var(--coral-tint, rgba(239, 68, 68, 0.1))',
            color: 'var(--coral, #dc2626)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px auto'
          }}>
            <AlertCircle size={28} />
          </div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: '0 0 8px 0', color: 'var(--ink)' }}>
            Document Processing Issue
          </h2>

          {errorCode && (
            <div style={{ margin: '0 0 12px 0' }}>
              <span style={{
                background: 'rgba(239, 68, 68, 0.1)',
                color: '#dc2626',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                padding: '3px 10px',
                borderRadius: '12px',
                fontSize: '0.78rem',
                fontFamily: 'monospace',
                fontWeight: 600
              }}>
                {errorCode}
              </span>
            </div>
          )}

          <p style={{ color: 'var(--muted)', fontSize: '0.95rem', maxWidth: '520px', margin: '0 auto 16px auto', lineHeight: 1.5 }}>
            {errorReason || 'We could not index your document.'}
          </p>

          {errorAction && (
            <div style={{
              background: 'var(--surface-muted, #f8fafc)',
              border: '1px solid var(--border, #e2e8f0)',
              borderLeft: '4px solid #6366f1',
              padding: '14px 18px',
              borderRadius: '8px',
              textAlign: 'left',
              margin: '0 auto 24px auto',
              maxWidth: '540px',
              fontSize: '0.88rem',
              color: 'var(--ink, #1e293b)'
            }}>
              <strong style={{ display: 'block', marginBottom: '6px', color: '#4f46e5' }}>Recommended Action:</strong>
              <div style={{ whiteSpace: 'pre-line', lineHeight: 1.5 }}>{errorAction}</div>
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <Button variant="secondary" onClick={handleReset}>
              Try Different File
            </Button>
            {isRetryable && (
              <Button
                variant="primary"
                onClick={handleRetryProcessing}
                disabled={isRetrying}
              >
                {isRetrying ? 'Resuming...' : 'Retry Document'}
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}

export default Upload;
