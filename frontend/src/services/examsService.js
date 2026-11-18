/**
=============================================================================
StudyAI — Exams Service
=============================================================================
Handles grounded exam generation, questions retrieval, and submission evaluation.
=============================================================================
*/

import { apiRequest } from './apiClient';
import { isUsingMocks, getActiveMaterialId } from './materialsService';
import { MOCK_QUESTIONS, MOCK_MATERIAL_ID } from './mocks/mockData';

export async function generateExam(config, options = {}) {
  if (isUsingMocks()) {
    // Check if cancelled before starting
    if (options.signal?.aborted) {
      const err = new Error('Exam generation cancelled by user.');
      err.name = 'AbortError';
      err.isCancelled = true;
      throw err;
    }

    await new Promise((resolve, reject) => {
      const timer = setTimeout(resolve, 500);
      if (options.signal) {
        options.signal.addEventListener('abort', () => {
          clearTimeout(timer);
          const err = new Error('Exam generation cancelled by user.');
          err.name = 'AbortError';
          err.isCancelled = true;
          reject(err);
        }, { once: true });
      }
    });

    const count = parseInt(config.questionCount || 8, 10);
    const selectedTopic = config.topic || 'All';
    const qType = (config.questionType || 'Mixed').toLowerCase();
    const marksPerQuestion = Number(config.marksPerQuestion) || 2;

    let pool = [...MOCK_QUESTIONS];
    if (selectedTopic !== 'All') {
      const filteredByTopic = pool.filter(q => q.topic.toLowerCase().includes(selectedTopic.toLowerCase()));
      if (filteredByTopic.length > 0) pool = filteredByTopic;
    }

    if (qType === 'mcq') {
      const mcqs = pool.filter(q => q.type === 'mcq');
      if (mcqs.length > 0) pool = mcqs;
    } else if (qType === 'true/false' || qType === 'tf') {
      const tfs = pool.filter(q => q.type === 'tf');
      if (tfs.length > 0) pool = tfs;
    } else if (qType === 'short' || qType === 'short answer') {
      const shorts = pool.filter(q => q.type === 'short');
      if (shorts.length > 0) pool = shorts;
    } else if (qType === 'long' || qType === 'long answer') {
      pool = pool.filter(q => q.type === 'long');
    } else if (qType === 'fill_blank' || qType === 'fill in the blank') {
      pool = pool.filter(q => q.type === 'fill_blank');
    } else if (qType === 'msq' || qType === 'multiple select') {
      pool = pool.filter(q => q.type === 'msq');
    } else if (qType === 'mixed') {
      // Balanced mix: take from each type
      const mcqs = pool.filter(q => q.type === 'mcq');
      const tfs = pool.filter(q => q.type === 'tf');
      const shorts = pool.filter(q => q.type === 'short');
      const msqs = pool.filter(q => q.type === 'msq');
      const mixed = [];
      const maxLen = Math.max(mcqs.length, tfs.length, shorts.length, msqs.length);
      for (let i = 0; i < maxLen; i++) {
        if (mcqs[i]) mixed.push(mcqs[i]);
        if (tfs[i]) mixed.push(tfs[i]);
        if (shorts[i]) mixed.push(shorts[i]);
        if (msqs[i]) mixed.push(msqs[i]);
      }
      if (mixed.length > 0) pool = mixed;
    }

    // If pool has fewer than count, duplicate/cycle
    let finalQuestions = [];
    while (finalQuestions.length < count) {
      for (const q of pool) {
        if (finalQuestions.length >= count) break;
        finalQuestions.push({
          ...q,
          id: `${q.id}-${finalQuestions.length + 1}`,
          number: finalQuestions.length + 1,
          marks: marksPerQuestion
        });
      }
    }

    const examId = `exam-${Date.now()}`;
    const examData = {
      id: examId,
      materialId: config.materialId || MOCK_MATERIAL_ID,
      title: `Practice Exam: ${selectedTopic === 'All' ? 'Comprehensive Assessment' : selectedTopic}`,
      difficulty: config.difficulty || 'Medium',
      questionType: config.questionType || 'Mixed',
      timeLimitMinutes: config.timeLimitMinutes || Math.max(5, Math.ceil(finalQuestions.length * 1.5)),
      totalQuestions: finalQuestions.length,
      totalMarks: finalQuestions.reduce((sum, question) => sum + (question.marks || 1), 0),
      questions: finalQuestions
    };

    localStorage.setItem(`studyai_exam_${examId}`, JSON.stringify(examData));
    return examData;
  }

  const payload = {
    ...config,
    document_id: config.materialId || getActiveMaterialId()
  };

  return await apiRequest('/api/v1/exams', {
    method: 'POST',
    body: JSON.stringify(payload),
    signal: options.signal
  });
}

export async function getExam(examId) {
  if (isUsingMocks()) {
    const saved = localStorage.getItem(`studyai_exam_${examId}`);
    if (saved) return JSON.parse(saved);
    return {
      id: examId,
      title: 'Practice Exam: Grounded Assessment',
      difficulty: 'Medium',
      timeLimitMinutes: 12,
      totalQuestions: MOCK_QUESTIONS.length,
      questions: MOCK_QUESTIONS.map((q, i) => ({ ...q, number: i + 1 }))
    };
  }

  return await apiRequest(`/api/v1/exams/${examId}`, { method: 'GET' });
}

export async function submitExam(examId, userAnswers, examData) {
  if (isUsingMocks()) {
    await new Promise(r => setTimeout(r, 600));

    const questions = examData?.questions || MOCK_QUESTIONS;
    let correct = 0;
    let marksScored = 0;
    const topicStats = {};
    const totalMarks = questions.reduce((sum, question) => sum + (question.marks || 1), 0);

    const detailed = questions.map(q => {
      const userAns = userAnswers[q.id];
      let isCorrect = false;

      if (userAns !== undefined && userAns !== null && String(userAns).trim() !== '') {
        const uStr = String(userAns).trim().toLowerCase();
        const cStr = String(q.correctAnswer || '').trim().toLowerCase();

        if (q.type === 'msq') {
          const expected = q.correctIndices || [];
          const actual = Array.isArray(userAns) ? userAns : [];
          isCorrect = actual.length === expected.length
            && new Set(actual).size === actual.length
            && expected.every(index => actual.includes(index));
        } else if (q.type === 'short' || q.type === 'long') {
          // Keyword overlap & substring matching
          const uWords = new Set(uStr.match(/\b\w{3,}\b/g) || []);
          const cWords = new Set(cStr.match(/\b\w{3,}\b/g) || []);
          const overlap = [...uWords].filter(w => cWords.has(w)).length;
          if (uStr === cStr || (cWords.size > 0 && overlap / cWords.size >= 0.35) || uStr.includes(cStr) || cStr.includes(uStr)) {
            isCorrect = true;
          }
        } else if (q.type === 'tf') {
          isCorrect = (uStr === cStr) || (uStr === 'true' && cStr === 'true') || (uStr === 'false' && cStr === 'false');
        } else {
          isCorrect = (uStr === cStr) || (userAns === q.correctIndex);
        }
      }

      if (isCorrect) correct += 1;
      if (isCorrect) marksScored += q.marks || 1;

      const tName = q.topic || 'General';
      if (!topicStats[tName]) {
        topicStats[tName] = { topic: tName, total: 0, correct: 0, marksTotal: 0, marksScored: 0 };
      }
      topicStats[tName].total += 1;
      topicStats[tName].marksTotal += q.marks || 1;
      if (isCorrect) topicStats[tName].correct += 1;
      if (isCorrect) topicStats[tName].marksScored += q.marks || 1;

      return {
        ...q,
        userAnswer: userAns,
        isCorrect
      };
    });

    const scorePercent = Math.round((marksScored / (totalMarks || 1)) * 100);

    const topicBreakdown = Object.values(topicStats).map(t => {
      const pct = Math.round((t.marksScored / (t.marksTotal || 1)) * 100);
      return {
        ...t,
        scorePercent: pct,
        isWeak: pct < 60
      };
    });

    const resultId = `res-${Date.now()}`;
    const resultObj = {
      id: resultId,
      resultId,
      examId,
      scorePercent,
      marksScored,
      totalMarks,
      correctCount: correct,
      incorrectCount: questions.length - correct,
      totalQuestions: questions.length,
      timeSpent: '8m 45s',
      feedbackText: scorePercent >= 75
        ? 'Solid conceptual grasp of assessed syllabus principles. Practice weaker concepts to close remaining gaps.'
        : 'Critical remediation required in identified weak focus areas. Recommended to review detailed notes and retake.',
      topicBreakdown,
      detailedQuestions: detailed
    };

    localStorage.setItem(`studyai_result_${resultId}`, JSON.stringify(resultObj));
    return { resultId, id: resultId };
  }

  return await apiRequest(`/api/v1/exams/${examId}/submit`, {
    method: 'POST',
    body: JSON.stringify({ answers: userAnswers })
  });
}
