/**
 * =============================================================================
 * StudyAI — Adaptive Learning Loop Service
 * =============================================================================
 * Connects the Weak Topic remediation workflow:
 * Weak Topic -> Targeted Practice (5 Qs) -> Mini-Test -> New Score -> Performance Comparison -> Priority Recalculation
 * =============================================================================
 */

import { apiRequest } from './apiClient';
import { isUsingMocks, getActiveMaterialId } from './materialsService';

export async function generateAdaptivePractice({
  documentId = null,
  topic = 'Core Concept',
  questionCount = 5,
  previousPerformance = 35,
  importance = 80,
  previousPriority = 'CRITICAL'
}) {
  const docId = documentId || getActiveMaterialId();

  if (isUsingMocks()) {
    await new Promise(r => setTimeout(r, 400));
    return {
      id: `exam-adapt-${Date.now()}`,
      exam_id: Date.now(),
      materialId: docId,
      title: `Adaptive Mini-Test: ${topic}`,
      topic,
      previousPerformance,
      importance,
      previousPriority,
      totalQuestions: 5,
      questions: [
        {
          id: 'q-ad-1',
          number: 1,
          question: `Which fundamental principle is central to understanding ${topic}?`,
          type: 'mcq',
          options: [
            'Mutual resource dependency and cyclic wait condition',
            'Preemptive batch scheduling',
            'Static allocation without runtime bounds',
            'Unbounded memory consumption'
          ],
          correctAnswer: 'Mutual resource dependency and cyclic wait condition',
          correctIndex: 0,
          explanation: `In the studied curriculum, ${topic} centers on resource ordering and state progression rules.`,
          citation: `Section 3.1: Foundational invariants and formal definitions governing ${topic}.`,
          topic,
          difficulty: 'Medium',
          source_page: 1
        },
        {
          id: 'q-ad-2',
          number: 2,
          question: `How can the system systematically detect or prevent hazards associated with ${topic}?`,
          type: 'mcq',
          options: [
            'By enforcing strict resource allocation hierarchy',
            'By ignoring concurrency locks',
            'By increasing thread priority arbitrarily',
            'By disabling cache coherence'
          ],
          correctAnswer: 'By enforcing strict resource allocation hierarchy',
          correctIndex: 0,
          explanation: `Systematic prevention ensures that hold-and-wait or circular structures cannot materialize.`,
          citation: `Section 3.4: Algorithmic prevention and detection strategies for ${topic}.`,
          topic,
          difficulty: 'Hard',
          source_page: 2
        },
        {
          id: 'q-ad-3',
          number: 3,
          question: `What distinguishes safe states from unsafe states in the context of ${topic}?`,
          type: 'mcq',
          options: [
            'A safe state guarantees an execution order where all processes can complete',
            'An unsafe state immediately causes catastrophic system halt',
            'Safe states do not utilize operating system synchronization primitives',
            'Unsafe states only occur in single-threaded environments'
          ],
          correctAnswer: 'A safe state guarantees an execution order where all processes can complete',
          correctIndex: 0,
          explanation: `A state is formally safe if there exists a sequence of allocations that allows every unit to finish.`,
          citation: `Section 4.2: Safe state invariant analysis.`,
          topic,
          difficulty: 'Medium',
          source_page: 2
        },
        {
          id: 'q-ad-4',
          number: 4,
          question: `Is preemption a viable mitigation strategy for resolving conditions in ${topic}?`,
          type: 'tf',
          options: ['True', 'False'],
          correctAnswer: 'True',
          correctIndex: 0,
          explanation: `Forcible preemption of held resources breaks the hold-and-wait invariant.`,
          citation: `Section 4.5: Preemption mechanisms and recovery techniques.`,
          topic,
          difficulty: 'Easy',
          source_page: 3
        },
        {
          id: 'q-ad-5',
          number: 5,
          question: `Summarize the primary trade-off when implementing avoidance algorithms for ${topic}.`,
          type: 'mcq',
          options: [
            'Computational overhead of runtime claim checks versus increased reliability',
            'Higher disk space requirements with zero runtime checks',
            'Lower CPU utilization with increased network bandwidth',
            'Manual operator intervention requirements'
          ],
          correctAnswer: 'Computational overhead of runtime claim checks versus increased reliability',
          correctIndex: 0,
          explanation: `Avoidance algorithms require prior claim vectors, introducing algorithmic check overhead at request time.`,
          citation: `Section 5.1: Performance trade-offs in avoidance algorithms.`,
          topic,
          difficulty: 'Hard',
          source_page: 3
        }
      ]
    };
  }

  return await apiRequest('/api/v1/adaptive/generate', {
    method: 'POST',
    body: JSON.stringify({
      document_id: docId,
      topic,
      question_count: questionCount,
      previous_performance: previousPerformance,
      importance,
      previous_priority: previousPriority
    })
  });
}

export async function submitAdaptivePractice({
  examId,
  topic,
  answers,
  previousPerformance = 35,
  importance = 80,
  previousPriority = 'CRITICAL'
}) {
  if (isUsingMocks()) {
    await new Promise(r => setTimeout(r, 450));
    // Calculate realistic mock score
    const totalQ = 5;
    const answeredCount = Object.keys(answers || {}).length;
    const correctCount = Math.min(totalQ, Math.max(3, answeredCount));
    const newPerformance = Math.round((correctCount / totalQ) * 100); // ~60-80%
    const improvement = newPerformance - previousPerformance;

    // 4-Quadrant recalculation
    let newPriority = 'PRACTICE';
    if (newPerformance >= 75) {
      newPriority = importance >= 60 ? 'MAINTAIN' : 'LOW PRIORITY';
    } else if (newPerformance >= 60) {
      newPriority = 'PRACTICE';
    } else {
      newPriority = importance >= 60 ? 'CRITICAL' : 'PRACTICE';
    }

    const result = {
      success: true,
      topic,
      previousPerformance,
      newPerformance,
      improvement,
      importance,
      previousPriority,
      newPriority,
      correctCount,
      totalQuestions: totalQ,
      feedbackText: `Targeted practice on ${topic} complete! Score advanced from ${previousPerformance}% to ${newPerformance}% (${improvement >= 0 ? '+' : ''}${improvement}%).`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    // Save mock loop to localStorage
    const saved = JSON.parse(localStorage.getItem('studyai_adaptive_loops') || '[]');
    saved.unshift(result);
    localStorage.setItem('studyai_adaptive_loops', JSON.stringify(saved.slice(0, 10)));

    return result;
  }

  return await apiRequest('/api/v1/adaptive/submit', {
    method: 'POST',
    body: JSON.stringify({
      exam_id: examId,
      topic,
      answers,
      previous_performance: previousPerformance,
      importance,
      previous_priority: previousPriority
    })
  });
}

export async function getAdaptiveHistory(documentId = null) {
  if (isUsingMocks()) {
    const saved = JSON.parse(localStorage.getItem('studyai_adaptive_loops') || '[]');
    if (saved.length > 0) return saved;
    return [
      {
        id: 1,
        topic: 'Deadlocks',
        previousPerformance: 35,
        newPerformance: 68,
        improvement: 33,
        importance: 94,
        previousPriority: 'CRITICAL',
        newPriority: 'PRACTICE',
        documentTitle: 'Operating Systems Notes',
        timestamp: 'Just now'
      }
    ];
  }

  const docId = documentId || getActiveMaterialId();
  return await apiRequest(`/api/v1/adaptive/history?doc_id=${docId}`, {
    method: 'GET'
  });
}
