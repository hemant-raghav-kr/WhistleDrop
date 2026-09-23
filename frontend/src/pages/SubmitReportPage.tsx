import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  ArrowRight,
  Check,
  CheckCircle2,
  Copy,
  FileText,
  Link as LinkIcon,
  ShieldAlert,
  Upload,
  X,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { submitReport } from '../services/api';
import { ReportCategory, ReportPublicCreated } from '../types';

const CATEGORIES: { label: string; value: ReportCategory; desc: string }[] = [
  { label: 'Security', value: 'SECURITY', desc: 'Vulnerabilities, data leaks, credential exposure' },
  { label: 'Harassment', value: 'HARASSMENT', desc: 'Bullying, discrimination, intimidation, abuse' },
  { label: 'Corruption', value: 'CORRUPTION', desc: 'Financial fraud, bribery, conflict of interest' },
  { label: 'Technical', value: 'TECHNICAL', desc: 'Outages, unapproved changes, data integrity' },
  { label: 'Other', value: 'OTHER', desc: 'Policy, safety, or ethical violations' },
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTS = ['.png', '.jpg', '.jpeg', '.webp', '.pdf', '.txt'];

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const SubmitReportPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form State
  const [category, setCategory] = useState<ReportCategory>('SECURITY');
  const [description, setDescription] = useState('');
  const [evidenceUrl, setEvidenceUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // UI State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [urlError, setUrlError] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [submittedData, setSubmittedData] = useState<ReportPublicCreated | null>(null);
  const [isCopied, setIsCopied] = useState(false);

  const validateUrl = (url: string): boolean => {
    if (!url.trim()) return true;
    try {
      const parsed = new URL(url.trim());
      return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setEvidenceUrl(val);
    if (val.trim() && !validateUrl(val)) {
      setUrlError('URL must begin with http:// or https://');
    } else {
      setUrlError(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFileError(null);
    const file = e.target.files?.[0];
    if (!file) {
      setSelectedFile(null);
      return;
    }

    const ext = '.' + (file.name.split('.').pop()?.toLowerCase() || '');
    if (!ALLOWED_EXTS.includes(ext)) {
      setFileError('Unsupported file type. Please choose PNG, JPG, WEBP, PDF, or TXT.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setFileError(`File size exceeds 10 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setSelectedFile(file);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setFileError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const trimmedDesc = description.trim();
    if (trimmedDesc.length < 10) {
      setFormError('Please enter at least 10 characters in the description.');
      return;
    }
    if (trimmedDesc.length > 10000) {
      setFormError('Description exceeds the maximum limit of 10,000 characters.');
      return;
    }

    if (evidenceUrl.trim() && !validateUrl(evidenceUrl)) {
      setFormError('Please provide a valid evidence URL starting with http:// or https://');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await submitReport({
        category,
        description: trimmedDesc,
        evidence_url: evidenceUrl.trim() || undefined,
        evidence_file: selectedFile || undefined,
      });
      setSubmittedData(result);
    } catch (err: any) {
      setFormError(err.message || 'Failed to submit report. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopyCode = async () => {
    if (!submittedData?.case_code) return;
    try {
      await navigator.clipboard.writeText(submittedData.case_code);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  // SUCCESS VIEW
  if (submittedData) {
    return (
      <div className="py-12 px-4 max-w-xl mx-auto space-y-6">
        <div className="p-6 rounded-lg bg-zinc-900/60 border border-zinc-800 space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-zinc-100">Report submitted successfully</h1>
              <p className="text-xs text-zinc-400">
                Your report has been encrypted and recorded.
              </p>
            </div>
          </div>

          {/* Case Code Banner */}
          <div className="p-4 rounded-md bg-zinc-950 border border-zinc-800 space-y-2.5">
            <div className="flex items-center justify-between text-xs text-zinc-400">
              <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">Your Case Code</span>
              <span className="text-[11px] text-zinc-400">Required to check status</span>
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              <div className="flex-1 py-2 px-3 rounded bg-zinc-900 border border-zinc-700/80 font-mono text-center sm:text-left text-base sm:text-lg font-semibold text-emerald-400 tracking-wider select-all">
                {submittedData.case_code}
              </div>
              <Button
                variant={isCopied ? 'primary' : 'secondary'}
                size="sm"
                onClick={handleCopyCode}
                icon={isCopied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              >
                {isCopied ? 'Copied' : 'Copy'}
              </Button>
            </div>
          </div>

          {/* Critical Warning */}
          <div className="p-3.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 space-y-1">
            <p className="font-medium text-amber-200">Save this code right now.</p>
            <p className="text-amber-300/80 leading-relaxed text-[11px]">
              WhistleDrop never saves your identity, and the server stores only a one-way HMAC hash of your code.
              If you lose this code, it cannot be reset or recovered.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex flex-col sm:flex-row gap-2.5">
            <Button
              variant="primary"
              onClick={() => navigate(`/track/${submittedData.case_code}`)}
              icon={<ArrowRight className="w-4 h-4" />}
              className="flex-1"
            >
              Track this report
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setSubmittedData(null);
                setDescription('');
                setEvidenceUrl('');
                setSelectedFile(null);
                setFileError(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
            >
              Submit another
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // SUBMISSION FORM VIEW
  return (
    <div className="py-12 px-4 max-w-xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">Submit a report</h1>
        <p className="text-xs sm:text-sm text-zinc-400">
          Describe what occurred with as much factual detail as possible. No identity, email, or account is required.
        </p>
      </div>

      {/* Main Submission Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Privacy Note Banner */}
        <div className="p-3 rounded-md bg-zinc-900/60 border border-zinc-800 text-xs text-zinc-400 flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <span className="font-medium text-zinc-200">Tip:</span> Avoid including personal names, phone numbers, or employee IDs in the text unless you intend to name them as part of the report.
          </p>
        </div>

        {/* Global Error Banner */}
        {formError && (
          <div className="p-3 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
            <span>{formError}</span>
          </div>
        )}

        {/* Category Selection */}
        <div className="space-y-2">
          <label className="block text-xs font-medium text-zinc-300">
            Category
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {CATEGORIES.map((cat) => {
              const isSelected = category === cat.value;
              return (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => setCategory(cat.value)}
                  className={`p-3 rounded-md text-left transition-colors border ${
                    isSelected
                      ? 'bg-zinc-900 border-zinc-700 text-zinc-100 ring-1 ring-zinc-700'
                      : 'bg-zinc-900/30 border-zinc-800 hover:border-zinc-700/80 text-zinc-400'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-medium">
                    <span className={isSelected ? 'text-zinc-100' : 'text-zinc-300'}>
                      {cat.label}
                    </span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-emerald-400" />}
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-1 line-clamp-1">
                    {cat.desc}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Description Textarea */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <label htmlFor="description" className="font-medium text-zinc-300">
              Incident description
            </label>
            <span
              className={`font-mono text-[11px] ${
                description.trim().length < 10
                  ? 'text-zinc-500'
                  : description.trim().length > 10000
                  ? 'text-rose-400'
                  : 'text-zinc-400'
              }`}
            >
              {description.trim().length} / 10,000
            </span>
          </div>
          <textarea
            id="description"
            rows={6}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="State the facts clearly: What happened? When? Which teams or systems were affected?"
            required
            className="w-full rounded-md bg-zinc-900/50 border border-zinc-800 p-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
          />
          {description.length > 0 && description.trim().length < 10 && (
            <p className="text-[11px] text-amber-400/90">
              Please enter at least 10 characters ({10 - description.trim().length} more needed).
            </p>
          )}
        </div>

        {/* Optional Evidence URL */}
        <div className="space-y-1.5">
          <label htmlFor="evidenceUrl" className="block text-xs font-medium text-zinc-300">
            Evidence or reference link <span className="text-zinc-500 font-normal">(optional)</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
              <LinkIcon className="w-3.5 h-3.5" />
            </div>
            <input
              id="evidenceUrl"
              type="url"
              value={evidenceUrl}
              onChange={handleUrlChange}
              placeholder="https://example.com/log-snapshot.pdf"
              className={`w-full rounded-md bg-zinc-900/50 border pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors ${
                urlError ? 'border-rose-500/50' : 'border-zinc-800'
              }`}
            />
          </div>
          {urlError && <p className="text-[11px] text-rose-400">{urlError}</p>}
          <p className="text-[11px] text-zinc-500">
            Ensure links do not reveal your personal Google Drive or Dropbox name.
          </p>
        </div>

        {/* Optional Evidence File Upload */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-medium text-zinc-300">
              Attach evidence file <span className="text-zinc-500 font-normal">(optional)</span>
            </label>
            <span className="text-[11px] text-zinc-500">Max 10 MB</span>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            accept=".png,.jpg,.jpeg,.webp,.pdf,.txt"
            className="hidden"
            id="evidence-file-input"
          />

          {!selectedFile ? (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-md bg-zinc-900/40 border border-dashed border-zinc-800 hover:border-zinc-700 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
            >
              <Upload className="w-3.5 h-3.5 text-zinc-500" />
              <span>Choose file to upload (PNG, JPG, WEBP, PDF, TXT)</span>
            </button>
          ) : (
            <div className="flex items-center justify-between p-3 rounded-md bg-zinc-900 border border-zinc-700/80 text-xs">
              <div className="flex items-center gap-2.5 min-w-0 pr-2">
                <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="text-zinc-200 font-medium truncate">{selectedFile.name}</span>
                <span className="text-zinc-500 shrink-0 font-mono text-[11px]">
                  ({formatBytes(selectedFile.size)})
                </span>
              </div>
              <button
                type="button"
                onClick={handleRemoveFile}
                className="p-1 rounded text-zinc-400 hover:text-rose-400 hover:bg-zinc-800 transition-colors shrink-0"
                title="Remove file"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {fileError && (
            <p className="text-[11px] text-rose-400 flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{fileError}</span>
            </p>
          )}

          <p className="text-[11px] text-zinc-500">
            Files are stored privately in encrypted object storage. Metadata such as local paths is stripped.
          </p>
        </div>

        {/* Submit Action */}
        <div className="pt-2">
          <Button
            type="submit"
            size="md"
            variant="primary"
            isLoading={isSubmitting}
            className="w-full"
          >
            {isSubmitting ? 'Submitting securely...' : 'Submit confidential report'}
          </Button>
        </div>
      </form>
    </div>
  );
};
