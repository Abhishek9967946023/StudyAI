/**
 * =============================================================================
 * StudyAI — Question Bank Screen (Screen 11)
 * =============================================================================
 * Features:
 * - Search bar across question texts, explanations, and topics
 * - Filter chips/selects by Topic, Difficulty, and Question Type
 * - Question cards displaying:
 *   - Topic, Difficulty, and Type chips
 *   - Question text
 *   - Selectable answers / reveal toggle
 *   - Verified AI Explanation
 *   - Exact source document citations (section & page)
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Database, 
  Search, 
  Filter, 
  BookOpen, 
  CheckCircle2, 
  ChevronDown, 
  ChevronUp, 
  Play, 
  Copy, 
  Check,
  FileText,
  Tag
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Skeleton } from '../components/ui/Skeleton';
import { getQuestions } from '../services/questionBankService';

export function QuestionBank() {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('All');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  const [selectedType, setSelectedType] = useState('All');

  // Expanded explanations
  const [expandedQuestions, setExpandedQuestions] = useState({});
  const [copiedId, setCopiedId] = useState(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await getQuestions({
          search,
          topic: selectedTopic,
          difficulty: selectedDifficulty,
          type: selectedType === 'All' ? 'All' : selectedType.toLowerCase()
        });
        setQuestions(data);
      } catch (err) {
        console.error('Failed to load questions:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [search, selectedTopic, selectedDifficulty, selectedType]);

  const toggleExpand = (id) => {
    setExpandedQuestions(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handleCopyCitation = (id, citation) => {
    if (!citation) return;
    navigator.clipboard.writeText(citation);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const availableTopics = Array.from(new Set(questions.map(q => q.topic).filter(Boolean)));
  const topicsList = ['All', ...(availableTopics.length > 0 ? availableTopics : ['Core Subject', 'Operational Mechanisms', 'Key Invariants'])];

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* 1. Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--indigo)', marginBottom: '4px' }}>
            <Database size={18} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Extracted Question Repository
            </span>
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
            Grounded Question Bank
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '0.96rem', margin: '6px 0 0 0' }}>
            Every item is strictly derived and grounded in your uploaded curriculum with exact source citations.
          </p>
        </div>

        <Button 
          variant="primary" 
          size="md"
          icon={<Play size={16} />}
          onClick={() => navigate('/exam-config')}
        >
          Generate Custom Exam
        </Button>
      </div>

      {/* 2. Search & Filter Bar */}
      <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Search Input */}
        <div style={{ position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)' }} />
          <input 
            type="text"
            placeholder="Search questions by concept, formula, keywords, or citations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 14px 12px 42px',
              borderRadius: '12px',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
              color: 'var(--ink)',
              fontSize: '0.95rem',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {/* Filter Controls Row */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', alignItems: 'center' }}>
          {/* Topic Select */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--muted)' }}>Topic:</span>
            <select 
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--ink)',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              {topicsList.map((t, idx) => (
                <option key={idx} value={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* Difficulty Select */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--muted)' }}>Difficulty:</span>
            <select 
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--ink)',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <option value="All">All Difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>
          </div>

          {/* Type Select */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--muted)' }}>Type:</span>
            <select 
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--ink)',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <option value="All">All Types</option>
              <option value="MCQ">Multiple Choice</option>
              <option value="TF">True / False</option>
              <option value="SHORT">Short Answer</option>
            </select>
          </div>

          <div style={{ marginLeft: 'auto', fontSize: '0.85rem', color: 'var(--muted)', fontWeight: 500 }}>
            Showing {questions.length} question{questions.length !== 1 ? 's' : ''}
          </div>
        </div>
      </Card>

      {/* 3. Question Cards Feed */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Skeleton height="140px" />
          <Skeleton height="140px" />
          <Skeleton height="140px" />
        </div>
      ) : questions.length === 0 ? (
        <Card style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--muted)' }}>
          <Database size={40} style={{ margin: '0 auto 12px auto', color: 'var(--muted)' }} />
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--ink)' }}>No questions found</div>
          <p style={{ margin: '6px 0 16px 0', fontSize: '0.9rem' }}>Try relaxing your search terms or filter criteria.</p>
          <Button variant="secondary" onClick={() => { setSearch(''); setSelectedTopic('All'); setSelectedDifficulty('All'); setSelectedType('All'); }}>
            Reset Filters
          </Button>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {questions.map((q, idx) => {
            const isExpanded = !!expandedQuestions[q.id];
            const qType = (q.type || 'mcq').toLowerCase();
            const isShort = qType === 'short' || qType === 'short_answer';

            return (
              <Card 
                key={q.id || idx}
                style={{ 
                  padding: '22px 24px', 
                  display: 'flex', 
                  flexDirection: 'column', 
                  gap: '14px',
                  border: '1px solid var(--border)' 
                }}
              >
                {/* Meta Badges */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, color: 'var(--muted)', fontSize: '0.88rem' }}>#{idx + 1}</span>
                    <Chip label={q.topic} variant="indigo" size="sm" />
                    <Chip label={q.difficulty} size="sm" />
                    <Chip label={isShort ? 'SHORT ANSWER' : q.type?.toUpperCase() || 'MCQ'} variant="neutral" size="sm" />
                  </div>

                  <button
                    onClick={() => toggleExpand(q.id)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--indigo)',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    {isExpanded ? 'Hide Solution' : 'View Solution & Citation'}
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                </div>

                {/* Prompt */}
                <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--ink)', lineHeight: 1.45 }}>
                  {q.question}
                </div>

                {/* Options List or Short Answer Hint */}
                {q.options && q.options.length > 0 ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '8px' }}>
                    {q.options.map((opt, oIdx) => {
                      const correctAnswers = Array.isArray(q.correctAnswer) ? q.correctAnswer : [q.correctAnswer];
                      const isCorrect = isExpanded && correctAnswers.includes(opt);
                      return (
                        <div 
                          key={oIdx}
                          style={{
                            padding: '10px 14px',
                            borderRadius: '10px',
                            fontSize: '0.88rem',
                            border: `1px solid ${isCorrect ? 'var(--teal)' : 'var(--border)'}`,
                            background: isCorrect ? 'var(--teal-tint)' : 'var(--bg)',
                            color: isCorrect ? 'var(--teal-text)' : 'var(--ink)',
                            fontWeight: isCorrect ? 600 : 400,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                          }}
                        >
                          {isCorrect && <CheckCircle2 size={16} color="var(--teal)" />}
                          <span>{opt}</span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: 'var(--muted)', fontStyle: 'italic', padding: '6px 0' }}>
                    Short Answer Format &bull; Click "View Solution & Citation" to inspect the reference model response.
                  </div>
                )}

                {/* Expanded Details: AI Explanation & Citation */}
                {isExpanded && (
                  <div style={{ marginTop: '6px', paddingTop: '14px', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ background: 'var(--bg)', padding: '12px 16px', borderRadius: '10px', fontSize: '0.9rem', lineHeight: 1.5, color: 'var(--ink)' }}>
                      <strong style={{ color: 'var(--teal-text)' }}>Correct Answer: </strong>
                      {Array.isArray(q.correctAnswer) ? q.correctAnswer.join(', ') : q.correctAnswer}
                      <div style={{ marginTop: '6px', color: 'var(--ink)' }}>
                        <strong>Explanation: </strong> {q.explanation}
                      </div>
                    </div>

                    {q.citation && (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--surface)', border: '1px dashed var(--border)', padding: '10px 14px', borderRadius: '10px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: 'var(--muted)' }}>
                          <FileText size={15} color="var(--indigo)" />
                          <span><strong>Source Evidence: </strong>{q.citation}</span>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          icon={copiedId === q.id ? <Check size={14} color="var(--teal)" /> : <Copy size={14} />}
                          onClick={() => handleCopyCitation(q.id, q.citation)}
                        >
                          {copiedId === q.id ? 'Copied' : 'Copy'}
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default QuestionBank;
