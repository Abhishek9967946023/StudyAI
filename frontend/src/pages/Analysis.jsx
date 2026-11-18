/**
=============================================================================
StudyAI — 4. Material Analysis Page (Step 2: Review)
=============================================================================
Features:
- Material Title, Page Count, Character Count, Estimated Reading Time
- Executive synthesis & Key Concepts
- Identified syllabus topics with calculated Material Importance scores
- Interactive Knowledge Map
- Action buttons to "View Full Summary" and "Generate Exam"
=============================================================================
*/

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  FileSearch, 
  BookOpen, 
  GraduationCap, 
  Layers, 
  ArrowRight, 
  Sparkles, 
  CheckCircle2,
  Share2
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { StepGuide } from '../components/layout/StepGuide';
import { getMaterialAnalysis, getActiveMaterialId } from '../services/materialsService';

export function Analysis() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const targetId = searchParams.get('id') || getActiveMaterialId();

  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    async function load() {
      setLoading(true);
      setErrorMsg('');
      try {
        const data = await getMaterialAnalysis(targetId);
        setAnalysis(data);
      } catch (err) {
        setErrorMsg(err.message || 'Failed to load analysis dossier.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [targetId]);

  if (loading) {
    return <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--muted)' }}>Analyzing curriculum and synthesizing topics...</div>;
  }

  if (errorMsg || !analysis) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--coral)', marginBottom: '16px' }}>{errorMsg || 'Analysis dossier could not be loaded.'}</p>
        <Button variant="secondary" onClick={() => navigate('/upload')}>Return to Upload</Button>
      </div>
    );
  }

  const concepts = analysis.keyConcepts || analysis.keyPoints || [];
  const topics = analysis.topics || [];

  return (
    <div className="fade-in">
      <StepGuide currentStep={2} nextUpText="Configure exam parameters or inspect detailed study notes." />

      {/* Header Info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
            <Chip variant="teal" icon={<CheckCircle2 size={13} />}>Indexed & Ready</Chip>
            {analysis.subject && <Chip variant="indigo">{analysis.subject}</Chip>}
            {analysis.original_language && <Chip variant="neutral">{analysis.original_language.toUpperCase()}</Chip>}
            <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
              {analysis.pages || analysis.page_count || 1} Pages &bull; {(analysis.charCount || 0).toLocaleString()} Characters &bull; ~{analysis.estimatedReadTime || '3 min'} Read
            </span>
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 700 }}>{analysis.title}</h1>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Button 
            variant="secondary"
            icon={<BookOpen size={16} />}
            onClick={() => navigate(`/summary?id=${targetId}`)}
          >
            Study Notes & Formulas
          </Button>
          <Button 
            variant="primary"
            icon={<GraduationCap size={16} />}
            iconRight={<ArrowRight size={16} />}
            onClick={() => navigate(`/exam-config?id=${targetId}`)}
          >
            Generate Practice Exam
          </Button>
        </div>
      </div>

      {/* Executive Synthesis Card */}
      <Card style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '8px', backgroundColor: 'var(--indigo-tint)', color: 'var(--indigo)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Sparkles size={16} />
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>Executive Synthesis</h3>
        </div>
        <p style={{ fontSize: '0.95rem', color: 'var(--ink)', lineHeight: 1.65 }}>
          {analysis.executiveSummary}
        </p>
      </Card>

      {/* Two Columns: Key Concepts & Extracted Topics with Importance */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Key Concepts */}
        <Card>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px' }}>
            Core Academic Principles
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {concepts.map((concept, idx) => (
              <div 
                key={idx}
                style={{
                  padding: '12px 14px',
                  borderRadius: '12px',
                  backgroundColor: 'var(--bg)',
                  border: '1px solid var(--border)'
                }}
              >
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--ink)', marginBottom: '4px' }}>
                  {concept.title || concept.concept || `Principle ${idx + 1}`}
                </div>
                <div style={{ fontSize: '0.825rem', color: 'var(--muted)', lineHeight: 1.5 }}>
                  {concept.text || concept.description || ''}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Extracted Syllabus Topics with Material Importance */}
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Identified Syllabus Topics</h3>
            <Chip variant="indigo">Curriculum Weight</Chip>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {topics.map((t, idx) => {
              const weightVal = t.weight !== undefined ? t.weight : (typeof t.importance === 'number' ? t.importance : 80);
              return (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ fontWeight: 600 }}>{t.name}</span>
                    <span style={{ fontWeight: 700, color: weightVal >= 80 ? 'var(--indigo)' : 'var(--muted)' }}>
                      {weightVal}% Weight
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border)', borderRadius: '999px', overflow: 'hidden' }}>
                    <div style={{ 
                      width: `${weightVal}%`, 
                      height: '100%', 
                      backgroundColor: weightVal >= 80 ? 'var(--indigo)' : 'var(--teal)' 
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Relational Knowledge Map Section */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Relational Knowledge Map</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>Theoretical dependencies between key concepts</span>
          </div>
          <Chip variant="neutral" icon={<Layers size={13} />}>Graph Dependencies</Chip>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {(analysis.knowledgeMap || topics.slice(0, 3).map((t, i, arr) => ({
            source: t.name,
            relation: "builds upon",
            target: arr[(i + 1) % arr.length]?.name || "Core Subject"
          }))).map((rel, idx) => (
            <div 
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                backgroundColor: 'var(--bg)',
                borderRadius: '10px',
                fontSize: '0.825rem'
              }}
            >
              <strong style={{ color: 'var(--ink)' }}>{rel.source}</strong>
              <span style={{ color: 'var(--muted)', fontSize: '0.75rem', fontStyle: 'italic' }}>&rarr; {rel.relation} &rarr;</span>
              <strong style={{ color: 'var(--indigo)' }}>{rel.target}</strong>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
