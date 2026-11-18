/**
=============================================================================
StudyAI — Settings Screen (Screen 13)
=============================================================================
Features:
- Live System Diagnostics: Backend connection & Ollama AI status
- Local Ollama AI inference model selector (llama3, gemma4, etc.)
- Output Language Preference (English, Hindi, etc.)
- Profile management
- Theme switcher: Light / Dark / System default
- Default Exam presets
=============================================================================
*/

import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Moon, 
  Sun, 
  Monitor, 
  Cpu, 
  ShieldCheck, 
  Sliders, 
  Bell, 
  User, 
  Check, 
  Save, 
  CheckCircle2, 
  Sparkles, 
  Languages 
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { useTheme } from '../hooks/useTheme';
import { apiRequest } from '../services/apiClient';

export function Settings() {
  const { theme, setTheme, isDark } = useTheme();

  // Backend & AI Live Status
  const [ollamaStatus, setOllamaStatus] = useState('checking');
  const [ollamaModels, setOllamaModels] = useState([]);
  const [aiProviderStatus, setAiProviderStatus] = useState(null);

  // Local storage profile state
  const [profile, setProfile] = useState(() => {
    try {
      const s = localStorage.getItem('studyai_profile');
      return s ? JSON.parse(s) : { name: 'Student', goal: 'Higher Education & Academic Mastery', targetScore: 80 };
    } catch {
      return { name: 'Student', goal: 'Higher Education & Academic Mastery', targetScore: 80 };
    }
  });

  // Output Language
  const [outputLanguage, setOutputLanguage] = useState(() => {
    return localStorage.getItem('studyai_output_language') || 'en';
  });

  // AI Inference Engine Configuration
  const [engineConfig, setEngineConfig] = useState(() => {
    try {
      const s = localStorage.getItem('studyai_config');
      return s ? JSON.parse(s) : {
        engine: 'ollama',
        ollamaHost: 'http://localhost:11434',
        ollamaModel: 'llama3:latest',
        temperature: 0.2
      };
    } catch {
      return {
        engine: 'ollama',
        ollamaHost: 'http://localhost:11434',
        ollamaModel: 'llama3:latest',
        temperature: 0.2
      };
    }
  });

  // Default Exam Preferences
  const [examDefaults, setExamDefaults] = useState(() => {
    try {
      const s = localStorage.getItem('studyai_exam_defaults');
      return s ? JSON.parse(s) : {
        questionCount: 8,
        difficulty: 'Medium',
        timeLimitMinutes: 12,
        randomize: true,
        importantOnly: true
      };
    } catch {
      return {
        questionCount: 8,
        difficulty: 'Medium',
        timeLimitMinutes: 12,
        randomize: true,
        importantOnly: true
      };
    }
  });

  const [savedSuccess, setSavedSuccess] = useState(false);

  // Ping backend & Ollama on mount
  useEffect(() => {
    async function checkHealth() {
      try {
        const oRes = await apiRequest('/api/ollama/status/', { timeout: 3000 });
        setAiProviderStatus(oRes?.ai_provider || null);
        if (oRes?.is_online) {
          setOllamaStatus('online');
          setOllamaModels(oRes.models || ['llama3:latest']);
        } else {
          setOllamaStatus('offline');
        }
      } catch {
        setOllamaStatus('offline');
      }
    }
    checkHealth();
  }, []);

  const handleSaveAll = () => {
    localStorage.setItem('studyai_profile', JSON.stringify(profile));
    localStorage.setItem('studyai_config', JSON.stringify(engineConfig));
    localStorage.setItem('studyai_exam_defaults', JSON.stringify(examDefaults));
    localStorage.removeItem('studyai_use_mocks');
    localStorage.setItem('studyai_output_language', outputLanguage);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* 1. Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--indigo)', marginBottom: '4px' }}>
            <SettingsIcon size={18} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Preferences & Configuration
            </span>
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
            System Settings
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '0.96rem', margin: '6px 0 0 0' }}>
            Configure real AI processing, local Ollama models, and interface parameters.
          </p>
        </div>

        <Button 
          variant="primary" 
          icon={<Save size={16} />}
          onClick={handleSaveAll}
        >
          {savedSuccess ? 'Saved Successfully!' : 'Save Preferences'}
        </Button>
      </div>





      {/* 4. Local AI Model & Language Preference */}
      <Card style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={20} color="var(--indigo)" />
              <h2 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
                Ollama Engine & Multilingual Settings
              </h2>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
              Local inference model, server-configured AI provider, and target summary language.
            </p>
          </div>
          <Chip label="Zero Cost • Offline Private" variant="teal" size="sm" />
        </div>

        {aiProviderStatus && (
          <div
            role="status"
            style={{
              border: '1px solid var(--border)',
              borderRadius: '10px',
              padding: '10px 12px',
              color: 'var(--muted)',
              fontSize: '0.8rem'
            }}
          >
            Active provider: <strong style={{ color: 'var(--ink)' }}>{aiProviderStatus.provider}</strong>
            {' · '}
            {aiProviderStatus.message}
            {' API keys are managed on the server and are never stored in this browser.'}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {/* Active Model Identifier */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--ink)' }}>
              Active AI Model
            </label>
            <select 
              value={engineConfig.ollamaModel}
              onChange={(e) => setEngineConfig({ ...engineConfig, ollamaModel: e.target.value })}
              style={{
                padding: '10px 14px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--ink)',
                fontSize: '0.9rem',
                cursor: 'pointer'
              }}
            >
              {ollamaModels.length > 0 ? (
                ollamaModels.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))
              ) : (
                <>
                  <option value="llama3:latest">llama3:latest (Default)</option>
                  <option value="gemma4:latest">gemma4:latest</option>
                  <option value="gemma4:e4b">gemma4:e4b</option>
                </>
              )}
            </select>
            <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
              Locally installed on Ollama daemon
            </span>
          </div>

          {/* Target Output Language */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--ink)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Languages size={14} /> Output Notes Language
            </label>
            <select 
              value={outputLanguage}
              onChange={(e) => setOutputLanguage(e.target.value)}
              style={{
                padding: '10px 14px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--ink)',
                fontSize: '0.9rem',
                cursor: 'pointer'
              }}
            >
              <option value="en">English (Default)</option>
              <option value="hi">Hindi (हिंदी)</option>
              <option value="kn">Kannada (ಕನ್ನಡ)</option>
              <option value="ta">Tamil (தமிழ்)</option>
              <option value="te">Telugu (తెలుగు)</option>
              <option value="es">Spanish (Español)</option>
              <option value="fr">French (Français)</option>
              <option value="de">German (Deutsch)</option>
            </select>
            <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
              Language used for synthesized notes & study plans
            </span>
          </div>
        </div>
      </Card>

      {/* 5. Theme Preference */}
      <Card style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
          Interface Appearance
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <button
            onClick={() => setTheme('light')}
            style={{
              padding: '16px',
              borderRadius: '14px',
              border: `2px solid ${theme === 'light' ? 'var(--indigo)' : 'var(--border)'}`,
              background: '#FFFFFF',
              color: '#0F172A',
              textAlign: 'left',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <Sun size={22} color="#F59E0B" />
            <div>
              <strong style={{ fontSize: '0.95rem' }}>Light Mode</strong>
              <div style={{ fontSize: '0.8rem', color: '#64748B', marginTop: '2px' }}>High contrast daylight</div>
            </div>
          </button>

          <button
            onClick={() => setTheme('dark')}
            style={{
              padding: '16px',
              borderRadius: '14px',
              border: `2px solid ${theme === 'dark' ? 'var(--indigo)' : 'var(--border)'}`,
              background: '#17152B',
              color: '#FFFFFF',
              textAlign: 'left',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <Moon size={22} color="#A78BFA" />
            <div>
              <strong style={{ fontSize: '0.95rem' }}>Dark Mode</strong>
              <div style={{ fontSize: '0.8rem', color: '#94A3B8', marginTop: '2px' }}>Eye-friendly night ground</div>
            </div>
          </button>

          <button
            onClick={() => setTheme('system')}
            style={{
              padding: '16px',
              borderRadius: '14px',
              border: `2px solid ${theme === 'system' ? 'var(--indigo)' : 'var(--border)'}`,
              background: 'var(--surface)',
              color: 'var(--ink)',
              textAlign: 'left',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <Monitor size={22} color="var(--muted)" />
            <div>
              <strong style={{ fontSize: '0.95rem' }}>System Preference</strong>
              <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '2px' }}>Matches your OS theme</div>
            </div>
          </button>
        </div>
      </Card>
    </div>
  );
}
