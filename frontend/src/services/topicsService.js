/**
=============================================================================
StudyAI — Topic Intelligence Service
=============================================================================
Strictly separates:
1. Material Importance (intrinsic syllabus weight, 0-100)
2. Student Performance (exam accuracy, 0-100)

Thresholds:
- HIGH_IMPORTANCE = 60
- WEAK_BELOW = 60
=============================================================================
*/

import { apiRequest } from './apiClient';
import { isUsingMocks, getActiveMaterialId } from './materialsService';
import { MOCK_TOPIC_INTELLIGENCE } from './mocks/mockData';

export const HIGH_IMPORTANCE = 60;
export const WEAK_BELOW = 60;

export function classifyTopicPriority(importance, performance) {
  const isHighImportance = importance >= HIGH_IMPORTANCE;
  const isWeak = performance < WEAK_BELOW;

  if (isHighImportance && isWeak) {
    return {
      quadrant: 'critical',
      label: 'Critical',
      color: 'var(--coral)',
      bg: 'var(--coral-tint)',
      textColor: 'var(--coral-text)',
      description: 'High syllabus weight + low student mastery. Immediate remediation priority.'
    };
  }
  if (isHighImportance && !isWeak) {
    return {
      quadrant: 'maintain',
      label: 'Maintain',
      color: 'var(--teal)',
      bg: 'var(--teal-tint)',
      textColor: 'var(--teal-text)',
      description: 'High syllabus weight + mastered. Maintain with periodic review.'
    };
  }
  if (!isHighImportance && isWeak) {
    return {
      quadrant: 'practice_if_time',
      label: 'Practice if time permits',
      color: 'var(--subtle)',
      bg: 'var(--border)',
      textColor: 'var(--muted)',
      description: 'Secondary syllabus topic with knowledge gap. Review after critical topics.'
    };
  }
  return {
    quadrant: 'low_priority',
    label: 'Low priority',
    color: 'var(--subtle)',
    bg: 'var(--bg)',
    textColor: 'var(--muted)',
    description: 'Foundational concept already mastered.'
  };
}

export async function getTopicIntelligence(documentId) {
  if (isUsingMocks()) {
    await new Promise(r => setTimeout(r, 200));
    return MOCK_TOPIC_INTELLIGENCE.map(item => ({
      ...item,
      category: classifyTopicPriority(item.importance, item.performance)
    }));
  }

  const docId = documentId || getActiveMaterialId();
  const raw = await apiRequest(`/api/v1/topics/intelligence?doc_id=${docId}`, { method: 'GET' });
  const list = Array.isArray(raw) ? raw : (raw?.topics || []);

  return list.map(item => ({
    ...item,
    category: classifyTopicPriority(item.importance, item.performance)
  }));
}
