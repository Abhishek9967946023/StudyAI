import React from 'react';

export function Skeleton({ 
  width = '100%', 
  height = '20px', 
  borderRadius = '8px',
  className = '',
  style = {} 
}) {
  return (
    <div 
      className={`sa-skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: 'var(--border)',
        opacity: 0.7,
        animation: 'pulse 1.5s ease-in-out infinite',
        ...style
      }}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="sa-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <Skeleton width="45%" height="24px" />
      <Skeleton width="85%" height="16px" />
      <Skeleton width="65%" height="16px" />
      <div style={{ marginTop: '8px', display: 'flex', gap: '10px' }}>
        <Skeleton width="90px" height="32px" borderRadius="999px" />
        <Skeleton width="90px" height="32px" borderRadius="999px" />
      </div>
    </div>
  );
}
