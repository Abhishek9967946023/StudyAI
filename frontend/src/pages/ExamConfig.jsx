/**
=============================================================================
StudyAI — 6. Exam Configuration Page (Step 3: Exam Setup)
=============================================================================
Configurable parameters:
- Number of questions (5, 8, 10, 15, 20)
- Question type (MCQ, True/False, Short, Long, Mixed)
- Difficulty (Easy, Medium, Hard, Adaptive)
- Dynamic Topic Selection (loaded from active material)
- Time Limit, Randomize, Citations toggle
=============================================================================
*/

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  GraduationCap, 
  Sparkles, 
  Clock, 
  Shuffle, 
  HelpCircle, 
  ShieldCheck, 
  ArrowRight,
  Loader2,
  X,
  Zap,
  AlertCircle,
  UploadCloud
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { StepGuide } from '../components/layout/StepGuide';
import { generateExam } from '../services/examsService';
import { getMaterialAnalysis, getMaterials, getActiveMaterialId, setActiveMaterialId } from '../services/materialsService';

const QUESTION_TYPES = [
  { value: 'MCQ', label: 'Multiple Choice' },
  { value: 'MSQ', label: 'Multiple Select' },
  { value: 'Mixed', label: 'Mixed' },
  { value: 'Short', label: 'Short Answer' },
  { value: 'Long', label: 'Long Answer' },
  { value: 'fill_blank', label: 'Fill in the Blank' },
  { value: 'numerical', label: 'Numerical' },
  { value: 'True/False', label: 'True / False' }
];

export function ExamConfig() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTargetId = searchParams.get('id') || getActiveMaterialId();

  const [selectedMaterialId, setSelectedMaterialId] = useState(initialTargetId);
  const [materialsList, setMaterialsList] = useState([]);
  const [questionCount, setQuestionCount] = useState(8);
  const [questionType, setQuestionType] = useState('Mixed');
  const [marksPerQuestion, setMarksPerQuestion] = useState(5);
  const [difficulty, setDifficulty] = useState('Medium');
  const [selectedTopic, setSelectedTopic] = useState('All Topics');
  const [timeLimitMinutes, setTimeLimitMinutes] = useState(12);
  const [randomize, setRandomize] = useState(true);
  const [includeExplanations, setIncludeExplanations] = useState(true);
  const [importantTopicsOnly, setImportantTopicsOnly] = useState(false);
  const [fastMode, setFastMode] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStage, setGenerationStage] = useState('Extracting verified syllabus context...');
  const [generateError, setGenerateError] = useState(null);
  const [topicsList, setTopicsList] = useState(['All Topics']);
  const [docSubject, setDocSubject] = useState('');
  const [docTitle, setDocTitle] = useState('');

  const abortControllerRef = useRef(null);

  // Clean up any ongoing generation on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Load materials list
  useEffect(() => {
    async function loadMats() {
      try {
        const mats = await getMaterials().catch(() => []);
        const valid = Array.isArray(mats) ? mats : [];
        setMaterialsList(valid);
        if (!selectedMaterialId && valid[0]) {
          setSelectedMaterialId(valid[0].id);
        }
      } catch {
        setMaterialsList([]);
      }
    }
    loadMats();
  }, []);

  // Dynamically load topics for the selected material
  useEffect(() => {
    if (!selectedMaterialId) return;
    async function loadTopics() {
      try {
        const analysis = await getMaterialAnalysis(selectedMaterialId);
        if (analysis?.subject) {
          setDocSubject(analysis.subject);
        }
        if (analysis?.title) {
          setDocTitle(analysis.title);
        }
        if (analysis?.topics && analysis.topics.length > 0) {
          const names = analysis.topics.map(t => t.name);
          setTopicsList(['All Topics', ...names]);
        }
      } catch (err) {
        console.warn('Could not load dynamic topics:', err);
      }
    }
    loadTopics();
  }, [selectedMaterialId]);

  const handleStartExam = async () => {
    setGenerateError(null);
    setIsGenerating(true);
    setGenerationStage('Reading syllabus & extracting document context...');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const timer1 = setTimeout(() => {
      setGenerationStage('Synthesizing grounded questions & citations...');
    }, 1200);

    const timer2 = setTimeout(() => {
      setGenerationStage('Validating answers & pedagogical models...');
    }, 2800);

    try {
      const exam = await generateExam({
        materialId: selectedMaterialId,
        questionCount,
        questionType,
        marksPerQuestion,
        difficulty,
        topic: selectedTopic === 'All Topics' ? 'All' : selectedTopic,
        timeLimitMinutes,
        randomize,
        includeExplanations,
        importantTopicsOnly,
        fast_mode: fastMode
      }, { signal: controller.signal });

      clearTimeout(timer1);
      clearTimeout(timer2);
      navigate(`/exam/${exam.id || exam.exam_id}`);
    } catch (err) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      if (err.name === 'AbortError' || err.isCancelled || controller.signal.aborted) {
        console.log('Exam generation cancelled by user.');
        setGenerateError('Exam generation was cancelled.');
      } else {
        console.error('Exam generation error:', err);
        setGenerateError(err.message || 'Failed to generate exam. Please check your network or try Fast Mode.');
      }
      setIsGenerating(false);
    }
  };

  const handleCancelGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsGenerating(false);
    setGenerateError('Exam generation cancelled.');
  };

  return (
    <div className="fade-in exam-config-page" style={{ maxWidth: '850px', margin: '0 auto' }}>
      <StepGuide currentStep={3} nextUpText="Take the timed practice exam in distraction-free mode." />

      <div className="upload-heading" style={{ marginBottom: '28px' }}>
        <p className="eyebrow-upload">STEP 3 • EXAM GENERATOR</p>
        <h1 style={{ fontSize: '2.1rem', fontWeight: 700, margin: '8px 0' }}>
          Configure Your Exam
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '0.95rem', margin: 0 }}>
          Choose question count, question type, and difficulty level to test your mastery.
        </p>
      </div>

      <Card style={{ padding: '32px' }}>
        {/* Material Selection Dropdown */}
        <div style={{ marginBottom: '24px', paddingBottom: '20px', borderBottom: '1px solid var(--border)' }}>
          <label style={{ display: 'block', fontSize: '0.95rem', fontWeight: 700, color: 'var(--ink)', marginBottom: '8px' }}>
            Select Study Material for Exam
          </label>
          <select
            value={selectedMaterialId}
            onChange={(e) => {
              setSelectedMaterialId(e.target.value);
              setActiveMaterialId(e.target.value);
            }}
            style={{
              width: '100%',
              padding: '12px 14px',
              borderRadius: 'var(--radius-btn)',
              border: '1px solid var(--border)',
              backgroundColor: 'var(--bg)',
              color: 'var(--ink)',
              fontSize: '0.92rem',
              fontWeight: 600
            }}
          >
            {materialsList.length > 0 ? (
              materialsList.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.title} ({m.subject || 'Academic Text'})
                </option>
              ))
            ) : (
              <option value="" disabled>
                No study materials uploaded yet — please upload a document first
              </option>
            )}
          </select>
        </div>
        {/* Friend's Option Rows: Number of Questions */}
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '8px' }}>Number of Questions</h2>
          <div className="option-row" style={{ margin: '8px 0 16px 0' }}>
            {[5, 10, 15, 20].map((count) => (
              <button
                key={count}
                type="button"
                className={questionCount === count ? 'option-button selected' : 'option-button'}
                onClick={() => {
                  setQuestionCount(count);
                  setTimeLimitMinutes(Math.max(5, Math.ceil(count * 1.5)));
                }}
              >
                {count} Questions
              </button>
            ))}
          </div>
        </div>

        {/* Friend's Option Rows: Question Type */}
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '8px' }}>Question Type</h2>
          <div className="option-row" style={{ margin: '8px 0 16px 0' }}>
            {QUESTION_TYPES.map(({ value, label }) => (
              <button
                key={value}
                type="button"
                className={questionType === value ? 'option-button selected' : 'option-button'}
                onClick={() => setQuestionType(value)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Friend's Option Rows: Difficulty Level */}
        <div style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '8px' }}>Difficulty Level</h2>
          <div className="option-row" style={{ margin: '8px 0 16px 0' }}>
            {['Easy', 'Medium', 'Hard', 'Adaptive'].map((level) => (
              <button
                key={level}
                type="button"
                className={difficulty === level ? 'option-button selected' : 'option-button'}
                onClick={() => setDifficulty(level)}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        {/* Detailed Controls */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '24px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '8px' }}>
              Question Count
            </label>
            <select
              value={questionCount}
              onChange={(e) => {
                const c = parseInt(e.target.value, 10);
                setQuestionCount(c);
                setTimeLimitMinutes(Math.max(5, Math.ceil(c * 1.5)));
              }}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 'var(--radius-btn)',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--bg)',
                color: 'var(--ink)',
                fontSize: '0.9rem'
              }}
            >
              <option value="5">5 Questions (~7 mins)</option>
              <option value="8">8 Questions (~12 mins)</option>
              <option value="10">10 Questions (~15 mins)</option>
              <option value="15">15 Questions (~25 mins)</option>
              <option value="20">20 Questions (~30 mins)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '8px' }}>
              Format & Types
            </label>
            <select
              value={questionType}
              onChange={(e) => setQuestionType(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 'var(--radius-btn)',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--bg)',
                color: 'var(--ink)',
                fontSize: '0.9rem'
              }}
            >
              {QUESTION_TYPES.map(({ value, label }) => (
                <option key={value} value={value}>{label}{value === 'Mixed' ? ' (varied formats)' : ' Only'}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '8px' }}>
              Difficulty Tier
            </label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 'var(--radius-btn)',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--bg)',
                color: 'var(--ink)',
                fontSize: '0.9rem'
              }}
            >
              <option value="Easy">Easy (Direct factual recall)</option>
              <option value="Medium">Medium (Mechanisms & processes)</option>
              <option value="Hard">Hard (Deep analytical synthesis)</option>
              <option value="Adaptive">Adaptive (Dynamic challenge)</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '8px' }}>
              Marks per Question
            </label>
            <select
              value={marksPerQuestion}
              onChange={(e) => setMarksPerQuestion(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 'var(--radius-btn)',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--bg)',
                color: 'var(--ink)',
                fontSize: '0.9rem'
              }}
            >
              <option value="2">2 marks — concise response</option>
              <option value="5">5 marks — explain the key steps</option>
              <option value="10">10 marks — structured explanation</option>
            </select>
          </div>
        </div>

        {/* Topic Focus Filter */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '8px' }}>
            Topic Focus
          </label>
          <select
            value={selectedTopic}
            onChange={(e) => setSelectedTopic(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: 'var(--radius-btn)',
              border: '1px solid var(--border)',
              backgroundColor: 'var(--bg)',
              color: 'var(--ink)',
              fontSize: '0.9rem'
            }}
          >
            {topicsList.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Time Limit & Toggles */}
        <div style={{ 
          padding: '16px', 
          backgroundColor: 'var(--bg)', 
          borderRadius: '14px', 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '14px',
          marginBottom: '28px'
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={randomize} 
              onChange={e => setRandomize(e.target.checked)} 
            />
            <span>Randomize Question Order</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={includeExplanations} 
              onChange={e => setIncludeExplanations(e.target.checked)} 
            />
            <span>Attach Grounded Citations</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={importantTopicsOnly} 
              onChange={e => setImportantTopicsOnly(e.target.checked)} 
            />
            <span>High-Yield Topics Only (&ge;60%)</span>
          </label>

          <label style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            fontSize: '0.85rem', 
            cursor: 'pointer',
            color: fastMode ? 'var(--indigo)' : 'inherit',
            fontWeight: fastMode ? 700 : 400
          }}>
            <input 
              type="checkbox" 
              checked={fastMode} 
              onChange={e => setFastMode(e.target.checked)} 
            />
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Zap size={14} color="var(--indigo)" />
              <span>⚡ Fast Synthesis (&lt;2s Instant)</span>
            </span>
          </label>
        </div>

        {/* Grounding Seal */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--teal)', fontWeight: 600, marginBottom: '20px' }}>
          <ShieldCheck size={16} />
          <span>Strict Material Grounding: Every question connects to verified source paragraphs.</span>
        </div>

        {/* Cancelled or Error Notice */}
        {generateError && (
          <div style={{
            padding: '12px 16px',
            borderRadius: '10px',
            backgroundColor: generateError.includes('cancelled') ? 'var(--bg)' : 'var(--coral-tint)',
            border: `1px solid ${generateError.includes('cancelled') ? 'var(--border)' : 'var(--coral)'}`,
            color: generateError.includes('cancelled') ? 'var(--muted)' : 'var(--coral-text)',
            fontSize: '0.88rem',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '10px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={16} />
              <span>{generateError}</span>
            </div>
            <button
              type="button"
              onClick={() => setGenerateError(null)}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'currentColor' }}
            >
              <X size={14} />
            </button>
          </div>
        )}

        {/* Active Generation State Banner with Cancel */}
        {isGenerating && (
          <div style={{
            padding: '16px 20px',
            borderRadius: '14px',
            backgroundColor: 'var(--indigo-tint)',
            border: '1.5px solid var(--indigo)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
            flexWrap: 'wrap'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Loader2 size={24} className="animate-spin" color="var(--indigo)" />
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--indigo-text)' }}>
                  Generating Practice Exam...
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                  {generationStage}
                </div>
              </div>
            </div>

            <Button
              type="button"
              variant="outline"
              size="sm"
              icon={<X size={15} />}
              onClick={handleCancelGeneration}
              style={{
                borderColor: 'var(--coral)',
                color: 'var(--coral)',
                fontWeight: 600
              }}
            >
              Cancel Generation
            </Button>
          </div>
        )}

        {/* Generate Primary CTA / Cancel Controls */}
        {!isGenerating ? (
          <Button 
            variant="primary" 
            size="lg"
            style={{ width: '100%' }}
            icon={materialsList.length === 0 ? <UploadCloud size={18} /> : <GraduationCap size={18} />}
            iconRight={<ArrowRight size={16} />}
            onClick={materialsList.length === 0 ? () => navigate('/upload') : handleStartExam}
          >
            {materialsList.length === 0 
              ? 'Upload Study Material First' 
              : `Generate Exam (${questionCount} Questions • ${timeLimitMinutes} min)`}
          </Button>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '12px' }}>
            <Button
              variant="primary"
              size="lg"
              loading={true}
              disabled={true}
              style={{ opacity: 0.9 }}
            >
              {generationStage}
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="lg"
              icon={<X size={16} />}
              onClick={handleCancelGeneration}
              style={{
                backgroundColor: 'var(--coral-tint)',
                color: 'var(--coral)',
                borderColor: 'var(--coral)',
                fontWeight: 700
              }}
            >
              Cancel
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
