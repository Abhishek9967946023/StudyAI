/**
=============================================================================
StudyAI — Complete Verified Study Notes & Syllabus Engine View
=============================================================================
Section-by-section hierarchical study note generation, real-time verification,
mathematical completeness auditing, defect repair, and publication export.
=============================================================================
*/

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
  Download,
  FileText,
  Sparkles,
  Play,
  RotateCcw,
  BookOpen,
  Hash,
  Layers,
} from 'lucide-react';
import { StudyMarkdown } from '../common/StudyMarkdown';
import {
  startNotesJob,
  getNotesJobStatus,
  retryNotesSection,
  resumeNotesJob,
  getMaterials,
  getReferenceStyleProfiles,
  analyzeReferenceStyle,
  getNotesDocxExportUrl,
  getNotesPdfExportUrl
} from '../../services/materialsService';

const ACTIVE_JOB_STATUSES = new Set(['QUEUED', 'PLANNING', 'GENERATING', 'VERIFYING', 'REPAIRING', 'IN_PROGRESS', 'NOT_STARTED']);
const COMPLETED_JOB_STATUSES = new Set(['COMPLETED', 'COMPLETED_WITH_WARNINGS']);

export function NotesEngineView({ materialId, title, subject, totalPages }) {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [selectedSectionId, setSelectedSectionId] = useState(null);
  const [filter, setFilter] = useState('ALL');
  const [statusError, setStatusError] = useState('');
  const [styleError, setStyleError] = useState('');
  const [referenceDocuments, setReferenceDocuments] = useState([]);
  const [styleProfiles, setStyleProfiles] = useState([]);
  const [selectedReferenceDocumentId, setSelectedReferenceDocumentId] = useState('');
  const [selectedStyleProfileId, setSelectedStyleProfileId] = useState('');
  const [analyzingStyle, setAnalyzingStyle] = useState(false);
  const pollTimerRef = useRef(null);

  useEffect(() => {
    let isMounted = true;
    Promise.allSettled([
      getMaterials(),
      getReferenceStyleProfiles(materialId)
    ]).then(([materialsResult, profilesResult]) => {
      if (!isMounted) return;
      if (materialsResult.status === 'fulfilled') {
        const materials = Array.isArray(materialsResult.value) ? materialsResult.value : [];
        setReferenceDocuments(materials.filter((material) => String(material.id) !== String(materialId)));
      } else {
        setStyleError(materialsResult.reason?.message || 'Could not load reference documents.');
      }
      if (profilesResult.status === 'fulfilled') {
        const profiles = Array.isArray(profilesResult.value?.profiles) ? profilesResult.value.profiles : [];
        setStyleProfiles(profiles);
      } else {
        setStyleError(profilesResult.reason?.message || 'Could not load reference style profiles.');
      }
    });
    return () => {
      isMounted = false;
    };
  }, [materialId]);

  async function fetchJobStatus() {
    try {
      const res = await getNotesJobStatus(materialId, 'latest');
      if (res && res.job_id) {
        setJob(res);
        return res;
      }
    } catch (error) {
      if (error.status !== 404) {
        setStatusError(error.message || 'Could not load notes status.');
      }
    } finally {
      setLoading(false);
    }
    return null;
  }

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    stopPolling();
    pollTimerRef.current = setInterval(async () => {
      try {
        const res = await getNotesJobStatus(materialId, 'latest');
        if (res && res.job_id) {
          setJob(res);
          if (COMPLETED_JOB_STATUSES.has(res.status) || res.status === 'FAILED' || res.status === 'CANCELLED') {
            stopPolling();
          }
        }
      } catch (error) {
        setStatusError(error.message || 'Could not refresh notes status.');
        stopPolling();
      }
    }, 2500);
  }, [materialId, stopPolling]);

  useEffect(() => {
    let isMounted = true;
    getNotesJobStatus(materialId, 'latest').then((currentJob) => {
      if (!isMounted) return;
      if (currentJob?.job_id) {
        setJob(currentJob);
        if (ACTIVE_JOB_STATUSES.has(currentJob.status)) {
          startPolling();
        }
      }
      setLoading(false);
    }).catch((error) => {
      if (!isMounted) return;
      if (error.status !== 404) {
        setStatusError(error.message || 'Could not load notes status.');
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
      stopPolling();
    };
  }, [materialId, startPolling, stopPolling]);

  const handleStartGeneration = async (forceRestart = false) => {
    setActionLoading(true);
    setStatusError('');
    try {
      const res = await startNotesJob(materialId, {
        mode: 'comprehensive',
        depth: 'thorough',
        language: 'en',
        force_restart: forceRestart,
        reference_style_profile_id: selectedStyleProfileId || null
      });
      if (res && res.job_id) {
        await fetchJobStatus();
        startPolling();
      }
    } catch (error) {
      setStatusError(error.message || 'Failed to start notes generation.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResumeJob = async () => {
    if (!job) return;
    setActionLoading(true);
    setStatusError('');
    try {
      await resumeNotesJob(materialId, job.job_id);
      await fetchJobStatus();
      startPolling();
    } catch (error) {
      setStatusError(error.message || 'Failed to resume notes generation.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetrySection = async (section) => {
    if (!job) return;
    setStatusError('');
    try {
      await retryNotesSection(materialId, job.job_id, {
        section_id: section.id,
        topic_id: section.topic_id
      });
      await fetchJobStatus();
      startPolling();
    } catch (error) {
      setStatusError(error.message || 'Failed to retry this section.');
    }
  };

  const handleAnalyzeReferenceStyle = async () => {
    if (!selectedReferenceDocumentId) return;
    setAnalyzingStyle(true);
    setStyleError('');
    try {
      const profile = await analyzeReferenceStyle(materialId, selectedReferenceDocumentId);
      setStyleProfiles((current) => [
        profile,
        ...current.filter((item) => String(item.id) !== String(profile.id))
      ]);
      setSelectedStyleProfileId(String(profile.id));
      setSelectedReferenceDocumentId('');
    } catch (error) {
      setStyleError(error.message || 'Could not analyze the reference document style.');
    } finally {
      setAnalyzingStyle(false);
    }
  };

  const sections = job?.sections || [];
  const selectedSection = sections.find((section) => section.id === selectedSectionId) || sections[0] || null;
  const totalSections = sections.length;
  const verifiedCount = sections.filter((s) => s.status === 'VERIFIED').length;
  const needsRepairCount = sections.filter((s) => s.status === 'NEEDS_REPAIR' || s.status === 'BLOCKED').length;
  const totalWords = sections.reduce((acc, s) => acc + (s.word_count || 0), 0);
  const isJobActive = job && ACTIVE_JOB_STATUSES.has(job.status);
  const isJobCompleted = job && COMPLETED_JOB_STATUSES.has(job.status);

  const filteredSections = sections.filter((s) => {
    if (filter === 'VERIFIED') return s.status === 'VERIFIED';
    if (filter === 'NEEDS_REPAIR') return s.status === 'NEEDS_REPAIR' || s.status === 'BLOCKED';
    if (filter === 'IN_PROGRESS') return s.status === 'IN_PROGRESS' || s.status === 'NOT_STARTED';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Overview & Hero Panel */}
      <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Learn in syllabus order
              </span>
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                Source-mapped sections
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Complete syllabus notes
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {subject || 'Study material'}{totalPages ? ` · ${totalPages} pages` : ''}
            </p>
            <p className="text-slate-400 text-sm max-w-2xl mt-1.5 leading-relaxed">
              Generate notes for every mapped section in <span className="text-slate-200">{title}</span>. For a single-topic deep dive, choose a topic in the Teach tab.
              Examples, formulas, and diagrams are included when supported or clearly marked as additional context.
              Formatting checks do not prove factual accuracy.
            </p>
          </div>

          {/* Action Trigger Buttons */}
          <div className="flex items-center gap-3 flex-wrap">
            {!job ? (
              <button
                onClick={() => handleStartGeneration(false)}
                disabled={actionLoading}
                className="flex items-center gap-2 px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors disabled:opacity-50"
              >
                <Sparkles size={18} />
                <span>Generate complete notes</span>
              </button>
            ) : isJobActive ? (
              <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-950/60 border border-indigo-500/40 text-indigo-300 text-sm font-medium">
                <RefreshCw size={16} className="animate-spin text-cyan-400" />
                <span>Generating Section by Section...</span>
              </div>
            ) : isJobCompleted ? (
              <div className="flex items-center gap-2 flex-wrap">
                <a
                  href={getNotesDocxExportUrl(materialId, job.job_id)}
                  download
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-sm font-semibold transition-all shadow-md"
                >
                  <FileText size={16} className="text-blue-400" />
                  <span>Download Word (.docx)</span>
                </a>
                <a
                  href={getNotesPdfExportUrl(materialId, job.job_id)}
                  download
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-sm font-semibold transition-all shadow-md"
                >
                  <Download size={16} className="text-rose-400" />
                  <span>Download PDF (.pdf)</span>
                </a>
                <button
                  onClick={() => handleStartGeneration(true)}
                  disabled={actionLoading}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs transition-colors"
                  title="Regenerate all sections from scratch"
                >
                  <RotateCcw size={14} />
                  <span>Regenerate</span>
                </button>
              </div>
            ) : (
              <button
                onClick={handleResumeJob}
                disabled={actionLoading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-sm shadow-md transition-all"
              >
                <Play size={16} />
                <span>Resume Notes Generation</span>
              </button>
            )}
          </div>
        </div>

        {statusError && (
          <div role="alert" className="rounded-xl border border-rose-500/30 bg-rose-950/30 px-4 py-3 text-sm text-rose-200">
            {statusError}
          </div>
        )}
        {loading && !job && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-5 text-sm text-slate-400">
            Checking for existing topic notes...
          </div>
        )}

        {/* Live Progress Bar & Status Callout */}
        {job && (
          <div className="mt-6 pt-6 border-t border-slate-800/80">
            <div className="flex items-center justify-between text-xs font-medium text-slate-400 mb-2">
              <span className="flex items-center gap-2 text-slate-300">
                {isJobActive && <RefreshCw size={13} className="animate-spin text-cyan-400" />}
                {isJobCompleted && <CheckCircle2 size={13} className="text-emerald-400" />}
                {job.current_step_label || 'Ready'}
              </span>
              <span className="font-mono text-indigo-300 font-bold">
                {job.progress_percent}% Complete
              </span>
            </div>
            <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 rounded-full transition-all duration-300"
                style={{ width: `${Math.max(job.progress_percent, 2)}%` }}
              />
            </div>

            {/* Quick Metrics Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <div className="text-[11px] text-slate-400 uppercase font-semibold">Planned Sections</div>
                  <div className="text-lg font-bold text-white font-mono mt-0.5">{totalSections}</div>
                </div>
                <Layers size={18} className="text-indigo-400" />
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <div className="text-[11px] text-emerald-400 uppercase font-semibold">Checks passed</div>
                  <div className="text-lg font-bold text-emerald-300 font-mono mt-0.5">{verifiedCount}</div>
                </div>
                <CheckCircle2 size={18} className="text-emerald-400" />
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <div className="text-[11px] text-amber-400 uppercase font-semibold">Needs review</div>
                  <div className="text-lg font-bold text-amber-300 font-mono mt-0.5">{needsRepairCount}</div>
                </div>
                <AlertTriangle size={18} className="text-amber-400" />
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <div className="text-[11px] text-cyan-400 uppercase font-semibold">Volume (Words)</div>
                  <div className="text-lg font-bold text-cyan-300 font-mono mt-0.5">
                    {totalWords.toLocaleString()}
                  </div>
                </div>
                <BookOpen size={18} className="text-cyan-400" />
              </div>
            </div>
          </div>
        )}
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4" aria-labelledby="reference-style-heading">
        <div>
          <h3 id="reference-style-heading" className="text-sm font-bold text-white">Optional presentation reference</h3>
          <p className="mt-1 text-xs leading-relaxed text-slate-400">
            Analyze another uploaded document for structure and formatting patterns only. Its facts and examples are never used as study evidence.
          </p>
        </div>
        <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
          <label className="space-y-1.5 text-xs text-slate-400">
            <span>Use an analyzed style</span>
            <select
              value={selectedStyleProfileId}
              onChange={(event) => setSelectedStyleProfileId(event.target.value)}
              disabled={isJobActive}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 disabled:opacity-50"
            >
              <option value="">Default StudyAI style</option>
              {styleProfiles.map((profile) => (
                <option key={profile.id} value={profile.id}>{profile.label}</option>
              ))}
            </select>
          </label>
          <label className="space-y-1.5 text-xs text-slate-400">
            <span>Analyze another uploaded document</span>
            <select
              value={selectedReferenceDocumentId}
              onChange={(event) => setSelectedReferenceDocumentId(event.target.value)}
              disabled={isJobActive || analyzingStyle}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 disabled:opacity-50"
            >
              <option value="">Choose a reference document</option>
              {referenceDocuments.map((document) => (
                <option key={document.id} value={document.id}>{document.title || `Document ${document.id}`}</option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={handleAnalyzeReferenceStyle}
            disabled={!selectedReferenceDocumentId || analyzingStyle || isJobActive}
            className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-4 py-2 text-sm font-semibold text-indigo-200 hover:bg-indigo-500/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {analyzingStyle ? 'Analyzing…' : 'Analyze style'}
          </button>
        </div>
        {referenceDocuments.length === 0 && (
          <p className="text-xs text-slate-500">Upload a separate reference document to create a style profile.</p>
        )}
        {styleError && <p role="alert" className="text-xs text-rose-300">{styleError}</p>}
      </section>

      {/* Main Checklist & Sections Viewer */}
      {job && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Syllabus Checklist Manifest */}
          <div className="lg:col-span-5 space-y-4">
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Hash size={16} className="text-indigo-400" />
                  <span>Syllabus Coverage Checklist</span>
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  {verifiedCount}/{totalSections} done
                </span>
              </div>

              {/* Status Filters */}
              <div className="flex items-center gap-1.5 pb-2 mb-2 border-b border-slate-800 text-xs overflow-x-auto scrollbar-none">
                <button
                  onClick={() => setFilter('ALL')}
                  className={`px-2.5 py-1 rounded-lg transition-colors font-medium ${
                    filter === 'ALL'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800/60 hover:bg-slate-800 text-slate-400'
                  }`}
                >
                  All ({totalSections})
                </button>
                <button
                  onClick={() => setFilter('VERIFIED')}
                  className={`px-2.5 py-1 rounded-lg transition-colors font-medium ${
                    filter === 'VERIFIED'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-800/60 hover:bg-slate-800 text-slate-400'
                  }`}
                >
                  Verified ({verifiedCount})
                </button>
                {needsRepairCount > 0 && (
                  <button
                    onClick={() => setFilter('NEEDS_REPAIR')}
                    className={`px-2.5 py-1 rounded-lg transition-colors font-medium ${
                      filter === 'NEEDS_REPAIR'
                        ? 'bg-amber-600 text-white'
                        : 'bg-slate-800/60 hover:bg-slate-800 text-slate-400'
                    }`}
                  >
                    Repairs ({needsRepairCount})
                  </button>
                )}
              </div>

              {/* Checklist Items */}
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {filteredSections.map((sec, idx) => {
                  const isSelected = selectedSection?.id === sec.id;
                  const isVerified = sec.status === 'VERIFIED';
                  const isNeedsRepair = sec.status === 'NEEDS_REPAIR' || sec.status === 'BLOCKED';
                  const isInProgress = sec.status === 'IN_PROGRESS';

                  return (
                    <div
                      key={sec.id || idx}
                      onClick={() => setSelectedSectionId(sec.id)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-indigo-950/40 border-indigo-500 shadow-md shadow-indigo-500/10'
                          : 'bg-slate-950/40 hover:bg-slate-800/50 border-slate-800/80'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2.5 min-w-0">
                          <div className="mt-0.5 shrink-0">
                            {isVerified && <CheckCircle2 size={16} className="text-emerald-400" />}
                            {isNeedsRepair && <AlertTriangle size={16} className="text-amber-400" />}
                            {isInProgress && <RefreshCw size={15} className="animate-spin text-cyan-400" />}
                            {sec.status === 'NOT_STARTED' && <Clock size={16} className="text-slate-500" />}
                          </div>
                          <div className="min-w-0">
                            <div className="text-[11px] font-semibold text-slate-400 truncate">
                              {sec.module_name}
                            </div>
                            <h4 className="text-sm font-semibold text-slate-200 line-clamp-1">
                              {sec.topic_name}
                            </h4>
                            {sec.subtopic_name && (
                              <p className="text-xs text-slate-400 line-clamp-1 mt-0.5">
                                {sec.subtopic_name}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="text-right shrink-0">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              isVerified
                                ? 'bg-emerald-950/80 border border-emerald-500/40 text-emerald-300'
                                : isNeedsRepair
                                ? 'bg-amber-950/80 border border-amber-500/40 text-amber-300'
                                : isInProgress
                                ? 'bg-cyan-950/80 border border-cyan-500/40 text-cyan-300'
                                : 'bg-slate-900 border border-slate-800 text-slate-400'
                            }`}
                          >
                            {isVerified ? 'CHECKS PASSED' : sec.status.replaceAll('_', ' ')}
                          </span>
                          {sec.word_count > 0 && (
                            <div className="text-[10px] text-slate-400 font-mono mt-1">
                              {sec.word_count} w
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Defects Callout & Targeted Repair Button */}
                      {isNeedsRepair && (
                        <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                          <span className="text-amber-400 text-[11px]">
                            {sec.verification_defects?.length || 1} defect(s) detected
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRetrySection(sec);
                            }}
                            className="px-2 py-0.5 rounded-md bg-amber-600/80 hover:bg-amber-600 text-white font-medium text-[11px] transition-colors"
                          >
                            Repair Now
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Section Content Reader */}
          <div className="lg:col-span-7 space-y-4">
            <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800 shadow-xl min-h-[500px]">
              {selectedSection ? (
                <div>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-800">
                    <div>
                      <div className="text-xs font-semibold text-indigo-400">
                        {selectedSection.module_name}
                      </div>
                      <h3 className="text-xl font-bold text-white tracking-tight">
                        {selectedSection.topic_name}
                      </h3>
                      {selectedSection.subtopic_name && (
                        <p className="text-sm text-slate-400 mt-0.5">
                          {selectedSection.subtopic_name}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {selectedSection.status === 'VERIFIED' ? (
                        <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 text-xs font-semibold">
                          <CheckCircle2 size={14} />
                          <span>Checks passed ({selectedSection.word_count} words)</span>
                        </span>
                      ) : (
                        <button
                          onClick={() => handleRetrySection(selectedSection)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition-colors"
                        >
                          <RotateCcw size={13} />
                          <span>Trigger Targeted Repair</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Defects Audit Details */}
                  <p className="mb-4 text-xs leading-relaxed text-slate-400">
                    These automated checks cover structure, length, and math formatting; they do not independently confirm factual accuracy.
                  </p>
                  {selectedSection.verification_defects && selectedSection.verification_defects.length > 0 && (
                    <div className="mb-4 p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-300 text-xs space-y-1">
                      <div className="font-bold flex items-center gap-1.5">
                        <AlertTriangle size={14} />
                        <span>Quality Defects Identified:</span>
                      </div>
                      <ul className="list-disc list-inside space-y-0.5 text-amber-200/90 pl-1">
                        {selectedSection.verification_defects.map((def, i) => (
                          <li key={i}>{def}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Markdown Notes Content */}
                  {selectedSection.content_markdown ? (
                    <StudyMarkdown content={selectedSection.content_markdown} />
                  ) : (
                    <div className="py-16 text-center text-slate-500 space-y-3">
                      <Clock size={32} className="mx-auto text-slate-600" />
                      <p className="text-sm">This section is scheduled for generation.</p>
                      {job.status === 'IN_PROGRESS' && (
                        <p className="text-xs text-indigo-400">Synthesizing in queue...</p>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-24 text-center text-slate-400 space-y-3">
                  <BookOpen size={40} className="mx-auto text-slate-600" />
                  <h4 className="text-base font-bold text-slate-200">Select a section to inspect</h4>
                  <p className="text-sm max-w-sm mx-auto text-slate-500">
                    Click any topic from the syllabus checklist on the left to read its verified notes, mathematical derivations, and defect reports.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
