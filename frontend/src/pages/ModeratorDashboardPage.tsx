import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Filter,
  RotateCcw,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { StatusBadge, CategoryBadge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';
import { getModeratorReports } from '../services/api';
import { ReportModeratorRead } from '../types';

export const ModeratorDashboardPage: React.FC = () => {
  const navigate = useNavigate();

  // Reports & Metrics State
  const [reports, setReports] = useState<ReportModeratorRead[]>([]);
  const [allReports, setAllReports] = useState<ReportModeratorRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Filter State
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const fetchReports = async (status = statusFilter, category = categoryFilter) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await getModeratorReports({
        status: status !== 'ALL' ? status : undefined,
        category: category !== 'ALL' ? category : undefined,
      });
      setReports(data);

      if (status === 'ALL' && category === 'ALL') {
        setAllReports(data);
      } else {
        const full = await getModeratorReports();
        setAllReports(full);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to fetch reports.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports(statusFilter, categoryFilter);
  }, [statusFilter, categoryFilter]);

  // Compute metrics
  const totalCount = allReports.length;
  const submittedCount = allReports.filter((r) => r.status === 'SUBMITTED').length;
  const underReviewCount = allReports.filter((r) => r.status === 'UNDER_REVIEW').length;
  const resolvedCount = allReports.filter((r) => r.status === 'RESOLVED').length;
  const dismissedCount = allReports.filter((r) => r.status === 'DISMISSED').length;

  const formatDate = (isoString?: string) => {
    if (!isoString) return '—';
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
    <div className="py-8 px-4 max-w-6xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-zinc-100">Moderator dashboard</h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Triage submitted reports, inspect evidence, and update investigation progress.
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => fetchReports(statusFilter, categoryFilter)}
          icon={<RotateCcw className="w-3.5 h-3.5" />}
        >
          Refresh
        </Button>
      </div>

      {/* Compact Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
        <div className="p-3.5 rounded-lg bg-zinc-900/40 border border-zinc-800">
          <span className="text-[11px] text-zinc-500 font-medium">All Reports</span>
          <p className="text-xl font-semibold text-zinc-100 mt-0.5">{totalCount}</p>
        </div>

        <div className="p-3.5 rounded-lg bg-zinc-900/40 border border-zinc-800">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            <span className="text-[11px] text-zinc-400 font-medium">Submitted</span>
          </div>
          <p className="text-xl font-semibold text-zinc-100 mt-0.5">{submittedCount}</p>
        </div>

        <div className="p-3.5 rounded-lg bg-zinc-900/40 border border-zinc-800">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            <span className="text-[11px] text-zinc-400 font-medium">Under Review</span>
          </div>
          <p className="text-xl font-semibold text-zinc-100 mt-0.5">{underReviewCount}</p>
        </div>

        <div className="p-3.5 rounded-lg bg-zinc-900/40 border border-zinc-800">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-[11px] text-zinc-400 font-medium">Resolved</span>
          </div>
          <p className="text-xl font-semibold text-zinc-100 mt-0.5">{resolvedCount}</p>
        </div>

        <div className="p-3.5 rounded-lg bg-zinc-900/40 border border-zinc-800 col-span-2 sm:col-span-1">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-zinc-500" />
            <span className="text-[11px] text-zinc-400 font-medium">Dismissed</span>
          </div>
          <p className="text-xl font-semibold text-zinc-100 mt-0.5">{dismissedCount}</p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-3 rounded-lg bg-zinc-900/30 border border-zinc-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 text-zinc-400 text-xs">
            <Filter className="w-3.5 h-3.5 text-zinc-500" />
            <span>Filter:</span>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-md bg-zinc-900 border border-zinc-800 px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
            >
              <option value="ALL">All Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="RESOLVED">Resolved</option>
              <option value="DISMISSED">Dismissed</option>
            </select>

            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="rounded-md bg-zinc-900 border border-zinc-800 px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
            >
              <option value="ALL">All Categories</option>
              <option value="SECURITY">Security</option>
              <option value="HARASSMENT">Harassment</option>
              <option value="CORRUPTION">Corruption</option>
              <option value="TECHNICAL">Technical</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {(statusFilter !== 'ALL' || categoryFilter !== 'ALL') && (
            <button
              onClick={() => {
                setStatusFilter('ALL');
                setCategoryFilter('ALL');
              }}
              className="text-zinc-400 hover:text-zinc-200 underline text-xs"
            >
              Reset filters
            </button>
          )}
          <span className="text-zinc-500 text-xs font-mono">
            {reports.length} report{reports.length === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      {/* Main Reports List */}
      <div>
        {isLoading ? (
          <LoadingSpinner message="Loading reports..." />
        ) : errorMessage ? (
          <ErrorState
            title="Failed to load reports"
            message={errorMessage}
            onRetry={() => fetchReports(statusFilter, categoryFilter)}
          />
        ) : reports.length === 0 ? (
          <EmptyState
            title="No reports match your filters"
            description="Try selecting a different status or category above."
            action={
              (statusFilter !== 'ALL' || categoryFilter !== 'ALL') ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setStatusFilter('ALL');
                    setCategoryFilter('ALL');
                  }}
                >
                  Clear filters
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div className="space-y-3">
            {/* Desktop Table */}
            <div className="hidden md:block overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
              <table className="w-full text-left text-xs">
                <thead className="bg-zinc-950/70 border-b border-zinc-800 text-zinc-500 font-mono text-[11px] uppercase">
                  <tr>
                    <th className="py-2.5 px-4 font-medium">Category</th>
                    <th className="py-2.5 px-4 font-medium">Status</th>
                    <th className="py-2.5 px-4 font-medium">Description Preview</th>
                    <th className="py-2.5 px-4 font-medium">Submitted</th>
                    <th className="py-2.5 px-4 font-medium">Updated</th>
                    <th className="py-2.5 px-4 text-right font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/80">
                  {reports.map((report) => (
                    <tr
                      key={report.id}
                      onClick={() => navigate(`/moderator/reports/${report.id}`)}
                      className="hover:bg-zinc-900/60 transition-colors cursor-pointer group"
                    >
                      <td className="py-3 px-4 whitespace-nowrap">
                        <CategoryBadge category={report.category} size="sm" />
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <StatusBadge status={report.status} size="sm" />
                      </td>
                      <td className="py-3 px-4 max-w-xs truncate text-zinc-300">
                        {report.description}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap text-zinc-500 font-mono text-[11px]">
                        {formatDate(report.created_at)}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap text-zinc-500 font-mono text-[11px]">
                        {formatDate(report.updated_at)}
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <span className="inline-flex items-center gap-1 text-zinc-400 group-hover:text-zinc-100 font-medium text-xs">
                          <span>Inspect</span>
                          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Cards */}
            <div className="grid grid-cols-1 gap-2.5 md:hidden">
              {reports.map((report) => (
                <div
                  key={report.id}
                  onClick={() => navigate(`/moderator/reports/${report.id}`)}
                  className="p-3.5 rounded-lg border border-zinc-800 bg-zinc-900/40 space-y-2.5 cursor-pointer hover:border-zinc-700 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <CategoryBadge category={report.category} size="sm" />
                    <StatusBadge status={report.status} size="sm" />
                  </div>

                  <p className="text-xs text-zinc-300 line-clamp-2">
                    {report.description}
                  </p>

                  <div className="flex items-center justify-between pt-2 border-t border-zinc-800/80 text-[11px] text-zinc-500">
                    <span className="font-mono">{formatDate(report.created_at)}</span>
                    <span className="text-zinc-300 font-medium flex items-center gap-1">
                      <span>Inspect</span>
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
