/**
=============================================================================
StudyAI — History Service
=============================================================================
*/

import { apiRequest } from './apiClient';
import { isUsingMocks } from './materialsService';
import { MOCK_HISTORY } from './mocks/mockData';

export async function getHistory() {
  if (isUsingMocks()) {
    const customExams = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('studyai_result_')) {
        try {
          const res = JSON.parse(localStorage.getItem(key));
          customExams.push({
            id: res.id,
            examTitle: res.examTitle || 'Custom Grounded Assessment',
            date: 'Recent Attempt',
            scorePercent: res.scorePercent,
            totalQuestions: res.totalQuestions,
            correctCount: res.correctCount,
            timeSpent: res.timeSpent || '6m 20s',
            weakTopics: res.topicBreakdown?.filter(t => t.isWeak).map(t => t.topic) || []
          });
        } catch {}
      }
    }
    return [...customExams, ...MOCK_HISTORY];
  }

  return await apiRequest('/api/v1/history', { method: 'GET' });
}
