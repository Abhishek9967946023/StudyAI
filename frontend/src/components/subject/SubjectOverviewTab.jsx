import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Compass,
  Layers,
  CheckCircle2,
  ArrowRight,
  BookOpen,
  Cpu,
  Globe,
  GitBranch,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { getSubjectOverview } from '../../services/materialsService';
import { StudyMarkdown } from '../common/StudyMarkdown';

export function SubjectOverviewTab({ documentId, onNavigateToSyllabus, onNavigateToTeach }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      if (!documentId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await getSubjectOverview(documentId);
        setData(res?.subject_overview || null);
      } catch (err) {
        console.error('Failed to load subject overview:', err);
        setError('Failed to load subject model. Ensure document processing is complete.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [documentId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <RefreshCw size={28} className="animate-spin text-indigo-400 mb-3" />
        <p className="text-sm font-medium">Analyzing document curriculum and subject architecture...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-2xl mx-auto rounded-2xl bg-slate-900/80 border border-slate-800 p-8 text-center">
        <AlertCircle size={32} className="text-amber-400 mx-auto mb-3" />
        <h3 className="text-base font-bold text-white mb-2">Subject Overview Unavailable</h3>
        <p className="text-sm text-slate-400 mb-4">{error || 'No subject model has been generated yet for this material.'}</p>
      </div>
    );
  }

  const {
    subject_name,
    subject_domain,
    subject_description,
    purpose,
    problems_solved = [],
    real_world_applications = [],
    prerequisites = [],
    major_knowledge_areas = [],
    logical_learning_order = [],
    mermaid_knowledge_map,
    analysis_source,
    source_note
  } = data;
  const sourceLabel = analysis_source === 'heuristic_fallback'
    ? 'Heuristic general context'
    : analysis_source === 'ai_generated'
      ? 'AI-generated; not fact-checked'
      : 'Generated overview; verify claims';

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      {/* 1. Subject Hero Card */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900/90 via-indigo-950/30 to-slate-900/90 border border-indigo-500/20 p-6 sm:p-10 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10">
          <div className="flex flex-wrap items-center gap-2.5 mb-4">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 border border-indigo-400/30 text-indigo-300">
              <Compass size={13} />
              {subject_domain || 'Higher Education Curriculum'}
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-950/60 border border-amber-500/30 text-amber-300">
              <AlertCircle size={13} />
              {sourceLabel}
            </span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
            {subject_name || 'Academic Subject'}
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-3xl mb-6">
            {subject_description}
          </p>

          <div className="rounded-xl bg-amber-950/30 border border-amber-500/20 p-3 text-xs text-amber-200/90 mb-6">
            {source_note || 'This overview is generated and has not been independently fact-checked. Compare the syllabus map with the uploaded pages.'}
          </div>

          {purpose && (
            <div className="rounded-2xl bg-indigo-950/40 border border-indigo-500/20 p-4 sm:p-5">
              <div className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1 flex items-center gap-1.5">
                <Sparkles size={14} />
                Core Engineering / Scientific Purpose
              </div>
              <p className="text-sm font-medium text-slate-200">{purpose}</p>
            </div>
          )}

          <div className="flex items-center gap-3 mt-6">
            {onNavigateToSyllabus && (
              <button
                onClick={onNavigateToSyllabus}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors shadow-lg shadow-indigo-600/30"
              >
                <span>Explore Full Syllabus Tree</span>
                <ArrowRight size={14} />
              </button>
            )}
            {onNavigateToTeach && (
              <button
                onClick={onNavigateToTeach}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs border border-slate-700 transition-colors"
              >
                <BookOpen size={14} className="text-cyan-400" />
                <span>Deep Topic Teacher</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 2. Problems Solved & Real-World Applications Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Problems Solved */}
        <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 shadow-xl">
          <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm mb-4">
            <Cpu size={18} />
            <h2>Core Problems Solved in Industry & Systems</h2>
          </div>
          <ul className="space-y-3">
            {problems_solved.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3 text-xs sm:text-sm text-slate-300">
                <span className="w-5 h-5 rounded-full bg-indigo-950 border border-indigo-500/40 text-indigo-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Real-World Applications */}
        <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 shadow-xl">
          <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm mb-4">
            <Globe size={18} />
            <h2>Modern Production & Hardware Applications</h2>
          </div>
          <ul className="space-y-3">
            {real_world_applications.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3 text-xs sm:text-sm text-slate-300">
                <CheckCircle2 size={16} className="text-cyan-400 shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* 3. Major Knowledge Areas / Pillars */}
      {major_knowledge_areas.length > 0 && (
        <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 sm:p-8 shadow-xl">
          <div className="flex items-center gap-2 text-white font-bold text-base mb-6">
            <Layers size={20} className="text-indigo-400" />
            <h2>Major Knowledge Areas (Curriculum Pillars)</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {major_knowledge_areas.map((area, idx) => (
              <div
                key={idx}
                className="rounded-xl bg-slate-950/60 border border-slate-800/80 p-5 hover:border-indigo-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <span className="text-[10px] font-mono text-indigo-400 uppercase tracking-widest">
                    Pillar {idx + 1}
                  </span>
                  <h3 className="text-sm font-bold text-white mt-1 mb-2">{area.name}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed mb-3">{area.description}</p>
                </div>
                {area.core_focus && (
                  <div className="pt-2 border-t border-slate-900 text-[11px] text-indigo-300 font-medium">
                    <span className="text-slate-500">Focus: </span>
                    {area.core_focus}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Interactive Knowledge Map Diagram */}
      {mermaid_knowledge_map && (
        <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 sm:p-8 shadow-xl">
          <div className="flex items-center gap-2 text-white font-bold text-base mb-2">
            <GitBranch size={20} className="text-cyan-400" />
            <h2>Subject Knowledge Architecture Map</h2>
          </div>
          <p className="text-xs text-slate-400 mb-6">
            Visual structural diagram of core knowledge areas and dependent topic relationships.
          </p>
          <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800/60 overflow-x-auto">
            <StudyMarkdown content={`\`\`\`mermaid\n${mermaid_knowledge_map}\n\`\`\``} />
          </div>
        </div>
      )}

      {/* 5. Logical Learning Progression & Prerequisites */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Prerequisites */}
        <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 shadow-xl">
          <div className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-3 flex items-center gap-1.5">
            <AlertCircle size={14} />
            Foundational Prerequisites
          </div>
          <ul className="space-y-2">
            {prerequisites.map((req, idx) => (
              <li key={idx} className="text-xs text-slate-300 bg-slate-950/60 border border-slate-800/60 px-3 py-2 rounded-lg flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span>{req}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Learning Progression Sequence */}
        <div className="md:col-span-2 rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 shadow-xl">
          <div className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-4 flex items-center gap-1.5">
            <ArrowRight size={14} />
            Recommended Pedagogical Learning Sequence
          </div>
          <div className="space-y-3">
            {logical_learning_order.map((step, idx) => (
              <div key={idx} className="flex items-start gap-3 bg-slate-950/60 border border-slate-800/60 p-3 rounded-xl">
                <div className="w-6 h-6 rounded-lg bg-emerald-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center text-xs font-bold shrink-0">
                  {step.step || idx + 1}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">{step.topic}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">{step.rationale}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

