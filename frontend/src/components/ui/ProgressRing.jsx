import React from 'react';

export function ProgressRing({ 
  value = 0, 
  size = 110, 
  strokeWidth = 9, 
  showText = true,
  subtitle = '',
  className = '' 
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const offset = circumference - (clamped / 100) * circumference;

  let strokeColor = 'var(--indigo)';
  if (clamped >= 75) strokeColor = 'var(--teal)';
  else if (clamped < 60) strokeColor = 'var(--coral)';

  return (
    <div className={`sa-progress-ring ${className}`} style={{ position: 'relative', width: size, height: size, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--border)"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Active progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s cubic-bezier(0.16, 1, 0.3, 1)' }}
        />
      </svg>
      {showText && (
        <div style={{ position: 'absolute', textAlign: 'center' }}>
          <div style={{ fontFamily: 'var(--font-heading)', fontSize: size > 90 ? '1.5rem' : '1.1rem', fontWeight: 700, lineHeight: 1 }}>
            {clamped}%
          </div>
          {subtitle && (
            <div style={{ fontSize: '0.68rem', color: 'var(--muted)', marginTop: '2px' }}>
              {subtitle}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
