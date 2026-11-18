/**
=============================================================================
StudyAI — Reference-Style ChatGPT-Like Document Summary & Study Engine (v4.0)
=============================================================================
Features:
- Dynamic Markdown & LaTeX math rendering via KaTeX
- Dynamic Mermaid diagram embedding
- Continuous multi-turn conversational AI Tutor drawer grounded in the document
- 5 Study Modes: Standard | Detailed | Deep Study | Quick Revision | Exam Prep
- Sticky Table of Contents navigator with smooth scroll
- High-yield quick-prompts (Intuitive analogies, Worked examples, 5 Practice questions)
- Full Markdown export & Print formatting
- Preserves all existing features (Exam Generation, Auth, Ownership, Security)
=============================================================================
*/

import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  GraduationCap,
  Printer,
  Download,
  ArrowRight,
  Zap,
  Check,
  CheckCircle2,
  Sparkles,
  Layers,
  FileText,
  RefreshCw,
  Search,
  AlertTriangle,
  Lightbulb,
  Compass,
  GitBranch,
  ShieldCheck,
  Target,
  Hash,
  Copy,
  Clock,
  Table,
  MessageSquare,
  Send,
  X,
  Bot,
  User,
  ArrowUpRight,
  Trash2
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { StepGuide } from '../components/layout/StepGuide';
import { StudyMarkdown } from '../components/common/StudyMarkdown';
import { NotesEngineView } from '../components/notes/NotesEngineView';
import { SubjectOverviewTab } from '../components/subject/SubjectOverviewTab';
import { SyllabusTreeTab } from '../components/subject/SyllabusTreeTab';
import { DeepTopicTeacherTab } from '../components/subject/DeepTopicTeacherTab';
import { DocumentCoverageTab } from '../components/subject/DocumentCoverageTab';
import {
  getMaterialSummary,
  regenerateMaterialSummary,
  getActiveMaterialId,
  deleteMaterial,
  chatWithMaterial
} from '../services/materialsService';

const SUMMARY_MODES = [
  {
    id: 'standard',
    label: 'Standard',
    badge: 'Balanced',
    icon: BookOpen,
    color: '#6366f1',
    glowColor: 'rgba(99, 102, 241, 0.25)',
    desc: 'Balanced academic depth, foundational concepts, visual models, and examples.'
  },
  {
    id: 'detailed',
    label: 'Detailed',
    badge: 'Comprehensive',
    icon: Layers,
    color: '#06b6d4',
    glowColor: 'rgba(6, 182, 212, 0.25)',
    desc: 'Exhaustive section-by-section breakdown with all proofs, workflows, and edge cases.'
  },
  {
    id: 'deep_study',
    label: 'Deep Study',
    badge: 'Rigor',
    icon: Compass,
    color: '#a855f7',
    glowColor: 'rgba(168, 85, 247, 0.25)',
    desc: 'Maximum theoretical rigor, complex architectural invariants, and nuanced mechanisms.'
  },
  {
    id: 'quick_revision',
    label: 'Quick Revision',
    badge: 'Cram Sheet',
    icon: Zap,
    color: '#f59e0b',
    glowColor: 'rgba(245, 158, 11, 0.25)',
    desc: 'High-yield definitions, formulas, and last-minute cram checklist for swift review.'
  },
  {
    id: 'exam_prep',
    label: 'Exam Prep',
    badge: 'High Yield',
    icon: Target,
    color: '#f43f5e',
    glowColor: 'rgba(244, 63, 94, 0.25)',
    desc: 'Laser-focused on scoring points, common traps, formula derivation, and question patterns.'
  }
];

export function Summary() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const targetId = searchParams.get('id') || getActiveMaterialId();

  const [activeMode, setActiveMode] = useState('standard');
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'overview'); // 'overview' | 'syllabus' | 'teach' | 'coverage' | 'notes' | 'guide'
  const [selectedTopicId, setSelectedTopicId] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [modeLoading, setModeLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [readingProgress, setReadingProgress] = useState(0);
  const [copiedMd, setCopiedMd] = useState(false);
  const [showToc, setShowToc] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Conversational AI Tutor State
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef(null);
  const activeModeRef = useRef(activeMode);

  useEffect(() => {
    activeModeRef.current = activeMode;
  }, [activeMode]);

  // Track reading progress
  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (totalHeight > 0) {
        const currentProgress = (window.scrollY / totalHeight) * 100;
        setReadingProgress(Math.min(100, Math.max(0, currentProgress)));
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Scroll chat to bottom on new messages
  useEffect(() => {
    if (isChatOpen) {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isChatOpen]);

  // Load summary
  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await getMaterialSummary(targetId, activeModeRef.current);
        setSummaryData(data);
        if (data?.active_mode) {
          setActiveMode(data.active_mode);
        }
        // Initialize welcome message for chat
        const title = data?.title || 'your uploaded study material';
        setChatMessages([
          {
            role: 'assistant',
            content: `Ask me about **${title}**. I'll use the extracted source context where it is available and tell you when the document does not support an answer.`
          }
        ]);
      } catch (err) {
        console.error('Failed to load study summary:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [targetId]);

  // Handle mode change
  const handleModeChange = async (newMode) => {
    if (newMode === activeMode || modeLoading) return;
    setActiveMode(newMode);

    if (summaryData?.modes && summaryData.modes[newMode]) {
      const cached = summaryData.modes[newMode];
      setSummaryData(prev => ({
        ...prev,
        active_mode: newMode,
        response: cached.response || cached.markdown_content || prev.response,
        markdown_content: cached.response || cached.markdown_content || prev.markdown_content,
        study_guide: cached
      }));
      return;
    }

    setModeLoading(true);
    try {
      const data = await getMaterialSummary(targetId, newMode);
      setSummaryData(data);
    } catch (err) {
      console.error(`Failed to switch mode to ${newMode}:`, err);
    } finally {
      setModeLoading(false);
    }
  };

  // Full regeneration
  const handleRegenerateFull = async () => {
    setRefreshing(true);
    try {
      const data = await regenerateMaterialSummary(targetId, { mode: activeMode });
      setSummaryData(data);
    } catch (err) {
      console.error('Failed to regenerate study guide:', err);
    } finally {
      setRefreshing(false);
    }
  };

  // Delete summary
  const handleDeleteSummary = async () => {
    if (!targetId || isDeleting) return;
    setIsDeleting(true);
    try {
      const isNumeric = !isNaN(Number(String(targetId).replace('mat-', '').replace('doc-', '')));
      if (isNumeric) {
        try {
          await deleteMaterial(targetId);
        } catch (apiErr) {
          console.warn('Backend delete returned warning:', apiErr);
        }
      }
      localStorage.removeItem(`studyai_chat_${targetId}`);
      if (getActiveMaterialId() === String(targetId)) {
        localStorage.removeItem('studyai_active_material_id');
      }
      navigate('/my-summaries');
    } catch (err) {
      console.error('Failed to delete summary:', err);
      navigate('/my-summaries');
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(false);
    }
  };

  // Copy Markdown
  const handleCopyMarkdown = () => {
    const md = activeMarkdown;
    if (md) {
      navigator.clipboard.writeText(md);
      setCopiedMd(true);
      setTimeout(() => setCopiedMd(false), 2000);
    }
  };

  // Chat message send handler
  const handleSendMessage = async (customPrompt) => {
    const textToSend = customPrompt || chatInput;
    if (!textToSend || !textToSend.trim() || chatLoading) return;

    const userMessage = { role: 'user', content: textToSend.trim() };
    const updatedHistory = [...chatMessages, userMessage];
    setChatMessages(updatedHistory);
    setChatInput('');
    setChatLoading(true);

    try {
      // Send conversation history to backend chat endpoint
      const formattedHistory = updatedHistory.map(m => ({
        role: m.role,
        content: m.content
      }));
      const res = await chatWithMaterial(targetId, textToSend.trim(), formattedHistory);
      const answer = res?.response || res?.answer || 'I could not find an answer in the uploaded document.';
      setChatMessages([...updatedHistory, { role: 'assistant', content: answer, sources: res?.sources }]);
    } catch (err) {
      console.error('Chat error:', err);
      setChatMessages([
        ...updatedHistory,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error communicating with the document intelligence service. Please try again.'
        }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // Active Markdown Content
  const activeMarkdown = !summaryData
    ? ''
    : summaryData.response ||
      summaryData.markdown_content ||
      summaryData.study_guide?.response ||
      summaryData.study_guide?.markdown_content ||
      '# Study Guide\n\nNo structured content available yet.';

  // Extract Table of Contents items from study guide or headings
  const tocItems = useMemo(() => {
    if (summaryData?.study_guide?.table_of_contents?.length > 0) {
      return summaryData.study_guide.table_of_contents.map(item => ({
        title: item.title,
        id: item.title.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-'),
        pages: item.pages
      }));
    }
    // Fallback: extract h2 headings from activeMarkdown
    const matches = activeMarkdown.matchAll(/^##\s+(.*)$/gm);
    const items = [];
    for (const m of matches) {
      const heading = m[1].trim();
      items.push({
        title: heading,
        id: heading.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-'),
        pages: ''
      });
    }
    return items;
  }, [summaryData, activeMarkdown]);

  const scrollToHeading = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6">
        <div className="relative w-16 h-16 mb-4">
          <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping" />
          <div className="absolute inset-0 rounded-full border-4 border-t-indigo-500 border-r-cyan-400 border-b-transparent border-l-transparent animate-spin" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Analyzing Document Intelligence...</h2>
        <p className="text-slate-400 text-sm max-w-md text-center">
          Loading the study material and its extracted sections.
        </p>
      </div>
    );
  }

  const title = summaryData?.title || 'Academic Study Guide';
  const subject = summaryData?.subject || summaryData?.study_guide?.subject || 'Curriculum Material';
  const totalPages = summaryData?.source_pages || summaryData?.study_guide?.total_pages;
  const coverageScore = summaryData?.quality_report?.coverage_score;
  const qualityScore = Number.isFinite(coverageScore) ? Math.round(coverageScore * 100) : null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500/30">
      {/* Top Reading Progress Bar */}
      <div className="fixed top-0 left-0 right-0 h-1 bg-slate-900 z-50">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-indigo-500 transition-all duration-150"
          style={{ width: `${readingProgress}%` }}
        />
      </div>

      {/* Primary Header */}
      <header className="sticky top-1 z-40 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80 px-4 sm:px-8 py-3.5 shadow-xl">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
              <Sparkles size={20} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-950/80 border border-indigo-500/30 text-indigo-300">
                  {subject}
                </span>
                {summaryData?.document_genre && (
                  <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-cyan-300 uppercase tracking-wider">
                    {summaryData.document_genre}
                  </span>
                )}
                <span className="text-xs text-slate-400">
                  {totalPages ? `${totalPages} pages` : 'Page count unavailable'}
                </span>
                <span
                  className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-900 border border-slate-700 text-slate-300"
                  title="Heuristic overlap with detected source headings, concepts, and formulas. This is not a factual-accuracy score."
                >
                  {qualityScore === null ? 'Coverage not measured' : `${qualityScore}% source-feature match`}
                </span>
              </div>
              <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight line-clamp-1">
                {title}
              </h1>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 self-end md:self-auto flex-wrap">
            {tocItems.length > 0 && (
              <div className="relative">
                <button
                  onClick={() => setShowToc(!showToc)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-sm font-medium transition-colors"
                  title="Table of Contents"
                >
                  <BookOpen size={15} />
                  <span>Sections</span>
                  {showToc ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                {showToc && (
                  <div className="absolute right-0 mt-2 w-72 max-h-96 overflow-y-auto rounded-xl bg-slate-900/95 backdrop-blur-xl border border-slate-800 shadow-2xl p-2 z-50">
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-2 py-1 mb-1 border-b border-slate-800 flex items-center justify-between">
                      <span>Table of Contents</span>
                      <span className="text-[10px] text-slate-500 font-mono">{tocItems.length}</span>
                    </div>
                    {tocItems.map((item, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          scrollToHeading(item.id);
                          setShowToc(false);
                        }}
                        className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors flex items-center gap-2"
                      >
                        <span className="text-indigo-400 font-mono text-[11px] shrink-0">{idx + 1}.</span>
                        <span className="truncate">{item.title}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <button
              onClick={() => setIsChatOpen(!isChatOpen)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all shadow-md ${isChatOpen
                  ? 'bg-cyan-500 text-slate-950 font-semibold shadow-cyan-500/25'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-500/20'
                }`}
            >
              <MessageSquare size={16} />
              <span>Ask AI Tutor</span>
            </button>

            <button
              onClick={handleCopyMarkdown}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-sm font-medium transition-colors"
            >
              {copiedMd ? <Check size={15} className="text-emerald-400" /> : <Copy size={15} />}
              <span>{copiedMd ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={() => window.print()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-sm font-medium transition-colors"
              title="Print or Save as PDF"
            >
              <Printer size={15} />
            </button>

            <div className="relative group">
              <button
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-sm font-medium transition-colors cursor-pointer"
                title="Download Summary as DOCX or PDF"
              >
                <Download size={15} />
                <span>Export</span>
                <ChevronDown size={13} />
              </button>
              <div className="hidden group-hover:block absolute right-0 mt-1 w-44 rounded-xl bg-slate-900/95 backdrop-blur-xl border border-slate-800 shadow-xl p-1.5 z-50">
                <a
                  href={`/api/documents/${targetId}/notes/export/docx/`}
                  download
                  className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors flex items-center gap-2"
                >
                  <FileText size={14} className="text-indigo-400" />
                  <span>Word (.DOCX)</span>
                </a>
                <a
                  href={`/api/documents/${targetId}/notes/export/pdf/`}
                  download
                  className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors flex items-center gap-2"
                >
                  <FileText size={14} className="text-cyan-400" />
                  <span>PDF Document</span>
                </a>
              </div>
            </div>

            <button
              onClick={handleRegenerateFull}
              disabled={refreshing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-sm font-medium transition-colors disabled:opacity-50"
              title="Regenerate summary with current mode"
            >
              <RefreshCw size={15} className={refreshing ? 'animate-spin text-cyan-400' : ''} />
            </button>

            <button
              onClick={() => setShowDeleteModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/40 border border-slate-800 hover:border-rose-700/50 text-slate-400 hover:text-rose-300 text-sm font-medium transition-colors"
              title="Delete this study summary"
            >
              <Trash2 size={15} />
              <span>Delete</span>
            </button>

            <button
              onClick={() => navigate(`/exam-config?id=${targetId}`)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold text-sm transition-colors"
            >
              <span>Practice Exam</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </div>

        {/* Primary View Switcher Tabs */}
        <div className="max-w-7xl mx-auto mt-3 pt-3 border-t border-slate-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'overview'
                  ? 'bg-slate-800 border border-slate-600 text-white'
                  : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <Compass size={14} className={activeTab === 'overview' ? 'text-cyan-300' : 'text-slate-500'} />
              <span>Start here</span>
            </button>

            <button
              onClick={() => setActiveTab('syllabus')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'syllabus'
                  ? 'bg-slate-800 border border-slate-600 text-white'
                  : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <GitBranch size={14} className={activeTab === 'syllabus' ? 'text-cyan-300' : 'text-slate-500'} />
              <span>Course map</span>
            </button>

            <button
              onClick={() => setActiveTab('teach')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'teach'
                  ? 'bg-slate-800 border border-slate-600 text-white'
                  : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <GraduationCap size={14} className={activeTab === 'teach' ? 'text-cyan-300' : 'text-slate-500'} />
              <span>Learn one topic</span>
            </button>

            <button
              onClick={() => setActiveTab('coverage')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'coverage'
                  ? 'bg-slate-800 border border-slate-600 text-white'
                  : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <ShieldCheck size={14} className={activeTab === 'coverage' ? 'text-cyan-300' : 'text-slate-500'} />
              <span>Source coverage</span>
            </button>

            <button
              onClick={() => setActiveTab('notes')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'notes'
                  ? 'bg-slate-800 border border-slate-600 text-white'
                  : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <Layers size={14} className={activeTab === 'notes' ? 'text-cyan-300' : 'text-slate-500'} />
              <span>Full notes</span>
            </button>

            <button
              onClick={() => setActiveTab('guide')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'guide'
                  ? 'bg-slate-800 border border-slate-600 text-white'
                  : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <BookOpen size={14} className={activeTab === 'guide' ? 'text-cyan-300' : 'text-slate-500'} />
              <span>Study Guide</span>
            </button>
          </div>

          {/* 5 Mode Selector Pills (Shown when in Guide Tab) */}
          {activeTab === 'guide' && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 shrink-0 mr-1">
                Guide Mode:
              </span>
              {SUMMARY_MODES.map((mode) => {
                const Icon = mode.icon;
                const isActive = activeMode === mode.id;
                return (
                  <button
                    key={mode.id}
                    onClick={() => handleModeChange(mode.id)}
                    disabled={modeLoading}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                      isActive
                        ? 'bg-slate-800 text-white border border-indigo-500/50 shadow-md'
                        : 'bg-slate-900/50 hover:bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800/60'
                    }`}
                    style={isActive ? { boxShadow: `0 0 12px ${mode.glowColor}` } : {}}
                  >
                    <Icon size={13} style={{ color: mode.color }} />
                    <span>{mode.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </header>

      {/* Main Document Flow */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-8 py-8 relative">
        {activeTab === 'overview' && (
          <SubjectOverviewTab
            documentId={targetId}
            onNavigateToSyllabus={() => setActiveTab('syllabus')}
            onNavigateToTeach={() => setActiveTab('teach')}
          />
        )}

        {activeTab === 'syllabus' && (
          <SyllabusTreeTab
            documentId={targetId}
            onSelectTopic={(id) => {
              setSelectedTopicId(id);
              setActiveTab('teach');
            }}
          />
        )}

        {activeTab === 'teach' && (
          <DeepTopicTeacherTab
            documentId={targetId}
            selectedTopicId={selectedTopicId}
            onSelectTopic={(id) => setSelectedTopicId(id)}
            onAskChat={(prompt) => {
              setIsChatOpen(true);
              setChatInput(prompt);
            }}
          />
        )}

        {activeTab === 'coverage' && (
          <DocumentCoverageTab
            documentId={targetId}
          />
        )}

        {activeTab === 'notes' && (
          <NotesEngineView
            materialId={targetId}
            title={title}
            subject={subject}
            totalPages={totalPages}
          />
        )}

        {activeTab === 'guide' && (
          <div className="max-w-4xl mx-auto rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800/80 p-6 sm:p-12 shadow-2xl">
            <StudyMarkdown
              content={activeMarkdown}
              onNavigateHeading={scrollToHeading}
            />

            {/* Bottom Next Step Callout */}
            <div className="mt-12 pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h4 className="text-base font-bold text-white">Ready to test your comprehension?</h4>
                <p className="text-sm text-slate-400">Generate a personalized adaptive exam tailored specifically to this document.</p>
              </div>
              <button
                onClick={() => navigate(`/exam-config?id=${targetId}`)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-semibold text-sm shadow-lg shadow-indigo-500/25 transition-all shrink-0"
              >
                <span>Launch Practice Exam</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Slide-Out AI Tutor Conversation Panel (ChatGPT Experience) */}
      {isChatOpen && (
        <aside className="fixed inset-y-0 right-0 z-50 w-full sm:w-[460px] bg-slate-950/95 backdrop-blur-2xl border-l border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
          {/* Chat Header */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-md">
                <Bot size={18} className="text-slate-950" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  StudyAI Tutor
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                </h3>
                <p className="text-[11px] text-slate-400">Using extracted source context</p>
              </div>
            </div>
            <button
              onClick={() => setIsChatOpen(false)}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Quick Prompt Chips */}
          <div className="p-3 border-b border-slate-800/80 bg-slate-900/30 flex gap-2 overflow-x-auto scrollbar-none text-xs">
            <button
              onClick={() => handleSendMessage("Explain the core concept in simple terms like I'm a beginner.")}
              className="px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 whitespace-nowrap transition-colors"
            >
              👶 Explain like I'm 5
            </button>
            <button
              onClick={() => handleSendMessage("Give me a concrete illustrative worked example not shown in the summary.")}
              className="px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 whitespace-nowrap transition-colors"
            >
              💡 Give me an example
            </button>
            <button
              onClick={() => handleSendMessage("Generate 5 practice exam questions with detailed answer keys based on this material.")}
              className="px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 whitespace-nowrap transition-colors"
            >
              📝 5 Practice questions
            </button>
          </div>

          {/* Chat Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 text-sm leading-relaxed ${msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
              >
                {msg.role !== 'user' && (
                  <div className="w-7 h-7 rounded-lg bg-indigo-600/80 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot size={15} className="text-white" />
                  </div>
                )}

                <div
                  className={`p-3.5 rounded-2xl max-w-[85%] ${msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-tr-none'
                      : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-md'
                    }`}
                >
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <StudyMarkdown content={msg.content} />
                  )}

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-slate-800 text-[11px] text-slate-400">
                      <span className="font-semibold text-slate-300">Sources: </span>
                      {msg.sources.map(s => `${s.section} (p. ${s.page})`).join(', ')}
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center shrink-0 mt-0.5">
                    <User size={15} className="text-slate-300" />
                  </div>
                )}
              </div>
            ))}

            {chatLoading && (
              <div className="flex items-center gap-2 text-xs text-slate-400 pl-10">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span>Thinking with document intelligence...</span>
              </div>
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Chat Input Box */}
          <div className="p-4 border-t border-slate-800 bg-slate-900/60">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask a question about this material..."
                className="flex-1 bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-colors"
              />
              <button
                type="submit"
                disabled={!chatInput.trim() || chatLoading}
                className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 transition-colors shadow-md"
              >
                <Send size={16} />
              </button>
            </form>
          </div>
        </aside>
      )}

      {/* Delete Summary Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => !isDeleting && setShowDeleteModal(false)}
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
                <strong style={{ color: 'var(--ink)' }}>{title}</strong>
                <br />
                This will permanently delete this document, its AI study notes, and conversation history.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
            <Button
              variant="secondary"
              size="sm"
              disabled={isDeleting}
              onClick={() => setShowDeleteModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="coral"
              size="sm"
              disabled={isDeleting}
              icon={<Trash2 size={15} />}
              onClick={handleDeleteSummary}
            >
              {isDeleting ? 'Deleting...' : 'Delete Summary'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
