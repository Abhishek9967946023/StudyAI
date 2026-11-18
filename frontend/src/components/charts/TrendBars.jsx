import React from 'react';

export function TrendBars({ 
  data = [65, 70, 60, 85, 78, 82, 90], 
  height = 140, 
  labels = ['Exam 1', 'Exam 2', 'Exam 3', 'Exam 4', 'Exam 5', 'Exam 6', 'Exam 7'] 
}) {
  const max = 100;
  const avg = Math.round(data.reduce((a, b) => a + b, 0) / (data.length || 1));

  return (
    <div style={{ position: 'relative', width: '100%', paddingTop: '10px' }}>
      {/* Average indicator badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '8px' }}>
        <span>7-Exam Mastery Trajectory</span>
        <span>Average: <strong style={{ color: 'var(--ink)' }}>{avg}%</strong></span>
      </div>

      <div style={{ 
        display: 'flex', 
        alignItems: 'flex-end', 
        justifyContent: 'space-between', 
        height, 
        paddingBottom: '24px', 
        position: 'relative',
        borderBottom: '1px solid var(--border)'
      }}>
        {/* Average dashed line */}
        <div style={{
          position: 'absolute',
          bottom: `calc(${avg}% * ${(height - 24) / 100} + 24px)`,
          left: 0,
          right: 0,
          borderBottom: '1px dashed var(--muted)',
          zIndex: 1,
          opacity: 0.5
        }} />

        {data.map((val, idx) => {
          const barHeight = Math.max(8, (val / max) * (height - 28));
          const isLatest = idx === data.length - 1;
          const isHigh = val >= 75;

          return (
            <div 
              key={idx} 
              style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                flex: 1, 
                gap: '6px',
                zIndex: 2
              }}
            >
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: isLatest ? 'var(--indigo)' : 'var(--muted)' }}>
                {val}%
              </span>
              <div 
                style={{ 
                  width: '60%', 
                  maxWidth: '24px', 
                  height: barHeight, 
                  backgroundColor: isLatest ? 'var(--indigo)' : (isHigh ? 'var(--teal)' : 'var(--coral)'),
                  borderRadius: '6px 6px 0 0',
                  transition: 'height 0.4s ease'
                }} 
                title={`${labels[idx] || `Exam ${idx+1}`}: ${val}%`}
              />
              <span style={{ 
                position: 'absolute', 
                bottom: 0, 
                fontSize: '0.68rem', 
                color: isLatest ? 'var(--ink)' : 'var(--muted)',
                fontWeight: isLatest ? 700 : 500
              }}>
                E{idx + 1}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
