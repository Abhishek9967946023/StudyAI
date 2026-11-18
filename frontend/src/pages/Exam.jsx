/**
 * =============================================================================
 * StudyAI — 7. Exam Page (Distraction-Free Test Harness)
 * =============================================================================
 * Distraction-Free:
 * - Hides Left Sidebar, Top Bar, and Floating Study Copilot!
 * - Thin Progress Bar along top
 * - Large Timer with aria-live="polite" announcement on low time
 * - Question Card with topic & difficulty chips
 * - Selectable answers with active states
 * - Previous, Next, Mark for Review buttons
 * - Right-hand navigator grid:
 *     * Answered = Indigo fill (#4F3FF0)
 *     * Current = Dark outline
 *     * Marked for review = Coral outline (#E5484D)
 *     * Unanswered = Border
 * - Footer counter: "X answered, Y marked, Z left"
 * - Autosave answers in localStorage
 * - Confirmation modal before final submit
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Clock, 
  Flag, 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle,
  Send,
  Eye,
  X
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Modal } from '../components/ui/Modal';
import { useTimer } from '../hooks/useTimer';
import { getExam, submitExam } from '../services/examsService';

export function Exam() {
  const { examId } = useParams();
  const navigate = useNavigate();

  const [exam, setExam] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [markedQuestions, setMarkedQuestions] = useState({});
  const [showCitation, setShowCitation] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load exam data
  useEffect(() => {
    async function load() {
      const data = await getExam(examId || 'exam-demo');
      setExam(data);

      // Restore autosaved answers if any
      const saved = localStorage.getItem(`studyai_autosave_${examId}`);
      if (saved) {
        try { setUserAnswers(JSON.parse(saved)); } catch {}
      }
    }
    load();
  }, [examId]);

  // Warn on page leave
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = '';
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Timer with submit on expire
  const timer = useTimer(exam?.timeLimitMinutes || 12, () => handleFinalSubmit());

  // Autosave answers
  const handleSelectAnswer = (ans) => {
    const currentQ = exam?.questions[currentIndex];
    if (!currentQ) return;
    const updated = { ...userAnswers, [currentQ.id]: ans };
    setUserAnswers(updated);
    localStorage.setItem(`studyai_autosave_${examId}`, JSON.stringify(updated));
  };

  const toggleAnswerOption = (optionIndex) => {
    const currentQ = exam?.questions[currentIndex];
    if (!currentQ) return;
    const selected = Array.isArray(userAnswers[currentQ.id]) ? userAnswers[currentQ.id] : [];
    handleSelectAnswer(
      selected.includes(optionIndex)
        ? selected.filter(index => index !== optionIndex)
        : [...selected, optionIndex]
    );
  };

  const toggleMarkForReview = () => {
    const currentQ = exam?.questions[currentIndex];
    if (!currentQ) return;
    setMarkedQuestions(prev => ({
      ...prev,
      [currentQ.id]: !prev[currentQ.id]
    }));
  };

  const handleFinalSubmit = async () => {
    setIsSubmitting(true);
    setShowConfirmModal(false);
    try {
      const result = await submitExam(examId, userAnswers, exam);
      localStorage.removeItem(`studyai_autosave_${examId}`);
      navigate(`/results/${result.resultId}`);
    } catch (err) {
      console.error(err);
      setIsSubmitting(false);
    }
  };

  if (!exam) {
    return <div style={{ padding: '3rem', textAlign: 'center' }}>Loading examination environment...</div>;
  }

  const currentQ = exam.questions[currentIndex];
  const total = exam.questions.length;
  const answeredCount = Object.keys(userAnswers).filter(k => {
    const val = userAnswers[k];
    return val !== undefined && val !== null && String(val).trim() !== '';
  }).length;
  const markedCount = Object.values(markedQuestions).filter(Boolean).length;
  const remainingCount = total - answeredCount;
  const progressPercent = Math.round(((currentIndex + 1) / total) * 100);

  const qType = (currentQ?.type || 'mcq').toLowerCase();
  const isMCQ = qType === 'mcq' || qType === 'numerical';
  const isMSQ = qType === 'msq';
  const isTF = qType === 'tf' || qType === 'true_false' || qType === 'true/false';
  const isLong = qType === 'long' || qType === 'long_answer';
  const isShort = qType === 'short' || qType === 'short_answer' || qType === 'sa' || isLong;
  const isFillBlank = qType === 'fill_blank';

  return (
    <div className="fade-in" style={{ maxWidth: '1100px', margin: '0 auto', padding: '16px 12px 40px 12px' }}>
      {/* Thin Progress Bar Along Top */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '4px',
        backgroundColor: 'var(--border)',
        zIndex: 200
      }}>
        <div style={{
          width: `${progressPercent}%`,
          height: '100%',
          backgroundColor: 'var(--indigo)',
          transition: 'width 0.3s ease'
        }} />
      </div>

      {/* Distraction-Free Exam Header */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 0',
        borderBottom: '1px solid var(--border)',
        marginBottom: '24px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>{exam.title}</h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
            Question {currentIndex + 1} of {total} &bull; {exam.difficulty} &bull; {exam.totalMarks || exam.total_marks || total} marks
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Large Countdown Timer */}
          <div 
            aria-live="polite"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: 'var(--radius-pill)',
              backgroundColor: timer.isLowTime ? 'var(--coral-tint)' : 'var(--bg)',
              border: `1.5px solid ${timer.isLowTime ? 'var(--coral)' : 'var(--border)'}`,
              color: timer.isLowTime ? 'var(--coral-text)' : 'var(--ink)',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              fontSize: '1.1rem'
            }}
          >
            <Clock size={18} style={{ color: timer.isLowTime ? 'var(--coral)' : 'var(--muted)' }} />
            <span>{timer.formatted}</span>
          </div>

          <Button 
            variant="teal" 
            size="sm" 
            icon={<Send size={14} />}
            onClick={() => setShowConfirmModal(true)}
            loading={isSubmitting}
          >
            Submit Exam
          </Button>
        </div>
      </header>

      {/* Main Grid: Question Viewport (Left) + Navigator Grid (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '24px', alignItems: 'start' }}>
        {/* Left: Question Card */}
        <Card style={{ padding: '28px', minHeight: '480px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            {/* Question Meta Chips */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <Chip variant="indigo">{currentQ.topic}</Chip>
                <Chip variant="neutral">{currentQ.difficulty}</Chip>
                <Chip variant="neutral">{currentQ.marks || 1} {currentQ.marks === 1 ? 'mark' : 'marks'}</Chip>
                <Chip variant={isShort || isFillBlank ? "coral" : isTF ? "teal" : "neutral"}>
                  {isLong ? "Long Answer" : isFillBlank ? "Fill in the Blank" : isShort ? "Short Answer" : isMSQ ? "Multiple Select" : isTF ? "True / False" : qType === 'numerical' ? "Numerical" : "Multiple Choice"}
                </Chip>
              </div>

              <button
                type="button"
                onClick={toggleMarkForReview}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: markedQuestions[currentQ.id] ? 'var(--coral-tint)' : 'transparent',
                  color: markedQuestions[currentQ.id] ? 'var(--coral-text)' : 'var(--muted)',
                  border: markedQuestions[currentQ.id] ? '1px solid var(--coral)' : '1px solid var(--border)',
                  borderRadius: 'var(--radius-pill)',
                  padding: '5px 12px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <Flag size={13} />
                <span>{markedQuestions[currentQ.id] ? 'Marked for Review' : 'Mark for Review'}</span>
              </button>
            </div>

            {/* Question Prompt */}
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, lineHeight: 1.5, marginBottom: '24px' }}>
              {currentQ.question}
            </h3>
            {isMSQ && (
              <p style={{ marginTop: '-16px', marginBottom: '18px', color: 'var(--muted)', fontSize: '0.88rem' }}>
                Select all that apply.
              </p>
            )}

            {/* Answer Options: MCQ and MSQ */}
            {(isMCQ || isMSQ) && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
                {(currentQ.options && currentQ.options.length > 0 ? currentQ.options : ['Option A', 'Option B', 'Option C', 'Option D']).map((opt, optIdx) => {
                  const isSelected = isMSQ
                    ? (Array.isArray(userAnswers[currentQ.id]) && userAnswers[currentQ.id].includes(optIdx))
                    : userAnswers[currentQ.id] === opt;
                  return (
                    <div
                      key={optIdx}
                      role={isMSQ ? 'checkbox' : 'button'}
                      tabIndex={0}
                      aria-checked={isMSQ ? isSelected : undefined}
                      onClick={() => isMSQ ? toggleAnswerOption(optIdx) : handleSelectAnswer(opt)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          isMSQ ? toggleAnswerOption(optIdx) : handleSelectAnswer(opt);
                        }
                      }}
                      style={{
                        padding: '14px 18px',
                        borderRadius: 'var(--radius-btn)',
                        border: isSelected ? '2px solid var(--indigo)' : '1px solid var(--border)',
                        backgroundColor: isSelected ? 'var(--indigo-tint)' : 'var(--surface)',
                        color: isSelected ? 'var(--indigo-text)' : 'var(--ink)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        transition: 'all var(--transition-fast)'
                      }}
                    >
                      <div style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: isMSQ ? '5px' : '50%',
                        border: isSelected ? '2px solid var(--indigo)' : '2px solid var(--border)',
                        backgroundColor: isSelected ? 'var(--indigo)' : 'transparent',
                        color: isSelected ? '#FFFFFF' : 'var(--muted)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        flexShrink: 0
                      }}>
                        {String.fromCharCode(65 + optIdx)}
                      </div>
                      <span style={{ fontSize: '0.95rem', fontWeight: isSelected ? 600 : 400 }}>
                        {opt}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Answer Options: True / False */}
            {isTF && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                {['True', 'False'].map((opt) => {
                  const isSelected = String(userAnswers[currentQ.id] || '').toLowerCase() === opt.toLowerCase();
                  const isTrue = opt === 'True';
                  return (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleSelectAnswer(opt)}
                      style={{
                        padding: '24px 20px',
                        borderRadius: '12px',
                        border: isSelected 
                          ? `2px solid ${isTrue ? 'var(--teal)' : 'var(--coral)'}` 
                          : '1.5px solid var(--border)',
                        backgroundColor: isSelected 
                          ? (isTrue ? 'var(--teal-tint)' : 'var(--coral-tint)') 
                          : 'var(--surface)',
                        color: isSelected 
                          ? (isTrue ? 'var(--teal-text)' : 'var(--coral-text)') 
                          : 'var(--ink)',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        transition: 'all var(--transition-fast)',
                        outline: 'none',
                        boxShadow: isSelected ? '0 4px 14px rgba(0,0,0,0.06)' : 'none'
                      }}
                    >
                      <div style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        backgroundColor: isSelected ? (isTrue ? 'var(--teal)' : 'var(--coral)') : 'var(--bg)',
                        color: isSelected ? '#FFFFFF' : 'var(--muted)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1rem',
                        fontWeight: 800
                      }}>
                        {isTrue ? '✓' : '✗'}
                      </div>
                      <span style={{ fontSize: '1.15rem', fontWeight: 700 }}>
                        {opt}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: isSelected ? 'currentColor' : 'var(--muted)' }}>
                        {isTrue ? 'Statement is accurate' : 'Statement is inaccurate'}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Answer Options: Short Answer */}
            {isShort && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
                <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', fontWeight: 600, color: 'var(--ink)' }}>
                  <span>Your Written Answer:</span>
                  <span style={{ fontSize: '0.78rem', color: 'var(--muted)', fontWeight: 400 }}>
                    {String(userAnswers[currentQ.id] || '').trim().split(/\s+/).filter(Boolean).length} words
                  </span>
                </label>

                <textarea
                  rows={isLong ? 10 : 5}
                  value={userAnswers[currentQ.id] || ''}
                  onChange={(e) => handleSelectAnswer(e.target.value)}
                  placeholder={isLong ? "Write a structured explanation using the source concepts..." : "Type your concise, grounded answer here (1-3 sentences)..."}
                  style={{
                    width: '100%',
                    padding: '14px 16px',
                    borderRadius: '12px',
                    border: (userAnswers[currentQ.id] && String(userAnswers[currentQ.id]).trim().length > 0)
                      ? '2px solid var(--indigo)'
                      : '1.5px solid var(--border)',
                    backgroundColor: 'var(--bg)',
                    color: 'var(--ink)',
                    fontSize: '0.95rem',
                    lineHeight: 1.6,
                    fontFamily: 'inherit',
                    resize: 'vertical',
                    outline: 'none',
                    boxShadow: (userAnswers[currentQ.id] && String(userAnswers[currentQ.id]).trim().length > 0)
                      ? '0 0 0 3px rgba(79, 63, 240, 0.12)'
                      : 'none',
                    transition: 'all 0.2s ease'
                  }}
                />

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: 'var(--muted)' }}>
                  <span>{isLong ? "Tip: Organize the explanation around the definition, mechanism, and any relevant rules." : "Tip: State key concepts, terms, or mechanisms directly."}</span>
                  {userAnswers[currentQ.id] && String(userAnswers[currentQ.id]).trim().length > 0 && (
                    <button
                      type="button"
                      onClick={() => handleSelectAnswer('')}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--coral)',
                        fontSize: '0.78rem',
                        cursor: 'pointer',
                        padding: 0,
                        textDecoration: 'underline'
                      }}
                    >
                      Clear Answer
                    </button>
                  )}
                </div>
              </div>
            )}

            {isFillBlank && (
              <div style={{ marginBottom: '20px' }}>
                <label htmlFor="fill-blank-answer" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '8px' }}>
                  Your answer:
                </label>
                <input
                  id="fill-blank-answer"
                  type="text"
                  value={userAnswers[currentQ.id] || ''}
                  onChange={(e) => handleSelectAnswer(e.target.value)}
                  placeholder="Enter the missing term"
                  style={{
                    width: '100%',
                    padding: '14px 16px',
                    borderRadius: '12px',
                    border: '1.5px solid var(--border)',
                    backgroundColor: 'var(--bg)',
                    color: 'var(--ink)',
                    fontSize: '0.95rem'
                  }}
                />
              </div>
            )}

            {/* Collapsible Source Citation Hint */}
            <div style={{ marginTop: '8px' }}>
              <button
                type="button"
                onClick={() => setShowCitation(!showCitation)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--muted)',
                  fontSize: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  cursor: 'pointer'
                }}
              >
                <Eye size={13} />
                <span>{showCitation ? 'Hide Material Reference' : 'Preview Source Grounding Excerpt'}</span>
              </button>
              {showCitation && (
                <div style={{
                  marginTop: '8px',
                  padding: '10px 14px',
                  backgroundColor: 'var(--bg)',
                  borderRadius: '10px',
                  fontSize: '0.8rem',
                  color: 'var(--muted)',
                  fontStyle: 'italic',
                  border: '1px solid var(--border)'
                }}>
                  {currentQ.citation}
                </div>
              )}
            </div>
          </div>

          {/* Navigation Controls */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '20px',
            borderTop: '1px solid var(--border)',
            marginTop: '24px'
          }}>
            <Button
              variant="secondary"
              disabled={currentIndex === 0}
              icon={<ArrowLeft size={16} />}
              onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))}
            >
              Previous
            </Button>

            <span style={{ fontSize: '0.825rem', color: 'var(--muted)' }}>
              {answeredCount} of {total} Answered
            </span>

            {currentIndex < total - 1 ? (
              <Button
                variant="primary"
                iconRight={<ArrowRight size={16} />}
                onClick={() => setCurrentIndex(prev => Math.min(total - 1, prev + 1))}
              >
                Next
              </Button>
            ) : (
              <Button
                variant="teal"
                icon={<CheckCircle2 size={16} />}
                onClick={() => setShowConfirmModal(true)}
              >
                Finish Exam
              </Button>
            )}
          </div>
        </Card>

        {/* Right: Question Navigator Grid */}
        <Card style={{ padding: '20px' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '12px' }}>
            Question Navigator
          </h4>

          {/* Legend */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: 'var(--indigo)' }} />
              <span>Answered</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '3px', border: '1.5px solid var(--coral)', backgroundColor: 'transparent' }} />
              <span>Marked for Review</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '3px', border: '1.5px solid var(--ink)', backgroundColor: 'transparent' }} />
              <span>Current</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: 'var(--border)' }} />
              <span>Unanswered</span>
            </div>
          </div>

          {/* Navigator Grid Buttons */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '20px' }}>
            {exam.questions.map((q, idx) => {
              const val = userAnswers[q.id];
              const isAnswered = val !== undefined && val !== null && String(val).trim() !== '';
              const isMarked = markedQuestions[q.id];
              const isCurrent = currentIndex === idx;

              let bg = 'var(--bg)';
              let color = 'var(--muted)';
              let border = '1px solid var(--border)';

              if (isAnswered) {
                bg = 'var(--indigo)';
                color = '#FFFFFF';
                border = '1px solid var(--indigo)';
              }
              if (isMarked) {
                border = '2px solid var(--coral)';
              }
              if (isCurrent) {
                border = '2px solid var(--ink)';
              }

              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentIndex(idx)}
                  style={{
                    aspectRatio: '1',
                    borderRadius: '8px',
                    backgroundColor: bg,
                    color,
                    border,
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          {/* Footer Counter Text */}
          <div style={{ 
            fontSize: '0.78rem', 
            color: 'var(--muted)', 
            paddingTop: '12px', 
            borderTop: '1px solid var(--border)',
            textAlign: 'center' 
          }}>
            {answeredCount} answered &bull; {markedCount} marked &bull; {remainingCount} left
          </div>
        </Card>
      </div>

      {/* Confirmation Modal */}
      <Modal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        title="Submit Examination"
      >
        <p style={{ fontSize: '0.9rem', color: 'var(--muted)', lineHeight: 1.5, marginBottom: '16px' }}>
          You have answered <strong>{answeredCount} of {total}</strong> questions.
          {remainingCount > 0 && (
            <span style={{ display: 'block', marginTop: '8px', color: 'var(--coral)', fontWeight: 600 }}>
              ⚠️ You have {remainingCount} unanswered question{remainingCount > 1 ? 's' : ''}!
            </span>
          )}
        </p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <Button variant="secondary" onClick={() => setShowConfirmModal(false)}>
            Keep Answering
          </Button>
          <Button variant="teal" onClick={handleFinalSubmit} loading={isSubmitting}>
            Confirm & Grade Now
          </Button>
        </div>
      </Modal>
    </div>
  );
}
