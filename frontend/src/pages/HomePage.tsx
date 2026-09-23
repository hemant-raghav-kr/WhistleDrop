import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, EyeOff, KeyRound, Lock, Search, ShieldCheck } from 'lucide-react';
import { Button } from '../components/common/Button';

export const HomePage: React.FC = () => {
  return (
    <div className="py-12 sm:py-16 px-4 max-w-5xl mx-auto space-y-20">
      {/* Hero Section */}
      <div className="text-center space-y-6 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-400 text-xs font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          <span>Confidential reporting system</span>
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-6xl font-semibold tracking-tight text-zinc-100 leading-tight">
          Speak without being seen.
        </h1>

        <p className="text-zinc-400 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed font-normal">
          WhistleDrop gives reporters a safe channel to surface sensitive issues without creating an
          account, entering personal information, or risking retaliation.
        </p>

        {/* Action CTAs */}
        <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
          <Link to="/report" className="inline-flex">
            <Button
              size="lg"
              variant="primary"
              icon={<EyeOff className="w-4 h-4 shrink-0" />}
            >
              Submit a report
            </Button>
          </Link>
          <Link to="/track" className="inline-flex">
            <Button
              size="lg"
              variant="secondary"
              icon={<Search className="w-4 h-4 shrink-0" />}
            >
              Track with case code
            </Button>
          </Link>
        </div>
      </div>

      {/* How It Works Flow */}
      <div className="border-t border-zinc-800/80 pt-12 space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2">
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-emerald-500">Workflow</span>
            <h2 className="text-xl sm:text-2xl font-semibold text-zinc-100 tracking-tight mt-1">
              How reports move through WhistleDrop
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-zinc-400 max-w-sm">
            Designed to guarantee anonymity at submission while preserving accountability.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-5 rounded-lg bg-zinc-900/40 border border-zinc-800/80 space-y-3">
            <span className="text-xs font-mono font-medium text-zinc-400">01</span>
            <h3 className="text-sm font-semibold text-zinc-100">Submit without identity</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Select a category, describe the incident, and optionally attach an evidence link. No names, emails, or phone numbers are ever requested.
            </p>
          </div>

          <div className="p-5 rounded-lg bg-zinc-900/40 border border-zinc-800/80 space-y-3">
            <span className="text-xs font-mono font-medium text-zinc-400">02</span>
            <h3 className="text-sm font-semibold text-zinc-100">Receive a one-time code</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              The system generates a random 16-character case code. Only an HMAC-SHA256 digest is stored in the database. Save your code securely.
            </p>
          </div>

          <div className="p-5 rounded-lg bg-zinc-900/40 border border-zinc-800/80 space-y-3">
            <span className="text-xs font-mono font-medium text-zinc-400">03</span>
            <h3 className="text-sm font-semibold text-zinc-100">Track resolution status</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Use your code to check when your case is reviewed, escalated, or resolved, and read official moderator audit notes.
            </p>
          </div>
        </div>
      </div>

      {/* Privacy Safeguards */}
      <div className="border-t border-zinc-800/80 pt-12 space-y-8">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-emerald-500">Security</span>
          <h2 className="text-xl sm:text-2xl font-semibold text-zinc-100 tracking-tight mt-1">
            Built for confidentiality from day one
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <div className="w-8 h-8 rounded-md bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300 mb-3">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <h3 className="text-sm font-semibold text-zinc-200">Zero reporter accounts</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              There is no user table for reporters. We don't store session cookies, client fingerprints, or IP headers alongside submissions.
            </p>
          </div>

          <div className="space-y-2">
            <div className="w-8 h-8 rounded-md bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300 mb-3">
              <KeyRound className="w-4 h-4 text-teal-400" />
            </div>
            <h3 className="text-sm font-semibold text-zinc-200">One-way case verification</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Case codes are hashed with HMAC-SHA256 upon submission. Even if the database were compromised, active tracking codes cannot be reversed.
            </p>
          </div>

          <div className="space-y-2">
            <div className="w-8 h-8 rounded-md bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300 mb-3">
              <Lock className="w-4 h-4 text-zinc-300" />
            </div>
            <h3 className="text-sm font-semibold text-zinc-200">Role-separated moderation</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Moderators log in through separate credentialed sessions with JWT authentication to review, triage, and record resolution notes.
            </p>
          </div>
        </div>
      </div>

      {/* Direct CTA box */}
      <div className="p-6 rounded-lg bg-zinc-900/60 border border-zinc-800/90 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-medium text-zinc-200">Need to file an urgent incident?</h4>
          <p className="text-xs text-zinc-400 mt-0.5">
            Takes under 2 minutes. No registration or personal data required.
          </p>
        </div>
        <Link to="/report">
          <Button size="sm" variant="primary" icon={<ArrowRight className="w-3.5 h-3.5" />}>
            File a report
          </Button>
        </Link>
      </div>
    </div>
  );
};
