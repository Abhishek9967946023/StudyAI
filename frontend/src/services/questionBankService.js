/**
=============================================================================
StudyAI — Question Bank Service
=============================================================================
*/

import { apiRequest } from './apiClient';
import { isUsingMocks } from './materialsService';
import { MOCK_QUESTIONS } from './mocks/mockData';

export async function getQuestions(filters = {}) {
  if (isUsingMocks()) {
    let list = [...MOCK_QUESTIONS];
    if (filters.topic && filters.topic !== 'All') {
      list = list.filter(q => q.topic.toLowerCase() === filters.topic.toLowerCase());
    }
    if (filters.difficulty && filters.difficulty !== 'All') {
      list = list.filter(q => q.difficulty.toLowerCase() === filters.difficulty.toLowerCase());
    }
    if (filters.type && filters.type !== 'All') {
      list = list.filter(q => q.type.toLowerCase() === filters.type.toLowerCase());
    }
    if (filters.search) {
      const s = filters.search.toLowerCase();
      list = list.filter(q => 
        q.question.toLowerCase().includes(s) || 
        q.explanation.toLowerCase().includes(s) ||
        q.topic.toLowerCase().includes(s)
      );
    }
    return list;
  }

  const query = new URLSearchParams(filters).toString();
  return await apiRequest(`/api/v1/questions?${query}`, { method: 'GET' });
}
