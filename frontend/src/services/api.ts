/**
 * WhistleDrop Centralized API Client Service
 *
 * Implements typed communication with the FastAPI backend,
 * automatic Bearer token injection for moderator sessions,
 * and unified error extraction.
 */

import {
  EvidenceDownloadResponse,
  LoginRequest,
  ReportCreate,
  ReportModeratorRead,
  ReportPublicCreated,
  ReportPublicLookup,
  ReportStatus,
  Token,
} from '../types';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');

// Storage key for moderator session
const TOKEN_KEY = 'whistledrop_moderator_token';

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch (err) {
    console.error('Failed to save auth token to localStorage', err);
  }
}

export function clearAuthToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch (err) {
    console.error('Failed to clear auth token from localStorage', err);
  }
}

/**
 * Standardized error handling extracting backend error descriptions.
 */
async function parseApiError(response: Response, defaultMessage: string): Promise<Error> {
  try {
    const data = await response.json();
    if (data.detail) {
      if (typeof data.detail === 'string') {
        return new Error(data.detail);
      }
      if (Array.isArray(data.detail)) {
        const messages = data.detail.map((d: { field?: string; message?: string; msg?: string }) => {
          const field = d.field ? `${d.field}: ` : '';
          return `${field}${d.message || d.msg || 'Invalid input'}`;
        });
        return new Error(messages.join(', '));
      }
    }
    return new Error(data.message || defaultMessage);
  } catch {
    return new Error(`Server returned status ${response.status}: ${defaultMessage}`);
  }
}

/**
 * Anonymous Report Submission (Public)
 * Supports JSON or multipart/form-data for optional evidence file upload.
 */
export async function submitReport(payload: ReportCreate): Promise<ReportPublicCreated> {
  let response: Response;

  if (payload.evidence_file) {
    const formData = new FormData();
    formData.append('category', payload.category);
    formData.append('description', payload.description);
    if (payload.evidence_url) {
      formData.append('evidence_url', payload.evidence_url);
    }
    formData.append('evidence_file', payload.evidence_file);

    response = await fetch(`${API_BASE}/reports`, {
      method: 'POST',
      body: formData,
    });
  } else {
    response = await fetch(`${API_BASE}/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        category: payload.category,
        description: payload.description,
        evidence_url: payload.evidence_url || undefined,
      }),
    });
  }

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to submit report. Please check your input.');
  }

  return response.json();
}

/**
 * Public Case Tracking by Case Code (Public)
 */
export async function trackReport(caseCode: string): Promise<ReportPublicLookup> {
  const trimmed = caseCode.trim();
  const response = await fetch(`${API_BASE}/reports/${encodeURIComponent(trimmed)}`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (response.status === 404) {
    throw new Error('That case code could not be found. Check the code and try again.');
  }

  if (!response.ok) {
    throw await parseApiError(response, 'Unable to track report.');
  }

  return response.json();
}

/**
 * Moderator Authentication Login (Public)
 */
export async function loginModerator(payload: LoginRequest): Promise<Token> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (response.status === 401) {
    throw new Error('Incorrect username/email or password.');
  }
  if (response.status === 403) {
    throw new Error('This moderator account has been deactivated. Please contact an administrator.');
  }

  if (!response.ok) {
    throw await parseApiError(response, 'Authentication failed.');
  }

  const tokenData: Token = await response.json();
  setAuthToken(tokenData.access_token);
  return tokenData;
}

/**
 * Get Moderator Reports Queue (Protected)
 */
export async function getModeratorReports(params?: {
  status?: string;
  category?: string;
  skip?: number;
  limit?: number;
}): Promise<ReportModeratorRead[]> {
  const token = getAuthToken();
  const searchParams = new URLSearchParams();

  if (params?.status && params.status !== 'ALL') {
    searchParams.append('status', params.status);
  }
  if (params?.category && params.category !== 'ALL') {
    searchParams.append('category', params.category);
  }
  if (params?.skip !== undefined) {
    searchParams.append('skip', String(params.skip));
  }
  if (params?.limit !== undefined) {
    searchParams.append('limit', String(params.limit));
  }

  const queryString = searchParams.toString() ? `?${searchParams.toString()}` : '';
  const response = await fetch(`${API_BASE}/moderator/reports${queryString}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  });

  if (response.status === 401 || response.status === 403) {
    clearAuthToken();
    throw new Error('Your session has expired or is unauthorized. Please log in again.');
  }

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to fetch reports.');
  }

  return response.json();
}

/**
 * Get Single Report Details (Protected)
 */
export async function getModeratorReport(reportId: string): Promise<ReportModeratorRead> {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE}/moderator/reports/${reportId}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  });

  if (response.status === 401 || response.status === 403) {
    clearAuthToken();
    throw new Error('Your session has expired or is unauthorized. Please log in again.');
  }
  if (response.status === 404) {
    throw new Error('Report not found with the specified ID.');
  }

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to fetch report details.');
  }

  return response.json();
}

/**
 * Transition Report Status (Protected)
 */
export async function updateReportStatus(
  reportId: string,
  newStatus: ReportStatus,
  message: string,
): Promise<ReportModeratorRead> {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE}/moderator/reports/${reportId}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      status: newStatus,
      message: message.trim(),
    }),
  });

  if (response.status === 401 || response.status === 403) {
    clearAuthToken();
    throw new Error('Your session has expired or is unauthorized. Please log in again.');
  }
  if (response.status === 400) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Invalid status transition attempted.');
  }

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to update report status.');
  }

  return response.json();
}

/**
 * Get Evidence File Download Details / Signed URL (Protected)
 */
export async function getEvidenceDownloadUrl(
  reportId: string,
  fileId: string,
): Promise<EvidenceDownloadResponse> {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE}/moderator/reports/${reportId}/evidence/${fileId}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  });

  if (response.status === 401 || response.status === 403) {
    clearAuthToken();
    throw new Error('Your session has expired or is unauthorized. Please log in again.');
  }
  if (response.status === 404) {
    throw new Error('Evidence file not found.');
  }

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to fetch evidence file download link.');
  }

  return response.json();
}

/**
 * Stream/Download Evidence File Blob directly (Protected)
 */
export async function downloadEvidenceFile(
  reportId: string,
  fileId: string,
  originalFilename: string,
): Promise<void> {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE}/moderator/reports/${reportId}/evidence/${fileId}/stream`, {
    method: 'GET',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  });

  if (response.status === 401 || response.status === 403) {
    clearAuthToken();
    throw new Error('Your session has expired or is unauthorized. Please log in again.');
  }
  if (!response.ok) {
    throw await parseApiError(response, 'Failed to download evidence file.');
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = originalFilename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

