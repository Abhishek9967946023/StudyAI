import React from 'react';

export function Button({ 
  children, 
  variant = 'primary', // 'primary' | 'secondary' | 'teal' | 'coral' | 'ghost'
  size = 'md',        // 'sm' | 'md' | 'lg'
  icon = null,
  iconRight = null,
  disabled = false,
  loading = false,
  className = '',
  onClick,
  type = 'button',
  ariaLabel,
  ...props 
}) {
  const variantClass = `sa-btn-${variant}`;
  const sizeClass = size === 'sm' ? 'sa-btn-sm' : (size === 'lg' ? 'sa-btn-lg' : '');

  return (
    <button
      type={type}
      className={`sa-btn ${variantClass} ${sizeClass} ${className}`.trim()}
      disabled={disabled || loading}
      onClick={onClick}
      aria-label={ariaLabel}
      {...props}
    >
      {loading ? (
        <span className="sa-spinner" style={{
          width: '16px', 
          height: '16px', 
          border: '2px solid rgba(255,255,255,0.3)', 
          borderTopColor: '#fff', 
          borderRadius: '50%', 
          animation: 'spin 0.6s linear infinite'
        }} />
      ) : icon}
      {children}
      {!loading && iconRight}
    </button>
  );
}
