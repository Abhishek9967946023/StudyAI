/**
 * =============================================================================
 * StudyAI — Topic Intelligence Screen (Screen 9)
 * =============================================================================
 * Strictly distinguishes Material Importance (curriculum weight) from
 * Student Performance (accuracy on assessments).
 *
 * Implements:
 * - 2x2 Priority Matrix with HIGH_IMPORTANCE=60 and WEAK_BELOW=60
 * - 4 Quadrants: Critical, Maintain, Practice if time permits, Low priority
 * - Detailed Intelligence Data Table with recommendations
 * - Direct practice triggers for critical items
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Compass, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ArrowRight, 
  Play, 
  BookOpen, 
  Filter, 
  Info,
  TrendingUp,
  Brain,
  HelpCircle
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { PriorityMatrix } from '../components/charts/PriorityMatrix';
import { Skeleton } from '../components/ui/Skeleton';
import { getTopicIntelligence, HIGH_IMPORTANCE, WEAK_BELOW } from '../services/topicsService';
import { getActiveMaterialId } from '../services/materialsService';

export function TopicIntelligence() {
  const navigate = useNavigate();
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterQuadrant, setFilterQuadrant] = useState('ALL');

  useEffect(() => {
    async function loadTopics() {
      setLoading(true);
      try {
        const data = await getTopicIntelligence(getActiveMaterialId());
        setTopics(data);
      } catch (err) {
        console.error('Error fetching topic intelligence:', err);
      } finally {
        setLoading(false);
      }
    }
    loadTopics();
  }, []);

  const criticalCount = topics.filter(t => t.importance >= HIGH_IMPORTANCE && t.performance < WEAK_BELOW).length;
  const maintainCount = topics.filter(t => t.importance >= HIGH_IMPORTANCE && t.performance >= WEAK_BELOW).length;
  const practiceCount = topics.filter(t => t.importance < HIGH_IMPORTANCE && t.performance < WEAK_BELOW).length;

  const filteredTopics = topics.filter(t => {
    if (filterQuadrant === 'ALL') return true;
    return t.category?.quadrant === filterQuadrant;
  });

  if (loading) {
    return (
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <Skeleton height="140px" />
        <Skeleton height="320px" />
        <Skeleton height="260px" />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* 1. Header with Concept Explanation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--indigo)', marginBottom: '4px' }}>
            <Compass size={18} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Cognitive Diagnostics
            </span>
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
            Topic Intelligence Matrix
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '0.96rem', margin: '6px 0 0 0', maxWidth: '680px', lineHeight: 1.5 }}>
            Separates <strong>Material Importance</strong> (what the source material emphasizes) from <strong>Student Performance</strong> (what you scored). Focus your revision on high-yield gaps.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <Button 
            variant="outline" 
            size="md"
            icon={<BookOpen size={16} />}
            onClick={() => navigate('/summary')}
          >
            Review Summary Notes
          </Button>
          <Button 
            variant="primary" 
            size="md"
            icon={<ArrowRight size={16} />}
            iconPosition="right"
            onClick={() => navigate('/revision')}
          >
            Build Revision Plan
          </Button>
        </div>
      </div>

      {/* 2. Educational Metric Summary Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <Card style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px', borderLeft: '4px solid var(--coral)' }}>
          <div style={{ width: 40, height: 40, borderRadius: '10px', background: 'var(--coral-tint)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--coral)' }}>
            <AlertTriangle size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>Critical Priority</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--coral)' }}>{criticalCount} Topics</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>High Imp &ge;60% &bull; Score &lt;60%</div>
          </div>
        </Card>

        <Card style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px', borderLeft: '4px solid var(--teal)' }}>
          <div style={{ width: 40, height: 40, borderRadius: '10px', background: 'var(--teal-tint)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--teal)' }}>
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>Maintain (Mastered)</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--teal)' }}>{maintainCount} Topics</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>High Imp &ge;60% &bull; Score &ge;60%</div>
          </div>
        </Card>

        <Card style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px', borderLeft: '4px solid var(--indigo)' }}>
          <div style={{ width: 40, height: 40, borderRadius: '10px', background: 'var(--indigo-tint)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--indigo)' }}>
            <Brain size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>Total Curriculum Topics</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--ink)' }}>{topics.length} Mapped</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>Extracted from document</div>
          </div>
        </Card>
      </div>

      {/* 3. The 2x2 Priority Matrix Visual Chart */}
      <Card style={{ padding: '24px' }}>
        <PriorityMatrix 
          topics={topics} 
          onSelectTopic={(t) => navigate(`/exam-config?topic=${encodeURIComponent(t.topic || t.name)}`)} 
        />
      </Card>

      {/* 4. Complete Topic Intelligence Table */}
      <Card style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>
              Syllabus Diagnostic Breakdown
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
              Actionable recommendations based on importance and mastery calibration
            </p>
          </div>

          {/* Filter Pills */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <button 
              className={`sa-chip ${filterQuadrant === 'ALL' ? 'active' : ''}`}
              onClick={() => setFilterQuadrant('ALL')}
              style={{ cursor: 'pointer', padding: '6px 14px', borderRadius: '999px', fontSize: '0.8rem', border: '1px solid var(--border)', background: filterQuadrant === 'ALL' ? 'var(--indigo)' : 'var(--surface)', color: filterQuadrant === 'ALL' ? '#FFF' : 'var(--ink)' }}
            >
              All ({topics.length})
            </button>
            <button 
              onClick={() => setFilterQuadrant('critical')}
              style={{ cursor: 'pointer', padding: '6px 14px', borderRadius: '999px', fontSize: '0.8rem', border: '1px solid var(--coral)', background: filterQuadrant === 'critical' ? 'var(--coral)' : 'var(--coral-tint)', color: filterQuadrant === 'critical' ? '#FFF' : 'var(--coral-text)', fontWeight: 600 }}
            >
              Critical ({criticalCount})
            </button>
            <button 
              onClick={() => setFilterQuadrant('maintain')}
              style={{ cursor: 'pointer', padding: '6px 14px', borderRadius: '999px', fontSize: '0.8rem', border: '1px solid var(--teal)', background: filterQuadrant === 'maintain' ? 'var(--teal)' : 'var(--teal-tint)', color: filterQuadrant === 'maintain' ? '#FFF' : 'var(--teal-text)', fontWeight: 600 }}
            >
              Maintain ({maintainCount})
            </button>
            <button 
              onClick={() => setFilterQuadrant('practice_if_time')}
              style={{ cursor: 'pointer', padding: '6px 14px', borderRadius: '999px', fontSize: '0.8rem', border: '1px solid var(--border)', background: filterQuadrant === 'practice_if_time' ? 'var(--muted)' : 'var(--bg)', color: filterQuadrant === 'practice_if_time' ? '#FFF' : 'var(--muted)' }}
            >
              Practice If Time ({practiceCount})
            </button>
          </div>
        </div>

        {/* Data Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border)', color: 'var(--muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                <th style={{ padding: '12px 14px' }}>Topic Name</th>
                <th style={{ padding: '12px 14px', width: '150px' }}>Material Importance</th>
                <th style={{ padding: '12px 14px', width: '150px' }}>Student Mastery</th>
                <th style={{ padding: '12px 14px', width: '140px' }}>Classification</th>
                <th style={{ padding: '12px 14px' }}>Adaptive Recommendation</th>
                <th style={{ padding: '12px 14px', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredTopics.map((item, idx) => {
                const topicName = item.topic || item.name;
                const isCritical = item.category?.quadrant === 'critical';
                const isMaintain = item.category?.quadrant === 'maintain';

                return (
                  <tr 
                    key={idx} 
                    style={{ 
                      borderBottom: '1px solid var(--border)',
                      backgroundColor: isCritical ? 'rgba(253, 236, 236, 0.25)' : 'transparent'
                    }}
                  >
                    <td style={{ padding: '16px 14px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--ink)' }}>{topicName}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '2px' }}>
                        {item.description || 'Core syllabus module extracted from study material'}
                      </div>
                    </td>

                    {/* Material Importance */}
                    <td style={{ padding: '16px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--ink)' }}>{item.importance}%</span>
                        <span style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>Weight</span>
                      </div>
                      <div style={{ height: '6px', background: 'var(--bg)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${item.importance}%`, background: 'var(--indigo)', borderRadius: '3px' }} />
                      </div>
                    </td>

                    {/* Student Performance */}
                    <td style={{ padding: '16px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.85rem', color: item.performance < WEAK_BELOW ? 'var(--coral)' : 'var(--teal)' }}>
                          {item.performance}%
                        </span>
                        <span style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>Score</span>
                      </div>
                      <div style={{ height: '6px', background: 'var(--bg)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div 
                          style={{ 
                            height: '100%', 
                            width: `${item.performance}%`, 
                            background: item.performance < WEAK_BELOW ? 'var(--coral)' : 'var(--teal)',
                            borderRadius: '3px' 
                          }} 
                        />
                      </div>
                    </td>

                    {/* Classification Badge */}
                    <td style={{ padding: '16px 14px' }}>
                      <Chip 
                        label={item.category?.label || (isCritical ? 'Critical' : isMaintain ? 'Maintain' : 'Secondary')} 
                        variant={isCritical ? 'coral' : isMaintain ? 'teal' : 'neutral'}
                        size="sm"
                      />
                    </td>

                    {/* Recommendation */}
                    <td style={{ padding: '16px 14px' }}>
                      <div style={{ fontSize: '0.85rem', color: 'var(--ink)', lineHeight: 1.4 }}>
                        {item.recommendation || (
                          isCritical 
                            ? 'Immediate 15-min drill on Z-scheme electron pathway.'
                            : isMaintain 
                            ? 'Retain with spaced repetition flashcards in 3 days.'
                            : 'Review key terms if remaining revision time permits.'
                        )}
                      </div>
                    </td>

                    {/* Action */}
                    <td style={{ padding: '16px 14px', textAlign: 'right' }}>
                      <Button 
                        size="sm"
                        variant={isCritical ? 'primary' : 'secondary'}
                        icon={<Play size={13} />}
                        onClick={() => navigate(`/exam-config?topic=${encodeURIComponent(topicName)}`)}
                      >
                        Drill
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 5. What Happens Next Card */}
      <Card style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px' }}>
        <div>
          <div style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '0.96rem' }}>
            Ready to close your critical gaps?
          </div>
          <div style={{ color: 'var(--muted)', fontSize: '0.88rem', marginTop: '2px' }}>
            Jump to your personalized daily revision schedule to practice questions and review targeted notes.
          </div>
        </div>
        <Button 
          variant="primary" 
          size="md"
          icon={<ArrowRight size={16} />}
          iconPosition="right"
          onClick={() => navigate('/revision')}
        >
          Open Daily Revision Plan
        </Button>
      </Card>
    </div>
  );
}

export default TopicIntelligence;
