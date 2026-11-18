/**
 * =============================================================================
 * StudyAI — AI Quality Evaluation Service
 * =============================================================================
 * Connects frontend to the AI Quality Evaluation engine:
 * - Fetches 20 real academic benchmark documents
 * - Retrieves latest verified 100-question audit report
 * - Triggers on-demand benchmark evaluation runs
 * - Retrieves historical audit runs
 * =============================================================================
 */

import { apiRequest } from './apiClient';

/**
 * Fetches the 20 benchmark documents and test suite configuration
 */
export async function fetchBenchmarkDocuments() {
  const result = await apiRequest('/api/evaluation/benchmark/');
  if (result.error) {
    console.warn('[EvaluationService] Failed to load benchmark documents from API:', result.error);
    return { data: null, error: result.error };
  }
  return { data: result.data, error: null };
}

/**
 * Fetches the latest evaluation report containing all 100 question audits
 */
export async function fetchLatestEvaluationReport(force = false, model = 'llama3:latest', fast = true) {
  const params = new URLSearchParams({
    force: force ? 'true' : 'false',
    model,
    fast: fast ? 'true' : 'false'
  });
  const result = await apiRequest(`/api/evaluation/latest/?${params.toString()}`);
  if (result.error) {
    console.warn('[EvaluationService] Failed to load latest evaluation report from API:', result.error);
    return { data: null, error: result.error };
  }
  return { data: result.data, error: null };
}

/**
 * Triggers an on-demand evaluation run across all 20 documents
 */
export async function runEvaluation(options = { model: 'llama3:latest', fast: true }) {
  const result = await apiRequest('/api/evaluation/run/', {
    method: 'POST',
    body: JSON.stringify({
      model: options.model || 'llama3:latest',
      fast: options.fast !== false
    }),
    timeout: 300000 // 5 minutes max for full evaluations
  });

  if (result.error) {
    console.error('[EvaluationService] Evaluation run failed:', result.error);
    return { data: null, error: result.error };
  }
  return { data: result.data, error: null };
}

/**
 * Fetches history of evaluation runs
 */
export async function fetchEvaluationRuns() {
  const result = await apiRequest('/api/evaluation/runs/');
  if (result.error) {
    return { data: [], error: result.error };
  }
  return { data: result.data || [], error: null };
}
