/**
 * =============================================================================
 * StudyAI — Central Dashboard Command Center
 * =============================================================================
 * Hub for the 5 Core Pillars:
 * 1. Upload Materials (with instant ChatGPT-style summary)
 * 2. My Summaries (Old Chats & Historical Summaries)
 * 3. Generate Exam (Distraction-free custom tests)
 * 4. Result (Detailed diagnostics & answer reviews)
 * 5. Revision (3D Flip flashcards & targeted drills)
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  UploadCloud,
  GraduationCap,
  Award,
  ArrowRight,
  AlertTriangle,
  BookOpen,
  Clock,
  CheckCircle2,
  FileText,
  Play,
  RotateCcw,
  MessageSquare,
  TrendingUp,
  Layers,
  ChevronRight,
  ShieldCheck,
  Check
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { ProgressRing } from '../components/ui/ProgressRing';
import { TrendBars } from '../components/charts/TrendBars';
import { getMaterials } from '../services/materialsService';
import { getHistory } from '../services/historyService';
import { getTopicIntelligence } from '../services/topicsService';
import { useAuth } from '../hooks/useAuth';

export function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [materials, setMaterials] = useState([]);
  const [history, setHistory] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadErrors, setLoadErrors] = useState([]);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboardData() {
      const results = await Promise.allSettled([
        getMaterials(),
        getHistory(),
        getTopicIntelligence()
      ]);
      if (cancelled) return;

      const [materialsResult, historyResult, topicsResult] = results;
      const isList = (result) => result.status === 'fulfilled' && Array.isArray(result.value);
      const sources = [
        ['study materials', materialsResult],
        ['exam history', historyResult],
        ['topic assessment', topicsResult]
      ];
      const failedSources = sources
        .filter(([, result]) => !isList(result))
        .map(([source, result]) => {
          if (result.status === 'rejected') {
            console.error(`Failed to load dashboard ${source}:`, result.reason);
          } else {
            console.error(`Dashboard ${source} response was not a list.`);
          }
          return source;
        });

      setMaterials(isList(materialsResult) ? materialsResult.value : []);
      setHistory(isList(historyResult) ? historyResult.value : []);
      setTopics(isList(topicsResult) ? topicsResult.value : []);
      setLoadErrors(failedSources);
      setLoading(false);
    }

    loadDashboardData();
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const materialsUnavailable = loadErrors.includes('study materials');
  const historyUnavailable = loadErrors.includes('exam history');
  const topicsUnavailable = loadErrors.includes('topic assessment');
  const activeMaterial = !materialsUnavailable && materials.length > 0 ? materials[0] : null;
  const activeTitle = activeMaterial?.title || 'No Material Selected';
  const activeSubject = activeMaterial?.subject || 'Curriculum';
  const assessedTopics = (topics || []).filter(t => Number.isFinite(t.performance));
  const weakTopics = assessedTopics.filter(t => t.performance < 60);
  const validScores = history.map((attempt) => attempt.scorePercent).filter(Number.isFinite);
  const avgScore = validScores.length
    ? Math.round(validScores.reduce((total, score) => total + score, 0) / validScores.length)
    : null;

  const latestAttempt = history[0] || null;

  const displayName = user?.name || user?.email?.split('@')[0] || localStorage.getItem('studyai_user_name') || 'Student';

  const [profile] = useState(() => {
    try {
      const s = localStorage.getItem('studyai_profile');
      return s ? JSON.parse(s) : { targetScore: 80 };
    } catch {
      return { targetScore: 80 };
    }
  });

  if (loading) {
    return (
      <div
        className="sa-card"
        role="status"
        aria-live="polite"
        aria-busy="true"
        style={{ padding: '2rem', color: 'var(--muted)' }}
      >
        Loading your study dashboard...
      </div>
    );
  }

  // The 5 Core Modules
  const coreModules = [
    {
      step: 'Step 1',
      title: '1. Upload Materials',
      desc: 'Upload notes, PDFs, or paste text to receive an immediate comprehensive ChatGPT-style summary.',
      icon: <UploadCloud size={22} />,
      bg: 'linear-gradient(135deg, #4F3FF0, #6366F1)',
      to: '/upload',
      cta: 'Upload & Summarize'
    },
    {
      step: 'Step 2',
      title: '2. My Summaries',
      desc: 'Browse saved document notes, read past ChatGPT summaries, and continue interactive AI conversations.',
      icon: <BookOpen size={22} />,
      bg: 'linear-gradient(135deg, #0B7F72, #10B981)',
      to: '/my-summaries',
      cta: 'View Library & Chats'
    },
    {
      step: 'Step 3',
      title: '3. Generate Exam',
      desc: 'Create tailored practice tests (MCQs, mixed, short answer) with customizable difficulty and timers.',
      icon: <GraduationCap size={22} />,
      bg: 'linear-gradient(135deg, #8B5CF6, #A855F7)',
      to: '/generate-exam',
      cta: 'Configure Exam'
    },
    {
      step: 'Step 4',
      title: '4. Result & Analytics',
      desc: 'Inspect detailed scores, topic-by-topic diagnostics, and question reviews with verified citations.',
      icon: <Award size={22} />,
      bg: 'linear-gradient(135deg, #E5484D, #F43F5E)',
      to: '/results',
      cta: 'View Diagnostics'
    },
    {
      step: 'Step 5',
      title: '5. Smart Revision',
      desc: 'Flip 3D interactive flashcards and practice weak-topic recall drills calibrated from your tests.',
      icon: <RotateCcw size={22} />,
      bg: 'linear-gradient(135deg, #F59E0B, #D97706)',
      to: '/revision',
      cta: 'Start 3D Flashcards'
    }
  ];

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {loadErrors.length > 0 && (
        <div
          role="alert"
          className="sa-card"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
            borderColor: 'var(--coral)',
            color: 'var(--coral-text)'
          }}
        >
          <p>
            Could not load {loadErrors.join(', ')}. Affected dashboard sections are marked unavailable.
          </p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setLoading(true);
              setReloadToken((token) => token + 1);
            }}
          >
            Retry
          </Button>
        </div>
      )}

      {/* 1. Hero Welcome Banner */}
      <section className="welcome" style={{
        background: 'linear-gradient(135deg, #5140a8, #7655dc)',
        color: 'white',
        borderRadius: '20px',
        padding: '32px 36px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '20px',
        boxShadow: 'var(--shadow-md)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="eyebrow" style={{ color: '#E2DCFF', fontWeight: 700, letterSpacing: '1.5px', fontSize: '0.74rem' }}>
              ACADEMIC INTELLIGENCE SUITE
            </span>
          </div>
          <h2 style={{ fontSize: '1.95rem', fontWeight: 700, margin: '6px 0 10px 0', lineHeight: 1.2 }}>
            Welcome back, {displayName}! 👋
          </h2>
          <p style={{ maxWidth: '640px', fontSize: '0.96rem', opacity: 0.95, margin: 0, lineHeight: 1.55 }}>
            Transform your study materials into structured intelligence, grounded exam questions, and flashcards.
          </p>

          <div style={{ display: 'flex', gap: '12px', marginTop: '20px', flexWrap: 'wrap' }}>
            <Button
              variant="secondary"
              size="md"
              icon={<UploadCloud size={16} />}
              onClick={() => navigate('/upload')}
              style={{ backgroundColor: '#FFFFFF', color: '#5140a8', border: 'none', fontWeight: 700 }}
            >
              Upload Material & Summarize
            </Button>
            <Button
              variant="secondary"
              size="md"
              icon={<Play size={16} />}
              onClick={() => navigate('/generate-exam')}
              style={{ backgroundColor: 'rgba(255, 255, 255, 0.18)', color: '#FFFFFF', border: 'none' }}
            >
              Start Practice Exam
            </Button>
          </div>
        </div>

        {/* Academic Mastery Mini Badge */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.12)',
          backdropFilter: 'blur(10px)',
          padding: '20px 24px',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '8px',
          minWidth: '150px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#FFD166', fontSize: '1.25rem', fontWeight: 800 }}>
            <Award size={24} />
            <span>{avgScore === null ? '—' : `${avgScore}%`}</span>
          </div>
          <span style={{ fontSize: '0.8rem', opacity: 0.85 }}>Average Exam Score</span>
          <div style={{ fontSize: '0.76rem', color: '#E2DCFF', fontWeight: 600 }}>
            Target: {profile?.targetScore || 80}%
          </div>
        </div>
      </section>

      {/* 2. The 5 Core Modules Hub */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
              Core Learning Modules
            </h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.88rem', margin: '2px 0 0 0' }}>
              Select any pillar below to upload, read summaries, test yourself, or revise.
            </p>
          </div>

        </div>

        <div className="modules-5-grid">
          {coreModules.map((mod, idx) => (
            <div
              key={idx}
              onClick={() => navigate(mod.to)}
              className="module-card"
            >
              <span className="module-card-step-badge">{mod.step}</span>
              <div>
                <div className="module-card-icon" style={{ background: mod.bg }}>
                  {mod.icon}
                </div>
                <h3 className="module-card-title">{mod.title}</h3>
                <p className="module-card-desc">{mod.desc}</p>
              </div>

              <div className="module-card-footer">
                <span>{mod.cta}</span>
                <ArrowRight size={14} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Active Study Material & Instant Actions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {/* Active Document Card or Empty State */}
        <Card style={{ padding: '24px 26px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          {materialsUnavailable ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--coral)', marginBottom: '12px' }}>
                <AlertTriangle size={18} />
                <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Study Materials Unavailable
                </span>
              </div>
              <p style={{ color: 'var(--muted)', fontSize: '0.88rem', lineHeight: 1.5 }}>
                The material list could not be loaded. Retry the dashboard before assuming your library is empty.
              </p>
            </div>
          ) : activeMaterial ? (
            <>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--indigo)' }}>
                    <FileText size={18} />
                    <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Active Study Material
                    </span>
                  </div>
                  <Chip variant="indigo">{activeSubject}</Chip>
                </div>

                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--ink)', margin: '0 0 8px 0', lineHeight: 1.3 }}>
                  {activeTitle}
                </h3>

                <p style={{ color: 'var(--muted)', fontSize: '0.88rem', margin: '0 0 16px 0', lineHeight: 1.5 }}>
                  Open the workspace to review the extracted topics and source evidence before you study or generate an exam.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<BookOpen size={14} />}
                  onClick={() => navigate(`/my-summaries?id=${activeMaterial.id}`)}
                >
                  AI Summary
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  icon={<GraduationCap size={14} />}
                  onClick={() => navigate(`/generate-exam?id=${activeMaterial.id}`)}
                >
                  Generate Exam
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<RotateCcw size={14} />}
                  onClick={() => navigate('/revision')}
                >
                  Flashcards
                </Button>
              </div>
            </>
          ) : (
            <>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--muted)', marginBottom: '12px' }}>
                  <FileText size={18} />
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Get Started
                  </span>
                </div>

                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--ink)', margin: '0 0 8px 0', lineHeight: 1.3 }}>
                  No Study Materials Yet
                </h3>

                <p style={{ color: 'var(--muted)', fontSize: '0.88rem', margin: '0 0 16px 0', lineHeight: 1.5 }}>
                  Upload your first PDF lecture notes, textbook chapters, or raw text to generate comprehensive AI study guides, flashcards, and practice exams.
                </p>
              </div>

              <div style={{ paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
                <Button
                  variant="primary"
                  size="sm"
                  icon={<UploadCloud size={14} />}
                  onClick={() => navigate('/upload')}
                >
                  Upload Your First Material
                </Button>
              </div>
            </>
          )}
        </Card>

        {/* Assessment Performance & Weak Topics Diagnostic */}
        <Card style={{ padding: '24px 26px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--teal)' }}>
                <Award size={18} />
                <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Performance Overview
                </span>
              </div>
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--muted)' }}>
                {historyUnavailable ? 'Exam history unavailable' : `${history.length} Exam Attempts`}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '20px', margin: '14px 0' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--indigo)', lineHeight: 1 }}>
                  {historyUnavailable ? 'Unavailable' : avgScore === null ? '—' : `${avgScore}%`}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '4px' }}>Average Exam Score</div>
              </div>

              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--muted)' }}>Topics above practice threshold:</span>
                  <strong style={{ color: topicsUnavailable ? 'var(--muted)' : 'var(--teal)' }}>
                    {topicsUnavailable ? 'Unavailable' : assessedTopics.length ? assessedTopics.length - weakTopics.length : 'Not assessed'}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--muted)' }}>Topics Needing Practice:</span>
                  <strong style={{ color: topicsUnavailable ? 'var(--muted)' : weakTopics.length > 0 ? 'var(--coral)' : 'var(--teal)' }}>
                    {topicsUnavailable ? 'Unavailable' : assessedTopics.length ? weakTopics.length : 'Not assessed'}
                  </strong>
                </div>
              </div>
            </div>
          </div>

          <div style={{ paddingTop: '12px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
              {historyUnavailable
                ? 'Exam history could not be loaded.'
                : latestAttempt
                  ? `Latest: ${latestAttempt.scorePercent}% on ${latestAttempt.date || 'Recent'}`
                  : 'Take an exam to record your first diagnostic score.'}
            </span>
            <Button
              variant="ghost"
              size="sm"
              iconRight={<ArrowRight size={14} />}
              onClick={() => navigate('/results')}
            >
              Full Results
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default Dashboard;
