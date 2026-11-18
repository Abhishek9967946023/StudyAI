import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, GraduationCap, Sparkles, Layers, LogOut, User as UserIcon, Settings, ChevronDown, Moon, Sun } from 'lucide-react';
import { Button } from '../ui/Button';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';
import { AccountSettingsModal } from './AccountSettingsModal';

export function TopBar() {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();
  const [isAccountModalOpen, setIsAccountModalOpen] = useState(false);

  return (
    <header
      className="sa-topbar"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backgroundColor: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        padding: '12px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backdropFilter: 'blur(10px)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 10px',
          backgroundColor: 'var(--indigo-tint)',
          borderRadius: 'var(--radius-pill)',
          color: 'var(--indigo-text)',
          fontSize: '0.78rem',
          fontWeight: 600
        }}>
          <Sparkles size={13} />
          <span>StudyAI Intelligence </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Button 
          variant="secondary" 
          size="sm" 
          icon={<Layers size={15} />}
          onClick={() => navigate('/workspace')}
        >
          Study Workspace
        </Button>

        <Button 
          variant="secondary" 
          size="sm" 
          icon={<GraduationCap size={15} />}
          onClick={() => navigate('/exam-config')}
        >
          Generate Exam
        </Button>

        <Button 
          variant="primary" 
          size="sm" 
          icon={<UploadCloud size={15} />}
          onClick={() => navigate('/upload')}
        >
          Analyze Material
        </Button>

        {/* Quick Theme Toggle Button */}
        <button
          type="button"
          onClick={toggleTheme}
          title={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
          aria-label="Toggle theme"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            border: '1px solid var(--border)',
            backgroundColor: 'var(--surface)',
            color: 'var(--muted)',
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--indigo)';
            e.currentTarget.style.borderColor = 'var(--indigo)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--muted)';
            e.currentTarget.style.borderColor = 'var(--border)';
          }}
        >
          {isDark ? <Sun size={17} color="#F59E0B" /> : <Moon size={17} />}
        </button>

        {/* Authenticated User Profile & Settings Trigger */}
        {isAuthenticated && user ? (
          <div
            className="profile"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              paddingLeft: '10px',
              borderLeft: '1px solid var(--border)'
            }}
          >
            {/* Clickable Account & Settings Badge */}
            <button
              type="button"
              onClick={() => setIsAccountModalOpen(true)}
              title="Click to view Account Information & App Settings"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 10px 4px 6px',
                borderRadius: '999px',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--surface)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: 'var(--shadow-sm)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--indigo)';
                e.currentTarget.style.backgroundColor = 'var(--indigo-tint)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.backgroundColor = 'var(--surface)';
              }}
            >
              <span
                className="avatar"
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--indigo), #8B5CF6)',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  boxShadow: '0 2px 6px rgba(79, 63, 240, 0.25)'
                }}
              >
                {(user.email || 'U').charAt(0).toUpperCase()}
              </span>
              <span
                style={{
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  color: 'var(--ink)',
                  maxWidth: '120px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
              >
                {user.name || user.email?.split('@')[0] || 'Account'}
              </span>
              <Settings size={14} color="var(--indigo)" style={{ opacity: 0.9 }} />
            </button>

            {/* Quick Logout Button */}
            <button
              type="button"
              onClick={async () => {
                await logout();
                navigate('/login');
              }}
              title="Sign Out"
              aria-label="Sign Out"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                backgroundColor: 'transparent',
                color: 'var(--muted)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--coral)';
                e.currentTarget.style.borderColor = 'var(--coral)';
                e.currentTarget.style.backgroundColor = 'var(--coral-tint)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--muted)';
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <Button
            variant="secondary"
            size="sm"
            icon={<UserIcon size={14} />}
            onClick={() => setIsAccountModalOpen(true)}
          >
            Account & Settings
          </Button>
        )}
      </div>

      {/* Account Information & Complete App Settings Modal */}
      <AccountSettingsModal 
        isOpen={isAccountModalOpen} 
        onClose={() => setIsAccountModalOpen(false)} 
      />
    </header>
  );
}
