/** Typed API client — always sends cookies with requests. */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    if (Array.isArray(detail)) {
      throw new Error(detail.map(d => `${d.loc?.join('.') || 'Field'}: ${d.msg}`).join(', '));
    }
    throw new Error(detail ?? `HTTP ${res.status}`);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export interface CurrentUser {
  id: number;
  email: string;
  name: string;
  avatar: string;
  has_gmail_connected: boolean;
  onboarding_done: boolean;
  scrape_status: 'pending' | 'running' | 'done' | 'failed';
}

export const getMe = () => apiFetch<CurrentUser>('/auth/me');
export const logout = () => apiFetch('/auth/logout', { method: 'POST' });

// ── Profile ───────────────────────────────────────────────────────────────────

export interface ProfileData {
  user_id?: number;
  full_name?: string;
  domain?: string;
  education_level?: string;
  grad_date?: string;
  looking_for?: string[];
  any_field_categories?: string[];
  availability?: string[];
  preferred_max_hours?: number;
  country?: string;
  city?: string;
  campus_address?: string;
  lat?: number;
  lng?: number;
  commute_radius_km?: number;
  visa_type?: string;
  hour_cap_term?: number;
  hour_cap_break?: number;
  work_rights_confirmed?: boolean;
  needs_sponsorship?: string;
  languages?: string[];
  local_language_level?: string;
  comfort_customer_facing?: boolean;
  resume_path?: string;
  onboarding_done?: boolean;
}

export const getProfile = () => apiFetch<ProfileData>('/profile');
export const saveStep = (step: number, data: object) =>
  apiFetch<ProfileData>(`/profile/step/${step}`, { method: 'PUT', body: JSON.stringify(data) });
export const completeOnboarding = () =>
  apiFetch('/profile/complete', { method: 'POST' });

export const uploadResume = (file: File) => {
  const form = new FormData();
  form.append('file', file);
  return fetch(`${BASE}/profile/resume`, {
    method: 'POST',
    credentials: 'include',
    body: form,
  });
};

// ── Scrape ────────────────────────────────────────────────────────────────────

export interface ScrapeStatus {
  status: 'pending' | 'running' | 'done' | 'failed';
  job_count: number;
  message?: string;
}

export const getScrapeStatus = () => apiFetch<ScrapeStatus>('/scrape/status');
export const startScrape = () => apiFetch('/scrape/start', { method: 'POST' });

// ── Jobs ─────────────────────────────────────────────────────────────────────

export interface JobAnalysis {
  trust_score: number | null;
  red_flags: string[];
  pay_label: string | null;
  hours_per_week: number | null;
  shift_info: string | null;
  work_rights_required: boolean | null;
  sponsorship: string | null;
  language_requirement: string | null;
}

export interface JobItem {
  id: number;
  title: string;
  employer: string;
  location: string;
  job_type: string;
  category?: string;
  pay_text: string | null;
  pay_min: number | null;
  pay_max: number | null;
  source: string;
  source_url: string;
  lat?: number;
  lng?: number;
  distance_km?: number;
  description: string;
  contact_email?: string | null;
  posted_at: string | null;
  scraped_at: string | null;
  analysis?: JobAnalysis | null;
}

export interface JobsResponse {
  total: number;
  items: JobItem[];
}

export const getJobs = (params?: { limit?: number; offset?: number; job_type?: string }) => {
  const qs = new URLSearchParams();
  if (params?.limit) qs.set('limit', String(params.limit));
  if (params?.offset) qs.set('offset', String(params.offset));
  if (params?.job_type) qs.set('job_type', params.job_type);
  return apiFetch<JobsResponse>(`/jobs?${qs}`);
};

export const autoApplyJob = (jobId: number) =>
  apiFetch<{ status: string; message: string }>(`/jobs/${jobId}/auto-apply`, { method: 'POST' });

// ── Country config ────────────────────────────────────────────────────────────

export interface VisaType { code: string; label: string; }
export interface CountryConfig {
  name: string;
  currency: string;
  visa_types: VisaType[];
  default_hour_caps: Record<string, [number | null, number | null]>;
}

export const getCountryConfig = (code: string) =>
  apiFetch<CountryConfig>(`/config/${code}`);

// ── Telegram ──────────────────────────────────────────────────────────────────

export const getTelegramLinkToken = () =>
  apiFetch<{ token: string; bot_username: string }>('/telegram/link-token', { method: 'POST' });

// ── Cold Email ───────────────────────────────────────────────────────────────

export interface EmailSettings {
  daily_limit: number;
  send_hour: number;
  send_minute: number;
  auto_send: boolean;
  default_subject: string;
  default_body: string;
}

export interface EmailQueueItem {
  id: number;
  job_id: number;
  subject: string;
  body: string;
  status: string;
  scheduled_at: string | null;
  sent_at: string | null;
  job_title: string | null;
  employer: string | null;
  contact_email: string | null;
}

export interface EmailContact {
  id: number;
  title: string;
  employer: string;
  location: string;
  contact_email: string;
  source: string;
  source_url: string;
}

export interface EmailStats {
  total_queued: number;
  total_sent: number;
  total_pending: number;
  total_contacts: number;
}

export const getEmailSettings = () => apiFetch<EmailSettings>('/email/settings');
export const updateEmailSettings = (settings: EmailSettings) =>
  apiFetch('/email/settings', { method: 'PUT', body: JSON.stringify(settings) });

export const getEmailQueue = (status?: string) => {
  const qs = new URLSearchParams();
  if (status) qs.set('status', status);
  return apiFetch<{ total: number; items: EmailQueueItem[] }>(`/email/queue?${qs}`);
};

export const queueEmails = (items: { job_id: number; to_email: string; subject: string; body: string }[]) =>
  apiFetch<{ queued: number }>('/email/queue', { method: 'POST', body: JSON.stringify({ items }) });

export const getEmailContacts = () =>
  apiFetch<{ total: number; items: EmailContact[] }>('/email/contacts');

export const getEmailStats = () => apiFetch<EmailStats>('/email/stats');
