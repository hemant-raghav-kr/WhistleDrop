import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  ExternalLink,
  FileText,
  History,
  Lock,
  MessageSquare,
  XCircle,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { StatusBadge, CategoryBadge } from '../components/common/Badge';
import { StatusTimeline } from '../components/common/StatusTimeline';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';
import { downloadEvidenceFile, getModeratorReport, updateReportStatus } from '../services/api';
import { ReportModeratorRead, ReportStatus } from '../types';

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const ModeratorReportDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<ReportModeratorRead | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [downloadingFileId, setDownloadingFileId] = useState<string | null>(null);

  // Transition Modal State
  const [targetStatus, setTargetStatus] = useState<ReportStatus | null>(null);
  const [transitionMessage, setTransitionMessage] = useState('');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const handleDownloadEvidence = async (fileId: string, filename: string) => {
    if (!id) return;
    try {
      setDownloadingFileId(fileId);
      await downloadEvidenceFile(id, fileId, filename);
    } catch (err: any) {
      alert(err.message || 'Failed to download evidence file.');
    } finally {
      setDownloadingFileId(null);
    }
  };

  const fetchReport = async () => {
    if (!id) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await getModeratorReport(id);
      setReport(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Unable to load report details.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [id]);

  const openTransitionModal = (status: ReportStatus) => {
    setTargetStatus(status);
    setTransitionError(null);
    if (status === 'UNDER_REVIEW') {
      setTransitionMessage('The report has been assigned for formal investigation.');
    } else if (status === 'RESOLVED') {
      setTransitionMessage('Investigation concluded and appropriate corrective actions taken.');
    } else if (status === 'DISMISSED') {
      setTransitionMessage('Report reviewed and dismissed due to insufficient actionable evidence.');
    } else {
      setTransitionMessage('');
    }
  };

  const handleExecuteTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !targetStatus) return;

    const trimmedMsg = transitionMessage.trim();
    if (!trimmedMsg) {
      setTransitionError('Please enter an explanatory update message.');
      return;
    }

    setIsTransitioning(true);
    setTransitionError(null);

    try {
      const updated = await updateReportStatus(id, targetStatus, trimmedMsg);
      setReport(updated);
      setTargetStatus(null);
      setSuccessToast(`Report status updated to ${targetStatus}.`);
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: any) {
      setTransitionError(err.message || 'Failed to update report status.');
    } finally {
      setIsTransitioning(false);
    }
  };

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

  if (isLoading) {
    return (
      <div className="py-12 max-w-4xl mx-auto px-4">
        <LoadingSpinner message="Loading report details..." />
      </div>
    );
  }

  if (errorMessage || !report) {
    return (
      <div className="py-12 max-w-2xl mx-auto px-4 space-y-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/moderator/dashboard')}
          icon={<ArrowLeft className="w-4 h-4" />}
        >
          Back to Dashboard
        </Button>
        <ErrorState
          title="Report Not Found"
          message={errorMessage || 'The requested report could not be found.'}
          onRetry={fetchReport}
        />
      </div>
    );
  }

  // Derive update history for timeline
  const timelineUpdates =
    report.updates ||
    report.status_updates?.map((u) => ({
      status: u.status,
      message: u.update_message || u.message || '',
      created_at: u.created_at,
    })) ||
    [];

  return (
    <div className="py-8 px-4 max-w-4xl mx-auto space-y-6">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <Link
          to="/moderator/dashboard"
          className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to queue</span>
        </Link>
        <span className="font-mono text-[11px] text-zinc-500">
          ID: {report.id}
        </span>
      </div>

      {/* Success Notification Toast */}
      {successToast && (
        <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{successToast}</span>
          </div>
          <button onClick={() => setSuccessToast(null)} className="text-emerald-400 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Report Details */}
      <div className="p-6 rounded-lg bg-zinc-900/40 border border-zinc-800 space-y-6">
        {/* Header Row */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-zinc-800">
          <div className="flex items-center gap-2.5">
            <CategoryBadge category={report.category} />
            <StatusBadge status={report.status} />
          </div>

          <div className="text-xs text-zinc-500 flex items-center gap-3">
            <span className="flex items-center gap-1 font-mono text-[11px]">
              <Calendar className="w-3.5 h-3.5" />
              {formatDate(report.created_at)}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1 font-mono text-[11px]">
              <Clock className="w-3.5 h-3.5" />
              Updated {formatDate(report.updated_at)}
            </span>
          </div>
        </div>

        {/* Narrative Content */}
        <div className="space-y-2">
          <h2 className="text-xs font-mono uppercase tracking-wider text-zinc-400">
            Incident Description
          </h2>
          <div className="p-4 rounded-md bg-zinc-950/60 border border-zinc-800/80 text-sm text-zinc-200 whitespace-pre-wrap leading-relaxed font-sans">
            {report.description}
          </div>
        </div>

        {/* Evidence URL if present */}
        {report.evidence_url && (
          <div className="space-y-1.5">
            <h2 className="text-xs font-mono uppercase tracking-wider text-zinc-400">
              Attached Evidence Link
            </h2>
            <a
              href={report.evidence_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-xs text-zinc-300 hover:text-white bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 px-3 py-2 rounded-md transition-colors break-all"
            >
              <ExternalLink className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
              <span>{report.evidence_url}</span>
            </a>
          </div>
        )}

        {/* Attached Evidence Files if present */}
        {report.evidence_files && report.evidence_files.length > 0 && (
          <div className="space-y-2">
            <h2 className="text-xs font-mono uppercase tracking-wider text-zinc-400">
              Attached Evidence Files ({report.evidence_files.length})
            </h2>
            <div className="space-y-2">
              {report.evidence_files.map((file) => (
                <div
                  key={file.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-md bg-zinc-950/60 border border-zinc-800/80 text-xs"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                    <div className="min-w-0">
                      <p className="font-medium text-zinc-200 truncate">{file.original_filename}</p>
                      <p className="text-[11px] text-zinc-500 font-mono">
                        {file.mime_type} • {formatBytes(file.file_size)} • Uploaded {formatDate(file.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleDownloadEvidence(file.id, file.original_filename)}
                      isLoading={downloadingFileId === file.id}
                      icon={<Download className="w-3.5 h-3.5" />}
                    >
                      Download
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STRICT LIFECYCLE ACTION CONTROLS */}
        <div className="pt-4 border-t border-zinc-800 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400">
              Lifecycle Actions
            </h3>
            <span className="text-[11px] text-zinc-500 font-mono">
              State Machine
            </span>
          </div>

          {/* Action Buttons strictly reflecting state machine */}
          {report.status === 'SUBMITTED' && (
            <div className="flex flex-wrap gap-2.5">
              <Button
                variant="primary"
                size="sm"
                onClick={() => openTransitionModal('UNDER_REVIEW')}
                icon={<Clock className="w-3.5 h-3.5" />}
              >
                Mark Under Review
              </Button>
            </div>
          )}

          {report.status === 'UNDER_REVIEW' && (
            <div className="flex flex-wrap gap-2.5">
              <Button
                variant="primary"
                size="sm"
                onClick={() => openTransitionModal('RESOLVED')}
                icon={<CheckCircle2 className="w-3.5 h-3.5" />}
              >
                Resolve Report
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => openTransitionModal('DISMISSED')}
                icon={<XCircle className="w-3.5 h-3.5" />}
              >
                Dismiss Report
              </Button>
            </div>
          )}

          {(report.status === 'RESOLVED' || report.status === 'DISMISSED') && (
            <div className="p-3 rounded-md bg-zinc-950/80 border border-zinc-800 flex items-center gap-2 text-xs text-zinc-400">
              <Lock className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
              <span>
                This report has reached a terminal status (<strong>{report.status}</strong>) and cannot be updated further.
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Audit History Timeline */}
      <div className="p-6 rounded-lg bg-zinc-900/40 border border-zinc-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-2">
            <History className="w-3.5 h-3.5 text-zinc-500" />
            <span>Audit History</span>
          </h2>
          <span className="text-xs text-zinc-500 font-mono">
            {timelineUpdates.length} update{timelineUpdates.length === 1 ? '' : 's'}
          </span>
        </div>

        <StatusTimeline updates={timelineUpdates} currentStatus={report.status} />
      </div>

      {/* Confirmation Modal for State Transition */}
      <Modal
        isOpen={!!targetStatus}
        onClose={() => setTargetStatus(null)}
        title={`Update status to ${targetStatus}`}
        description="Provide a note for the audit history. This message is visible to the reporter when they track the case."
      >
        <form onSubmit={handleExecuteTransition} className="space-y-4">
          {transitionError && (
            <div className="p-3 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
              <p>{transitionError}</p>
            </div>
          )}

          <div className="space-y-1.5">
            <label
              htmlFor="transitionMsg"
              className="block text-xs font-medium text-zinc-300"
            >
              Public explanation note <span className="text-rose-400">*</span>
            </label>
            <textarea
              id="transitionMsg"
              rows={3}
              value={transitionMessage}
              onChange={(e) => setTransitionMessage(e.target.value)}
              placeholder="Explain the reason for this status change..."
              required
              className="w-full rounded-md bg-zinc-950 border border-zinc-800 p-2.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setTargetStatus(null)}
              disabled={isTransitioning}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant={targetStatus === 'DISMISSED' ? 'danger' : 'primary'}
              size="sm"
              isLoading={isTransitioning}
              icon={<MessageSquare className="w-3.5 h-3.5" />}
            >
              Confirm
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
