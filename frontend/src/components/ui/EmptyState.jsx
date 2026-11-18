import React from 'react';
import { Button } from './Button';

export function EmptyState({ 
  icon = null, 
  title = 'No items found', 
  description = 'Get started by creating or analyzing your study material.', 
  actionLabel = 'Get Started',
  onAction = null,
  actionIcon = null,
  className = '' 
}) {
  return (
    <div 
      className={`sa-card ${className}`} 
      style={{ 
        textAlign: 'center', 
        padding: '3rem 1.5rem', 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}
    >
      {icon && (
        <div style={{ 
          width: '56px', 
          height: '56px', 
          borderRadius: '16px', 
          backgroundColor: 'var(--indigo-tint)', 
          color: 'var(--indigo)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          marginBottom: '1.25rem' 
        }}>
          {icon}
        </div>
      )}
      <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.4rem' }}>{title}</h3>
      <p style={{ fontSize: '0.9rem', color: 'var(--muted)', maxWidth: '440px', marginBottom: '1.5rem' }}>
        {description}
      </p>
      {onAction && (
        <Button variant="primary" icon={actionIcon} onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
