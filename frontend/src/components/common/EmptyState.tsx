import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No items found',
  description = 'There are no records matching your current filter criteria.',
  icon,
  action,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-lg border border-dashed border-zinc-800 bg-zinc-900/20 ${className}`}
    >
      <div className="w-10 h-10 rounded-md bg-zinc-900 border border-zinc-800 text-zinc-500 flex items-center justify-center mb-3">
        {icon || <Inbox className="w-5 h-5" />}
      </div>
      <h4 className="text-sm font-medium text-zinc-200 mb-1">{title}</h4>
      <p className="text-xs text-zinc-500 max-w-sm mb-3">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
