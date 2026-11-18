import React from 'react';

export function Tabs({ 
  tabs = [], 
  activeTab, 
  onChange, 
  className = '' 
}) {
  return (
    <div 
      className={`sa-tabs-container ${className}`}
      style={{
        display: 'inline-flex',
        padding: '4px',
        backgroundColor: 'var(--border)',
        borderRadius: 'var(--radius-pill)',
        gap: '4px'
      }}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            style={{
              padding: '6px 16px',
              borderRadius: 'var(--radius-pill)',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
              fontSize: '0.875rem',
              fontWeight: 600,
              backgroundColor: isActive ? 'var(--surface)' : 'transparent',
              color: isActive ? 'var(--ink)' : 'var(--muted)',
              boxShadow: isActive ? 'var(--shadow-sm)' : 'none',
              transition: 'all var(--transition-fast)'
            }}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
