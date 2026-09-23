import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
  className = '',
}) => {
  return (
    <div
      className={`p-6 rounded-lg border border-rose-500/20 bg-rose-500/10 text-center flex flex-col items-center justify-center ${className}`}
    >
      <div className="w-9 h-9 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mb-3">
        <AlertCircle className="w-4 h-4" />
      </div>
      <h4 className="text-sm font-medium text-rose-200 mb-1">{title}</h4>
      <p className="text-xs text-rose-300/80 max-w-md mb-4">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
};
