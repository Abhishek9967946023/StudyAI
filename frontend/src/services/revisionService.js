/**
=============================================================================
StudyAI — Revision Service
=============================================================================
Handles adaptive revision plans and real-time item completion status.
=============================================================================
*/

import { apiRequest } from './apiClient';
import { isUsingMocks, getActiveMaterialId } from './materialsService';
import { MOCK_REVISION_PLAN } from './mocks/mockData';

export async function getRevisionPlan(documentId) {
  if (isUsingMocks()) {
    const saved = localStorage.getItem('studyai_custom_revision');
    if (saved) return JSON.parse(saved);
    return MOCK_REVISION_PLAN;
  }

  const docId = documentId || getActiveMaterialId();
  const validDocId = (docId && !['null', 'undefined', 'none'].includes(String(docId).toLowerCase())) ? docId : null;
  const queryStr = validDocId ? `?doc_id=${validDocId}` : '';
  const body = validDocId ? { document_id: validDocId } : {};

  return await apiRequest(`/api/v1/revision/plan${queryStr}`, {
    method: 'POST',
    body: JSON.stringify(body)
  });
}

export async function markRevisionItemCompleted(itemId, completed = true) {
  if (isUsingMocks()) {
    const current = await getRevisionPlan();
    const updatedItems = (current.items || []).map(it => 
      it.id === itemId ? { ...it, completed } : it
    );
    const completedCount = updatedItems.filter(it => it.completed).length;

    const updatedPlan = {
      ...current,
      completedItemsCount: completedCount,
      items: updatedItems
    };
    localStorage.setItem('studyai_custom_revision', JSON.stringify(updatedPlan));
    return updatedPlan;
  }

  return await apiRequest(`/api/v1/revision/items/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify({ completed })
  });
}

/**
 * Normalizes any card representation into the canonical Revision Card Data Contract:
 * { id, question, prompt, answer, explanation, topic, priority, difficulty, category, source, bulletPoints }
 */
export function normalizeRevisionCard(raw, index = 0) {
  if (!raw || typeof raw !== 'object') {
    return {
      id: `fc-${index}`,
      question: 'Core Academic Principle',
      prompt: 'Core Academic Principle',
      answer: 'Standard syllabus principle verified from curriculum.',
      explanation: '',
      topic: 'General Topic',
      priority: 'Standard',
      difficulty: 'medium',
      category: 'Concept',
      source: {},
      bulletPoints: []
    };
  }

  const cleanStr = (val, fallback = '') => {
    if (!val || typeof val !== 'string') return fallback;
    const s = val.replace(/:\s*undefined\b/g, '').replace(/\b(?:undefined|null|None|NaN|\[object Object\])\b/g, '').trim();
    return s || fallback;
  };

  const id = raw.id || `fc-${index}`;
  const rawQ = raw.question || raw.prompt || (raw.term ? `Define and explain: **${raw.term}**` : '');
  const question = cleanStr(rawQ, `Key principle of ${raw.topic || 'this topic'}`);
  const rawA = raw.answer || raw.definition || raw.conceptNotes || (Array.isArray(raw.notes) ? raw.notes.join('\n') : '');
  const answer = cleanStr(rawA, '');
  const explanation = cleanStr(raw.explanation || raw.detailed_explanation || raw.in_depth || '');
  const topic = cleanStr(raw.topic || raw.term || raw.name, 'Curriculum');
  const priority = raw.priority || 'Standard';
  const difficulty = raw.difficulty || 'medium';
  const category = raw.category || 'Active Recall';
  
  let bulletPoints = [];
  if (Array.isArray(raw.bulletPoints)) {
    bulletPoints = raw.bulletPoints.map(b => cleanStr(b)).filter(Boolean);
  } else if (Array.isArray(raw.notes)) {
    bulletPoints = raw.notes.map(b => cleanStr(b)).filter(Boolean);
  }

  return {
    id,
    question,
    prompt: question,
    answer,
    explanation,
    topic,
    priority,
    difficulty,
    category,
    source: raw.source || {},
    bulletPoints
  };
}
