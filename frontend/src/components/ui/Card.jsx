import React from 'react';

export function Card({ 
  children, 
  variant = 'default', // 'default' | 'dark' | 'interactive'
  className = '', 
  style = {},
  onClick,
  ...props 
}) {
  let cardClass = 'sa-card';
  if (variant === 'dark') cardClass = 'sa-card-dark';
  if (variant === 'interactive') cardClass = 'sa-card sa-card-interactive';

  return (
    <div 
      className={`${cardClass} ${className}`.trim()} 
      style={style}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  );
}
