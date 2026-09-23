import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-7 h-7',
  };

  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-zinc-400 gap-2.5 ${className}`}
    >
      <Loader2 className={`${sizeClasses[size]} animate-spin text-emerald-500`} />
      {message && <p className="text-xs text-zinc-500">{message}</p>}
    </div>
  );
};
