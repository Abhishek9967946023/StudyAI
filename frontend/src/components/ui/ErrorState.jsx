import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export function ErrorState({ 
  title = 'Something went wrong', 
  message = 'We encountered an unexpected error while loading this data.', 
  onRetry = null,
  className = '' 
}) {
  return (
    <div 
      className={`sa-card ${className}`} 
      style={{ 
        textAlign: 'center', 
        padding: '2.5rem 1.5rem', 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center',
        borderColor: 'var(--coral-tint)'
      }}
    >
      <div style={{ 
        width: '48px', 
        height: '48px', 
        borderRadius: '50%', 
        backgroundColor: 'var(--coral-tint)', 
        color: 'var(--coral)', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        marginBottom: '1rem' 
      }}>
        <AlertCircle size={24} />
      </div>
      <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.4rem', color: 'var(--coral-text)' }}>
        {title}
      </h3>
      <p style={{ fontSize: '0.875rem', color: 'var(--muted)', maxWidth: '400px', marginBottom: '1.25rem' }}>
        {message}
      </p>
      {onRetry && (
        <Button variant="secondary" icon={<RefreshCw size={14} />} onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}
