/**
=============================================================================
StudyAI — Results Service
=============================================================================
*/

import { apiRequest } from './apiClient';
import { isUsingMocks } from './materialsService';

export async function getResult(resultId) {
  if (isUsingMocks()) {
    const saved = localStorage.getItem(`studyai_result_${resultId}`);
    if (saved) return JSON.parse(saved);

    // Fallback default realistic result for mock mode
    return {
      id: resultId || 'res-default',
      scorePercent: 75,
      correctCount: 6,
      incorrectCount: 2,
      totalQuestions: 8,
      timeSpent: '7m 30s',
      feedbackText: 'Solid foundation in curriculum core concepts. Knowledge gaps identified in secondary focus topics.',
      topicBreakdown: [
        { topic: 'Core Principles', total: 3, correct: 1, scorePercent: 35, isWeak: true, importance: 94, priority: 'CRITICAL' },
        { topic: 'Operational Mechanisms', total: 3, correct: 3, scorePercent: 100, isWeak: false, importance: 85, priority: 'MAINTAIN' },
        { topic: 'System Invariants', total: 2, correct: 2, scorePercent: 100, isWeak: false, importance: 70, priority: 'MAINTAIN' }
      ]
    };
  }

  return await apiRequest(`/api/v1/results/${resultId}`, { method: 'GET' });
}
