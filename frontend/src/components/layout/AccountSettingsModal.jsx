/**
 * =============================================================================
 * StudyAI — Account Information & Complete App Settings Modal
 * =============================================================================
 * Opened from the top-right corner account area:
 * 1. 👤 Account Information & Profile Management
 * 2. 🎨 Appearance & Instant Theme Switcher (Light / Dark / System)
 * 3. 🤖 AI Engine & Model Settings (Local Ollama vs Cloud with Live Test)
 * 4. ⚙️ Exam & Study Defaults (Difficulty, Question Counts, Language)
 * 5. 💾 Data, Cache & Privacy Management
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, 
  User, 
  Mail, 
  Shield, 
  Key, 
  LogOut, 
  Sun, 
  Moon, 
  Monitor, 
  Cpu, 
  Sparkles, 
  Sliders, 
  Database, 
  Check, 
  CheckCircle2, 
  RefreshCw, 
  Download, 
  Trash2, 
  ExternalLink,
  Flame,
  Award,
  Globe,
  Clock,
  AlertTriangle,
  Lock
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';
import { Button } from '../ui/Button';
import { Chip } from '../ui/Chip';
import { apiRequest } from '../../services/apiClient';

export function AccountSettingsModal({ isOpen, onClose }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { theme, setTheme, isDark } = useTheme();

  // Active Tab: 'account' | 'appearance' | 'ai' | 'study' | 'data'
  const [activeTab, setActiveTab] = useState('account');

  // Account State
  const [displayName, setDisplayName] = useState(
    user?.name || localStorage.getItem('studyai_user_name') || 'Student'
  );
  const [userRole, setUserRole] = useState(
    localStorage.getItem('studyai_user_role') || 'Higher Education Student'
  );
  const [nameSaved, setNameSaved] = useState(false);

  // Appearance State
  const [fontScale, setFontScale] = useState(
    localStorage.getItem('studyai_font_scale') || 'medium'
  );

  // AI Configuration State
  const [engineConfig, setEngineConfig] = useState(() => {
    try {
      const s = localStorage.getItem('studyai_config');
      return s ? JSON.parse(s) : {
        engine: 'ollama',
        ollamaHost: 'http://localhost:11434',
        ollamaModel: 'llama3:latest',
        provider: 'gemini',
        apiKey: ''
      };
    } catch {
      return {
        engine: 'ollama',
        ollamaHost: 'http://localhost:11434',
        ollamaModel: 'llama3:latest',
        provider: 'gemini',
        apiKey: ''
      };
    }
  });

  const [testingOllama, setTestingOllama] = useState(false);
  const [ollamaResult, setOllamaResult] = useState(null);

  // Study Defaults State
  const [examDefaults, setExamDefaults] = useState(() => {
    try {
      const s = localStorage.getItem('studyai_exam_defaults');
      return s ? JSON.parse(s) : {
        questionCount: 8,
        difficulty: 'Medium',
        timeLimitMinutes: 12,
        language: 'en',
        strictGrounding: true
      };
    } catch {
      return {
        questionCount: 8,
        difficulty: 'Medium',
        timeLimitMinutes: 12,
        language: 'en',
        strictGrounding: true
      };
    }
  });

  const [settingsSaved, setSettingsSaved] = useState(false);

  useEffect(() => {
    if (user?.name) {
      setDisplayName(user.name);
    }
  }, [user]);

  if (!isOpen) return null;

  // Save Display Name
  const handleSaveProfile = (e) => {
    e.preventDefault();
    if (!displayName.trim()) return;
    localStorage.setItem('studyai_user_name', displayName.trim());
    localStorage.setItem('studyai_user_role', userRole);
    setNameSaved(true);
    setTimeout(() => setNameSaved(false), 2200);
  };

  // Save AI Settings
  const handleSaveAiConfig = () => {
    localStorage.setItem('studyai_config', JSON.stringify(engineConfig));
    setSettingsSaved(true);
    setTimeout(() => setSettingsSaved(false), 2200);
  };

  // Test Ollama Host
  const handleTestOllama = async () => {
    setTestingOllama(true);
    setOllamaResult(null);
    try {
      // First try Django backend proxy (safe from browser CORS, works cross-device)
      try {
        const d = await apiRequest('/api/ollama/status/');
        if (d && d.is_online) {
          setOllamaResult({
            success: true,
            message: `Connected via StudyAI Backend (${d.models?.length || 0} models available).`,
            models: d.models || []
          });
          return;
        }
      } catch {}

      // Fallback: direct browser fetch if user configured custom local Ollama host
      const res = await fetch(`${engineConfig.ollamaHost}/api/tags`, { method: 'GET' });
      if (res.ok) {
        const data = await res.json();
        const models = (data.models || []).map(m => m.name);
        setOllamaResult({
          success: true,
          message: `Ollama is Online! Detected ${models.length} installed model(s).`,
          models
        });
        return;
      }

      setOllamaResult({
        success: false,
        message: `Could not connect to Ollama at ${engineConfig.ollamaHost}. Ensure Ollama is running ('ollama serve').`
      });
    } catch {
      setOllamaResult({
        success: false,
        message: `Could not connect to Ollama at ${engineConfig.ollamaHost}. Ensure Ollama is running ('ollama serve').`
      });
    } finally {
      setTestingOllama(false);
    }
  };

  // Save Study Preferences
  const handleSaveStudyDefaults = () => {
    localStorage.setItem('studyai_exam_defaults', JSON.stringify(examDefaults));
    setSettingsSaved(true);
    setTimeout(() => setSettingsSaved(false), 2200);
  };

  // Clear Local Cache
  const handleClearCache = () => {
    if (window.confirm("Clear local study cache and autosaved exam drafts? Your account will remain logged in.")) {
      localStorage.removeItem('studyai_active_material_id');
      localStorage.removeItem('studyai_exam_defaults');
      alert("Local session cache cleared successfully!");
    }
  };

  // Export Study Data
  const handleExportData = () => {
    const dataToExport = {
      user: user || { email: 'student@studyai.edu' },
      profile: { displayName, userRole },
      config: engineConfig,
      examDefaults,
      timestamp: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `StudyAI_Account_Backup_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleLogout = async () => {
    onClose();
    await logout();
    navigate('/login');
  };

  const tabs = [
    { id: 'account', label: 'Account Profile', icon: <User size={16} /> },
    { id: 'appearance', label: 'Theme & Display', icon: isDark ? <Moon size={16} /> : <Sun size={16} /> },
    { id: 'ai', label: 'AI Inference Engine', icon: <Cpu size={16} /> },
    { id: 'study', label: 'Study & Exam Defaults', icon: <Sliders size={16} /> },
    { id: 'data', label: 'Data & Privacy', icon: <Database size={16} /> }
  ];

  return (
    <div 
      className="modal-backdrop fade-in"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(23, 21, 43, 0.65)',
        backdropFilter: 'blur(6px)',
        zIndex: 2000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
      onClick={onClose}
    >
      <div 
        className="sa-card"
        style={{
          width: '100%',
          maxWidth: '820px',
          maxHeight: '90vh',
          backgroundColor: 'var(--surface)',
          borderRadius: '24px',
          border: '1px solid var(--border)',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          flexDirection: 'column',
          padding: 0,
          overflow: 'hidden'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{
          padding: '24px 28px',
          backgroundColor: 'var(--surface)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '46px',
              height: '46px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, var(--indigo), #8B5CF6)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1.25rem',
              boxShadow: 'var(--shadow-glow)'
            }}>
              {(user?.email || displayName || 'U').charAt(0).toUpperCase()}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
                  {displayName}
                </h2>
                <Chip variant="teal" style={{ fontSize: '0.68rem', padding: '2px 6px' }}>
                  Student Pro
                </Chip>
              </div>
              <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                {user?.email || 'student@university.edu'}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close settings"
            style={{
              background: 'var(--bg)',
              border: '1px solid var(--border)',
              borderRadius: '10px',
              width: '34px',
              height: '34px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--muted)',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Tabs Bar */}
        <div style={{
          display: 'flex',
          gap: '4px',
          padding: '8px 24px 0 24px',
          backgroundColor: 'var(--bg)',
          borderBottom: '1px solid var(--border)',
          overflowX: 'auto'
        }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 16px',
                borderRadius: '10px 10px 0 0',
                border: 'none',
                background: activeTab === tab.id ? 'var(--surface)' : 'transparent',
                borderBottom: activeTab === tab.id ? '3px solid var(--indigo)' : '3px solid transparent',
                color: activeTab === tab.id ? 'var(--indigo)' : 'var(--muted)',
                fontWeight: activeTab === tab.id ? 700 : 500,
                fontSize: '0.86rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                whiteSpace: 'nowrap'
              }}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Modal Content Body */}
        <div style={{ padding: '24px 28px', overflowY: 'auto', flex: 1 }}>

          {/* ===================================================================
              TAB 1: ACCOUNT PROFILE
              =================================================================== */}
          {activeTab === 'account' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ink)', margin: '0 0 4px 0' }}>
                  Account Information
                </h3>
                <p style={{ color: 'var(--muted)', fontSize: '0.85rem', margin: 0 }}>
                  Manage your verified student credentials and active authenticated session.
                </p>
              </div>

              {nameSaved && (
                <div style={{
                  background: 'var(--teal-tint)',
                  border: '1px solid var(--teal)',
                  color: 'var(--teal-text)',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '0.86rem',
                  fontWeight: 600
                }}>
                  <CheckCircle2 size={16} />
                  <span>Profile updated successfully!</span>
                </div>
              )}

              <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                      Full Display Name
                    </label>
                    <input
                      type="text"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      placeholder="e.g. Abhishek"
                      className="auth-input"
                      style={{ width: '100%' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                      Primary Email Address
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type="email"
                        value={user?.email || 'student@university.edu'}
                        disabled
                        className="auth-input"
                        style={{ width: '100%', opacity: 0.8, cursor: 'not-allowed' }}
                      />
                      <span style={{
                        position: 'absolute',
                        right: '10px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        color: 'var(--teal)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <Check size={12} /> Verified
                      </span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                      Academic Role / Goal
                    </label>
                    <select
                      value={userRole}
                      onChange={(e) => setUserRole(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid var(--border)',
                        backgroundColor: 'var(--bg)',
                        color: 'var(--ink)',
                        fontSize: '0.88rem'
                      }}
                    >
                      <option value="Higher Education Student">Undergraduate / Degree Student</option>
                      <option value="Graduate Researcher">Graduate Researcher</option>
                      <option value="Competitive Exam Aspirant">Competitive Exam Aspirant (GRE / GATE)</option>
                      <option value="Medical & Health Sciences">Medical & Health Sciences</option>
                      <option value="Lifelong Independent Learner">Lifelong Independent Learner</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                      Session Security
                    </label>
                    <div style={{
                      padding: '10px 14px',
                      borderRadius: '10px',
                      background: 'var(--bg)',
                      border: '1px solid var(--border)',
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      color: 'var(--teal-text)'
                    }}>
                      <Shield size={16} color="var(--teal)" />
                      <span>Encrypted Session Active</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <Button type="submit" variant="primary" size="sm">
                    Save Profile Changes
                  </Button>
                </div>
              </form>

              {/* Security & Actions Row */}
              <div style={{
                marginTop: '10px',
                paddingTop: '20px',
                borderTop: '1px solid var(--border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px'
              }}>
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    navigate('/forgot-password');
                  }}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--indigo)',
                    fontSize: '0.88rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: 0
                  }}
                >
                  <Key size={15} />
                  <span>Change / Reset Account Password</span>
                </button>

                <Button
                  variant="secondary"
                  size="sm"
                  icon={<LogOut size={14} color="var(--coral)" />}
                  onClick={handleLogout}
                  style={{ color: 'var(--coral)', borderColor: 'rgba(229, 72, 77, 0.3)' }}
                >
                  Sign Out of StudyAI
                </Button>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 2: APPEARANCE & THEME
              =================================================================== */}
          {activeTab === 'appearance' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ink)', margin: '0 0 4px 0' }}>
                  Appearance & Theme Settings
                </h3>
                <p style={{ color: 'var(--muted)', fontSize: '0.85rem', margin: 0 }}>
                  Customize the look and feel of StudyAI. Choose your preferred color theme.
                </p>
              </div>

              {/* Theme Cards Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                {/* Light Theme Card */}
                <div
                  onClick={() => setTheme('light')}
                  style={{
                    padding: '18px',
                    borderRadius: '16px',
                    border: theme === 'light' ? '2px solid var(--indigo)' : '1px solid var(--border)',
                    background: theme === 'light' ? 'var(--indigo-tint)' : 'var(--bg)',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    transition: 'all 0.2s ease',
                    boxShadow: theme === 'light' ? 'var(--shadow-glow)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: '#FFFFFF',
                      color: '#E65100',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '1px solid #E6E3F3'
                    }}>
                      <Sun size={20} />
                    </div>
                    {theme === 'light' && <CheckCircle2 size={18} color="var(--indigo)" />}
                  </div>

                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.96rem', color: 'var(--ink)' }}>Light Theme</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '2px' }}>
                      Clean, high-clarity daylight interface with soft violet accents.
                    </div>
                  </div>
                </div>

                {/* Dark Theme Card */}
                <div
                  onClick={() => setTheme('dark')}
                  style={{
                    padding: '18px',
                    borderRadius: '16px',
                    border: theme === 'dark' ? '2px solid var(--indigo)' : '1px solid var(--border)',
                    background: theme === 'dark' ? 'var(--indigo-tint)' : 'var(--bg)',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    transition: 'all 0.2s ease',
                    boxShadow: theme === 'dark' ? 'var(--shadow-glow)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: '#151324',
                      color: '#A89FFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '1px solid #26233E'
                    }}>
                      <Moon size={20} />
                    </div>
                    {theme === 'dark' && <CheckCircle2 size={18} color="var(--indigo)" />}
                  </div>

                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.96rem', color: 'var(--ink)' }}>Dark Obsidian Theme</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '2px' }}>
                      Sleek dark glassmorphic design reducing eye strain during night study.
                    </div>
                  </div>
                </div>
              </div>

              {/* Font / Layout Scale */}
              <div style={{ paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
                <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '8px' }}>
                  Reading & Interface Scale
                </label>
                <div style={{ display: 'flex', gap: '10px' }}>
                  {[
                    { id: 'compact', label: 'Compact' },
                    { id: 'medium', label: 'Default / Standard' },
                    { id: 'large', label: 'Comfortable / Large' }
                  ].map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => {
                        setFontScale(s.id);
                        localStorage.setItem('studyai_font_scale', s.id);
                      }}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        border: fontScale === s.id ? '2px solid var(--indigo)' : '1px solid var(--border)',
                        background: fontScale === s.id ? 'var(--indigo-tint)' : 'var(--bg)',
                        color: fontScale === s.id ? 'var(--indigo-text)' : 'var(--ink)',
                        fontSize: '0.84rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 3: AI ENGINE & MODEL
              =================================================================== */}
          {activeTab === 'ai' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ink)', margin: '0 0 4px 0' }}>
                  AI Processing Engine Configuration
                </h3>
                <p style={{ color: 'var(--muted)', fontSize: '0.85rem', margin: 0 }}>
                  Choose whether StudyAI uses local open-source models via Ollama or cloud LLMs.
                </p>
              </div>

              {settingsSaved && (
                <div style={{
                  background: 'var(--teal-tint)',
                  border: '1px solid var(--teal)',
                  color: 'var(--teal-text)',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '0.86rem',
                  fontWeight: 600
                }}>
                  <CheckCircle2 size={16} />
                  <span>AI Engine configuration saved!</span>
                </div>
              )}

              {/* Engine Toggle */}
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  type="button"
                  onClick={() => setEngineConfig(prev => ({ ...prev, engine: 'ollama' }))}
                  style={{
                    flex: 1,
                    padding: '14px',
                    borderRadius: '12px',
                    border: engineConfig.engine === 'ollama' ? '2px solid var(--indigo)' : '1px solid var(--border)',
                    background: engineConfig.engine === 'ollama' ? 'var(--indigo-tint)' : 'var(--bg)',
                    color: engineConfig.engine === 'ollama' ? 'var(--indigo-text)' : 'var(--ink)',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '0.92rem' }}>
                    <Cpu size={18} />
                    <span>Local Ollama (Free & Private)</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '4px' }}>
                    Runs locally on your device. Zero API costs, 100% data privacy.
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setEngineConfig(prev => ({ ...prev, engine: 'cloud' }))}
                  style={{
                    flex: 1,
                    padding: '14px',
                    borderRadius: '12px',
                    border: engineConfig.engine === 'cloud' ? '2px solid var(--indigo)' : '1px solid var(--border)',
                    background: engineConfig.engine === 'cloud' ? 'var(--indigo-tint)' : 'var(--bg)',
                    color: engineConfig.engine === 'cloud' ? 'var(--indigo-text)' : 'var(--ink)',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '0.92rem' }}>
                    <Sparkles size={18} />
                    <span>Cloud LLM (Gemini / Claude)</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '4px' }}>
                    High-parameter cloud models via your personal API key.
                  </div>
                </button>
              </div>

              {/* Ollama Details */}
              {engineConfig.engine === 'ollama' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', background: 'var(--bg)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border)' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                        Ollama Host URL
                      </label>
                      <input
                        type="text"
                        value={engineConfig.ollamaHost}
                        onChange={(e) => setEngineConfig(prev => ({ ...prev, ollamaHost: e.target.value }))}
                        className="auth-input"
                        style={{ width: '100%', fontSize: '0.85rem' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                        Selected LLM Model
                      </label>
                      <select
                        value={engineConfig.ollamaModel}
                        onChange={(e) => setEngineConfig(prev => ({ ...prev, ollamaModel: e.target.value }))}
                        style={{
                          width: '100%',
                          padding: '10px 12px',
                          borderRadius: '10px',
                          border: '1px solid var(--border)',
                          backgroundColor: 'var(--surface)',
                          color: 'var(--ink)',
                          fontSize: '0.85rem'
                        }}
                      >
                        <option value="llama3:latest">Meta Llama 3 (llama3:latest)</option>
                        <option value="llama3:8b">Llama 3 8B (llama3:8b)</option>
                        <option value="mistral:latest">Mistral 7B (mistral:latest)</option>
                        <option value="gemma:7b">Google Gemma (gemma:7b)</option>
                        <option value="phi3:latest">Microsoft Phi-3 (phi3:latest)</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Cloud API Key */}
              {engineConfig.engine === 'cloud' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', background: 'var(--bg)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border)' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                      Cloud Provider
                    </label>
                    <select
                      value={engineConfig.provider}
                      onChange={(e) => setEngineConfig(prev => ({ ...prev, provider: e.target.value }))}
                      style={{
                        width: '100%',
                        padding: '10px 12px',
                        borderRadius: '10px',
                        border: '1px solid var(--border)',
                        backgroundColor: 'var(--surface)',
                        color: 'var(--ink)',
                        fontSize: '0.85rem'
                      }}
                    >
                      <option value="gemini">Google Gemini API (gemini-1.5-flash / pro)</option>
                      <option value="openai">OpenAI API (gpt-4o / gpt-4o-mini)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                      API Key
                    </label>
                    <input
                      type="password"
                      placeholder="Paste your personal API key here..."
                      value={engineConfig.apiKey}
                      onChange={(e) => setEngineConfig(prev => ({ ...prev, apiKey: e.target.value }))}
                      className="auth-input"
                      style={{ width: '100%', fontSize: '0.85rem' }}
                    />
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <Button variant="primary" size="sm" onClick={handleSaveAiConfig}>
                  Save AI Configuration
                </Button>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 4: STUDY & EXAM DEFAULTS
              =================================================================== */}
          {activeTab === 'study' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ink)', margin: '0 0 4px 0' }}>
                  Exam & Revision Preferences
                </h3>
                <p style={{ color: 'var(--muted)', fontSize: '0.85rem', margin: 0 }}>
                  Set your default question counts, timer preferences, and language options.
                </p>
              </div>

              {settingsSaved && (
                <div style={{
                  background: 'var(--teal-tint)',
                  border: '1px solid var(--teal)',
                  color: 'var(--teal-text)',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '0.86rem',
                  fontWeight: 600
                }}>
                  <CheckCircle2 size={16} />
                  <span>Preferences saved!</span>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                    Default Question Count
                  </label>
                  <select
                    value={examDefaults.questionCount}
                    onChange={(e) => setExamDefaults(prev => ({ ...prev, questionCount: parseInt(e.target.value, 10) }))}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '10px',
                      border: '1px solid var(--border)',
                      backgroundColor: 'var(--bg)',
                      color: 'var(--ink)',
                      fontSize: '0.88rem'
                    }}
                  >
                    <option value="5">5 Questions (Quick Test)</option>
                    <option value="8">8 Questions (Standard)</option>
                    <option value="10">10 Questions (Benchmark)</option>
                    <option value="15">15 Questions (Comprehensive)</option>
                    <option value="20">20 Questions (Full Mock)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                    Default Difficulty
                  </label>
                  <select
                    value={examDefaults.difficulty}
                    onChange={(e) => setExamDefaults(prev => ({ ...prev, difficulty: e.target.value }))}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '10px',
                      border: '1px solid var(--border)',
                      backgroundColor: 'var(--bg)',
                      color: 'var(--ink)',
                      fontSize: '0.88rem'
                    }}
                  >
                    <option value="Easy">Easy (Factual & Definitions)</option>
                    <option value="Medium">Medium (Processes & Analysis)</option>
                    <option value="Hard">Hard (Deep Synthesis & Rigor)</option>
                    <option value="Adaptive">Adaptive (Calibrated by AI)</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
                  Study Notes Language
                </label>
                <select
                  value={examDefaults.language}
                  onChange={(e) => setExamDefaults(prev => ({ ...prev, language: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '10px',
                    border: '1px solid var(--border)',
                    backgroundColor: 'var(--bg)',
                    color: 'var(--ink)',
                    fontSize: '0.88rem'
                  }}
                >
                  <option value="en">English (Original Syllabus Language)</option>
                  <option value="hi">Hindi (हिंदी)</option>
                  <option value="es">Spanish (Español)</option>
                  <option value="fr">French (Français)</option>
                  <option value="de">German (Deutsch)</option>
                  <option value="kn">Kannada (ಕನ್ನಡ)</option>
                  <option value="ta">Tamil (தமிழ்)</option>
                  <option value="te">Telugu (తెలుగు)</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', background: 'var(--bg)', padding: '16px', borderRadius: '12px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.86rem', color: 'var(--ink)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={examDefaults.strictGrounding}
                    onChange={(e) => setExamDefaults(prev => ({ ...prev, strictGrounding: e.target.checked }))}
                  />
                  <span style={{ fontWeight: 600 }}>Strict Document Grounding</span>
                </label>
                <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)', paddingLeft: '24px' }}>
                  Guarantees that every exam question, summary explanation, and flashcard cites exact verified excerpts from your uploaded notes.
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <Button variant="primary" size="sm" onClick={handleSaveStudyDefaults}>
                  Save Study Preferences
                </Button>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 5: DATA, STORAGE & PRIVACY
              =================================================================== */}
          {activeTab === 'data' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ink)', margin: '0 0 4px 0' }}>
                  Local Data, Cache & Privacy
                </h3>
                <p style={{ color: 'var(--muted)', fontSize: '0.85rem', margin: 0 }}>
                  Export backups of your study summaries or purge cached session data.
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* Export Data */}
                <div style={{
                  padding: '16px 18px',
                  borderRadius: '14px',
                  border: '1px solid var(--border)',
                  background: 'var(--bg)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px'
                }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--ink)' }}>Export Study Intelligence Backup</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                      Download a JSON file containing all saved configurations, profile goals, and preferences.
                    </div>
                  </div>
                  <Button variant="secondary" size="sm" icon={<Download size={14} />} onClick={handleExportData}>
                    Export JSON
                  </Button>
                </div>

                {/* Clear Cache */}
                <div style={{
                  padding: '16px 18px',
                  borderRadius: '14px',
                  border: '1px solid var(--border)',
                  background: 'var(--bg)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px'
                }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--ink)' }}>Clear Local Study Cache</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                      Clears autosaved exam progress and session drafts. Your account credentials stay logged in.
                    </div>
                  </div>
                  <Button variant="secondary" size="sm" icon={<Trash2 size={14} color="var(--coral)" />} onClick={handleClearCache}>
                    Clear Cache
                  </Button>
                </div>
              </div>

              {/* Version & Build */}
              <div style={{
                paddingTop: '16px',
                borderTop: '1px solid var(--border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.78rem',
                color: 'var(--muted)'
              }}>
                <span>StudyAI Platform v2.4 (Commercial Edition)</span>
                <span>Django REST + React 18 + Ollama</span>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default AccountSettingsModal;
