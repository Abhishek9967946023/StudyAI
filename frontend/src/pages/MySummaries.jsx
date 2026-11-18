/**
 * =============================================================================
 * StudyAI — 2. My Summaries (Old Chats & Historical Summaries)
 * =============================================================================
 * ChatGPT / Notion Style Split Layout:
 * - Left Panel: Searchable list of past materials & study sessions
 * - Right Panel: Complete ChatGPT-style summary + persistent chat conversation
 * =============================================================================
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  BookOpen,
  Sparkles,
  Search,
  UploadCloud,
  GraduationCap,
  RotateCcw,
  Copy,
  Check,
  Send,
  Clock,
  FileText,
  Layers,
  Download,
  Share2,
  Trash2,
  ChevronRight,
  HelpCircle,
  MessageSquare,
  AlertTriangle,
  X
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Skeleton } from '../components/ui/Skeleton';
import { Modal } from '../components/ui/Modal';
import { Toast } from '../components/ui/Toast';
import { EmptyState } from '../components/ui/EmptyState';
import { 
  getMaterials, 
  getMaterialSummary, 
  getActiveMaterialId, 
  setActiveMaterialId,
  deleteMaterial,
  bulkDeleteMaterials
} from '../services/materialsService';
import { askCopilot } from '../services/copilotService';
import { StudyMarkdown } from '../components/common/StudyMarkdown';

let msgCounter = 0;
const generateMessageId = (prefix) => `${prefix}-${Date.now()}-${++msgCounter}`;
const formatCurrentTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export function MySummaries() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const targetIdParam = searchParams.get('id');

  const [materials, setMaterials] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [copied, setCopied] = useState(false);

  // Deletion state
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [toast, setToast] = useState(null);

  const messagesEndRef = useRef(null);

  // Load materials list
  useEffect(() => {
    async function loadAllMaterials() {
      setLoading(true);
      try {
        const list = await getMaterials().catch(() => []);
        const validList = Array.isArray(list) ? list : [];
        setMaterials(validList);

        // Find active document
        if (validList.length > 0) {
          const targetId = targetIdParam || getActiveMaterialId();
          const active = validList.find(m => String(m.id) === String(targetId)) || validList[0];
          setSelectedDoc(active);
          setActiveMaterialId(active.id);
        } else {
          setSelectedDoc(null);
        }
      } catch (err) {
        console.error('Failed to load materials:', err);
        setMaterials([]);
        setSelectedDoc(null);
      } finally {
        setLoading(false);
      }
    }
    loadAllMaterials();
  }, [targetIdParam]);

  // Load summary and chat history whenever selectedDoc changes
  useEffect(() => {
    if (!selectedDoc) return;

    async function loadDocSummary() {
      try {
        const sum = await getMaterialSummary(selectedDoc.id).catch(() => null);
        setSummaryData(sum);
      } catch (err) {
        setSummaryData(null);
      }

      // Load saved chat history from localStorage
      const savedChat = localStorage.getItem(`studyai_chat_${selectedDoc.id}`);
      if (savedChat) {
        try {
          setChatMessages(JSON.parse(savedChat));
        } catch {
          setChatMessages([]);
        }
      } else {
        // Initial welcome chat
        setChatMessages([
          {
            id: 'init-1',
            sender: 'assistant',
            text: `Here is your verified study summary for "${selectedDoc.title}". Ask me any follow-up questions, explanations, or exam questions about this document below!`,
            time: 'Just now'
          }
        ]);
      }
    }
    loadDocSummary();
  }, [selectedDoc]);

  // Scroll to bottom on new chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSelectDoc = (doc) => {
    setSelectedDoc(doc);
    setActiveMaterialId(doc.id);
    setSearchParams({ id: doc.id });
  };

  const handleSendMessage = async (textToSend = null) => {
    const q = textToSend || chatInput;
    if (!q.trim() || isSending || !selectedDoc) return;

    const userMsg = {
      id: generateMessageId('usr'),
      sender: 'user',
      text: q.trim(),
      time: formatCurrentTime()
    };

    const nextMessages = [...chatMessages, userMsg];
    setChatMessages(nextMessages);
    if (!textToSend) setChatInput('');
    setIsSending(true);

    try {
      const res = await askCopilot(q.trim(), selectedDoc.id);
      const botMsg = {
        id: generateMessageId('bot'),
        sender: 'assistant',
        text: res.answer,
        sources: res.sources || [],
        time: formatCurrentTime()
      };
      const updatedChat = [...nextMessages, botMsg];
      setChatMessages(updatedChat);
      localStorage.setItem(`studyai_chat_${selectedDoc.id}`, JSON.stringify(updatedChat));
    } catch {
      const errMsg = {
        id: generateMessageId('err'),
        sender: 'assistant',
        text: "I couldn't find a direct verification for that in this document. Ask about the concepts, mechanisms, or definitions outlined in the summary above.",
        sources: [],
        time: formatCurrentTime()
      };
      const updatedChat = [...nextMessages, errMsg];
      setChatMessages(updatedChat);
      localStorage.setItem(`studyai_chat_${selectedDoc.id}`, JSON.stringify(updatedChat));
    } finally {
      setIsSending(false);
    }
  };

  const handleCopySummary = () => {
    if (!summaryData) return;
    let fullText = `${selectedDoc?.title}\n======================\n\n`;
    if (summaryData.sections) {
      summaryData.sections.forEach(s => {
        fullText += `${s.title}\n`;
        if (s.content) fullText += `${s.content}\n\n`;
        if (s.items) {
          s.items.forEach(it => {
            if (typeof it === 'string') {
              fullText += `• ${it}\n`;
            } else if (it.term) {
              const desc = it.definition || it.def || it.in_depth || it.meaning || it.intuition || '';
              fullText += desc ? `• ${it.term}: ${desc}\n` : `• ${it.term}\n`;
            } else if (it.formula) {
              const lbl = it.label || it.name || 'Formula';
              fullText += `• ${lbl}: ${it.formula}\n`;
            } else if (it.title) {
              const dt = it.detail || it.content || '';
              fullText += dt ? `• ${it.title}: ${dt}\n` : `• ${it.title}\n`;
            }
          });
          fullText += '\n';
        }
      });
    }
    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDeleteSingle = async () => {
    if (!deleteTarget || isDeleting) return;
    setIsDeleting(true);
    const targetTitle = deleteTarget.title || 'Untitled Material';
    const targetId = deleteTarget.id;

    try {
      // If it's a numeric ID, call backend delete API
      const isNumeric = !isNaN(Number(String(targetId).replace('mat-', '').replace('doc-', '')));
      if (isNumeric) {
        try {
          await deleteMaterial(targetId);
        } catch (apiErr) {
          console.warn('Backend delete returned warning:', apiErr);
        }
      }

      // Clean local chat and active id
      localStorage.removeItem(`studyai_chat_${targetId}`);

      // Update state
      const remaining = materials.filter(m => String(m.id) !== String(targetId));
      setMaterials(remaining);

      if (selectedDoc && String(selectedDoc.id) === String(targetId)) {
        if (remaining.length > 0) {
          const nextDoc = remaining[0];
          setSelectedDoc(nextDoc);
          setActiveMaterialId(nextDoc.id);
          setSearchParams({ id: nextDoc.id });
        } else {
          setSelectedDoc(null);
          setSummaryData(null);
          setChatMessages([]);
          localStorage.removeItem('studyai_active_material_id');
        }
      }

      setToast({ message: `Deleted summary: "${targetTitle}"`, variant: 'success' });
      setDeleteTarget(null);
    } catch (err) {
      console.error('Failed to delete summary:', err);
      // Ensure UI remains consistent
      const remaining = materials.filter(m => String(m.id) !== String(targetId));
      setMaterials(remaining);
      setDeleteTarget(null);
      setToast({ message: `Removed summary: "${targetTitle}"`, variant: 'success' });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleBulkDelete = async () => {
    if (!filteredMaterials.length || isDeleting) return;
    setIsDeleting(true);
    const idsToDelete = filteredMaterials.map(m => m.id);
    const count = idsToDelete.length;

    try {
      // Attempt backend bulk delete on real numeric IDs
      const realIds = idsToDelete.filter(id => !isNaN(Number(String(id).replace('mat-', '').replace('doc-', ''))));
      if (realIds.length > 0) {
        try {
          await bulkDeleteMaterials(realIds);
        } catch (apiErr) {
          console.warn('Backend bulk delete warning:', apiErr);
        }
      }

      idsToDelete.forEach(id => {
        localStorage.removeItem(`studyai_chat_${id}`);
      });

      const remaining = materials.filter(m => !idsToDelete.some(delId => String(delId) === String(m.id)));
      setMaterials(remaining);
      setSearchQuery('');

      if (remaining.length > 0) {
        const nextDoc = remaining[0];
        setSelectedDoc(nextDoc);
        setActiveMaterialId(nextDoc.id);
        setSearchParams({ id: nextDoc.id });
      } else {
        setSelectedDoc(null);
        setSummaryData(null);
        setChatMessages([]);
        localStorage.removeItem('studyai_active_material_id');
      }

      setToast({ message: `Deleted ${count} searched summaries.`, variant: 'success' });
      setShowBulkDeleteModal(false);
    } catch (err) {
      console.error('Failed to delete summaries:', err);
      setShowBulkDeleteModal(false);
    } finally {
      setIsDeleting(false);
    }
  };

  // Filter materials by search query
  const filteredMaterials = (materials || []).filter(m => {
    const q = searchQuery.toLowerCase();
    return (
      (m.title && m.title.toLowerCase().includes(q)) ||
      (m.subject && m.subject.toLowerCase().includes(q))
    );
  });

  if (loading) {
    return (
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <Skeleton height="80px" />
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
          <Skeleton height="500px" />
          <Skeleton height="500px" />
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in" style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--indigo)', marginBottom: '4px' }}>
            <BookOpen size={18} />
            <span style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Study Material Library
            </span>
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
            My Summaries & Old Chats
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '0.94rem', margin: '4px 0 0 0' }}>
            Browse through your saved notes, complete AI-style summaries, and continue AI discussions.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          icon={<UploadCloud size={16} />}
          onClick={() => navigate('/upload')}
        >
          + Upload New Material
        </Button>
      </div>

      {/* Split Layout: Left List | Right ChatGPT Summary & Chat */}
      <div className="summaries-split-layout">
        {/* Left Panel: Past Materials & Chat History */}
        <aside className="summaries-sidebar-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Saved Documents ({filteredMaterials.length})
            </span>
            <Chip variant="indigo" style={{ fontSize: '0.7rem' }}>
              Active Archive
            </Chip>
          </div>

          {/* Search Input */}
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)' }} />
            <input
              type="text"
              placeholder="Search summaries & topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="summaries-search-input"
              style={{ paddingRight: searchQuery ? '32px' : '14px' }}
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--muted)',
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center'
                }}
                title="Clear search"
                aria-label="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Search result indicator and Bulk Delete Searched Summaries */}
          {searchQuery.trim() && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 2px', marginTop: '-6px' }}>
              <span style={{ fontSize: '0.76rem', color: 'var(--muted)' }}>
                Found <strong>{filteredMaterials.length}</strong> {filteredMaterials.length === 1 ? 'summary' : 'summaries'}
              </span>
              {filteredMaterials.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowBulkDeleteModal(true)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    background: 'rgba(239, 68, 68, 0.08)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    color: '#ef4444',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    padding: '3px 7px',
                    borderRadius: '6px',
                    transition: 'all 0.15s ease'
                  }}
                  title="Delete all matching searched summaries"
                >
                  <Trash2 size={12} />
                  <span>Delete all searched</span>
                </button>
              )}
            </div>
          )}

          {/* List of Summaries */}
          <div className="summaries-list">
            {filteredMaterials.map((doc) => {
              const isActive = selectedDoc && String(selectedDoc.id) === String(doc.id);
              return (
                <div
                  key={doc.id}
                  onClick={() => handleSelectDoc(doc)}
                  className={`summary-item-card ${isActive ? 'active' : ''}`}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
                    <span className="summary-item-title">{doc.title}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteTarget(doc);
                        }}
                        className="summary-item-delete-btn"
                        title={`Delete "${doc.title}"`}
                        aria-label={`Delete "${doc.title}"`}
                      >
                        <Trash2 size={14} />
                      </button>
                      {isActive && <ChevronRight size={16} color="var(--indigo)" style={{ flexShrink: 0, marginTop: '2px' }} />}
                    </div>
                  </div>
                  <div className="summary-item-meta">
                    <span style={{ color: 'var(--indigo-text)', fontWeight: 600 }}>{doc.subject || 'Academic Text'}</span>
                    <span>{doc.pageCount ? `${doc.pageCount} pgs` : 'PDF'}</span>
                  </div>
                </div>
              );
            })}

            {filteredMaterials.length === 0 && (
              <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--muted)', fontSize: '0.88rem' }}>
                <p>No matching materials found.</p>
                <Button variant="secondary" size="sm" onClick={() => setSearchQuery('')} style={{ marginTop: '8px' }}>
                  Clear Search
                </Button>
              </div>
            )}
          </div>
        </aside>

        {/* Right Panel: Selected Document Summary & ChatGPT Conversation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {selectedDoc ? (
            <>
              {/* Document Banner */}
              <div className="chatgpt-header-card">
                <div className="chatgpt-header-left">
                  <div className="chatgpt-doc-icon">
                    <FileText size={24} />
                  </div>
                  <div>
                    <h2 className="chatgpt-header-title">{selectedDoc.title}</h2>
                    <div className="chatgpt-header-meta">
                      <Chip variant="indigo">{selectedDoc.subject || 'Verified Subject'}</Chip>
                      <span>•</span>
                      <span>{selectedDoc.pageCount || 1} Pages</span>
                      <span>•</span>
                      <span>{selectedDoc.charCount ? `${Math.round(selectedDoc.charCount / 5)} words` : 'Full Text'}</span>
                      <span>•</span>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={12} /> Ready for testing
                      </span>
                    </div>
                  </div>
                </div>

                <div className="chatgpt-actions-row">
                  <button
                    onClick={handleCopySummary}
                    className="chatgpt-copy-btn"
                    title="Copy formatted summary to clipboard"
                  >
                    {copied ? <Check size={14} color="var(--teal)" /> : <Copy size={14} />}
                    <span>{copied ? 'Copied!' : 'Copy Summary'}</span>
                  </button>

                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<RotateCcw size={14} />}
                    onClick={() => {
                      if (selectedDoc?.id) {
                        setActiveMaterialId(selectedDoc.id);
                        navigate(`/revision?id=${selectedDoc.id}`);
                      } else {
                        navigate('/revision');
                      }
                    }}
                  >
                    Flashcards
                  </Button>

                  <Button
                    variant="primary"
                    size="sm"
                    icon={<GraduationCap size={15} />}
                    onClick={() => navigate(`/generate-exam?id=${selectedDoc.id}`)}
                  >
                    Generate Exam
                  </Button>

                  <button
                    type="button"
                    onClick={() => setDeleteTarget(selectedDoc)}
                    className="chatgpt-delete-action-btn"
                    title={`Delete summary "${selectedDoc.title}"`}
                  >
                    <Trash2 size={14} />
                    <span>Delete</span>
                  </button>
                </div>
              </div>

              {/* ChatGPT Summary Message Bubble */}
              <div className="chatgpt-msg-wrapper">
                <div className="chatgpt-avatar-ai">
                  <Sparkles size={20} />
                </div>
                <div className="chatgpt-bubble-ai">
                  <div className="chatgpt-bubble-header">
                    <div className="chatgpt-author-label">
                      <span>StudyAI Synthesis Assistant</span>
                      <Chip variant="teal" style={{ fontSize: '0.68rem', padding: '2px 6px' }}>Grounded Analysis</Chip>
                    </div>
                    <span style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>Executive Summary</span>
                  </div>

                  <div className="summary-prose">
                    {summaryData?.markdown_content || summaryData?.summary || summaryData?.response ? (
                      <StudyMarkdown content={summaryData.markdown_content || summaryData.summary || summaryData.response} />
                    ) : (
                      <div>
                        {summaryData?.sections && summaryData.sections.map((section) => (
                          <div key={section.id} style={{ marginBottom: '20px' }}>
                            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ink)', marginBottom: '8px' }}>
                              {section.title}
                            </h3>
                            {section.content && (
                              <p style={{ margin: '0 0 10px 0', fontSize: '0.94rem', lineHeight: 1.6, color: 'var(--ink)' }}>
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

              {/* Chat Thread: User queries & AI responses */}
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

                      {/* Source Citations */}
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

              {/* ChatGPT Floating Input Dock */}
              <div className="chatgpt-input-dock">
                <div className="chatgpt-suggestions-row">
                  {[
                    "Explain the core mechanisms simply",
                    "What are high-yield exam pitfalls?",
                    "Give me 3 practice recall questions",
                    "Summarize key formulas"
                  ].map((chipText, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSendMessage(chipText)}
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
                        handleSendMessage();
                      }
                    }}
                    placeholder={`Ask StudyAI anything about ${selectedDoc.title}...`}
                    className="chatgpt-input-field"
                  />
                  <button
                    type="button"
                    onClick={() => handleSendMessage()}
                    disabled={!chatInput.trim() || isSending}
                    className="chatgpt-send-btn"
                    title="Send query"
                  >
                    <Send size={18} />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <EmptyState
              icon={<BookOpen size={28} />}
              title="No Study Summaries Available"
              description="You don't have any study summaries saved. Upload study materials or notes to generate your first AI study guide."
              actionLabel="Upload Material"
              actionIcon={<UploadCloud size={16} />}
              onAction={() => navigate('/upload')}
            />
          )}
        </div>
      </div>

      {/* Delete Single Summary Modal */}
      <Modal
        isOpen={Boolean(deleteTarget)}
        onClose={() => !isDeleting && setDeleteTarget(null)}
        title="Delete Study Summary"
        maxWidth="460px"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '8px 0 0 0' }}>
          <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(239, 68, 68, 0.12)',
              color: '#ef4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <Trash2 size={22} />
            </div>
            <div>
              <p style={{ margin: '0 0 6px 0', fontSize: '0.96rem', fontWeight: 600, color: 'var(--ink)' }}>
                Are you sure you want to delete this summary?
              </p>
              <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--muted)', lineHeight: 1.5 }}>
                <strong style={{ color: 'var(--ink)' }}>{deleteTarget?.title}</strong>
                <br />
                This will permanently delete this document, its AI summary, notes, and conversation history.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
            <Button
              variant="secondary"
              size="sm"
              disabled={isDeleting}
              onClick={() => setDeleteTarget(null)}
            >
              Cancel
            </Button>
            <Button
              variant="coral"
              size="sm"
              disabled={isDeleting}
              icon={<Trash2 size={15} />}
              onClick={handleDeleteSingle}
            >
              {isDeleting ? 'Deleting...' : 'Delete Summary'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Bulk Delete Searched Summaries Modal */}
      <Modal
        isOpen={showBulkDeleteModal}
        onClose={() => !isDeleting && setShowBulkDeleteModal(false)}
        title="Delete Searched Summaries"
        maxWidth="480px"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '8px 0 0 0' }}>
          <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(239, 68, 68, 0.12)',
              color: '#ef4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <AlertTriangle size={22} />
            </div>
            <div>
              <p style={{ margin: '0 0 6px 0', fontSize: '0.96rem', fontWeight: 600, color: 'var(--ink)' }}>
                Delete {filteredMaterials.length} searched summaries?
              </p>
              <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--muted)', lineHeight: 1.5 }}>
                You are about to permanently delete all {filteredMaterials.length} summaries matching search query <strong>"{searchQuery}"</strong>.
                <br />
                This action cannot be undone.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
            <Button
              variant="secondary"
              size="sm"
              disabled={isDeleting}
              onClick={() => setShowBulkDeleteModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="coral"
              size="sm"
              disabled={isDeleting}
              icon={<Trash2 size={15} />}
              onClick={handleBulkDelete}
            >
              {isDeleting ? 'Deleting...' : `Delete All ${filteredMaterials.length} Summaries`}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          variant={toast.variant}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default MySummaries;
