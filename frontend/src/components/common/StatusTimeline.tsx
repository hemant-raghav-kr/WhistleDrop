import React from 'react';
import { PublicStatusUpdateRead, ReportStatus } from '../../types';
import { StatusBadge } from './Badge';

interface StatusTimelineProps {
  updates: PublicStatusUpdateRead[];
  currentStatus: ReportStatus;
}

export const StatusTimeline: React.FC<StatusTimelineProps> = ({ updates }) => {
  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      }).format(date);
    } catch {
      return isoString;
    }
  };

  return (
    <div className="relative pl-5 space-y-5 before:absolute before:left-1.5 before:top-2 before:bottom-2 before:w-px before:bg-zinc-800">
      {updates.map((update, index) => {
        let dotColor = 'bg-zinc-600 border-zinc-500';
        if (update.status === 'SUBMITTED') {
          dotColor = 'bg-amber-400 border-amber-300';
        } else if (update.status === 'UNDER_REVIEW') {
          dotColor = 'bg-blue-400 border-blue-300';
        } else if (update.status === 'RESOLVED') {
          dotColor = 'bg-emerald-400 border-emerald-300';
        }

        return (
          <div key={index} className="relative">
            {/* Minimal Timeline Node */}
            <div
              className={`absolute -left-5 top-1.5 w-3 h-3 rounded-full border ${dotColor} bg-zinc-950 flex items-center justify-center`}
            />

            {/* Entry Content */}
            <div className="space-y-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <StatusBadge status={update.status} size="sm" />
                <span className="text-[11px] font-mono text-zinc-400">
                  {formatDate(update.created_at)}
                </span>
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed pt-0.5">
                {update.message}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
