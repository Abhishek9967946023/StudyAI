import React from 'react';

export function ProgressBar({ 
  value = 0, // 0 to 100
  variant = 'indigo', // 'indigo' | 'teal' | 'coral'
  height = '8px',
  showLabel = false,
  className = '',
  style = {}
}) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  
  let fillColor = 'var(--indigo)';
  if (variant === 'teal') fillColor = 'var(--teal)';
  if (variant === 'coral') fillColor = 'var(--coral)';

  return (
    <div className={`sa-progress-container ${className}`} style={{ width: '100%', ...style }}>
      {showLabel && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.25rem' }}>
          <span>Progress</span>
          <span>{clamped}%</span>
        </div>
      )}
      <div style={{
        width: '100%',
        height,
        backgroundColor: 'var(--border)',
        borderRadius: 'var(--radius-pill)',
        overflow: 'hidden',
        position: 'relative'
      }}>
        <div style={{
          width: `${clamped}%`,
          height: '100%',
          backgroundColor: fillColor,
          borderRadius: 'var(--radius-pill)',
          transition: 'width 0.4s cubic-bezier(0.16, 1, 0.3, 1)'
        }} />
      </div>
    </div>
  );
}
