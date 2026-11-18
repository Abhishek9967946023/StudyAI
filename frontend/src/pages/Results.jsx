/**
 * =============================================================================
 * StudyAI — Results Screen (Screen 8)
 * =============================================================================
 * Features:
 * - Headline score with ProgressRing
 * - Key metrics: Correct / Incorrect / Skipped / Time
 * - Topic performance breakdown with BarList
 * - Dark AI-feedback card with actionable cognitive diagnostics
 * - Detailed question review panel with explanations
 * - Actions: "Build my revision plan", "Review my answers", "Retake weak topics"
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useParams, Link } from 'react-router-dom';
import { 
  Trophy, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  HelpCircle, 
  Sparkles, 
  ArrowRight, 
  RotateCcw, 
  Eye, 
  EyeOff, 
  BookOpen, 
  ChevronRight,
  ShieldCheck,
  AlertTriangle,
  Zap,
  TrendingUp,
  Award,
  Check
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Modal } from '../components/ui/Modal';
import { ProgressRing } from '../components/ui/ProgressRing';
import { BarList } from '../components/charts/BarList';
import { StepGuide } from '../components/layout/StepGuide';
import { Skeleton } from '../components/ui/Skeleton';
import { getResult } from '../services/resultsService';
import { getExam } from '../services/examsService';
import { generateAdaptivePractice, submitAdaptivePractice } from '../services/adaptiveService';
import { setActiveMaterialId } from '../services/materialsService';

export function Results() {
  const navigate = useNavigate();
  const { resultId: routeResultId } = useParams();
  const [searchParams] = useSearchParams();
  const resultId = routeResultId || searchParams.get('id') || 'res-default';

  const [result, setResult] = useState(null);
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showReview, setShowReview] = useState(false);

  // Adaptive Learning Loop State
  const [practiceModalOpen, setPracticeModalOpen] = useState(false);
  const [activePracticeTopic, setActivePracticeTopic] = useState(null);
  const [isGeneratingPractice, setIsGeneratingPractice] = useState(false);
  const [isSubmittingPractice, setIsSubmittingPractice] = useState(false);
  const [practiceExam, setPracticeExam] = useState(null);
  const [practiceAnswers, setPracticeAnswers] = useState({});
  const [practiceResult, setPracticeResult] = useState(null);
  const [practiceError, setPracticeError] = useState(null);
  const [completedPracticeLoops, setCompletedPracticeLoops] = useState([]);

  const handleNavigateToRevision = () => {
    const docId = result?.documentId || result?.document_id || exam?.document_id || exam?.document;
    if (docId) {
      setActiveMaterialId(docId);
      navigate(`/revision?id=${docId}`);
    } else {
      navigate('/revision');
    }
  };

  const handleStartPractice = async (topicItem) => {
    const importance = topicItem.importance ?? (topicItem.scorePercent < 40 ? 94 : 85);
    const performance = topicItem.scorePercent;
    const priority = topicItem.priority ?? (performance < 60 ? (importance >= 60 ? 'CRITICAL' : 'PRACTICE') : 'MAINTAIN');

    const topicData = {
      ...topicItem,
      importance,
      priority
    };

    setActivePracticeTopic(topicData);
    setPracticeModalOpen(true);
    setIsGeneratingPractice(true);
    setPracticeError(null);
    setPracticeExam(null);
    setPracticeAnswers({});
    setPracticeResult(null);

    try {
      const data = await generateAdaptivePractice({
        documentId: result?.documentId || result?.document_id || exam?.document_id,
        topic: topicItem.topic,
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
    setPracticeAnswers(prev => ({
      ...prev,
      [qKey]: optVal
    }));
  };

  const togglePracticeOption = (qKey, optionIndex) => {
    const selected = Array.isArray(practiceAnswers[qKey]) ? practiceAnswers[qKey] : [];
    handleSelectAnswer(
      qKey,
      selected.includes(optionIndex)
        ? selected.filter(index => index !== optionIndex)
        : [...selected, optionIndex]
    );
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
        previousPerformance: activePracticeTopic.scorePercent,
        importance: activePracticeTopic.importance,
        previousPriority: activePracticeTopic.priority
      });

      setPracticeResult(submitRes);
      setCompletedPracticeLoops(prev => [submitRes, ...prev]);

      // Immediately update local topicBreakdown so results reflect new performance and priority
      setResult(prev => {
        if (!prev) return prev;
        const updatedBreakdown = (prev.topicBreakdown || []).map(tb => {
          if (tb.topic.toLowerCase() === activePracticeTopic.topic.toLowerCase()) {
            return {
              ...tb,
              scorePercent: submitRes.newPerformance,
              isWeak: submitRes.newPerformance < 60,
              importance: submitRes.importance,
              priority: submitRes.newPriority,
              correct: submitRes.correctCount,
              total: submitRes.totalQuestions
            };
          }
          return tb;
        });

        // Recalculate overall score if updated
        const newOverall = Math.round(
          updatedBreakdown.reduce((acc, t) => acc + (t.scorePercent || 0), 0) / (updatedBreakdown.length || 1)
        );

        return {
          ...prev,
          scorePercent: newOverall,
          topicBreakdown: updatedBreakdown
        };
      });
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

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const resData = await getResult(resultId);
        setResult(resData);
        if (resData.examId) {
          const exData = await getExam(resData.examId).catch(() => null);
          setExam(exData);
        } else {
          const defaultEx = await getExam('exam-default').catch(() => null);
          setExam(defaultEx);
        }
      } catch (err) {
        console.error('Error fetching result:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [resultId]);

  if (loading || !result) {
    return (
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <StepGuide currentStep={4} />
        <Skeleton height="180px" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <Skeleton height="100px" />
          <Skeleton height="100px" />
          <Skeleton height="100px" />
          <Skeleton height="100px" />
        </div>
        <Skeleton height="260px" />
      </div>
    );
  }

  const score = result.scorePercent ?? 75;
  const earnedMarks = result.marksScored ?? result.marks_scored;
  const totalMarks = result.totalMarks ?? result.total_marks;
  const isPassed = score >= 60;
  const skippedCount = result.skippedCount ?? Math.max(0, (result.totalQuestions || 8) - (result.correctCount || 6) - (result.incorrectCount || 2));

  const weakTopics = result.topicBreakdown?.filter(t => t.isWeak || t.scorePercent < 60) || [];

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* 1. Step Progression Bar */}
      <StepGuide currentStep={4} />

      {/* 2. Headline Score Hero Card */}
      <Card style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: '32px', alignItems: 'center' }}>
        <div>
          <ProgressRing 
            percent={score} 
            size={120} 
            strokeWidth={10} 
            color={score >= 70 ? 'var(--teal)' : score >= 50 ? 'var(--indigo)' : 'var(--coral)'}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <p className="eyebrow-upload" style={{ margin: 0 }}>YOUR EXAM REPORT</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h1 style={{ fontSize: '1.85rem', fontWeight: 700, margin: 0 }}>
              Exam Results 🎉
            </h1>
            <Chip 
              label={isPassed ? 'Passed' : 'Action Required'} 
              variant={isPassed ? 'teal' : 'coral'} 
              size="md" 
            />
          </div>
          <p style={{ color: 'var(--muted)', fontSize: '0.98rem', margin: 0, maxWidth: '620px', lineHeight: 1.5 }}>
            You scored <strong>{result.correctCount} out of {result.totalQuestions}</strong> questions correctly
            {Number.isFinite(earnedMarks) && Number.isFinite(totalMarks) && totalMarks > 0
              ? <> and <strong> {earnedMarks}/{totalMarks} marks</strong> ({score}% weighted score).</>
              : <> ({score}% score).</>}
            StudyAI has isolated your specific misconceptions for immediate adaptive recovery.
          </p>
          <p style={{ color: score >= 70 ? 'var(--teal-text)' : 'var(--coral-text)', fontSize: '0.92rem', fontWeight: 600, margin: '2px 0 0 0' }}>
            {score >= 80 ? '🌟 Excellent work! Keep it up.' : score >= 50 ? '👍 Good effort! Revise the topics you found difficult.' : '⚠️ Keep practising. Review your study material and try again.'}
          </p>
        </div>

        {/* Primary CTA */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', minWidth: '220px' }}>
          <Button 
            variant="primary" 
            size="lg"
            icon={<ArrowRight size={18} />}
            iconPosition="right"
            onClick={handleNavigateToRevision}
          >
            Build my revision plan
          </Button>
          <Button 
            variant="secondary" 
            size="md"
            icon={showReview ? <EyeOff size={16} /> : <Eye size={16} />}
            onClick={() => setShowReview(!showReview)}
          >
            {showReview ? 'Hide Answers' : 'Review my answers'}
          </Button>
        </div>
      </Card>

      {/* 3. Four Metric Stat Tiles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <Card style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '18px 20px' }}>
          <div style={{ width: 44, height: 44, borderRadius: '12px', background: 'var(--teal-tint)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--teal)' }}>
            <CheckCircle2 size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.82rem', color: 'var(--muted)', fontWeight: 500 }}>Correct Answers</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--ink)' }}>{result.correctCount}</div>
          </div>
        </Card>

        <Card style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '18px 20px' }}>
          <div style={{ width: 44, height: 44, borderRadius: '12px', background: 'var(--coral-tint)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--coral)' }}>
            <XCircle size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.82rem', color: 'var(--muted)', fontWeight: 500 }}>Incorrect Answers</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--ink)' }}>{result.incorrectCount}</div>
          </div>
        </Card>

        <Card style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '18px 20px' }}>
          <div style={{ width: 44, height: 44, borderRadius: '12px', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)' }}>
            <HelpCircle size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.82rem', color: 'var(--muted)', fontWeight: 500 }}>Skipped Questions</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--ink)' }}>{skippedCount}</div>
          </div>
        </Card>

        <Card style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '18px 20px' }}>
          <div style={{ width: 44, height: 44, borderRadius: '12px', background: 'var(--indigo-tint)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--indigo)' }}>
            <Clock size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.82rem', color: 'var(--muted)', fontWeight: 500 }}>Time Elapsed</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--ink)' }}>{result.timeSpent || '7m 30s'}</div>
          </div>
        </Card>
      </div>

      {/* 3.5. Completed Adaptive Learning Loop Improvements Banner */}
      {completedPracticeLoops.length > 0 && (
        <Card style={{ 
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%)',
          border: '1px solid rgba(16, 185, 129, 0.35)',
          padding: '20px 24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={20} color="var(--teal)" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>
                Adaptive Learning Progress Recorded
              </h3>
            </div>
            <Chip label="Loop Closed" variant="teal" size="sm" />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {completedPracticeLoops.map((loop, idx) => (
              <div 
                key={idx}
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  background: 'var(--surface)',
                  borderRadius: '10px',
                  border: '1px solid var(--border)',
                  flexWrap: 'wrap',
                  gap: '10px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--ink)' }}>
                    {loop.topic}
                  </span>
                  <span style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
                    {loop.previousPerformance}% → <strong style={{ color: 'var(--teal)' }}>{loop.newPerformance}%</strong>
                  </span>
                  <span style={{ 
                    color: 'var(--teal)', 
                    fontWeight: 700, 
                    fontSize: '0.9rem',
                    background: 'var(--teal-tint)',
                    padding: '2px 8px',
                    borderRadius: '6px'
                  }}>
                    {loop.improvement >= 0 ? `+${loop.improvement}%` : `${loop.improvement}%`}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>Priority Recalculation:</span>
                  <Chip label={`Before: ${loop.previousPriority}`} variant="coral" size="sm" />
                  <ArrowRight size={14} style={{ color: 'var(--muted)' }} />
                  <Chip label={`After: ${loop.newPriority}`} variant={loop.newPriority === 'MAINTAIN' ? 'teal' : 'indigo'} size="sm" />
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 3.6. Targeted Weak Topic Remediation Cards */}
      {weakTopics.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="badge badge-rose" style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <AlertTriangle size={13} /> Adaptive Learning Loop
                </span>
                <span style={{ fontSize: '0.85rem', color: 'var(--muted)', fontWeight: 600 }}>
                  Active Misconception Remediation
                </span>
              </div>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: '6px 0 0 0' }}>
                Targeted Weak Topic Practice
              </h2>
            </div>
            <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
              Short 5-question test strictly grounded in your active material
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {weakTopics.map((topicItem, i) => {
              const importance = topicItem.importance ?? (topicItem.scorePercent < 40 ? 94 : 85);
              const performance = topicItem.scorePercent;
              const priority = topicItem.priority ?? (performance < 60 ? (importance >= 60 ? 'CRITICAL' : 'PRACTICE') : 'MAINTAIN');

              return (
                <Card 
                  key={i} 
                  style={{ 
                    border: '1px solid rgba(229, 72, 77, 0.35)', 
                    background: 'linear-gradient(135deg, rgba(254, 242, 242, 0.7) 0%, var(--surface) 100%)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '16px',
                    padding: '20px'
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
                        "{topicItem.topic}"
                      </h3>
                      <Chip 
                        label={priority} 
                        variant={priority === 'CRITICAL' ? 'coral' : 'indigo'} 
                        size="md" 
                      />
                    </div>

                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: 'repeat(3, 1fr)', 
                      gap: '12px', 
                      background: 'var(--bg)', 
                      padding: '12px 14px', 
                      borderRadius: '12px',
                      border: '1px solid var(--border)'
                    }}>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Importance:
                        </div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--ink)', marginTop: '2px' }}>
                          {importance}%
                        </div>
                      </div>

                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--coral)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Performance:
                        </div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--coral)', marginTop: '2px' }}>
                          {performance}%
                        </div>
                      </div>

                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Priority:
                        </div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 800, color: priority === 'CRITICAL' ? 'var(--coral)' : 'var(--indigo)', marginTop: '4px' }}>
                          {priority}
                        </div>
                      </div>
                    </div>
                  </div>

                  <Button 
                    variant="primary" 
                    size="md"
                    icon={<RotateCcw size={16} />}
                    style={{ 
                      width: '100%', 
                      background: 'linear-gradient(135deg, #E5484D 0%, #DC2626 100%)', 
                      color: '#FFFFFF',
                      fontWeight: 700,
                      boxShadow: '0 4px 12px rgba(229, 72, 77, 0.25)'
                    }}
                    onClick={() => handleStartPractice(topicItem)}
                  >
                    Practice This Topic
                  </Button>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Main Diagnostic Grid: Dark AI Feedback & Topic Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '24px' }}>
        {/* Dark AI-Feedback Card */}
        <Card variant="dark" style={{ display: 'flex', flexDirection: 'column', gap: '18px', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} style={{ color: '#A78BFA' }} />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#C4B5FD' }}>
                  AI Cognitive Diagnostic
                </span>
              </div>
              <Chip label="Exam Evaluator" variant="indigo" size="sm" />
            </div>

            <p style={{ fontSize: '1.02rem', lineHeight: 1.6, color: '#E2E8F0', margin: '0 0 16px 0' }}>
              {result.feedbackText || 
                (result.scorePercent >= 75
                  ? "Demonstrated high competence across assessed concepts. Core syllabus principles are solidly internalized."
                  : (weakTopics.length > 0 
                      ? `Targeted revision recommended for identified knowledge gaps: ${weakTopics.map(t => t.topic).join(', ')}.`
                      : "Knowledge gaps detected in the assessed syllabus. Complete personalized revision plan to improve mastery."))}
            </p>

            {weakTopics.length > 0 && (
              <div style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', padding: '14px', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <AlertTriangle size={20} color="#F87171" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <div style={{ color: '#FCA5A5', fontWeight: 600, fontSize: '0.9rem' }}>
                    Detected Misconception Focus:
                  </div>
                  <div style={{ color: '#E2E8F0', fontSize: '0.85rem', marginTop: '4px' }}>
                    {weakTopics.map(t => t.topic).join(' • ')}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '12px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <Button 
              variant="outline" 
              size="md"
              style={{ color: '#FFFFFF', borderColor: 'rgba(255,255,255,0.2)' }}
              icon={<RotateCcw size={15} />}
              onClick={() => navigate('/exam-config?topic=Light+Reactions+%26+Photolysis')}
            >
              Retake weak topics
            </Button>
            <Button 
              variant="primary" 
              size="md"
              style={{ background: 'var(--indigo)', color: '#FFFFFF' }}
              onClick={() => navigate('/topics')}
            >
              View Topic Intelligence
            </Button>
          </div>
        </Card>

        {/* Topic Performance Breakdown Card */}
        <Card style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 600, margin: 0 }}>Topic-Wise Accuracy</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>Performance mapped against syllabus curriculum</p>
            </div>
            <Link to="/topics" style={{ fontSize: '0.85rem', color: 'var(--indigo)', textDecoration: 'none', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
              Deep Matrix <ChevronRight size={14} />
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {result.topicBreakdown?.map((topic, i) => {
              const isWeak = topic.isWeak || topic.scorePercent < 60;
              return (
                <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.9rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--ink)' }}>{topic.topic}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>
                        {topic.correct}/{topic.total} ({topic.scorePercent}%)
                        {Number.isFinite(topic.marksScored) && Number.isFinite(topic.marksTotal)
                          ? ` | ${topic.marksScored}/${topic.marksTotal} marks`
                          : ''}
                      </span>
                      <Chip 
                        label={isWeak ? 'Weak' : 'Strong'} 
                        variant={isWeak ? 'coral' : 'teal'} 
                        size="sm" 
                      />
                      {isWeak && (
                        <button
                          type="button"
                          onClick={() => handleStartPractice(topic)}
                          style={{
                            border: '1px solid var(--coral)',
                            background: 'var(--coral-tint)',
                            color: 'var(--coral)',
                            borderRadius: '6px',
                            padding: '2px 8px',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            cursor: 'pointer'
                          }}
                        >
                          Practice
                        </button>
                      )}
                    </div>
                  </div>
                  {/* Visual Bar */}
                  <div style={{ height: '8px', background: 'var(--bg)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div 
                      style={{ 
                        height: '100%', 
                        width: `${topic.scorePercent}%`, 
                        background: isWeak ? 'var(--coral)' : 'var(--teal)',
                        borderRadius: '4px',
                        transition: 'width 0.4s ease'
                      }} 
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* 5. Review Answers Section (Expandable/Toggleable) */}
      {showReview && (
        <Card style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0 }}>Comprehensive Question Review</h2>
              <p style={{ fontSize: '0.88rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                Verify rationales, mathematical formulas, and document citations for each prompt
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setShowReview(false)}>
              Close Review
            </Button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {(result.detailedQuestions && result.detailedQuestions.length > 0 ? result.detailedQuestions : (exam?.questions || [])).map((q, idx) => {
              const userAnswer = q.userAnswer !== undefined ? q.userAnswer : (result.userAnswers?.[q.id] ?? result.userAnswers?.[`q-${q.id}`]);
              const qType = (q.type || 'mcq').toLowerCase();
              const isShort = qType === 'short' || qType === 'short_answer';
              const isTF = qType === 'tf' || qType === 'true_false';
              const isMSQ = qType === 'msq';
              const questionMarks = q.marks || 1;
              const shownUserAnswer = Array.isArray(userAnswer)
                ? userAnswer.map(index => q.options?.[index] ?? index).join(', ')
                : userAnswer;
              const shownCorrectAnswer = Array.isArray(q.correctAnswer)
                ? q.correctAnswer.join(', ')
                : q.correctAnswer;
              const isCorrect = q.isCorrect !== undefined ? q.isCorrect : isMSQ
                ? Array.isArray(userAnswer)
                  && userAnswer.length === (q.correctIndices || []).length
                  && new Set(userAnswer).size === userAnswer.length
                  && (q.correctIndices || []).every(index => userAnswer.includes(index))
                : String(userAnswer || '').trim().toLowerCase()
                  === String(q.correctAnswer || '').trim().toLowerCase();

              return (
                <div 
                  key={q.id || idx}
                  style={{ 
                    padding: '18px', 
                    borderRadius: '14px', 
                    border: `1px solid ${isCorrect ? 'var(--border)' : 'rgba(229, 72, 77, 0.35)'}`,
                    background: isCorrect ? 'var(--surface)' : 'rgba(253, 236, 236, 0.4)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--muted)' }}>Q{idx + 1}.</span>
                      <Chip label={q.topic} variant="indigo" size="sm" />
                      <Chip label={q.difficulty} size="sm" />
                      <Chip label={isShort ? 'Short Answer' : isMSQ ? 'Multiple Select' : isTF ? 'True / False' : 'Multiple Choice'} variant="neutral" size="sm" />
                    </div>
                    <Chip 
                      label={isCorrect ? `Correct (+${questionMarks} marks)` : `Incorrect (0/${questionMarks} marks)`} 
                      variant={isCorrect ? 'teal' : 'coral'} 
                      size="sm" 
                    />
                  </div>

                  <p style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--ink)', margin: 0 }}>
                    {q.question}
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
                    <div style={{ padding: '10px 14px', borderRadius: '10px', background: isCorrect ? 'var(--teal-tint)' : 'var(--coral-tint)', border: `1px solid ${isCorrect ? 'var(--teal)' : 'var(--coral)'}` }}>
                      <div style={{ fontSize: '0.78rem', fontWeight: 600, color: isCorrect ? 'var(--teal-text)' : 'var(--coral-text)' }}>
                        Your Answer
                      </div>
                      <div style={{ fontWeight: 500, fontSize: '0.92rem', color: 'var(--ink)', marginTop: '2px', wordBreak: 'break-word' }}>
                        {shownUserAnswer || 'No answer provided'}
                      </div>
                    </div>

                    {!isCorrect && (
                      <div style={{ padding: '10px 14px', borderRadius: '10px', background: 'var(--teal-tint)', border: '1px solid var(--teal)' }}>
                        <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--teal-text)' }}>
                          Grounded Correct Answer
                        </div>
                        <div style={{ fontWeight: 500, fontSize: '0.92rem', color: 'var(--ink)', marginTop: '2px', wordBreak: 'break-word' }}>
                          {shownCorrectAnswer}
                        </div>
                      </div>
                    )}
                  </div>

                  {q.explanation && (
                    <div style={{ background: 'var(--bg)', borderRadius: '10px', padding: '12px 14px', fontSize: '0.88rem', color: 'var(--ink)', lineHeight: 1.5 }}>
                      <strong>AI Explanation: </strong>
                      {q.explanation}
                      {(q.citation || q.sourceReference) && (
                        <div style={{ color: 'var(--muted)', fontSize: '0.8rem', marginTop: '6px', fontStyle: 'italic' }}>
                          Source: {q.citation || q.sourceReference}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* 6. What Happens Next Guidance Footer */}
      <Card style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px', background: 'var(--surface)', border: '1px solid var(--border)' }}>
        <div>
          <div style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '0.96rem' }}>
            What happens next: Step 5 of 5
          </div>
          <div style={{ color: 'var(--muted)', fontSize: '0.88rem', marginTop: '2px' }}>
            StudyAI synthesizes your exam telemetry into a 3-step personalized recovery plan with notes and targeted mini-drills.
          </div>
        </div>
        <Button 
          variant="primary" 
          size="md"
          icon={<ArrowRight size={16} />}
          iconPosition="right"
          onClick={handleNavigateToRevision}
        >
          Proceed to Revision
        </Button>
      </Card>

      {/* 7. Adaptive Learning Loop Mini-Test Modal */}
      <Modal 
        isOpen={practiceModalOpen} 
        onClose={handleClosePracticeModal}
        title={practiceResult ? "Targeted Practice Diagnostic Comparison" : `Adaptive Practice: ${activePracticeTopic?.topic || 'Selected Topic'}`}
        maxWidth="680px"
      >
        {/* Loading State */}
        {isGeneratingPractice && (
          <div style={{ padding: '36px 16px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--indigo-tint)', color: 'var(--indigo)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <RotateCcw size={28} className="animate-spin" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 6px 0' }}>
                Synthesizing Targeted Mini-Test...
              </h3>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem', margin: 0 }}>
                Retrieving active document context & citations for <strong>"{activePracticeTopic?.topic}"</strong>
              </p>
            </div>
            <div style={{ display: 'flex', gap: '8px', fontSize: '0.8rem', color: 'var(--muted)' }}>
              <span>• 5 Questions</span>
              <span>• Document Grounded</span>
              <span>• Mixed Difficulty</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {practiceError && (
          <div style={{ padding: '16px', borderRadius: '10px', background: 'var(--coral-tint)', border: '1px solid var(--coral)', color: 'var(--coral)', marginBottom: '16px', fontSize: '0.9rem' }}>
            {practiceError}
          </div>
        )}

        {/* 5-Question Targeted Practice Test Harness */}
        {!isGeneratingPractice && practiceExam && !practiceResult && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Topic Context Pill Banner */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg)', padding: '12px 16px', borderRadius: '12px', border: '1px solid var(--border)' }}>
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--muted)', fontWeight: 600 }}>TARGET TOPIC</span>
                <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--ink)' }}>{activePracticeTopic?.topic}</div>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <Chip label={`Importance: ${activePracticeTopic?.importance || 94}%`} size="sm" />
                <Chip label={`Prior: ${activePracticeTopic?.scorePercent}%`} variant="coral" size="sm" />
                <Chip label={`Priority: ${activePracticeTopic?.priority || 'CRITICAL'}`} variant="coral" size="sm" />
              </div>
            </div>

            {/* Questions List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', maxHeight: '55vh', overflowY: 'auto', paddingRight: '6px' }}>
              {(practiceExam.questions || []).map((q, qIndex) => {
                const qKey = q.id || `q-${qIndex + 1}`;
                const selectedVal = practiceAnswers[qKey];
                const qType = String(q.type || '').toLowerCase();
                const isMSQ = qType === 'msq';
                const isTextAnswer = ['short', 'long', 'short_answer', 'long_answer'].includes(qType);
                const isFillBlank = qType === 'fill_blank';

                return (
                  <div 
                    key={qKey} 
                    style={{ 
                      padding: '16px', 
                      borderRadius: '12px', 
                      border: '1px solid var(--border)', 
                      background: 'var(--surface)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '12px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--muted)' }}>
                        Question {qIndex + 1} of {practiceExam.questions?.length || 5}
                      </span>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <Chip label={q.difficulty || 'Medium'} size="sm" />
                      </div>
                    </div>

                    <p style={{ fontWeight: 600, fontSize: '0.98rem', color: 'var(--ink)', margin: 0 }}>
                      {q.question}
                    </p>

                    {/* Grounded Citation */}
                    {q.citation && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--muted)', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <BookOpen size={13} />
                        Source: {q.citation}
                      </div>
                    )}

                    {isTextAnswer ? (
                      <textarea
                        rows={qType === 'long' || qType === 'long_answer' ? 6 : 3}
                        value={selectedVal || ''}
                        onChange={(event) => handleSelectAnswer(qKey, event.target.value)}
                        aria-label={`Answer to practice question ${qIndex + 1}`}
                        style={{
                          width: '100%',
                          padding: '10px 12px',
                          borderRadius: '8px',
                          border: '1px solid var(--border)',
                          background: 'var(--bg)',
                          color: 'var(--ink)',
                          font: 'inherit'
                        }}
                      />
                    ) : isFillBlank ? (
                      <input
                        type="text"
                        value={selectedVal || ''}
                        onChange={(event) => handleSelectAnswer(qKey, event.target.value)}
                        aria-label={`Answer to practice question ${qIndex + 1}`}
                        style={{
                          width: '100%',
                          padding: '10px 12px',
                          borderRadius: '8px',
                          border: '1px solid var(--border)',
                          background: 'var(--bg)',
                          color: 'var(--ink)',
                          font: 'inherit'
                        }}
                      />
                    ) : (
                    /* Options Selection */
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {(q.options || ['True', 'False']).map((opt, optIdx) => {
                        const isChosen = isMSQ
                          ? Array.isArray(selectedVal) && selectedVal.includes(optIdx)
                          : selectedVal === opt || selectedVal === optIdx;
                        return (
                          <div 
                            key={optIdx}
                            role={isMSQ ? 'checkbox' : 'button'}
                            tabIndex={0}
                            aria-checked={isMSQ ? isChosen : undefined}
                            onClick={() => isMSQ ? togglePracticeOption(qKey, optIdx) : handleSelectAnswer(qKey, opt)}
                            onKeyDown={(event) => {
                              if (event.key === 'Enter' || event.key === ' ') {
                                event.preventDefault();
                                isMSQ ? togglePracticeOption(qKey, optIdx) : handleSelectAnswer(qKey, opt);
                              }
                            }}
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
                              fontWeight: isChosen ? 600 : 400,
                              color: isChosen ? 'var(--indigo)' : 'var(--ink)',
                              transition: 'all 0.15s ease'
                            }}
                          >
                            <span>{opt}</span>
                            {isChosen && <Check size={16} color="var(--indigo)" />}
                          </div>
                        );
                      })}
                    </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Submit Action */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '14px', borderTop: '1px solid var(--border)' }}>
              <span style={{ fontSize: '0.84rem', color: 'var(--muted)' }}>
                {Object.values(practiceAnswers).filter(answer => Array.isArray(answer)
                  ? answer.length > 0
                  : String(answer ?? '').trim() !== '').length} of {practiceExam.questions?.length || 5} answered
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
                  icon={isSubmittingPractice ? <RotateCcw size={15} className="animate-spin" /> : <CheckCircle2 size={15} />}
                >
                  {isSubmittingPractice ? 'Grading Test...' : 'Submit Practice Test'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* AFTER PRACTICE: Diagnostic Comparison Display */}
        {practiceResult && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ 
              padding: '16px 20px', 
              borderRadius: '12px', 
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(99, 102, 241, 0.1) 100%)',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Trophy size={20} color="var(--teal)" />
                <h4 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--ink)' }}>
                  Targeted Practice Complete!
                </h4>
              </div>
              <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--muted)' }}>
                {practiceResult.feedbackText}
              </p>
            </div>

            {/* Performance Comparison Tile Grid */}
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

            {/* Priority Recalculation Card */}
            <Card style={{ padding: '16px 20px', background: 'var(--bg)', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '10px' }}>
                4-Quadrant Priority Recalculation
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', alignItems: 'center' }}>
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

            {/* Detailed Question Review */}
            {practiceResult.questions && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '35vh', overflowY: 'auto' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--ink)' }}>Mini-Test Question Review</span>
                {practiceResult.questions.map((pq, idx) => (
                  <div 
                    key={idx}
                    style={{ 
                      padding: '12px 14px', 
                      borderRadius: '10px', 
                      background: pq.isCorrect ? 'var(--teal-tint)' : 'var(--coral-tint)',
                      border: `1px solid ${pq.isCorrect ? 'var(--teal)' : 'var(--coral)'}`,
                      fontSize: '0.86rem'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 700 }}>Q{idx + 1}. {pq.question}</span>
                      <Chip label={pq.isCorrect ? 'Correct' : 'Missed'} variant={pq.isCorrect ? 'teal' : 'coral'} size="sm" />
                    </div>
                    <div style={{ color: 'var(--ink)', fontSize: '0.82rem' }}>
                      <strong>Answer: </strong> {Array.isArray(pq.correctAnswer) ? pq.correctAnswer.join(', ') : pq.correctAnswer}
                    </div>
                    {pq.explanation && (
                      <div style={{ color: 'var(--muted)', fontSize: '0.78rem', marginTop: '4px' }}>
                        {pq.explanation}
                      </div>
                    )}
                    {pq.citation && (
                      <div style={{ color: 'var(--muted)', fontSize: '0.74rem', marginTop: '2px', fontStyle: 'italic' }}>
                        Citation: {pq.citation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Action Footer */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
              <Button 
                variant="primary" 
                size="md" 
                icon={<CheckCircle2 size={16} />}
                onClick={handleClosePracticeModal}
              >
                Apply & Return to Results
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default Results;
