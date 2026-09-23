import React from 'react';

interface CardProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  headerRight?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  headerRight,
  children,
  className = '',
  padding = 'md',
}) => {
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-5 sm:p-6',
    lg: 'p-6 sm:p-8',
  };

  const hasHeader = title || subtitle || headerRight;

  return (
    <div
      className={`bg-zinc-900/40 border border-zinc-800/80 rounded-lg ${className}`}
    >
      {hasHeader && (
        <div className="px-5 py-3.5 border-b border-zinc-800/80 flex items-center justify-between gap-4">
          <div>
            {title && <h3 className="font-semibold text-zinc-100 text-sm">{title}</h3>}
            {subtitle && <p className="text-xs text-zinc-400 mt-0.5">{subtitle}</p>}
          </div>
          {headerRight && <div>{headerRight}</div>}
        </div>
      )}
      <div className={paddingStyles[padding]}>{children}</div>
    </div>
  );
};
