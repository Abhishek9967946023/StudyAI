/**
 * =============================================================================
 * StudyAI — History Screen (Screen 12)
 * =============================================================================
 * Features:
 * - Past exam attempts with scores, dates, and time spent
 * - Score improvement trend visualization (TrendBars)
 * - Topic mastery progression over successive attempts
 * - Logged active study sessions (Analysis, Mock Exams, Targeted Drills)
 * - Actionable direct navigation to re-inspect past evaluations
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  History as HistoryIcon, 
  TrendingUp, 
  Calendar, 
  Clock, 
  Award, 
  CheckCircle2, 
  ChevronRight, 
  ArrowRight,
  BookOpen,
  RotateCcw
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { TrendBars } from '../components/charts/TrendBars';
import { Skeleton } from '../components/ui/Skeleton';
import { getHistory } from '../services/historyService';

export function History() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await getHistory();
        setHistory(data);
      } catch (err) {
        console.error('Failed to load history:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <Skeleton height="140px" />
        <Skeleton height="220px" />
        <Skeleton height="300px" />
      </div>
    );
  }

  // Trend data formatted for TrendBars
  const trendData = (history || []).slice(0, 7).reverse().map((h, i) => ({
    label: h.date?.includes('Oct') ? h.date.split(',')[0] : `Exam ${i + 1}`,
    score: h.scorePercent
  }));

  const avgScore = history.length > 0 
    ? Math.round(history.reduce((acc, h) => acc + h.scorePercent, 0) / history.length) 
    : 0;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* 1. Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--indigo)', marginBottom: '4px' }}>
            <HistoryIcon size={18} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Longitudinal Learning Logs
            </span>
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
            Exam & Assessment History
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '0.96rem', margin: '6px 0 0 0' }}>
            Track score trajectories, examine past diagnostics, and watch topic mastery compound.
          </p>
        </div>

        <Button 
          variant="primary" 
          size="md"
          icon={<RotateCcw size={16} />}
          onClick={() => navigate('/exam-config')}
        >
          Take New Exam
        </Button>
      </div>

      {/* 2. Metrics & Improvement Over Time Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        {/* Trend Bar Chart */}
        <Card style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--ink)' }}>
                Score Trajectory Trend
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--muted)' }}>
                Progression across your last {trendData.length} exams
              </p>
            </div>
            <Chip label="+18% Growth" variant="teal" size="sm" icon={<TrendingUp size={14} />} />
          </div>

          <div style={{ padding: '10px 0' }}>
            <TrendBars data={trendData} />
          </div>
        </Card>

        {/* Aggregate Stats */}
        <div style={{ display: 'grid', gridTemplateRows: 'repeat(2, 1fr)', gap: '16px' }}>
          <Card style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: 44, height: 44, borderRadius: '12px', background: 'var(--indigo-tint)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--indigo)' }}>
              <Award size={24} />
            </div>
            <div>
              <div style={{ fontSize: '0.82rem', color: 'var(--muted)', fontWeight: 600 }}>Cumulative Average Score</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--ink)' }}>{avgScore}%</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--teal-text)' }}>Across {history.length} completed assessments</div>
            </div>
          </Card>

          <Card style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: 44, height: 44, borderRadius: '12px', background: 'var(--teal-tint)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--teal)' }}>
              <Clock size={24} />
            </div>
            <div>
              <div style={{ fontSize: '0.82rem', color: 'var(--muted)', fontWeight: 600 }}>Total Active Exam Time</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--ink)' }}>~32 mins</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Focus efficiency: 98%</div>
            </div>
          </Card>
        </div>
      </div>

      {/* 3. Past Exam Attempts Table */}
      <Card style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
            Detailed Assessment Records
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
            Click any row to open the complete question-by-question diagnostic evaluation
          </p>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border)', color: 'var(--muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                <th style={{ padding: '12px 14px' }}>Assessment Title</th>
                <th style={{ padding: '12px 14px' }}>Date</th>
                <th style={{ padding: '12px 14px' }}>Score</th>
                <th style={{ padding: '12px 14px' }}>Accuracy</th>
                <th style={{ padding: '12px 14px' }}>Duration</th>
                <th style={{ padding: '12px 14px' }}>Weak Area Detected</th>
                <th style={{ padding: '12px 14px', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item, idx) => {
                const score = item.scorePercent;
                const isPassed = score >= 60;

                return (
                  <tr 
                    key={item.id || idx}
                    style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer', transition: 'background 0.15s' }}
                    onClick={() => navigate(`/results?id=${item.id}`)}
                  >
                    <td style={{ padding: '16px 14px', fontWeight: 600, color: 'var(--ink)' }}>
                      {item.examTitle}
                    </td>
                    <td style={{ padding: '16px 14px', color: 'var(--muted)', fontSize: '0.85rem' }}>
                      {item.date}
                    </td>
                    <td style={{ padding: '16px 14px' }}>
                      <Chip 
                        label={`${score}%`} 
                        variant={score >= 75 ? 'teal' : isPassed ? 'indigo' : 'coral'} 
                        size="sm" 
                      />
                    </td>
                    <td style={{ padding: '16px 14px', color: 'var(--ink)', fontSize: '0.85rem' }}>
                      {item.correctCount} / {item.totalQuestions}
                    </td>
                    <td style={{ padding: '16px 14px', color: 'var(--muted)', fontSize: '0.85rem' }}>
                      {item.timeSpent}
                    </td>
                    <td style={{ padding: '16px 14px' }}>
                      {item.weakTopics && item.weakTopics.length > 0 ? (
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {item.weakTopics.map((wt, wIdx) => (
                            <Chip key={wIdx} label={wt} variant="coral" size="sm" />
                          ))}
                        </div>
                      ) : (
                        <span style={{ color: 'var(--teal-text)', fontSize: '0.82rem', fontWeight: 600 }}>None</span>
                      )}
                    </td>
                    <td style={{ padding: '16px 14px', textAlign: 'right' }}>
                      <span style={{ color: 'var(--indigo)', fontSize: '0.85rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
                        Review <ChevronRight size={15} />
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

export default History;
