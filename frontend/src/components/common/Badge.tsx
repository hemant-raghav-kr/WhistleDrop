import React from 'react';
import { ReportStatus } from '../../types';

interface StatusBadgeProps {
  status: ReportStatus;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const sizeClasses = size === 'sm' ? 'text-[11px] px-2 py-0.5' : 'text-xs px-2.5 py-0.5';

  switch (status) {
    case 'SUBMITTED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-amber-950/20 text-amber-400 border border-amber-900/30 ${sizeClasses}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          <span>Submitted</span>
        </span>
      );
    case 'UNDER_REVIEW':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-blue-950/20 text-blue-400 border border-blue-900/30 ${sizeClasses}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          <span>Under Review</span>
        </span>
      );
    case 'RESOLVED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-emerald-950/20 text-emerald-400 border border-emerald-900/30 ${sizeClasses}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>Resolved</span>
        </span>
      );
    case 'DISMISSED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-zinc-900 text-zinc-400 border border-zinc-800 ${sizeClasses}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
          <span>Dismissed</span>
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-zinc-900 text-zinc-400 border border-zinc-800 ${sizeClasses}`}
        >
          <span>{status}</span>
        </span>
      );
  }
};

interface CategoryBadgeProps {
  category: string;
  size?: 'sm' | 'md';
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ category, size = 'md' }) => {
  const sizeClasses = size === 'sm' ? 'text-[11px] px-1.5 py-0.25' : 'text-xs px-2 py-0.5';

  return (
    <span
      className={`inline-flex items-center font-mono font-normal rounded bg-zinc-900 text-zinc-300 border border-zinc-800 tracking-tight ${sizeClasses}`}
    >
      {category.toUpperCase()}
    </span>
  );
};
