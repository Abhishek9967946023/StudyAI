/**
 * =============================================================================
 * StudyAI — Centralized API Client
 * =============================================================================
 * Handles all network requests, base URLs, X-API-Key headers, and error normalization.
 * Returns standard { data, error } results so UI components never crash.
 * =============================================================================
 */

function resolveApiBaseUrl() {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '');
  }
  if (typeof window !== 'undefined' && window.location) {
    const loc = window.location;
    // If running on Vite dev server (e.g. port 5173 or 3000), target the same hostname on port 8000
    if (loc.port === '5173' || loc.port === '3000') {
      return `${loc.protocol}//${loc.hostname}:8000`;
    }
    // If served in production or reverse proxy, use current origin
    return loc.origin;
  }
  return 'http://127.0.0.1:8000';
}

const BASE_URL = resolveApiBaseUrl();

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function checkBackendHealth() {
  const candidates = [
    '/api/health/',
    `${BASE_URL}/api/health/`
  ];
  const uniqueCandidates = [...new Set(candidates)];
  for (const testUrl of uniqueCandidates) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);
      const res = await fetch(testUrl, { signal: controller.signal, credentials: 'include' });
      clearTimeout(timeoutId);
      if (res.ok) {
        const data = await res.json();
        return { isOnline: true, data, endpoint: testUrl };
      }
    } catch {
      // Continue to next candidate
    }
  }
  return { isOnline: false, data: null, endpoint: null };
}

/**
 * Standard fetch wrapper with centralized error handling and automatic proxy fallback
 */
export async function apiRequest(endpoint, options = {}) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // Try candidate URLs: In development prefer the local proxy to eliminate CORS mismatches; fallback to direct BASE_URL
  const candidateUrls = import.meta.env.VITE_API_BASE_URL
    ? [`${BASE_URL}${cleanEndpoint}`, cleanEndpoint]
    : [cleanEndpoint, `${BASE_URL}${cleanEndpoint}`];

  // Remove duplicates
  const uniqueUrls = [...new Set(candidateUrls)];

  function getCsrfToken() {
    if (typeof document === 'undefined') return null;
    const match = document.cookie.match(/(^|;\s*)csrftoken=([^;]*)/);
    return match ? decodeURIComponent(match[2]) : null;
  }

  const method = (options.method || 'GET').toUpperCase();
  const isMutation = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);
  const csrfToken = isMutation ? getCsrfToken() : null;

  const authToken = typeof window !== 'undefined' ? localStorage.getItem('studyai_auth_token') : null;

  const headers = {
    'Accept': 'application/json',
    ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
    ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    ...(options.headers || {})
  };

  // Do not set Content-Type for FormData (browser sets boundary automatically)
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  let lastError = null;

  for (let i = 0; i < uniqueUrls.length; i++) {
    const targetUrl = uniqueUrls[i];
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), options.timeout || 300000);

      // Link external abort signal if provided
      if (options.signal) {
        if (options.signal.aborted) {
          controller.abort();
        } else {
          options.signal.addEventListener('abort', () => controller.abort(), { once: true });
        }
      }

      const response = await fetch(targetUrl, {
        credentials: 'include',
        ...options,
        headers,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorMsg = `Server error (${response.status})`;
        let errorData = null;

        try {
          errorData = await response.json();
          errorMsg = errorData.detail || errorData.message || errorData.error || errorMsg;
        } catch {
          errorMsg = await response.text() || errorMsg;
        }

        if (response.status === 401) {
          if (!cleanEndpoint.includes('/auth/login') && !cleanEndpoint.includes('/auth/register')) {
            if (typeof window !== 'undefined') {
              localStorage.removeItem('studyai_auth_token');
              localStorage.removeItem('studyai_user');
              window.dispatchEvent(new CustomEvent('studyai_auth_expired'));
            }
          }
          if (!errorData?.error && !errorData?.message) {
            errorMsg = 'Unauthorized. Please verify your login credentials or session.';
          }
        }
        if (response.status === 422) errorMsg = 'Invalid request parameters. Please verify input.';
        if (response.status === 429) errorMsg = errorMsg || 'Rate limit exceeded. Please wait a moment before trying again.';
        if (response.status >= 500) errorMsg = errorMsg !== `Server error (${response.status})` ? errorMsg : 'Backend service temporarily unavailable. Please try again.';

        throw new ApiError(errorMsg, response.status, errorData);
      }

      // Handle 204 No Content
      if (response.status === 204) return null;

      return await response.json();
    } catch (err) {
      if (err instanceof ApiError) throw err;
      if (err.name === 'AbortError') {
        if (options.signal?.aborted) {
          const cancelErr = new ApiError('Request cancelled by user.', 499);
          cancelErr.name = 'AbortError';
          cancelErr.isCancelled = true;
          throw cancelErr;
        }
        throw new ApiError('Request timed out while indexing the document. Please try again.', 408);
      }

      lastError = err;
      // If network error ("Failed to fetch"), attempt next candidate URL
      const isNetworkErr = err.message === 'Failed to fetch' || err.name === 'TypeError';
      if (!isNetworkErr || i === uniqueUrls.length - 1) {
        break;
      }
    }
  }

  if (lastError && (lastError.message === 'Failed to fetch' || lastError.name === 'TypeError')) {
    throw new ApiError(
      `Could not connect to StudyAI backend server (Failed to fetch). Ensure the backend is running at ${BASE_URL} (e.g. run start_studyai.bat or npm run start).`,
      0
    );
  }
  throw new ApiError(lastError?.message || 'Network connection failed.', 0);
}
