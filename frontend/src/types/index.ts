/**
 * WhistleDrop Frontend Type Definitions
 * Matches backend schemas and API contracts.
 */

export type ReportStatus = 'SUBMITTED' | 'UNDER_REVIEW' | 'RESOLVED' | 'DISMISSED';

export type UserRole = 'USER' | 'MODERATOR' | 'ADMIN';

export type ReportCategory =
  | 'SECURITY'
  | 'HARASSMENT'
  | 'CORRUPTION'
  | 'TECHNICAL'
  | 'OTHER';

export interface PublicStatusUpdateRead {
  status: ReportStatus;
  message: string;
  created_at: string;
}

export interface StatusUpdateRead {
  id: string;
  status: ReportStatus;
  update_message: string;
  message?: string;
  created_at: string;
}

export interface EvidenceFileRead {
  id: string;
  report_id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  created_at: string;
}

export interface EvidenceDownloadResponse {
  file_id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  download_url: string;
  expires_in: number;
}

export interface ReportCreate {
  category: ReportCategory | string;
  description: string;
  evidence_url?: string;
  evidence_file?: File | null;
}

export interface ReportPublicCreated {
  case_code: string;
  category: string;
  status: ReportStatus;
  created_at: string;
  has_evidence?: boolean;
}

export interface ReportPublicLookup {
  category: string;
  status: ReportStatus;
  submitted_at: string;
  created_at: string;
  updated_at: string;
  has_evidence?: boolean;
  is_closed?: boolean;
  closed_at?: string;
  updates: PublicStatusUpdateRead[];
  status_updates?: StatusUpdateRead[];
}

export interface ReportModeratorRead {
  id: string;
  category: string;
  description: string;
  evidence_url?: string;
  status: ReportStatus;
  is_closed?: boolean;
  closed_at?: string;
  created_at: string;
  updated_at: string;
  status_updates: StatusUpdateRead[];
  updates?: PublicStatusUpdateRead[];
  evidence_files?: EvidenceFileRead[];
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface UserRead {
  id: string;
  name?: string;
  email: string;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface UserAdminRead {
  id: string;
  name?: string;
  email: string;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username_or_email: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  role?: string;
  name?: string;
  email?: string;
}
