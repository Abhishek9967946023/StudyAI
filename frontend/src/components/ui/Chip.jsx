import React from 'react';

export function Chip({ 
  children, 
  variant = 'indigo', // 'indigo' | 'teal' | 'coral' | 'neutral'
  icon = null,
  className = '',
  style = {},
  ...props 
}) {
  return (
    <span 
      className={`sa-chip sa-chip-${variant} ${className}`.trim()} 
      style={style}
      {...props}
    >
      {icon}
      <span>{children}</span>
    </span>
  );
}
