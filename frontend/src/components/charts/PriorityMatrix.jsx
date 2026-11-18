/**
 * =============================================================================
 * StudyAI — Topic Priority Matrix (Week 11 & Spec Core Requirement)
 * =============================================================================
 * Distinguishes Material Importance (what the curriculum demands, 0-100)
 * from Student Performance (what the student scored, 0-100).
 *
 * Quadrants:
 * 1. High Importance + Weak Performance = Critical (Coral #E5484D)
 * 2. High Importance + Strong Performance = Maintain (Teal #0B7F72)
 * 3. Low Importance + Weak Performance = Practice if time permits (#FDECEC / Tint)
 * 4. Low Importance + Strong Performance = Low priority (Subtle)
 *
 * Threshold Constants: HIGH_IMPORTANCE = 60, WEAK_BELOW = 60
 * =============================================================================
 */

import React from 'react';
import { Card } from '../ui/Card';
import { Chip } from '../ui/Chip';
import { HIGH_IMPORTANCE, WEAK_BELOW } from '../../services/topicsService';
import { AlertTriangle, CheckCircle2, Clock, Check } from 'lucide-react';

export function PriorityMatrix({ topics = [], onSelectTopic = null }) {
  const critical = topics.filter(t => t.importance >= HIGH_IMPORTANCE && t.performance < WEAK_BELOW);
  const maintain = topics.filter(t => t.importance >= HIGH_IMPORTANCE && t.performance >= WEAK_BELOW);
  const practiceIfTime = topics.filter(t => t.importance < HIGH_IMPORTANCE && t.performance < WEAK_BELOW);
  const lowPriority = topics.filter(t => t.importance < HIGH_IMPORTANCE && t.performance >= WEAK_BELOW);

  return (
    <div className="sa-priority-matrix" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
        <div>
          <h4 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Material Importance vs. Student Performance</h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
            Thresholds: High Importance &ge; {HIGH_IMPORTANCE}% &bull; Weak Score &lt; {WEAK_BELOW}%
          </p>
        </div>
        <Chip variant="coral" icon={<AlertTriangle size={13} />}>
          {critical.length} Critical Gap{critical.length !== 1 ? 's' : ''}
        </Chip>
      </div>

      {/* 2x2 Quadrant Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
        {/* Quadrant 1: Critical (High Importance + Weak) */}
        <div 
          className="sa-card"
          style={{ 
            backgroundColor: 'var(--coral-tint)', 
            borderColor: 'var(--coral)',
            borderWidth: '1.5px',
            padding: '16px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ 
              fontSize: '0.75rem', 
              fontWeight: 700, 
              color: 'var(--coral-text)', 
              textTransform: 'uppercase', 
              letterSpacing: '0.05em',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              <AlertTriangle size={14} /> Critical Priority
            </span>
            <Chip variant="coral">{critical.length}</Chip>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--coral-text)', marginBottom: '10px' }}>
            High syllabus importance + Low student score. Study these first!
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {critical.length === 0 ? (
              <span style={{ fontSize: '0.75rem', color: 'var(--muted)', fontStyle: 'italic' }}>No critical gaps detected!</span>
            ) : (
              critical.map(t => (
                <div 
                  key={t.topic || t.id}
                  onClick={() => onSelectTopic && onSelectTopic(t)}
                  style={{
                    backgroundColor: 'var(--surface)',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: onSelectTopic ? 'pointer' : 'default',
                    border: '1px solid rgba(229, 72, 77, 0.2)'
                  }}
                >
                  <strong style={{ fontSize: '0.825rem', color: 'var(--ink)' }}>{t.name || t.topic}</strong>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--coral)' }}>
                    {t.performance}% score
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quadrant 2: Maintain (High Importance + Strong) */}
        <div 
          className="sa-card"
          style={{ 
            backgroundColor: 'var(--teal-tint)', 
            borderColor: 'var(--teal)',
            padding: '16px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ 
              fontSize: '0.75rem', 
              fontWeight: 700, 
              color: 'var(--teal-text)', 
              textTransform: 'uppercase', 
              letterSpacing: '0.05em',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              <CheckCircle2 size={14} /> Maintain (Mastered)
            </span>
            <Chip variant="teal">{maintain.length}</Chip>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--teal-text)', marginBottom: '10px' }}>
            High syllabus importance + Strong student score. Maintain retention.
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {maintain.length === 0 ? (
              <span style={{ fontSize: '0.75rem', color: 'var(--muted)', fontStyle: 'italic' }}>None yet.</span>
            ) : (
              maintain.map(t => (
                <div 
                  key={t.topic || t.id}
                  style={{
                    backgroundColor: 'var(--surface)',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    border: '1px solid rgba(11, 127, 114, 0.2)'
                  }}
                >
                  <strong style={{ fontSize: '0.825rem', color: 'var(--ink)' }}>{t.name || t.topic}</strong>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--teal)' }}>
                    {t.performance}% score
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quadrant 3: Practice If Time (Low Importance + Weak) */}
        <div 
          className="sa-card"
          style={{ 
            backgroundColor: 'var(--surface)', 
            borderColor: 'var(--border)',
            padding: '16px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Practice If Time Permits
            </span>
            <Chip variant="neutral">{practiceIfTime.length}</Chip>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginBottom: '10px' }}>
            Secondary topic with score gap. Address after critical topics.
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {practiceIfTime.length === 0 ? (
              <span style={{ fontSize: '0.75rem', color: 'var(--muted)', fontStyle: 'italic' }}>None.</span>
            ) : (
              practiceIfTime.map(t => (
                <div 
                  key={t.topic || t.id}
                  style={{
                    backgroundColor: 'var(--bg)',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span style={{ fontSize: '0.825rem', color: 'var(--ink)' }}>{t.name || t.topic}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>{t.performance}%</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quadrant 4: Low Priority (Low Importance + Strong) */}
        <div 
          className="sa-card"
          style={{ 
            backgroundColor: 'var(--surface)', 
            borderColor: 'var(--border)',
            padding: '16px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Low Priority
            </span>
            <Chip variant="neutral">{lowPriority.length}</Chip>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginBottom: '10px' }}>
            Foundational material mastered. No immediate intervention needed.
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {lowPriority.length === 0 ? (
              <span style={{ fontSize: '0.75rem', color: 'var(--muted)', fontStyle: 'italic' }}>None.</span>
            ) : (
              lowPriority.map(t => (
                <div 
                  key={t.topic || t.id}
                  style={{
                    backgroundColor: 'var(--bg)',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span style={{ fontSize: '0.825rem', color: 'var(--ink)' }}>{t.name || t.topic}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--teal)' }}>{t.performance}%</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
