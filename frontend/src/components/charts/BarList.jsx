import React from 'react';

export function BarList({ 
  items = [], // [{ label: 'Light Reactions', value: 50, isWeak: true }]
  maxValue = 100 
}) {
  return (
    <div className="sa-bar-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {items.map((it, idx) => {
        const pct = Math.max(0, Math.min(100, Math.round((it.value / maxValue) * 100)));
        const isWeak = it.isWeak !== undefined ? it.isWeak : it.value < 60;
        const color = isWeak ? 'var(--coral)' : 'var(--teal)';

        return (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span style={{ fontWeight: 600, color: 'var(--ink)' }}>{it.label || it.topic || it.name}</span>
              <span style={{ fontWeight: 700, color }}>{it.value}%</span>
            </div>
            <div style={{ 
              width: '100%', 
              height: '8px', 
              backgroundColor: 'var(--border)', 
              borderRadius: 'var(--radius-pill)', 
              overflow: 'hidden' 
            }}>
              <div style={{ 
                width: `${pct}%`, 
                height: '100%', 
                backgroundColor: color, 
                borderRadius: 'var(--radius-pill)',
                transition: 'width 0.5s ease' 
              }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
