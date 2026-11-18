import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, X } from 'lucide-react';

export function Toast({ 
  message, 
  variant = 'success', // 'success' | 'warning' | 'error'
  onClose 
}) {
  if (!message) return null;

  let bg = 'var(--surface)';
  let borderColor = 'var(--border)';
  let icon = <CheckCircle2 size={18} style={{ color: 'var(--teal)' }} />;

  if (variant === 'warning') {
    icon = <AlertTriangle size={18} style={{ color: 'var(--coral)' }} />;
    borderColor = 'var(--coral-tint)';
  } else if (variant === 'error') {
    icon = <AlertCircle size={18} style={{ color: 'var(--coral)' }} />;
    borderColor = 'var(--coral)';
  }

  return (
    <div 
      className="fade-in"
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        backgroundColor: bg,
        border: `1px solid ${borderColor}`,
        borderRadius: 'var(--radius-btn)',
        boxShadow: 'var(--shadow-md)',
        padding: '12px 18px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        zIndex: 2000,
        maxWidth: '400px'
      }}
    >
      {icon}
      <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--ink)' }}>{message}</span>
      {onClose && (
        <button 
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', marginLeft: 'auto', color: 'var(--muted)' }}
          aria-label="Close notification"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
