/**
=============================================================================
StudyAI — Study Copilot Service
=============================================================================
Grounded AI chat tutor strictly limited to the uploaded material.
Emits answers with precise source chips (section & page) and excerpts.
Never invents facts outside the material.
=============================================================================
*/

import { apiRequest } from './apiClient';
import { isUsingMocks, getActiveMaterialId } from './materialsService';

export async function askCopilot(question, materialId) {
  if (isUsingMocks()) {
    await new Promise(r => setTimeout(r, 600));

    return {
      answer: `Based strictly on the verified study material, "${question}" relates to the core concepts and principles documented in this text. StudyAI restricts all tutor answers strictly to verified citations from your uploaded material.`,
      sources: [
        { section: 'Section 1: Core Principles', page: 1, excerpt: 'Foundational concepts and verified mechanisms from the study material.' }
      ]
    };
  }

  const targetId = materialId || getActiveMaterialId();
  return await apiRequest('/api/v1/copilot/ask', {
    method: 'POST',
    body: JSON.stringify({ materialId: targetId, question })
  });
}
