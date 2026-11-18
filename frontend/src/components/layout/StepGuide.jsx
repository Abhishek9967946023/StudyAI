/**
 * =============================================================================
 * StudyAI — StepGuide Component (Core Main Journey Progression)
 * =============================================================================
 * 1 Upload -> 2 Review (Analysis/Summary) -> 3 Exam -> 4 Results -> 5 Revise
 * Finished steps: Teal (#0B7F72)
 * Current step: Indigo (#4F3FF0)
 * Upcoming steps: Gray / Subtle
 * =============================================================================
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Check } from 'lucide-react';

export function StepGuide({ currentStep = 1, nextUpText = '' }) {
  const navigate = useNavigate();

  const steps = [
    { number: 1, label: 'Upload', path: '/upload' },
    { number: 2, label: 'Review', path: '/analysis' },
    { number: 3, label: 'Exam', path: '/exam-config' },
    { number: 4, label: 'Results', path: '/results' },
    { number: 5, label: 'Revise', path: '/revision' }
  ];

  return (
    <div style={{ marginBottom: '28px' }}>
      <div 
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-pill)',
          padding: '8px 16px',
          overflowX: 'auto',
          gap: '12px'
        }}
      >
        {steps.map((s, idx) => {
          const isDone = s.number < currentStep;
          const isCurrent = s.number === currentStep;

          let badgeBg = 'var(--border)';
          let badgeColor = 'var(--muted)';
          let textWeight = 500;
          let textColor = 'var(--muted)';

          if (isDone) {
            badgeBg = 'var(--teal)';
            badgeColor = '#FFFFFF';
            textColor = 'var(--teal-text)';
            textWeight = 600;
          } else if (isCurrent) {
            badgeBg = 'var(--indigo)';
            badgeColor = '#FFFFFF';
            textColor = 'var(--indigo)';
            textWeight = 700;
          }

          return (
            <React.Fragment key={s.number}>
              <button
                type="button"
                onClick={() => isDone && navigate(s.path)}
                disabled={!isDone && !isCurrent}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: 'transparent',
                  border: 'none',
                  cursor: isDone ? 'pointer' : 'default',
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-pill)',
                  whiteSpace: 'nowrap'
                }}
              >
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  backgroundColor: badgeBg,
                  color: badgeColor,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem',
                  fontWeight: 700
                }}>
                  {isDone ? <Check size={14} strokeWidth={3} /> : s.number}
                </div>
                <span style={{ fontSize: '0.825rem', color: textColor, fontWeight: textWeight }}>
                  {s.label}
                </span>
              </button>

              {idx < steps.length - 1 && (
                <div style={{ 
                  flex: 1, 
                  height: '2px', 
                  backgroundColor: isDone ? 'var(--teal)' : 'var(--border)', 
                  minWidth: '16px' 
                }} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {nextUpText && (
        <div style={{ 
          fontSize: '0.8rem', 
          color: 'var(--muted)', 
          marginTop: '8px', 
          paddingLeft: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <span style={{ fontWeight: 600, color: 'var(--ink)' }}>What happens next:</span>
          <span>{nextUpText}</span>
        </div>
      )}
    </div>
  );
}
