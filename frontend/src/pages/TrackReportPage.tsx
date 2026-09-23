import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  Calendar,
  Clock,
  RotateCcw,
  Search,
  ShieldCheck,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { StatusBadge, CategoryBadge } from '../components/common/Badge';
import { StatusTimeline } from '../components/common/StatusTimeline';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { trackReport } from '../services/api';
import { ReportPublicLookup } from '../types';

export const TrackReportPage: React.FC = () => {
  const { caseCode: urlCaseCode } = useParams<{ caseCode?: string }>();
  const navigate = useNavigate();

  const [inputCode, setInputCode] = useState(urlCaseCode || '');
  const [report, setReport] = useState<ReportPublicLookup | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [searchedCode, setSearchedCode] = useState<string | null>(null);

  const handleTrack = async (codeToSearch: string) => {
    const trimmed = codeToSearch.trim();
    if (!trimmed) {
      setErrorMessage('Please enter your case code.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setSearchedCode(trimmed);

    try {
      const data = await trackReport(trimmed);
      setReport(data);
      if (urlCaseCode !== trimmed) {
        navigate(`/track/${encodeURIComponent(trimmed)}`, { replace: true });
      }
    } catch (err: any) {
      setReport(null);
      setErrorMessage(err.message || 'Unable to track report. Please verify your case code.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (urlCaseCode) {
      setInputCode(urlCaseCode);
      handleTrack(urlCaseCode);
    }
  }, [urlCaseCode]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleTrack(inputCode);
  };

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'N/A';
    try {
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      }).format(new Date(isoString));
    } catch {
      return isoString;
    }
  };

  return (
    <div className="py-12 px-4 max-w-2xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">Track a report</h1>
        <p className="text-xs sm:text-sm text-zinc-400">
          Enter your 16-character case code to check triage progress and official moderator updates.
        </p>
      </div>

      {/* Case Code Search Box */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
              <Search className="w-3.5 h-3.5" />
            </div>
            <input
              id="caseCodeInput"
              type="text"
              value={inputCode}
              onChange={(e) => setInputCode(e.target.value)}
              placeholder="e.g. 7K9X-3MP8-Y4B2-RTC1"
              className="w-full rounded-md bg-zinc-900/50 border border-zinc-800 pl-9 pr-3 py-2 font-mono text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors uppercase"
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
          >
            Check status
          </Button>
        </div>
        <p className="text-[11px] text-zinc-500 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
          <span>Lookups verify HMAC digests without keeping a search log.</span>
        </p>
      </form>

      {/* Loading State */}
      {isLoading && <LoadingSpinner message="Checking case digest..." />}

      {/* Error Message */}
      {errorMessage && !isLoading && (
        <div className="p-3.5 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-0.5">
            <p className="font-medium text-rose-200">Unable to find report</p>
            <p className="text-rose-300/80 leading-relaxed">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Report Status Results */}
      {report && !isLoading && (
        <div className="rounded-lg bg-zinc-900/40 border border-zinc-800 p-5 space-y-6">
          {/* Status Header Overview */}
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-zinc-800">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-xs text-zinc-400">Case code:</span>
                <span className="font-mono text-xs font-semibold text-zinc-200 px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800">
                  {searchedCode}
                </span>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <CategoryBadge category={report.category} />
                <StatusBadge status={report.status} />
              </div>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleTrack(searchedCode || inputCode)}
              icon={<RotateCcw className="w-3.5 h-3.5" />}
            >
              Refresh
            </Button>
          </div>

          {/* Timestamp Metadata */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-md bg-zinc-950/60 border border-zinc-800/80 space-y-1">
              <span className="text-zinc-500 flex items-center gap-1.5 text-[11px]">
                <Calendar className="w-3.5 h-3.5 text-zinc-500" />
                Submitted
              </span>
              <p className="font-medium text-zinc-200">{formatDate(report.submitted_at || report.created_at)}</p>
            </div>

            <div className="p-3 rounded-md bg-zinc-950/60 border border-zinc-800/80 space-y-1">
              <span className="text-zinc-500 flex items-center gap-1.5 text-[11px]">
                <Clock className="w-3.5 h-3.5 text-zinc-500" />
                Latest update
              </span>
              <p className="font-medium text-zinc-200">{formatDate(report.updated_at)}</p>
            </div>
          </div>

          {/* Updates Timeline */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-mono uppercase tracking-wider text-zinc-400">
                Timeline & Updates
              </h2>
              <span className="text-[11px] text-zinc-500">
                {report.updates?.length || 0} event{report.updates?.length === 1 ? '' : 's'}
              </span>
            </div>

            {report.updates && report.updates.length > 0 ? (
              <StatusTimeline updates={report.updates} currentStatus={report.status} />
            ) : (
              <p className="text-xs text-zinc-500 italic py-2">No updates recorded yet.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
