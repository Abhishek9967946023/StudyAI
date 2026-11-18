/**
 * =============================================================================
 * StudyAI — 5. Revision Screen (3D Flashcards & Adaptive Learning Loop)
 * =============================================================================
 * Features:
 * - Multi-document selector dropdown with URL param and localStorage synchronization
 * - 3D Interactive Flip Flashcards (Front: Question/Formula -> Back: Grounded Answer & Math)
 * - Category filter pills (All, Remediation, Formulas, Algorithms, Concepts, Traps)
 * - Keyboard navigation (Space to flip, Arrow keys to navigate, M for Mastered, R for Review)
 * - Active Recall Scratchpad for typing answers before revealing
 * - Priority Adaptive Curriculum Schedule with task persistence
 * - Quick Recall Drills for weak topics
 * - Printable High-Yield Revision Cheat Sheet with KaTeX math
 * - Zero infinite skeletons: authentic empty and error states
 * =============================================================================
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  CheckCircle2, 
  Circle, 
  Clock, 
  BookOpen, 
  Play, 
  RotateCcw, 
  Sparkles, 
  Calendar, 
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  X,
  Check,
  ArrowRight,
  HelpCircle,
  Award,
  Layers,
  Zap,
  Printer,
  Flame,
  XCircle,
  Shuffle,
  FileText,
  UploadCloud,
  LogIn
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { ProgressBar } from '../components/ui/ProgressBar';
import { StepGuide } from '../components/layout/StepGuide';
import { Modal } from '../components/ui/Modal';
import { Skeleton } from '../components/ui/Skeleton';
import { getRevisionPlan, markRevisionItemCompleted, normalizeRevisionCard } from '../services/revisionService';
import { getQuestions } from '../services/questionBankService';
import { getMaterials, getActiveMaterialId, setActiveMaterialId, getMaterialSummary } from '../services/materialsService';
import { StudyMarkdown } from '../components/common/StudyMarkdown';

export function Revision() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Materials & Document Selection
  const [materialsList, setMaterialsList] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [materialsLoaded, setMaterialsLoaded] = useState(false);

  // Plan and Summary State
  const [plan, setPlan] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [authRequired, setAuthRequired] = useState(false);

  // Active Tab: 'flashcards' | 'plan' | 'cheatsheet'
  const [activeTab, setActiveTab] = useState('flashcards');

  // Flashcards state
  const [cardIndex, setCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [masteredCards, setMasteredCards] = useState({});
  const [scratchpadAnswers, setScratchpadAnswers] = useState({});
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isShuffled, setIsShuffled] = useState(false);

  // Modals state
  const [activeNotesModal, setActiveNotesModal] = useState(null);
  const [activeDrillModal, setActiveDrillModal] = useState(null);
  const [drillQuestions, setDrillQuestions] = useState([]);
  const [drillAnswers, setDrillAnswers] = useState({});
  const [drillSubmitted, setDrillSubmitted] = useState(false);

  // 1. Initial Load: Fetch available materials list
  useEffect(() => {
    let isMounted = true;
    async function loadMaterials() {
      try {
        const mats = await getMaterials().catch((err) => {
          if (err?.status === 401) setAuthRequired(true);
          return [];
        });
        if (!isMounted) return;

        const validMats = Array.isArray(mats) ? mats : [];
        setMaterialsList(validMats);

        // Determine initial document ID:
        // Priority 1: Query param `?id=` or `?doc_id=`
        // Priority 2: Stored active material ID in localStorage
        // Priority 3: First available material
        const queryId = searchParams.get('id') || searchParams.get('doc_id');
        const storedId = getActiveMaterialId();

        let initialId = null;
        if (queryId && validMats.some(m => String(m.id) === String(queryId))) {
          initialId = String(queryId);
        } else if (storedId && validMats.some(m => String(m.id) === String(storedId))) {
          initialId = String(storedId);
        } else if (validMats.length > 0) {
          initialId = String(validMats[0].id);
        }

        if (initialId) {
          setSelectedDocId(initialId);
          setActiveMaterialId(initialId);
        }
      } catch (err) {
        console.error('Failed to load materials list for revision:', err);
      } finally {
        if (isMounted) setMaterialsLoaded(true);
      }
    }

    loadMaterials();
    return () => { isMounted = false; };
  }, [searchParams]);

  // 2. Fetch revision plan and summary whenever selectedDocId changes
  const loadPlanAndSummary = useCallback(async (docId) => {
    setLoading(true);
    setFetchError(null);
    setAuthRequired(false);
    setIsFlipped(false);
    setCardIndex(0);

    try {
      const [planData, sumData] = await Promise.all([
        getRevisionPlan(docId).catch(err => {
          if (err?.status === 401) setAuthRequired(true);
          throw err;
        }),
        getMaterialSummary(docId).catch(() => null)
      ]);

      setPlan(planData);
      setSummaryData(sumData);

      // If backend returned a canonical documentId, ensure local sync
      if (planData?.documentId && String(planData.documentId) !== String(docId)) {
        setSelectedDocId(String(planData.documentId));
        setActiveMaterialId(String(planData.documentId));
      }
    } catch (err) {
      console.error('Failed to load revision plan:', err);
      if (err?.status === 401) {
        setAuthRequired(true);
      } else {
        setFetchError(err?.message || 'Unable to connect to revision service.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!materialsLoaded) return;
    loadPlanAndSummary(selectedDocId);
  }, [selectedDocId, materialsLoaded, loadPlanAndSummary]);

  // Handle Document Selection Switcher
  const handleDocChange = (e) => {
    const newDocId = e.target.value;
    setSelectedDocId(newDocId);
    setActiveMaterialId(newDocId);
    setSearchParams({ id: newDocId });
  };

  const handleToggleCompleted = async (itemId, currentCompleted) => {
    setPlan(prev => {
      if (!prev) return prev;
      const updatedItems = (prev.items || []).map(it => 
        it.id === itemId ? { ...it, completed: !currentCompleted } : it
      );
      const count = updatedItems.filter(it => it.completed).length;
      return {
        ...prev,
        completedItemsCount: count,
        items: updatedItems
      };
    });

    try {
      const updatedPlan = await markRevisionItemCompleted(itemId, !currentCompleted);
      if (updatedPlan) setPlan(updatedPlan);
    } catch (err) {
      console.error('Error marking item completed:', err);
    }
  };

  const handleOpenDrill = async (item) => {
    try {
      const qs = await getQuestions({ topic: item.topic });
      setDrillQuestions(qs.length > 0 ? qs.slice(0, 3) : []);
      setDrillAnswers({});
      setDrillSubmitted(false);
      setActiveDrillModal(item);
    } catch (err) {
      console.error('Failed to load drill questions:', err);
    }
  };

  // Construct Canonical Flashcards Deck
  const allFlashcards = useMemo(() => {
    const list = [];
    const seenPrompts = new Set();

    const addCard = (rawCard, idx) => {
      const card = normalizeRevisionCard(rawCard, idx);
      if (!card.answer || card.answer.trim().length < 3) return;
      const key = (card.question || card.prompt || '').toLowerCase().trim();
      if (key && !seenPrompts.has(key)) {
        seenPrompts.add(key);
        list.push(card);
      }
    };

    // 1. Canonical cards generated by backend revision engine
    if (Array.isArray(plan?.cards) && plan.cards.length > 0) {
      plan.cards.forEach((c, i) => addCard(c, i));
    }

    // 2. Plan items enriched with question/answer
    if (Array.isArray(plan?.items)) {
      plan.items.forEach((item, i) => {
        if (item.question && item.answer) {
          addCard({
            id: `fc-plan-${item.id}`,
            topic: item.topic,
            priority: item.priority || 'High',
            category: 'Remediation Task',
            question: item.question,
            prompt: item.question,
            answer: item.answer,
            explanation: item.explanation || item.reason || '',
            bulletPoints: item.notes || [],
            source: item.source || {}
          }, list.length + i);
        } else if (item.topic) {
          const notesText = Array.isArray(item.notes) ? item.notes.join('\n') : '';
          const ansText = item.conceptNotes || notesText || item.reason || '';
          if (ansText && ansText.length > 3) {
            addCard({
              id: `fc-plan-${item.id}`,
              topic: item.topic,
              priority: item.priority || 'High',
              category: 'Remediation Task',
              question: `What is the key mechanism and function of ${item.topic}?`,
              prompt: `What is the key mechanism and function of ${item.topic}?`,
              answer: ansText,
              explanation: item.reason || '',
              bulletPoints: item.notes || []
            }, list.length + i);
          }
        }
      });
    }

    // 3. Complement from summaryData (concept cards & formulas)
    const sg = summaryData?.study_guide || summaryData?.modes?.standard || summaryData || {};
    
    (sg.concept_cards || sg.concepts || []).forEach((c, i) => {
      const term = c.term || c.concept;
      const ans = c.definition || c.def || c.intuition || c.simple_explanation;
      if (term && ans) {
        addCard({
          id: `fc-sum-c-${i}`,
          topic: term,
          category: 'Definition & Concept',
          priority: 'Standard',
          question: `Define and explain: **${term}**`,
          prompt: `Define and explain: **${term}**`,
          answer: ans,
          explanation: c.in_depth || c.detailed_explanation || c.why_it_matters || '',
          bulletPoints: [c.intuition, c.why_it_matters].filter(Boolean),
          source: { page: c.source_page || 1 }
        }, list.length + i);
      }
    });

    (sg.formulas || []).forEach((f, i) => {
      const name = f.name || f.title;
      const form = f.formula || f.value;
      if (name && form) {
        addCard({
          id: `fc-sum-f-${i}`,
          topic: name,
          category: 'Mathematical Formula',
          priority: 'High',
          question: `What is the mathematical equation and definition for **${name}**?`,
          prompt: `What is the mathematical equation and definition for **${name}**?`,
          answer: `$$\n${form}\n$$`,
          explanation: f.intuition || '',
          bulletPoints: [`Equation: ${form}`],
          source: { page: f.page || 1 }
        }, list.length + i);
      }
    });

    // Fallback card if empty
    if (list.length === 0) {
      list.push(normalizeRevisionCard({
        id: 'fc-default-1',
        topic: 'Active Recall',
        category: 'Concept Review',
        question: 'What is the primary topic of this study material?',
        prompt: 'What is the primary topic of this study material?',
        answer: plan?.documentTitle ? `The core subject is **${plan.documentTitle}**, covering essential concepts, formulas, and verified exam principles.` : 'Comprehensive technical concepts and principles from your uploaded document.',
        explanation: 'Review the generated summary and exam questions for targeted practice.'
      }, 0));
    }

    return list;
  }, [plan, summaryData]);

  // Extract Categories for Filtering
  const availableCategories = useMemo(() => {
    const cats = new Set(['All']);
    allFlashcards.forEach(c => {
      if (c.category) cats.add(c.category);
    });
    return Array.from(cats);
  }, [allFlashcards]);

  // Filter & Shuffle Flashcards
  const flashcards = useMemo(() => {
    let filtered = selectedCategory === 'All' 
      ? [...allFlashcards]
      : allFlashcards.filter(c => c.category === selectedCategory);

    if (isShuffled) {
      // Deterministic seeded shuffle based on id
      filtered = [...filtered].sort((a, b) => (a.id > b.id ? 1 : -1));
    }
    return filtered.length > 0 ? filtered : allFlashcards;
  }, [allFlashcards, selectedCategory, isShuffled]);

  const safeCardIndex = Math.min(cardIndex, Math.max(0, flashcards.length - 1));
  const currentCard = flashcards[safeCardIndex] || flashcards[0];
  const masteredCount = Object.values(masteredCards).filter(Boolean).length;
  const flashcardProgress = Math.round((masteredCount / (flashcards.length || 1)) * 100);

  const handleRateCard = (isMastered) => {
    if (!currentCard) return;
    setMasteredCards(prev => ({
      ...prev,
      [currentCard.id]: isMastered
    }));
    // Auto advance to next card after slight delay
    setTimeout(() => {
      setIsFlipped(false);
      if (cardIndex < flashcards.length - 1) {
        setCardIndex(cardIndex + 1);
      }
    }, 250);
  };

  const handleNextCard = () => {
    setIsFlipped(false);
    setCardIndex((prev) => (prev + 1) % flashcards.length);
  };

  const handlePrevCard = () => {
    setIsFlipped(false);
    setCardIndex((prev) => (prev - 1 + flashcards.length) % flashcards.length);
  };

  const handleCardClick = (e) => {
    // If user highlighted text to copy, do not trigger card flip
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) return;
    // If click originated from input, button, select, or link, do not trigger flip
    if (e.target.closest('button, input, textarea, a, select')) return;
    setIsFlipped(prev => !prev);
  };

  // Keyboard navigation for active recall
  useEffect(() => {
    if (activeTab !== 'flashcards') return;

    const handleKeyDown = (e) => {
      // Ignore if user is typing into input or textarea
      const tag = document.activeElement?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

      if (e.code === 'Space') {
        e.preventDefault();
        setIsFlipped(prev => !prev);
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        handleNextCard();
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        handlePrevCard();
      } else if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        handleRateCard(true);
      } else if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        handleRateCard(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeTab, flashcards.length, currentCard]);

  const items = Array.isArray(plan?.items) ? plan.items : [];
  const completedCount = items.filter(i => i.completed).length;
  const totalCount = items.length || 1;
  const progressPercent = Math.round((completedCount / totalCount) * 100);

  // =========================================================================
  // VIEW: AUTHENTICATION REQUIRED
  // =========================================================================
  if (authRequired) {
    return (
      <div className="fade-in" style={{ maxWidth: '800px', margin: '40px auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <StepGuide currentStep={5} />
        <Card style={{ padding: '48px 32px', textAlign: 'center', background: 'var(--surface)' }}>
          <LogIn size={40} color="var(--indigo)" style={{ margin: '0 auto 16px auto', display: 'block' }} />
          <h2 style={{ fontSize: '1.45rem', fontWeight: 700, margin: '0 0 8px 0', color: 'var(--ink)' }}>
            Please Log In to Access Revision
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.94rem', maxWidth: '460px', margin: '0 auto 24px auto' }}>
            Your personalized revision plan, 3D flashcards, and topic progress are synchronized securely with your student account.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
            <Button variant="primary" icon={<LogIn size={16} />} onClick={() => navigate('/login')}>
              Log In
            </Button>
            <Button variant="outline" onClick={() => loadPlanAndSummary(selectedDocId)}>
              Retry Connection
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // =========================================================================
  // VIEW: NO STUDY MATERIALS UPLOADED
  // =========================================================================
  if (materialsLoaded && materialsList.length === 0 && !loading) {
    return (
      <div className="fade-in" style={{ maxWidth: '800px', margin: '40px auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <StepGuide currentStep={5} />
        <Card style={{ padding: '48px 32px', textAlign: 'center', background: 'var(--surface)' }}>
          <UploadCloud size={44} color="var(--indigo)" style={{ margin: '0 auto 16px auto', display: 'block', opacity: 0.85 }} />
          <h2 style={{ fontSize: '1.45rem', fontWeight: 700, margin: '0 0 8px 0', color: 'var(--ink)' }}>
            No Study Materials Uploaded Yet
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.94rem', maxWidth: '480px', margin: '0 auto 24px auto', lineHeight: 1.6 }}>
            Upload your lecture notes, textbook chapters, or exam syllabus in the Upload section. StudyAI will automatically generate grounded 3D flashcards, formula cheat sheets, and priority practice drills.
          </p>
          <Button variant="primary" size="lg" icon={<UploadCloud size={18} />} onClick={() => navigate('/upload')}>
            Upload Your First Document
          </Button>
        </Card>
      </div>
    );
  }

  // =========================================================================
  // VIEW: LOADING SKELETON
  // =========================================================================
  if (loading && !plan) {
    return (
      <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <StepGuide currentStep={5} />
        <Skeleton height="80px" />
        <Skeleton height="380px" />
        <Skeleton height="120px" />
      </div>
    );
  }

  // =========================================================================
  // VIEW: ERROR STATE (WITH RETRY)
  // =========================================================================
  if (fetchError && !plan) {
    return (
      <div className="fade-in" style={{ maxWidth: '800px', margin: '40px auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <StepGuide currentStep={5} />
        <Card style={{ padding: '40px 32px', textAlign: 'center', background: 'var(--surface)' }}>
          <AlertTriangle size={36} color="var(--coral)" style={{ margin: '0 auto 14px auto', display: 'block' }} />
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: '0 0 8px 0', color: 'var(--ink)' }}>
            Could Not Load Revision Deck
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.92rem', maxWidth: '460px', margin: '0 auto 20px auto' }}>
            {fetchError}
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
            <Button variant="primary" icon={<RotateCcw size={16} />} onClick={() => loadPlanAndSummary(selectedDocId)}>
              Retry Loading
            </Button>
            <Button variant="outline" onClick={() => navigate('/upload')}>
              Upload New PDF
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // =========================================================================
  // MAIN VIEW: REVISION DASHBOARD
  // =========================================================================
  return (
    <div className="fade-in" style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <StepGuide currentStep={5} nextUpText="Master key flashcards and complete your daily revision plan." />

      {/* Header with Title and Document Switcher Dropdown */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--indigo)', marginBottom: '4px' }}>
            <RotateCcw size={18} />
            <span style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Adaptive Revision Loop
            </span>
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
            Smart Revision & Flashcards
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '0.94rem', margin: '4px 0 0 0' }}>
            Active recall calibrated from your study documents. Flip 3D flashcards and drill core principles.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Material Selector Dropdown */}
          {materialsList.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--surface)', padding: '6px 12px', borderRadius: '10px', border: '1px solid var(--border)' }}>
              <BookOpen size={16} color="var(--indigo)" />
              <label htmlFor="material-select" style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--muted)', whiteSpace: 'nowrap' }}>
                Material:
              </label>
              <select
                id="material-select"
                value={selectedDocId || ''}
                onChange={handleDocChange}
                style={{
                  background: 'transparent',
                  border: 'none',
                  fontSize: '0.88rem',
                  fontWeight: 700,
                  color: 'var(--ink)',
                  outline: 'none',
                  cursor: 'pointer',
                  maxWidth: '240px'
                }}
              >
                {materialsList.map(m => (
                  <option key={m.id} value={m.id} style={{ background: 'var(--surface)', color: 'var(--ink)' }}>
                    {m.title} {m.subject ? `(${m.subject})` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          <Button
            variant="primary"
            size="md"
            icon={<Play size={16} />}
            onClick={() => navigate(selectedDocId ? `/generate-exam?id=${selectedDocId}` : '/generate-exam')}
          >
            Practice Exam
          </Button>
        </div>
      </div>

      {/* Mode Selector Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        borderBottom: '1px solid var(--border)',
        paddingBottom: '2px',
        overflowX: 'auto'
      }}>
        {[
          { id: 'flashcards', label: '🗂️ 3D Flip Flashcards', badge: `${flashcards.length} Cards` },
          { id: 'plan', label: '📋 Targeted Revision Plan', badge: `${progressPercent}% Done` },
          { id: 'cheatsheet', label: '⚡ High-Yield Cheat Sheet', badge: 'Formulas' }
        ].map(tab => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 18px',
              borderRadius: '12px 12px 0 0',
              border: 'none',
              background: activeTab === tab.id ? 'var(--surface)' : 'transparent',
              borderBottom: activeTab === tab.id ? '3px solid var(--indigo)' : '3px solid transparent',
              color: activeTab === tab.id ? 'var(--indigo)' : 'var(--muted)',
              fontWeight: activeTab === tab.id ? 700 : 500,
              fontSize: '0.92rem',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.15s ease',
              whiteSpace: 'nowrap'
            }}
          >
            <span>{tab.label}</span>
            <span style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '999px',
              background: activeTab === tab.id ? 'var(--indigo-tint)' : 'var(--bg)',
              color: activeTab === tab.id ? 'var(--indigo-text)' : 'var(--muted)'
            }}>
              {tab.badge}
            </span>
          </button>
        ))}
      </div>

      {/* =========================================================================
          TAB 1: 3D INTERACTIVE FLIP FLASHCARDS
          ========================================================================= */}
      {activeTab === 'flashcards' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Category Filter Pills & Controls */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
              {availableCategories.map(cat => {
                const count = cat === 'All' 
                  ? allFlashcards.length 
                  : allFlashcards.filter(c => c.category === cat).length;
                const isSelected = selectedCategory === cat;
                return (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => {
                      setSelectedCategory(cat);
                      setCardIndex(0);
                      setIsFlipped(false);
                    }}
                    style={{
                      padding: '5px 12px',
                      borderRadius: '999px',
                      border: isSelected ? '1px solid var(--indigo)' : '1px solid var(--border)',
                      background: isSelected ? 'var(--indigo-tint)' : 'var(--surface)',
                      color: isSelected ? 'var(--indigo-text)' : 'var(--muted)',
                      fontSize: '0.8rem',
                      fontWeight: isSelected ? 700 : 500,
                      cursor: 'pointer',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {cat} ({count})
                  </button>
                );
              })}
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={() => {
                  setIsShuffled(!isShuffled);
                  setCardIndex(0);
                  setIsFlipped(false);
                }}
                className="sa-btn sa-btn-neutral sa-btn-sm"
                title="Shuffle card order"
                style={{ fontSize: '0.78rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Shuffle size={13} />
                <span>{isShuffled ? 'Shuffled' : 'Shuffle'}</span>
              </button>

              {masteredCount > 0 && (
                <button
                  type="button"
                  onClick={() => setMasteredCards({})}
                  className="sa-btn sa-btn-neutral sa-btn-sm"
                  title="Reset mastered status"
                  style={{ fontSize: '0.78rem' }}
                >
                  Reset Progress
                </button>
              )}
            </div>
          </div>

          {/* Deck Progress Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.86rem', color: 'var(--muted)' }}>
            <span>
              Card <strong style={{ color: 'var(--ink)' }}>{safeCardIndex + 1}</strong> of <strong>{flashcards.length}</strong>
            </span>
            <span>
              Mastered: <strong style={{ color: 'var(--teal)' }}>{masteredCount}</strong> ({flashcardProgress}%)
            </span>
          </div>
          <ProgressBar percent={flashcardProgress} color="var(--teal)" height="6px" />

          {/* 3D Card Stage */}
          {currentCard ? (
            <div className="flashcard-stage">
              <div
                className={`flashcard-card-3d ${isFlipped ? 'flipped' : ''}`}
                onClick={handleCardClick}
                title="Click anywhere to flip the card!"
              >
                {/* Front of Card */}
                <div className="flashcard-face flashcard-front">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div className="flashcard-hint-pill">
                      <Sparkles size={13} />
                      <span>{currentCard.category || 'Concept Prompt'}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      {currentCard.difficulty && (
                        <span style={{
                          fontSize: '0.72rem',
                          textTransform: 'uppercase',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: 'var(--bg)',
                          color: 'var(--muted)',
                          fontWeight: 600
                        }}>
                          {currentCard.difficulty}
                        </span>
                      )}
                      <Chip variant="indigo">{currentCard.topic}</Chip>
                    </div>
                  </div>

                  <div style={{ margin: 'auto 0', padding: '12px 0' }}>
                    <div className="flashcard-prompt-text" style={{ fontSize: '1.28rem', textAlign: 'center', lineHeight: '1.45' }}>
                      <StudyMarkdown content={currentCard.question || currentCard.prompt} />
                    </div>

                    {/* Active Recall Scratchpad */}
                    <div 
                      onClick={(e) => e.stopPropagation()} 
                      style={{ marginTop: '14px', maxWidth: '480px', margin: '14px auto 0 auto' }}
                    >
                      <input
                        type="text"
                        placeholder="🧠 Type your quick recall answer before flipping... (optional)"
                        value={scratchpadAnswers[currentCard.id] || ''}
                        onChange={(e) => setScratchpadAnswers(prev => ({ ...prev, [currentCard.id]: e.target.value }))}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            setIsFlipped(true);
                          }
                        }}
                        style={{
                          width: '100%',
                          padding: '8px 14px',
                          borderRadius: '8px',
                          border: '1px solid var(--border)',
                          background: 'var(--bg)',
                          fontSize: '0.84rem',
                          color: 'var(--ink)',
                          boxSizing: 'border-box',
                          outline: 'none'
                        }}
                      />
                    </div>
                  </div>

                  <div className="flashcard-footer-tap">
                    <RotateCcw size={14} />
                    <span>Click card or press Space to reveal verified answer</span>
                  </div>
                </div>

                {/* Back of Card */}
                <div className="flashcard-face flashcard-back">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div className="flashcard-hint-pill">
                      <CheckCircle2 size={13} />
                      <span>Verified Answer & Insight</span>
                    </div>
                    <Chip variant="teal" style={{ background: 'rgba(29, 184, 166, 0.2)', color: '#73EAD9' }}>
                      {currentCard.topic}
                    </Chip>
                  </div>

                  <div 
                    className="flashcard-back-scroll"
                    style={{ 
                      margin: 'auto 0', 
                      maxHeight: '255px', 
                      overflowY: 'auto', 
                      paddingRight: '6px',
                      textAlign: 'left'
                    }}
                  >
                    {scratchpadAnswers[currentCard.id] && (
                      <div style={{ marginBottom: '12px', padding: '8px 12px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.08)', fontSize: '0.84rem' }}>
                        <span style={{ color: '#A89FFF', fontWeight: 600 }}>Your Recall Attempt: </span>
                        <span style={{ color: '#FFF' }}>{scratchpadAnswers[currentCard.id]}</span>
                      </div>
                    )}

                    <div className="flashcard-answer-markdown" style={{ color: '#F1F0FB', fontSize: '1rem', lineHeight: '1.65' }}>
                      <StudyMarkdown content={currentCard.answer} />
                    </div>

                    {currentCard.explanation && currentCard.explanation !== currentCard.answer && (
                      <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid rgba(255, 255, 255, 0.12)' }}>
                        <div style={{ fontSize: '0.76rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#A89FFF', marginBottom: '6px' }}>
                          Explanation & In-Depth Insight
                        </div>
                        <div style={{ color: '#D6D3F5', fontSize: '0.9rem', lineHeight: '1.55' }}>
                          <StudyMarkdown content={currentCard.explanation} />
                        </div>
                      </div>
                    )}

                    {currentCard.bulletPoints && currentCard.bulletPoints.length > 0 && (
                      <ul style={{ margin: '12px 0 0 0', paddingLeft: '20px', color: '#C8C4E8', fontSize: '0.88rem' }}>
                        {currentCard.bulletPoints.map((pt, i) => (
                          <li key={i} style={{ marginTop: '4px' }}>
                            <StudyMarkdown content={pt} />
                          </li>
                        ))}
                      </ul>
                    )}

                    {currentCard.source && (currentCard.source.reference || currentCard.source.page) && (
                      <div style={{ marginTop: '12px', fontSize: '0.74rem', color: '#8E87C7' }}>
                        Source: {currentCard.source.reference || `Page ${currentCard.source.page}`}
                      </div>
                    )}
                  </div>

                  <div className="flashcard-footer-tap">
                    <RotateCcw size={14} />
                    <span>Click card or press Space to flip back to question</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <Card style={{ padding: '36px', textAlign: 'center', color: 'var(--muted)' }}>
              <Sparkles size={28} style={{ margin: '0 auto 12px auto', display: 'block', opacity: 0.6 }} />
              <p style={{ margin: '0 0 6px 0', fontWeight: 600, color: 'var(--ink)' }}>No flashcards found in this category.</p>
              <button 
                type="button" 
                onClick={() => setSelectedCategory('All')}
                className="sa-btn sa-btn-neutral sa-btn-sm"
                style={{ marginTop: '10px' }}
              >
                Show All Flashcards
              </button>
            </Card>
          )}

          {/* Flashcard Action & Rating Controls */}
          {currentCard && (
            <div className="flashcard-controls-row">
              <Button
                variant="secondary"
                size="md"
                icon={<ChevronLeft size={16} />}
                onClick={handlePrevCard}
                disabled={flashcards.length <= 1}
              >
                Previous
              </Button>

              {/* Self-Rating Mastery Buttons */}
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => handleRateCard(false)}
                  className="sa-btn sa-btn-coral sa-btn-sm"
                  title="Mark this card as still needing practice (or press 'R')"
                >
                  <XCircle size={15} />
                  <span>Need Review</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleRateCard(true)}
                  className="sa-btn sa-btn-teal sa-btn-sm"
                  title="Mark this card as mastered (or press 'M')"
                >
                  <CheckCircle2 size={15} />
                  <span>Mastered!</span>
                </button>
              </div>

              <Button
                variant="secondary"
                size="md"
                iconRight={<ChevronRight size={16} />}
                onClick={handleNextCard}
                disabled={flashcards.length <= 1}
              >
                Next Card
              </Button>
            </div>
          )}

          <div style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--muted)' }}>
            Keyboard shortcuts: <kbd style={{ padding: '2px 5px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '4px' }}>Space</kbd> to flip • <kbd style={{ padding: '2px 5px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '4px' }}>←</kbd> <kbd style={{ padding: '2px 5px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '4px' }}>→</kbd> to navigate • <kbd style={{ padding: '2px 5px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '4px' }}>M</kbd> for mastered
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 2: PRIORITY PLAN & TOPIC DRILLS
          ========================================================================= */}
      {activeTab === 'plan' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Hero: Plan Progress Card */}
          <Card style={{ padding: '24px 28px', background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: '0 0 4px 0', color: 'var(--ink)' }}>
                  Daily Curriculum Schedule
                </h2>
                <p style={{ color: 'var(--muted)', fontSize: '0.9rem', margin: 0 }}>
                  Targeted remediation modules organized to eliminate misconceptions and strengthen weak concepts.
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--bg)', padding: '10px 16px', borderRadius: '12px' }}>
                <Clock size={18} color="var(--indigo)" />
                <span style={{ fontWeight: 700, color: 'var(--ink)' }}>{plan?.totalEstimatedMinutes || 60} min</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>total study time</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ fontWeight: 600 }}>Completion Status</span>
                <span style={{ fontWeight: 700, color: progressPercent === 100 ? 'var(--teal)' : 'var(--indigo)' }}>
                  {completedCount} of {totalCount} Completed ({progressPercent}%)
                </span>
              </div>
              <ProgressBar percent={progressPercent} color={progressPercent === 100 ? 'var(--teal)' : 'var(--indigo)'} height="8px" />
            </div>
          </Card>

          {/* List of Prioritized Items */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {items.length === 0 ? (
              <Card style={{ padding: '36px', textAlign: 'center', color: 'var(--muted)' }}>
                <Calendar size={28} style={{ margin: '0 auto 12px auto', display: 'block', opacity: 0.6 }} />
                <p style={{ margin: '0 0 6px 0', fontWeight: 600, color: 'var(--ink)' }}>No Daily Revision Tasks Scheduled</p>
                <p style={{ margin: 0, fontSize: '0.88rem' }}>Take practice exams to automatically generate focused remediation tasks for any weak topics detected.</p>
              </Card>
            ) : (
              items.map((item) => {
                const isCritical = item.priority === 'Critical';
                const isCompleted = item.completed;

                return (
                  <Card 
                    key={item.id}
                    style={{ 
                      padding: '20px 22px', 
                      display: 'flex', 
                      flexDirection: 'column', 
                      gap: '14px',
                      border: isCompleted 
                        ? '1px solid var(--border)' 
                        : isCritical 
                        ? '1px solid rgba(229, 72, 77, 0.4)' 
                        : '1px solid var(--border)',
                      background: isCompleted ? 'rgba(246, 245, 251, 0.6)' : 'var(--surface)',
                      opacity: isCompleted ? 0.78 : 1
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                        <button 
                          onClick={() => handleToggleCompleted(item.id, isCompleted)}
                          style={{ 
                            background: isCompleted ? 'var(--teal)' : 'var(--surface)', 
                            border: `2px solid ${isCompleted ? 'var(--teal)' : 'var(--muted)'}`,
                            borderRadius: '8px', 
                            width: '24px', 
                            height: '24px', 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center', 
                            cursor: 'pointer',
                            marginTop: '2px',
                            flexShrink: 0
                          }}
                        >
                          {isCompleted && <Check size={16} color="#FFF" />}
                        </button>

                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: 'var(--ink)', textDecoration: isCompleted ? 'line-through' : 'none' }}>
                              {item.topic}
                            </h3>
                            <Chip 
                              label={item.priority || (isCritical ? 'Critical' : 'Maintain')} 
                              variant={isCritical ? 'coral' : 'neutral'} 
                              size="sm" 
                            />
                          </div>
                          <div style={{ fontSize: '0.86rem', color: isCompleted ? 'var(--muted)' : 'var(--ink)', marginTop: '4px' }}>
                            {item.actionTitle || item.action || item.reason}
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.84rem' }}>
                        <span style={{ color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Clock size={14} /> {item.estimatedMinutes || 15} min
                        </span>
                        <span>
                          Score: <strong style={{ color: (item.currentScore ?? item.performance ?? 75) < 60 ? 'var(--coral)' : 'var(--teal)' }}>{item.currentScore ?? item.performance ?? 75}%</strong>
                        </span>
                      </div>
                    </div>

                    {/* Notes Snippet */}
                    {((item.notes && item.notes.length > 0) || item.answer || item.conceptNotes) && (
                      <div style={{ background: 'var(--bg)', borderRadius: '10px', padding: '12px 14px', fontSize: '0.85rem', color: 'var(--ink)', lineHeight: 1.5 }}>
                        {item.notes && item.notes.length > 0 ? (
                          <ul style={{ margin: 0, paddingLeft: '18px' }}>
                            {item.notes.map((n, idx) => (
                              <li key={idx} style={{ marginTop: idx > 0 ? '4px' : '0' }}>{n}</li>
                            ))}
                          </ul>
                        ) : (
                          <div>{item.answer || item.conceptNotes}</div>
                        )}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      <Button 
                        variant="outline" 
                        size="sm"
                        icon={<BookOpen size={14} />}
                        onClick={() => setActiveNotesModal(item)}
                      >
                        Read Full Notes
                      </Button>

                      <Button 
                        variant="secondary" 
                        size="sm"
                        icon={<Zap size={14} color="var(--indigo)" />}
                        onClick={() => handleOpenDrill(item)}
                      >
                        Practice 3 Recall Questions
                      </Button>
                    </div>
                  </Card>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 3: HIGH-YIELD REVISION CHEAT SHEET
          ========================================================================= */}
      {activeTab === 'cheatsheet' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <p style={{ margin: 0, fontSize: '0.92rem', color: 'var(--muted)' }}>
              Print-friendly reference deck containing verified equations, definitions, and distinction points.
            </p>
            <Button
              variant="secondary"
              size="sm"
              icon={<Printer size={15} />}
              onClick={() => window.print()}
            >
              Print / Save PDF
            </Button>
          </div>

          {summaryData?.markdown_content || summaryData?.summary || summaryData?.response ? (
            <Card style={{ padding: '24px 32px' }}>
              <StudyMarkdown content={summaryData.markdown_content || summaryData.summary || summaryData.response} />
            </Card>
          ) : summaryData?.sections && summaryData.sections.length > 0 ? (
            summaryData.sections.map((section) => (
              <Card key={section.id || section.title} style={{ padding: '22px 24px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--indigo-text)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BookOpen size={18} />
                  <span>{section.title}</span>
                </h3>
                {section.content && (
                  <div style={{ fontSize: '0.92rem', lineHeight: 1.6, color: 'var(--ink)', marginBottom: '14px' }}>
                    <StudyMarkdown content={section.content} />
                  </div>
                )}
              </Card>
            ))
          ) : (
            <Card style={{ padding: '36px', textAlign: 'center', color: 'var(--muted)' }}>
              <BookOpen size={28} style={{ margin: '0 auto 12px auto', display: 'block', opacity: 0.6 }} />
              <p style={{ margin: '0 0 6px 0', fontWeight: 600, color: 'var(--ink)' }}>No Cheatsheet Notes Available</p>
              <p style={{ margin: 0, fontSize: '0.88rem' }}>Upload or select a study material to generate instant cheatsheet formulas and concepts.</p>
            </Card>
          )}
        </div>
      )}

      {/* Practice Drill Modal */}
      {activeDrillModal && (
        <Modal
          isOpen={!!activeDrillModal}
          onClose={() => setActiveDrillModal(null)}
          title={`Quick Recall Drill: ${activeDrillModal.topic}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <p style={{ fontSize: '0.9rem', color: 'var(--muted)', margin: 0 }}>
              Test your recall on this topic with 3 instant questions. Select your answer and click submit.
            </p>

            {drillQuestions.map((q, idx) => (
              <div key={idx} style={{ background: 'var(--bg)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <div style={{ fontWeight: 600, fontSize: '0.94rem', marginBottom: '10px' }}>
                  {idx + 1}. {q.prompt || q.question}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {q.options?.map((opt, oIdx) => {
                    const isSelected = drillAnswers[idx] === opt;
                    const isSubmitted = drillSubmitted;
                    const isCorrect = isSubmitted && (opt === q.correctAnswer || oIdx === q.correctIndex);

                    return (
                      <button
                        key={oIdx}
                        type="button"
                        onClick={() => !drillSubmitted && setDrillAnswers(prev => ({ ...prev, [idx]: opt }))}
                        style={{
                          padding: '10px 14px',
                          borderRadius: '8px',
                          border: isSelected ? '2px solid var(--indigo)' : '1px solid var(--border)',
                          background: isCorrect ? 'var(--teal-tint)' : (isSelected ? 'var(--indigo-tint)' : 'var(--surface)'),
                          color: isCorrect ? 'var(--teal-text)' : (isSelected ? 'var(--indigo-text)' : 'var(--ink)'),
                          textAlign: 'left',
                          fontSize: '0.88rem',
                          cursor: drillSubmitted ? 'default' : 'pointer'
                        }}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <Button variant="secondary" onClick={() => setActiveDrillModal(null)}>
                Close
              </Button>
              {!drillSubmitted && (
                <Button
                  variant="primary"
                  onClick={() => setDrillSubmitted(true)}
                  disabled={Object.keys(drillAnswers).length === 0}
                >
                  Check Answers
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Notes Modal */}
      {activeNotesModal && (
        <Modal
          isOpen={!!activeNotesModal}
          onClose={() => setActiveNotesModal(null)}
          title={`Core Concept Notes: ${activeNotesModal.topic}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ fontSize: '0.95rem', lineHeight: 1.6, color: 'var(--ink)', margin: 0 }}>
              <StudyMarkdown content={activeNotesModal.answer || activeNotesModal.conceptNotes || (Array.isArray(activeNotesModal.notes) ? activeNotesModal.notes.join('\n\n') : activeNotesModal.reason)} />
            </div>
            {activeNotesModal.explanation && (
              <div style={{ padding: '12px', background: 'var(--bg)', borderRadius: '8px', fontSize: '0.88rem' }}>
                <StudyMarkdown content={activeNotesModal.explanation} />
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="primary" onClick={() => setActiveNotesModal(null)}>
                Done Reviewing
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default Revision;
