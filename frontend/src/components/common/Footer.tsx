import React from 'react';
import { ExternalLink, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-zinc-800/80 bg-zinc-950 py-6 mt-auto">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-zinc-500">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
          <span>Anonymous reporting — no accounts, cookies, or identifier logs collected.</span>
        </div>
        <div className="flex items-center gap-3">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-zinc-300 transition-colors inline-flex items-center gap-1"
          >
            <span>API Docs</span>
            <ExternalLink className="w-3 h-3" />
          </a>
          <span>•</span>
          <span className="text-zinc-600">GDG on Campus SRM Recruitment</span>
        </div>
      </div>
    </footer>
  );
};
