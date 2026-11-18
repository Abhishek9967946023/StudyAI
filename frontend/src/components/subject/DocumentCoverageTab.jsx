import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Layers,
  FileText,
  Calculator,
  Cpu,
  BookmarkCheck,
  Compass
} from 'lucide-react';
import { getDocumentCoverage } from '../../services/materialsService';

export function DocumentCoverageTab({ documentId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      if (!documentId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await getDocumentCoverage(documentId);
        setData(res?.coverage || null);
      } catch (err) {
        console.error('Failed to load coverage:', err);
        setError('Failed to load document coverage matrix.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [documentId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <RefreshCw size={28} className="animate-spin text-emerald-400 mb-3" />
        <p className="text-sm font-medium">Calculating which pages are mapped to topics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-2xl mx-auto rounded-2xl bg-slate-900/80 border border-slate-800 p-8 text-center">
        <AlertTriangle size={32} className="text-amber-400 mx-auto mb-3" />
        <h3 className="text-base font-bold text-white mb-2">Coverage Report Unavailable</h3>
        <p className="text-sm text-slate-400">{error || 'No coverage data available.'}</p>
      </div>
    );
  }

  const {
    total_pages = 1,
    covered_pages_count = 0,
    coverage_percentage = 0,
    total_topics = 0,
    by_status = {},
    by_node_type = {},
    formulas_count = 0,
    algorithms_count = 0,
    gaps = []
  } = data;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* 1. Header Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {/* Coverage Percentage */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-950/80 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-extrabold text-sm shrink-0">
            {Math.round(coverage_percentage)}%
          </div>
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Page Coverage</div>
            <div className="text-lg font-extrabold text-white">
              {covered_pages_count} / {total_pages} Pages
            </div>
          </div>
        </div>

        {/* Total Topics */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-950/80 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
            <Layers size={22} />
          </div>
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Total Topics</div>
            <div className="text-lg font-extrabold text-white">{total_topics} Nodes</div>
          </div>
        </div>

        {/* Formulas Indexed */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-950/80 border border-purple-500/30 flex items-center justify-center text-purple-400 shrink-0">
            <Calculator size={22} />
          </div>
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Formulas Indexed</div>
            <div className="text-lg font-extrabold text-white">{formulas_count} Equations</div>
          </div>
        </div>

        {/* Algorithms Cataloged */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-cyan-950/80 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
            <Cpu size={22} />
          </div>
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Algorithms / Protocols</div>
            <div className="text-lg font-extrabold text-white">{algorithms_count} Procedures</div>
          </div>
        </div>
      </div>

      {/* 2. Breakdown by Granularity & Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Granularity by Node Type */}
        <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 shadow-xl">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <Compass size={16} className="text-indigo-400" />
            Curriculum Hierarchy Granularity
          </h3>
          <div className="space-y-3">
            {Object.entries(by_node_type).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-900">
                <span className="capitalize text-slate-300">{type.replace('_', ' ')}</span>
                <span className="font-mono text-indigo-400 font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Pedagogical Teaching Readiness Status */}
        <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 shadow-xl">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <ShieldCheck size={16} className="text-emerald-400" />
            Pedagogical Teaching Readiness
          </h3>
          <div className="space-y-3">
            {Object.entries(by_status).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-900">
                <span className="capitalize text-slate-300">{status.replace('_', ' ').toLowerCase()}</span>
                <span className="font-mono text-emerald-400 font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Gap Analysis Report */}
      <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 shadow-xl">
        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
          <BookmarkCheck size={16} className="text-cyan-400" />
          Page Mapping & Gap Analysis
        </h3>
        {gaps.length === 0 ? (
          <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 flex items-center gap-3 text-emerald-300 text-xs font-semibold">
            <CheckCircle2 size={18} className="shrink-0" />
            <span>
              All {total_pages} pages are mapped to at least one topic. This measures page mapping only; it does not confirm that every concept was understood or taught.
            </span>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-xs text-amber-400 font-medium mb-1">
              {gaps.length} page region(s) currently unassigned to explicit topics:
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {gaps.map((g, idx) => (
                <div key={idx} className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-center text-xs text-slate-300 font-mono">
                  Pages {g.start}–{g.end}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

