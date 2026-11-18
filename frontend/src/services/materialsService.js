import { apiRequest } from './apiClient';

export const isUsingMocks = () => false;

export const getActiveMaterialId = () => {
  const val = localStorage.getItem('studyai_active_material_id');
  if (!val || ['null', 'undefined', 'none', '1'].includes(String(val).toLowerCase())) {
    return null;
  }
  return val;
};

export const setActiveMaterialId = (id) => {
  if (id && !['null', 'undefined', 'none'].includes(String(id).toLowerCase())) {
    localStorage.setItem('studyai_active_material_id', String(id));
  }
};

export async function uploadMaterial(formDataOrJson) {
  const isFile = formDataOrJson instanceof FormData;
  const res = await apiRequest('/api/v1/materials', {
    method: 'POST',
    body: isFile ? formDataOrJson : JSON.stringify(formDataOrJson),
    timeout: 300000
  });

  if (res && (res.id || res.document_id)) {
    setActiveMaterialId(res.id || res.document_id);
  }
  return res;
}

export async function getMaterials() {
  return await apiRequest('/api/v1/materials/', { method: 'GET' });
}

export async function deleteMaterial(materialId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}`, {
    method: 'DELETE'
  });
}

export async function bulkDeleteMaterials(materialIds) {
  return await apiRequest('/api/v1/materials', {
    method: 'DELETE',
    body: JSON.stringify({ ids: materialIds })
  });
}

export async function getMaterialStatus(materialId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/status`, { method: 'GET' });
}

export async function retryMaterialProcessing(materialId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/retry`, { method: 'POST' });
}

export async function cancelMaterialProcessing(materialId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/cancel`, { method: 'POST' });
}

export async function getMaterialAnalysis(materialId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/analysis`, { method: 'GET' });
}

export async function getMaterialSummary(materialId, mode = 'standard', refresh = false) {
  const rawTarget = materialId || getActiveMaterialId();
  const targetId = (rawTarget && !['null', 'undefined', 'none'].includes(String(rawTarget).toLowerCase())) ? rawTarget : 'latest';
  const params = new URLSearchParams();
  if (mode) params.set('mode', mode);
  if (refresh) params.set('refresh', 'true');
  const queryStr = params.toString() ? `?${params.toString()}` : '';

  return await apiRequest(`/api/v1/materials/${targetId}/summary${queryStr}`, { method: 'GET' });
}

export async function regenerateMaterialSummary(materialId, { mode = 'standard', sectionId = null } = {}) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/summary/regenerate`, {
    method: 'POST',
    body: JSON.stringify({ mode, section_id: sectionId })
  });
}

export async function getMaterialSummaryStatus(materialId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/summary/status`, { method: 'GET' });
}

export async function getMaterialSummaryVisuals(materialId, mode = 'standard') {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/summary/visuals?mode=${mode}`, { method: 'GET' });
}

export async function chatWithMaterial(materialId, message, history = []) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message, history })
  });
}

// ----------------- Complete Verified Notes Engine API -----------------

export async function getReferenceStyleProfiles(materialId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/reference-styles`, { method: 'GET' });
}

export async function analyzeReferenceStyle(materialId, referenceDocumentId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/reference-styles`, {
    method: 'POST',
    body: JSON.stringify({ reference_document_id: referenceDocumentId })
  });
}

export async function startNotesJob(materialId, { mode = 'comprehensive', depth = 'thorough', language = 'en', syllabus = null, force_restart = false, reference_style_profile_id = null } = {}) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/notes/start`, {
    method: 'POST',
    body: JSON.stringify({ mode, depth, language, syllabus, force_restart, reference_style_profile_id })
  });
}

export async function getNotesJobStatus(materialId, jobId = 'latest') {
  const targetId = materialId || getActiveMaterialId();
  const endpoint = jobId && jobId !== 'latest' 
    ? `/api/v1/materials/${targetId}/notes/job/${jobId}` 
    : `/api/v1/materials/${targetId}/notes/latest`;
  return await apiRequest(endpoint, { method: 'GET' });
}

export async function retryNotesSection(materialId, jobId, { topic_id = null, section_id = null } = {}) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/notes/job/${jobId}/retry-section`, {
    method: 'POST',
    body: JSON.stringify({ topic_id, section_id })
  });
}

export async function resumeNotesJob(materialId, jobId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/notes/job/${jobId}/resume`, {
    method: 'POST',
    body: JSON.stringify({})
  });
}

export function getNotesDocxExportUrl(materialId, jobId = null) {
  const targetId = materialId || getActiveMaterialId();
  const query = jobId ? `?job_id=${encodeURIComponent(jobId)}` : '';
  return `/api/v1/materials/${targetId}/notes/export/docx${query}`;
}

export function getNotesPdfExportUrl(materialId, jobId = null) {
  const targetId = materialId || getActiveMaterialId();
  const query = jobId ? `?job_id=${encodeURIComponent(jobId)}` : '';
  return `/api/v1/materials/${targetId}/notes/export/pdf${query}`;
}

// ----------------- Subject Understanding & Teaching Engine API -----------------

export async function getSubjectOverview(materialId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/subject-overview`, { method: 'GET' });
}

export async function getSyllabusTree(materialId, includeContent = false) {
  const targetId = materialId || getActiveMaterialId();
  const query = includeContent ? '?include_content=true' : '';
  return await apiRequest(`/api/v1/materials/${targetId}/syllabus${query}`, { method: 'GET' });
}

export async function getTopicTeaching(materialId, topicId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/topics/${topicId}/teach`, { method: 'GET' });
}

export async function generateTopicTeaching(materialId, topicId, force = false) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/topics/${topicId}/teach`, {
    method: 'POST',
    body: JSON.stringify({ force })
  });
}

export async function getDocumentCoverage(materialId) {
  const targetId = materialId || getActiveMaterialId();
  return await apiRequest(`/api/v1/materials/${targetId}/coverage`, { method: 'GET' });
}



