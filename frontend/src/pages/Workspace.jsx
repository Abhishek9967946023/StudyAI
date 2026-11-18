/**
 * =============================================================================
 * StudyAI — Unified Study Workspace (Obsidian Dark Glass Architecture)
 * =============================================================================
 * Central experience anchored around the user's currently active document.
 * 
 * Features:
 * - Active Document Hub: Title, Subject, Language, Page count, Status
 * - Unified Navigation Bar: Summary, Topics, Exam, Question Bank, Analytics, Revision, Copilot
 * - Topic Intelligence Cards: Topic name, Importance, Student performance, Priority, Source pages
 * - Next Best Action Engine: Automatically identifies highest-priority item with estimated time
 * - Integrated 5-Question Adaptive Practice Loop modal
 * - Embedded Grounded Copilot Drawer trigger
 * =============================================================================
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams, useParams, Link } from 'react-router-dom';
import { 
  Compass, 
  Layers, 
  Sparkles, 
  BookOpen, 
  Crosshair, 
  GraduationCap, 
  HelpCircle, 
  BarChart3, 
  RotateCcw, 
  Award, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  ExternalLink, 
  FileText, 
  Check, 
  RefreshCw,
  Trophy,
  Filter
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Modal } from '../components/ui/Modal';
import { ProgressRing } from '../components/ui/ProgressRing';
import { Skeleton } from '../components/ui/Skeleton';
import { CopilotPanel } from '../components/copilot/CopilotPanel';

import { 
  getMaterials, 
  getActiveMaterialId, 
  setActiveMaterialId, 
  getMaterialAnalysis, 
  getMaterialStatus 
} from '../services/materialsService';
import { getTopicIntelligence } from '../services/topicsService';
import { getRevisionPlan } from '../services/revisionService';
import { generateAdaptivePractice, submitAdaptivePractice } from '../services/adaptiveService';

export function Workspace() {
  const navigate = useNavigate();
  const { materialId: routeMatId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeId = routeMatId || searchParams.get('id') || getActiveMaterialId();

  // Core Data State
  const [materials, setMaterials] = useState([]);
  const [activeDoc, setActiveDoc] = useState(null);
  const [topics, setTopics] = useState([]);
  const [revisionPlan, setRevisionPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);

  // Targeted Practice State
  const [practiceModalOpen, setPracticeModalOpen] = useState(false);
  const [activePracticeTopic, setActivePracticeTopic] = useState(null);
  const [isGeneratingPractice, setIsGeneratingPractice] = useState(false);
  const [isSubmittingPractice, setIsSubmittingPractice] = useState(false);
  const [practiceExam, setPracticeExam] = useState(null);
  const [practiceAnswers, setPracticeAnswers] = useState({});
  const [practiceResult, setPracticeResult] = useState(null);
  const [practiceError, setPracticeError] = useState(null);

  // Load Active Document and Telemetry
  useEffect(() => {
    async function loadWorkspaceData() {
      setLoading(true);
      try {
        const [allMats, analysis, topicList, revPlan] = await Promise.all([
          getMaterials().catch(() => []),
          getMaterialAnalysis(activeId).catch(() => null),
          getTopicIntelligence(activeId).catch(() => []),
          getRevisionPlan(activeId).catch(() => null)
        ]);

        setMaterials(Array.isArray(allMats) ? allMats : []);

        const docData = analysis || (allMats?.length > 0 ? allMats.find(m => String(m.id) === String(activeId)) || allMats[0] : null);
        setActiveDoc(docData);
        setTopics(Array.isArray(topicList) ? topicList : []);
        setRevisionPlan(revPlan);

        if (docData?.id) {
          setActiveMaterialId(String(docData.id));
        }
      } catch (err) {
        console.error('Failed to load workspace data:', err);
      } finally {
        setLoading(false);
      }
    }

    loadWorkspaceData();
  }, [activeId]);

  // Switch Active Document
  const handleSwitchDocument = (newId) => {
    setActiveMaterialId(String(newId));
    setSearchParams({ id: String(newId) });
  };

  // Next Best Action Engine: Automatically identify the highest-priority action
  const nextBestAction = useMemo(() => {
    const measuredTopics = (topics || []).filter((topic) => Number.isFinite(topic.performance));
    if (measuredTopics.length === 0) return null;

    // Prioritize topics with highest severity in 4-Quadrant Matrix:
    // Highest Material Importance + Lowest Student Performance
    const sorted = [...measuredTopics].sort((a, b) => {
      const aPriority = (a.priority || a.category?.label || '').toUpperCase();
      const bPriority = (b.priority || b.category?.label || '').toUpperCase();

      if (aPriority === 'CRITICAL' && bPriority !== 'CRITICAL') return -1;
      if (bPriority === 'CRITICAL' && aPriority !== 'CRITICAL') return 1;

      const aWeight = Number.isFinite(a.importance) ? Math.max(0, a.importance) / 100 : 1;
      const bWeight = Number.isFinite(b.importance) ? Math.max(0, b.importance) / 100 : 1;
      const aDeficit = aWeight * (100 - a.performance);
      const bDeficit = bWeight * (100 - b.performance);
      return bDeficit - aDeficit;
    });

    const topTopic = sorted[0];
    if (!topTopic) return null;

    const importance = Number.isFinite(topTopic.importance) ? topTopic.importance : null;
    const performance = topTopic.performance;
    const isWeak = performance < 60;

    let reason = '';
    if (importance !== null && importance >= 60 && isWeak) {
      reason = 'High importance + low performance';
    } else if (isWeak) {
      reason = 'Recorded topic performance is below 60%';
    } else {
      reason = 'Lowest recorded performance among assessed topics';
    }

    return {
      topic: topTopic.name || topTopic.topic,
      importance,
      performance,
      priority: topTopic.priority || (importance !== null && importance >= 60 && isWeak ? 'CRITICAL' : 'PRACTICE'),
      sourcePages: topTopic.source_pages || topTopic.source_reference || (topTopic.source_page ? `Page ${topTopic.source_page}` : 'Evidence location unavailable'),
      reason
    };
  }, [topics]);

  // Handle Practice Initiation
  const handleStartPractice = async (topicItem) => {
    const topicName = topicItem.name || topicItem.topic;
    const importance = topicItem.importance ?? 90;
    const performance = topicItem.performance ?? 35;
    const priority = topicItem.priority || (importance >= 60 && performance < 60 ? 'CRITICAL' : 'PRACTICE');

    setActivePracticeTopic({
      topic: topicName,
      importance,
      performance,
      priority
    });
    setPracticeModalOpen(true);
    setIsGeneratingPractice(true);
    setPracticeError(null);
    setPracticeExam(null);
    setPracticeAnswers({});
    setPracticeResult(null);

    try {
      const data = await generateAdaptivePractice({
        documentId: activeDoc?.id || activeId,
        topic: topicName,
        questionCount: 5,
        previousPerformance: performance,
        importance,
        previousPriority: priority
      });
      setPracticeExam(data);
    } catch (err) {
      console.error('Failed to generate adaptive practice:', err);
      setPracticeError('Could not generate practice questions for this topic. Please try again.');
    } finally {
      setIsGeneratingPractice(false);
    }
  };

  const handleSelectAnswer = (qKey, optVal) => {
    setPracticeAnswers(prev => ({ ...prev, [qKey]: optVal }));
  };

  const handleSubmitPractice = async () => {
    if (!practiceExam || !activePracticeTopic) return;
    setIsSubmittingPractice(true);
    setPracticeError(null);

    try {
      const submitRes = await submitAdaptivePractice({
        examId: practiceExam.id || practiceExam.exam_id,
        topic: activePracticeTopic.topic,
        answers: practiceAnswers,
        previousPerformance: activePracticeTopic.performance,
        importance: activePracticeTopic.importance,
        previousPriority: activePracticeTopic.priority
      });

      setPracticeResult(submitRes);

      // Real-time local state update of Topic Intelligence
      setTopics(prev => prev.map(t => {
        const tName = t.name || t.topic;
        if (tName.toLowerCase() === activePracticeTopic.topic.toLowerCase()) {
          return {
            ...t,
            performance: submitRes.newPerformance,
            priority: submitRes.newPriority,
            category: {
              ...t.category,
              label: submitRes.newPriority
            }
          };
        }
        return t;
      }));
    } catch (err) {
      console.error('Failed to submit adaptive practice:', err);
      setPracticeError('Failed to evaluate practice test. Please try again.');
    } finally {
      setIsSubmittingPractice(false);
    }
  };

  const handleClosePracticeModal = () => {
    setPracticeModalOpen(false);
    setActivePracticeTopic(null);
    setPracticeExam(null);
    setPracticeAnswers({});
    setPracticeResult(null);
    setPracticeError(null);
  };

  // Overall Document Mastery Metric
  const overallMastery = useMemo(() => {
    const measuredTopics = (topics || []).filter((topic) => Number.isFinite(topic.performance));
    if (measuredTopics.length === 0) return null;
    const sum = measuredTopics.reduce((total, topic) => total + topic.performance, 0);
    return Math.round(sum / measuredTopics.length);
  }, [topics]);

  if (loading) {
    return (
      <div style={{ maxWidth: '1180px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <Skeleton height="180px" />
        <Skeleton height="70px" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <Skeleton height="160px" />
          <Skeleton height="160px" />
          <Skeleton height="160px" />
        </div>
        <Skeleton height="320px" />
      </div>
    );
  }

  const docTitle = activeDoc?.title || 'No active study material';
  const docSubject = activeDoc?.subject || 'Not identified';
  const docLanguage = activeDoc?.language || activeDoc?.original_language?.toUpperCase() || 'Not identified';
  const docPages = activeDoc?.page_count ?? activeDoc?.pages ?? null;
  const docStatus = (activeDoc?.status || 'UNKNOWN').toUpperCase();
  const statusColor = ['READY', 'COMPLETED', 'PARTIAL'].includes(docStatus)
    ? '#1DB8A6'
    : docStatus === 'FAILED'
      ? '#F87171'
      : ['QUEUED', 'PROCESSING'].includes(docStatus)
        ? '#FBBF24'
        : '#9E9BB5';

  return (
    <div className="fade-in" style={{ maxWidth: '1180px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* =========================================================================
          1. WORKSPACE HEADER — Obsidian Glass Hero
          ========================================================================= */}
      <div 
        style={{
          background: 'radial-gradient(ellipse at 85% 15%, rgba(79, 63, 240, 0.22) 0%, rgba(13, 12, 21, 0.95) 75%)',
          borderRadius: '24px',
          padding: '30px 32px',
          border: '1px solid rgba(255, 255, 255, 0.09)',
          boxShadow: '0 20px 48px -12px rgba(0, 0, 0, 0.65)',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        {/* Subtle Ambient Backdrop Line */}
        <div style={{ position: 'absolute', top: 0, right: 0, width: '380px', height: '100%', background: 'linear-gradient(90deg, transparent, rgba(79, 63, 240, 0.08))', pointerEvents: 'none' }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '780px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <span 
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(79, 63, 240, 0.18)',
                  color: '#A89FFF',
                  padding: '4px 12px',
                  borderRadius: '999px',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                  border: '1px solid rgba(105, 91, 255, 0.35)'
                }}
              >
                <Compass size={13} /> Active Study Workspace
              </span>

              {/* Document Switcher if multiple documents exist */}
              {materials.length > 1 && (
                <select
                  value={activeDoc?.id || activeId}
                  onChange={(e) => handleSwitchDocument(e.target.value)}
                  style={{
                    background: 'rgba(21, 19, 36, 0.85)',
                    color: '#F2F0FC',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: '8px',
                    padding: '4px 10px',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  {materials.map(m => (
                    <option key={m.id} value={m.id}>
                      {m.title || `Document #${m.id}`}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Document Title */}
            <h1 style={{ fontSize: '2.15rem', fontWeight: 800, margin: 0, letterSpacing: '-0.025em', color: '#FFFFFF', lineHeight: 1.2 }}>
              {docTitle}
            </h1>

            {/* Document Metadata Badges */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', marginTop: '4px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#C4B5FD', fontSize: '0.88rem', fontWeight: 600 }}>
                <BookOpen size={15} />
                <span>Subject: <strong>{docSubject}</strong></span>
              </div>

              <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'rgba(255, 255, 255, 0.3)' }} />

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#9E9BB5', fontSize: '0.88rem' }}>
                <span>Language: <strong style={{ color: '#F2F0FC' }}>{docLanguage}</strong></span>
              </div>

              <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'rgba(255, 255, 255, 0.3)' }} />

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#9E9BB5', fontSize: '0.88rem' }}>
                <span>Page Count: <strong style={{ color: '#F2F0FC' }}>{docPages === null ? '—' : `${docPages} Pages`}</strong></span>
              </div>

              <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'rgba(255, 255, 255, 0.3)' }} />

              {/* Processing Status with Live Pulse Indicator */}
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: statusColor, boxShadow: `0 0 8px ${statusColor}` }} />
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: statusColor }}>
                  Status: {docStatus}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Mastery Progress Ring Card */}
          <div 
            style={{ 
              background: 'rgba(21, 19, 36, 0.65)', 
              borderRadius: '16px', 
              padding: '16px 20px', 
              border: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              gap: '16px'
            }}
          >
            <ProgressRing percent={overallMastery ?? 0} size={70} strokeWidth={7} color="var(--teal)" />
            <div>
              <div style={{ fontSize: '0.74rem', color: '#9E9BB5', fontWeight: 600, textTransform: 'uppercase' }}>
                Recorded Topic Performance
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFFFFF' }}>
                {overallMastery === null ? '—' : `${overallMastery}%`}
              </div>
              <span style={{ fontSize: '0.75rem', color: '#73EAD9' }}>
                {overallMastery === null ? 'Complete practice to establish a baseline' : `${topics.filter((topic) => Number.isFinite(topic.performance)).length} topics assessed`}
              </span>
            </div>
          </div>
        </div>

        {/* =========================================================================
            2. UNIFIED WORKSPACE NAVIGATION TOOLBAR
            Connects existing functionality into one central experience
            ========================================================================= */}
        <div 
          style={{
            marginTop: '26px',
            paddingTop: '20px',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '10px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={() => navigate(`/summary?id=${activeDoc?.id || activeId}`)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '7px',
                padding: '8px 14px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#FFFFFF',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <BookOpen size={15} color="#A78BFA" />
              <span>Summary</span>
            </button>

            <button
              onClick={() => navigate(`/topics?id=${activeDoc?.id || activeId}`)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '7px',
                padding: '8px 14px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#FFFFFF',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <Crosshair size={15} color="#38BDF8" />
              <span>Topics</span>
            </button>

            <button
              onClick={() => navigate(`/exam-config?id=${activeDoc?.id || activeId}`)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '7px',
                padding: '8px 14px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#FFFFFF',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <GraduationCap size={15} color="#34D399" />
              <span>Exam</span>
            </button>

            <button
              onClick={() => navigate(`/questions?id=${activeDoc?.id || activeId}`)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '7px',
                padding: '8px 14px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#FFFFFF',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <HelpCircle size={15} color="#FBBF24" />
              <span>Question Bank</span>
            </button>

            <button
              onClick={() => navigate(`/results`)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '7px',
                padding: '8px 14px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#FFFFFF',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <BarChart3 size={15} color="#F472B6" />
              <span>Analytics</span>
            </button>

            <button
              onClick={() => navigate(`/revision?id=${activeDoc?.id || activeId}`)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '7px',
                padding: '8px 14px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#FFFFFF',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <RotateCcw size={15} color="#F87171" />
              <span>Revision</span>
            </button>
          </div>

          {/* Copilot Action Trigger */}
          <button
            onClick={() => setIsCopilotOpen(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #4F3FF0 0%, #3B2FC9 100%)',
              color: '#FFFFFF',
              fontSize: '0.85rem',
              fontWeight: 700,
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(79, 63, 240, 0.35)'
            }}
          >
            <Sparkles size={15} />
            <span>Ask Copilot</span>
          </button>
        </div>
      </div>

      {/* =========================================================================
          3. NEXT BEST ACTION (Automatic Priority Recommendation Engine)
          ========================================================================= */}
      {nextBestAction && (
        <Card 
          style={{
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(21, 19, 36, 0.95) 100%)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            boxShadow: '0 12px 36px -8px rgba(229, 72, 77, 0.18)',
            padding: '24px 28px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '20px'
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: '680px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span 
                style={{
                  background: 'var(--coral)',
                  color: '#FFFFFF',
                  padding: '3px 10px',
                  borderRadius: '999px',
                  fontSize: '0.72rem',
                  fontWeight: 800,
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase'
                }}
              >
                RECOMMENDED NEXT STEP
              </span>
              <span style={{ fontSize: '0.8rem', color: '#9E9BB5', fontWeight: 600 }}>
                Based on recorded topic performance
              </span>
            </div>

            <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--ink)' }}>
              Study: <span style={{ color: 'var(--coral)' }}>"{nextBestAction.topic}"</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap', color: 'var(--muted)', fontSize: '0.88rem' }}>
              <span>Reason: <strong>{nextBestAction.reason}</strong></span>
              <span>&bull;</span>
              <span>Source: <strong>{nextBestAction.sourcePages}</strong></span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Button
              variant="secondary"
              size="md"
              icon={<RotateCcw size={15} />}
              onClick={() => handleStartPractice(nextBestAction)}
            >
              Practice Mini-Test
            </Button>

            <Button
              variant="primary"
              size="lg"
              icon={<ArrowRight size={17} />}
              iconPosition="right"
              style={{
                background: 'linear-gradient(135deg, #E5484D 0%, #D03B40 100%)',
                color: '#FFFFFF',
                boxShadow: '0 4px 16px rgba(229, 72, 77, 0.35)'
              }}
              onClick={() => navigate(`/revision?id=${activeDoc?.id || activeId}&topic=${encodeURIComponent(nextBestAction.topic)}`)}
            >
              Start Revision
            </Button>
          </div>
        </Card>
      )}
      {!nextBestAction && topics.length > 0 && (
        <Card style={{ padding: '22px 26px', border: '1px solid var(--border)' }}>
          <h3 style={{ margin: '0 0 6px', color: 'var(--ink)', fontSize: '1rem' }}>Personalized recommendations need assessment data</h3>
          <p style={{ margin: '0 0 14px', color: 'var(--muted)', fontSize: '0.88rem', lineHeight: 1.5 }}>
            Topic performance has not been recorded yet. Take a diagnostic exam to identify where practice will help most.
          </p>
          <Button
            variant="primary"
            size="sm"
            icon={<GraduationCap size={14} />}
            onClick={() => navigate(`/exam-config?id=${activeDoc?.id || activeId}`)}
          >
            Start a diagnostic exam
          </Button>
        </Card>
      )}

      {/* =========================================================================
          4. TOPIC INTELLIGENCE GRID
          For each topic displays: Topic name, Importance, Your performance, Priority, Source pages
          ========================================================================= */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Crosshair size={18} color="var(--indigo)" />
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
                Topic Intelligence Matrix
              </h2>
            </div>
            <p style={{ color: 'var(--muted)', fontSize: '0.88rem', margin: '4px 0 0 0' }}>
              Material Importance vs Student Performance with verified document grounding
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Chip label={`${topics.length} Syllabus Topics`} variant="indigo" size="sm" />
            <Button variant="ghost" size="sm" onClick={() => navigate(`/topics?id=${activeDoc?.id || activeId}`)}>
              <span>Deep Matrix</span>
              <ArrowRight size={13} />
            </Button>
          </div>
        </div>

        {/* Dynamic Topic Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '18px' }}>
          {topics.map((topicItem, idx) => {
            const topicName = topicItem.name || topicItem.topic;
            const importance = Number.isFinite(topicItem.importance) ? topicItem.importance : null;
            const performance = Number.isFinite(topicItem.performance) ? topicItem.performance : null;
            const isWeak = performance !== null && performance < 60;
            const priority = (topicItem.priority || (
              performance === null
                ? 'NOT ASSESSED'
                : importance !== null && importance >= 60 && isWeak
                  ? 'CRITICAL'
                  : performance >= 75
                    ? (importance !== null && importance >= 60 ? 'MAINTAIN' : 'LOW PRIORITY')
                    : 'PRACTICE'
            )).toUpperCase();
            const sourcePages = topicItem.source_pages || topicItem.source_reference || (topicItem.source_page ? `Page ${topicItem.source_page}` : 'Evidence location unavailable');

            const priorityColor = priority === 'CRITICAL' ? 'var(--coral)' : priority === 'MAINTAIN' ? 'var(--teal)' : 'var(--indigo)';
            const performanceColor = performance === null ? 'var(--muted)' : isWeak ? 'var(--coral)' : 'var(--teal)';
            const priorityChipVariant = priority === 'CRITICAL' ? 'coral' : priority === 'MAINTAIN' ? 'teal' : 'indigo';

            return (
              <Card 
                key={topicItem.id || idx}
                style={{
                  padding: '22px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '16px',
                  border: `1px solid ${priority === 'CRITICAL' ? 'rgba(229, 72, 77, 0.35)' : 'var(--border)'}`,
                  background: priority === 'CRITICAL' ? 'linear-gradient(135deg, rgba(254, 242, 242, 0.4) 0%, var(--surface) 100%)' : 'var(--surface)',
                  transition: 'transform 0.2s ease, box-shadow 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {/* Topic Title & Priority Badge */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px' }}>
                    <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
                      "{topicName}"
                    </h3>
                    <Chip label={priority} variant={priorityChipVariant} size="sm" />
                  </div>

                  {/* 3 Metrics Box */}
                  <div 
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(3, 1fr)',
                      gap: '8px',
                      background: 'var(--bg)',
                      padding: '12px 14px',
                      borderRadius: '12px',
                      border: '1px solid var(--border)'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                        Importance:
                      </div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--ink)', marginTop: '2px' }}>
                        {importance === null ? '—' : `${importance}%`}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.72rem', color: performanceColor, fontWeight: 600, textTransform: 'uppercase' }}>
                        Performance:
                      </div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: performanceColor, marginTop: '2px' }}>
                        {performance === null ? 'Not assessed' : `${performance}%`}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                        Priority:
                      </div>
                      <div style={{ fontSize: '1.05rem', fontWeight: 800, color: priorityColor, marginTop: '4px' }}>
                        {priority}
                      </div>
                    </div>
                  </div>

                  {/* Visual Duel Bars */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '3px' }}>
                        <span>Syllabus Importance</span>
                        <span>{importance === null ? 'Not rated' : `${importance}%`}</span>
                      </div>
                      <div style={{ height: '6px', background: 'var(--bg)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${importance ?? 0}%`, background: 'var(--indigo)', borderRadius: '3px' }} />
                      </div>
                    </div>

                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: performanceColor, marginBottom: '3px' }}>
                        <span>Your Performance</span>
                        <span>{performance === null ? 'Not assessed' : `${performance}%`}</span>
                      </div>
                      <div style={{ height: '6px', background: 'var(--bg)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${performance ?? 0}%`, background: isWeak ? 'var(--coral)' : 'var(--teal)', borderRadius: '3px' }} />
                      </div>
                    </div>
                  </div>

                  {/* Source Page Citation */}
                  <div style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '6px', fontStyle: 'italic' }}>
                    <BookOpen size={13} />
                    <span>Source: <strong>{sourcePages}</strong></span>
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div style={{ display: 'flex', gap: '8px', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
                  <Button
                    variant={isWeak ? "primary" : "secondary"}
                    size="sm"
                    style={{ flex: 1, ...(isWeak ? { background: 'var(--coral)', color: '#FFF' } : {}) }}
                    icon={<RotateCcw size={14} />}
                    onClick={() => handleStartPractice(topicItem)}
                  >
                    Practice This Topic
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(`/revision?id=${activeDoc?.id || activeId}&topic=${encodeURIComponent(topicName)}`)}
                  >
                    Review Notes
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* =========================================================================
          5. TARGETED ADAPTIVE PRACTICE MODAL
          ========================================================================= */}
      <Modal
        isOpen={practiceModalOpen}
        onClose={handleClosePracticeModal}
        title={practiceResult ? "Targeted Practice Performance Comparison" : `Adaptive Practice: ${activePracticeTopic?.topic || 'Selected Topic'}`}
        maxWidth="680px"
      >
        {isGeneratingPractice && (
          <div style={{ padding: '36px 16px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--indigo-tint)', color: 'var(--indigo)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <RefreshCw size={28} className="animate-spin" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 6px 0' }}>
                Synthesizing Targeted 5-Question Mini-Test...
              </h3>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem', margin: 0 }}>
                Retrieving active document context & citations for <strong>"{activePracticeTopic?.topic}"</strong>
              </p>
            </div>
          </div>
        )}

        {practiceError && (
          <div style={{ padding: '16px', borderRadius: '10px', background: 'var(--coral-tint)', border: '1px solid var(--coral)', color: 'var(--coral)', marginBottom: '16px', fontSize: '0.9rem' }}>
            {practiceError}
          </div>
        )}

        {!isGeneratingPractice && practiceExam && !practiceResult && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg)', padding: '12px 16px', borderRadius: '12px', border: '1px solid var(--border)' }}>
              <div>
                <span style={{ fontSize: '0.76rem', color: 'var(--muted)', fontWeight: 600 }}>TARGET TOPIC</span>
                <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--ink)' }}>{activePracticeTopic?.topic}</div>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <Chip label={`Importance: ${activePracticeTopic?.importance}%`} size="sm" />
                <Chip label={`Prior: ${activePracticeTopic?.performance}%`} variant="coral" size="sm" />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '55vh', overflowY: 'auto', paddingRight: '6px' }}>
              {(practiceExam.questions || []).map((q, qIndex) => {
                const qKey = q.id || `q-${qIndex + 1}`;
                const selectedVal = practiceAnswers[qKey];

                return (
                  <div key={qKey} style={{ padding: '16px', borderRadius: '12px', border: '1px solid var(--border)', background: 'var(--surface)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--muted)' }}>
                        Question {qIndex + 1} of {practiceExam.questions?.length || 5}
                      </span>
                      <Chip label={q.difficulty || 'Medium'} size="sm" />
                    </div>

                    <p style={{ fontWeight: 600, fontSize: '0.96rem', color: 'var(--ink)', margin: 0 }}>
                      {q.question}
                    </p>

                    {q.citation && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--muted)', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <BookOpen size={13} />
                        Source: {q.citation}
                      </div>
                    )}

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {(q.options || ['True', 'False']).map((opt, optIdx) => {
                        const isChosen = selectedVal === opt || selectedVal === optIdx;
                        return (
                          <div 
                            key={optIdx}
                            onClick={() => handleSelectAnswer(qKey, opt)}
                            style={{ 
                              padding: '10px 14px', 
                              borderRadius: '8px', 
                              border: isChosen ? '2px solid var(--indigo)' : '1px solid var(--border)',
                              background: isChosen ? 'var(--indigo-tint)' : 'var(--bg)',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              fontSize: '0.9rem',
                              color: isChosen ? 'var(--indigo)' : 'var(--ink)',
                              fontWeight: isChosen ? 600 : 400
                            }}
                          >
                            <span>{opt}</span>
                            {isChosen && <Check size={16} color="var(--indigo)" />}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                {Object.keys(practiceAnswers).length} of {practiceExam.questions?.length || 5} answered
              </span>
              <div style={{ display: 'flex', gap: '10px' }}>
                <Button variant="ghost" size="md" onClick={handleClosePracticeModal}>
                  Cancel
                </Button>
                <Button 
                  variant="primary" 
                  size="md"
                  onClick={handleSubmitPractice}
                  disabled={isSubmittingPractice}
                  icon={isSubmittingPractice ? <RefreshCw size={15} className="animate-spin" /> : <CheckCircle2 size={15} />}
                >
                  {isSubmittingPractice ? 'Grading Test...' : 'Submit Practice Test'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* AFTER PRACTICE: Diagnostic Comparison */}
        {practiceResult && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ padding: '16px 20px', borderRadius: '12px', background: 'var(--teal-tint)', border: '1px solid var(--teal)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Trophy size={20} color="var(--teal)" />
              <div>
                <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--teal-text)' }}>
                  Targeted Practice Complete!
                </h4>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--muted)', marginTop: '2px' }}>
                  {practiceResult.feedbackText}
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
              <Card style={{ padding: '14px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Previous Performance:
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--coral)', marginTop: '4px' }}>
                  {practiceResult.previousPerformance}%
                </div>
              </Card>

              <Card style={{ padding: '14px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  New Performance:
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--teal)', marginTop: '4px' }}>
                  {practiceResult.newPerformance}%
                </div>
              </Card>

              <Card style={{ padding: '14px', textAlign: 'center', background: 'var(--teal-tint)', borderColor: 'var(--teal)' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--teal-text)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Improvement:
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--teal)', marginTop: '4px' }}>
                  {practiceResult.improvement >= 0 ? `+${practiceResult.improvement}%` : `${practiceResult.improvement}%`}
                </div>
              </Card>
            </div>

            <Card style={{ padding: '16px 20px', background: 'var(--bg)', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '10px' }}>
                Priority Recalculation
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Importance:</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{practiceResult.importance}%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Performance:</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--teal)' }}>{practiceResult.newPerformance}%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '4px' }}>Priority:</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Chip label={`Before: ${practiceResult.previousPriority}`} variant="coral" size="sm" />
                    <ArrowRight size={12} color="var(--muted)" />
                    <Chip label={`After: ${practiceResult.newPriority}`} variant={practiceResult.newPriority === 'MAINTAIN' ? 'teal' : 'indigo'} size="sm" />
                  </div>
                </div>
              </div>
            </Card>

            <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
              <Button variant="primary" size="md" icon={<CheckCircle2 size={16} />} onClick={handleClosePracticeModal}>
                Apply to Workspace
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Embedded Study Copilot Drawer */}
      <CopilotPanel 
        isOpen={isCopilotOpen} 
        onClose={() => setIsCopilotOpen(false)} 
        materialId={activeDoc?.id || activeId} 
      />
    </div>
  );
}

export default Workspace;
