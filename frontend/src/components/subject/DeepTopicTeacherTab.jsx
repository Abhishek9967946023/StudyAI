import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Sparkles,
  RefreshCw,
  GitBranch,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  MessageSquare,
  Printer,
  Copy,
  Check,
  ArrowRight,
  Calculator,
  Cpu,
  Layers,
  Scale,
  Workflow,
  FileText
} from 'lucide-react';
import { getTopicTeaching, generateTopicTeaching, getSyllabusTree } from '../../services/materialsService';
import { StudyMarkdown } from '../common/StudyMarkdown';

const ARCHETYPE_CONFIG = {
  NUMERICAL: {
    label: 'Numerical Problem Solver',
    color: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    icon: Calculator,
    desc: 'Step-by-step calculation with formula breakdown and units'
  },
  ALGORITHM: {
    label: 'Algorithm & Complexity',
    color: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
    icon: Cpu,
    desc: 'Logic, operational stages, flowchart & asymptotic complexity'
  },
  ARCHITECTURE: {
    label: 'System Architecture',
    color: 'bg-blue-500/10 text-blue-300 border-blue-500/30',
    icon: Layers,
    desc: 'Component hierarchy, data flow & modular layout'
  },
  COMPARISON: {
    label: 'Comparative Analysis',
    color: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
    icon: Scale,
    desc: 'Side-by-side trade-offs, distinction table & decision criteria'
  },
  PROCESS: {
    label: 'Sequential Workflow',
    color: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
    icon: Workflow,
    desc: 'Ordered stages, state transitions & lifecycle protocol'
  },
  CASE_STUDY: {
    label: 'Applied Case Study',
    color: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
    icon: FileText,
    desc: 'Context, problem diagnosis, intervention & measured outcomes'
  },
  THEORETICAL: {
    label: 'Theoretical Foundation',
    color: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
    icon: BookOpen,
    desc: 'Core principles, rigorous definitions & intuitive mechanisms'
  }
};

export function DeepTopicTeacherTab({
  documentId,
  selectedTopicId,
  onSelectTopic,
  onAskChat
}) {
  const [topicList, setTopicList] = useState([]);
  const [localTopicId, setLocalTopicId] = useState(null);
  const currentTopicId = selectedTopicId || localTopicId || topicList[0]?.id || null;
  const [topicData, setTopicData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  // Load flat topics list for dropdown
  useEffect(() => {
    async function loadTopics() {
      if (!documentId) return;
      try {
        const res = await getSyllabusTree(documentId, false);
        const flat = [];
        const flatten = (nodes) => {
          nodes.forEach(n => {
            flat.push({ id: n.id, name: n.name, path: n.hierarchy_path, page: n.page_start });
            if (n.subtopics) flatten(n.subtopics);
          });
        };
        flatten(res?.syllabus || []);
        setTopicList(flat);
      } catch (err) {
        console.error('Failed to load topic list:', err);
      }
    }
    loadTopics();
  }, [documentId]);

  // Load teaching content for currentTopicId
  useEffect(() => {
    async function loadTeaching() {
      if (!documentId || !currentTopicId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await getTopicTeaching(documentId, currentTopicId);
        setTopicData(res?.topic || null);
      } catch (err) {
        console.error('Failed to load topic teaching:', err);
        setError('Failed to load teaching notes for this topic.');
      } finally {
        setLoading(false);
      }
    }
    loadTeaching();
  }, [documentId, currentTopicId]);

  const handleRegenerate = async () => {
    if (!documentId || !currentTopicId || regenerating) return;
    setRegenerating(true);
    try {
      const res = await generateTopicTeaching(documentId, currentTopicId, true);
      setTopicData(res?.topic || null);
    } catch (err) {
      console.error('Failed to regenerate teaching:', err);
    } finally {
      setRegenerating(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (!topicData?.teaching_content) return;
    navigator.clipboard.writeText(topicData.teaching_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleAskTutor = () => {
    if (onAskChat && topicData?.name) {
      onAskChat(`Can you explain the key concepts, mathematical equations, and common exam traps of "${topicData.name}"?`);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Topic Switcher Bar */}
      <div className="rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-800 p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3 w-full sm:w-auto flex-1">
          <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
            <BookOpen size={18} />
          </div>
          <div className="flex-1 min-w-0">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Select Curriculum Topic to Teach:
            </label>
            <div className="relative">
              <select
                value={currentTopicId || ''}
                onChange={(e) => {
                  const id = e.target.value;
                  setLocalTopicId(id);
                  if (onSelectTopic) onSelectTopic(id);
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-semibold text-white focus:outline-none focus:border-indigo-500 appearance-none pr-8 cursor-pointer"
              >
                {topicList.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.path} {t.name} (p.{t.page})
                  </option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
          <button
            onClick={handleCopyMarkdown}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
            title="Copy teaching notes to clipboard"
          >
            {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/30 text-indigo-300 text-xs font-semibold transition-colors"
            title="Regenerate masterclass teaching notes with AI"
          >
            <RefreshCw size={13} className={regenerating ? 'animate-spin' : ''} />
            <span>{regenerating ? 'Generating...' : 'Regenerate'}</span>
          </button>

          <button
            onClick={handleAskTutor}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold text-xs transition-all shadow-md shadow-cyan-500/20"
          >
            <MessageSquare size={14} />
            <span>Ask AI Tutor</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-12 text-center text-slate-400">
          <RefreshCw size={28} className="animate-spin text-indigo-400 mx-auto mb-3" />
          <p className="text-sm font-medium">Preparing deep pedagogical masterclass for this topic...</p>
        </div>
      ) : error || !topicData ? (
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-8 text-center text-slate-400">
          <AlertCircle size={28} className="text-amber-400 mx-auto mb-3" />
          <p className="text-sm">{error || 'No teaching content available.'}</p>
        </div>
      ) : (
        (() => {
          const currentArchetypeKey = (topicData?.archetype || topicData?.metadata?.archetype || 'THEORETICAL').toUpperCase();
          const currentArchetype = ARCHETYPE_CONFIG[currentArchetypeKey] || ARCHETYPE_CONFIG.THEORETICAL;
          const ArchetypeIcon = currentArchetype.icon;

          return (
            <div className="space-y-6">
              {/* Header Meta Pill with Archetype Badge */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400 px-2">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-mono text-indigo-400">Hierarchy Path: {topicData.hierarchy_path}</span>
                  <span>•</span>
                  <span>Pages {topicData.page_start}–{topicData.page_end}</span>
                  <span>•</span>
                  <span className="text-slate-300 flex items-center gap-1">
                    <BookOpen size={13} />
                    {topicData.coverage_status === 'EXTRACTED'
                      ? 'Source excerpts (offline)'
                      : 'AI explanation — check against source'}
                  </span>
                </div>

                <div
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${currentArchetype.color}`}
                  title={currentArchetype.desc}
                >
                  <ArchetypeIcon size={13} />
                  <span>{currentArchetype.label}</span>
                </div>
              </div>

              {/* Standalone Mermaid Diagram if exists */}
              {topicData.diagram_mermaid && (
                <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 shadow-xl">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-400 mb-3">
                    <GitBranch size={15} />
                    Visual Architecture / State Machine Diagram
                  </div>
                  <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800/60 overflow-x-auto">
                    <StudyMarkdown content={`\`\`\`mermaid\n${topicData.diagram_mermaid}\n\`\`\``} />
                  </div>
                </div>
              )}

              {/* Full Pedagogical Markdown Body */}
              <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800/80 p-6 sm:p-12 shadow-2xl">
                <StudyMarkdown content={topicData.teaching_content} />
              </div>
            </div>
          );
        })()
      )}
    </div>
  );
}

