const BASE = ''
const MAX_RETRIES = 2
const RETRY_DELAY_MS = 1000

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let lastError: Error | null = null
  const isIdempotent = !options?.method || options.method === 'GET'

  for (let attempt = 0; attempt <= (isIdempotent ? MAX_RETRIES : 0); attempt++) {
    try {
      if (attempt > 0) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS * attempt))
      }
      const res = await fetch(`${BASE}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      if (res.status === 204) return undefined as T
      return res.json()
    } catch (e) {
      lastError = e instanceof Error ? e : new Error(String(e))
      if (!isIdempotent) throw lastError
    }
  }
  throw lastError!
}

// Types
export interface JobResponse {
  job_id: string
  video_id: string | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  topic: string
  pattern: string
  format: string
  color_preset: string | null
  render_engine: string | null
  created_at: string
  completed_at: string | null
  video_path: string | null
  thumbnail_path: string | null
  errors: string[]
  stages: StageInfo[]
  current_stage: string | null
}

export interface StageInfo {
  name: string
  duration_sec: number
  success: boolean
  error: string | null
}

export interface VideoInfo {
  video_id: string
  topic: string | null
  pattern: string | null
  format: string | null
  created_at: string | null
  video_path: string
  thumbnail_path: string | null
  duration_sec: number | null
  success: boolean
  stages: StageInfo[]
}

export interface PatternInfo {
  id: string
  name: string
  description: string
  difficulty: number
}

export interface FormatInfo {
  id: string
  duration_sec: number
  aspect_ratio: string
  resolution: number[]
  max_scenes: number
}

export interface ColorInfo {
  id: string
  name: string
  primary: string
  accent: string
  background: string
  mood: string
}

export interface EngineInfo {
  id: string
  name: string
  description: string
}

export interface CreateJobParams {
  topic: string
  pattern: string
  format: string
  color_preset?: string
  render_engine?: string
  upload?: boolean
  platforms?: string[]
}

export interface PlatformInfo {
  id: string
  label: string
  width: number
  height: number
  max_duration_sec: number | null
  description: string
}

export interface BatchJobItem {
  topic: string
  pattern?: string
  format?: string
  color_preset?: string
  render_engine?: string
  upload?: boolean
  csv_path?: string
  platforms?: string[]
}

export interface CreateBatchParams {
  defaults?: Partial<BatchJobItem>
  jobs: BatchJobItem[]
}

export interface BatchSummary {
  batch_id: string
  total: number
  done: number
  success: number
  failed: number
  created_at: string
  job_ids: string[]
}

// API functions
export const api = {
  health: () => request<{ status: string }>('/api/health'),

  // Jobs
  createJob: (params: CreateJobParams) =>
    request<JobResponse>('/api/jobs', { method: 'POST', body: JSON.stringify(params) }),
  listJobs: (status?: string) =>
    request<{ jobs: JobResponse[]; total: number }>(`/api/jobs${status ? `?status=${status}` : ''}`),
  getJob: (id: string) => request<JobResponse>(`/api/jobs/${id}`),
  deleteJob: (id: string) => request<void>(`/api/jobs/${id}`, { method: 'DELETE' }),

  // Batch
  createBatch: (params: CreateBatchParams) =>
    request<{ batch_id: string; total: number; job_ids: string[]; created_at: string }>(
      '/api/jobs/batch',
      { method: 'POST', body: JSON.stringify(params) },
    ),
  listBatches: () =>
    request<{ batches: BatchSummary[]; total: number }>('/api/jobs/batches'),

  // Presets
  getPatterns: () => request<PatternInfo[]>('/api/presets/patterns'),
  getFormats: () => request<FormatInfo[]>('/api/presets/formats'),
  getColors: () => request<ColorInfo[]>('/api/presets/colors'),
  getEngines: () => request<EngineInfo[]>('/api/presets/engines'),
  getPlatforms: () => request<PlatformInfo[]>('/api/presets/platforms'),

  // Settings
  getSettings: () => request<Record<string, unknown>>('/api/settings'),
  updateSettings: (params: Record<string, string>) =>
    request<Record<string, unknown>>('/api/settings', { method: 'PUT', body: JSON.stringify(params) }),

  // Videos
  listVideos: () => request<{ videos: VideoInfo[]; total: number }>('/api/videos'),
  getVideoStreamUrl: (id: string) => `/api/videos/${id}/stream`,
  getThumbnailUrl: (id: string) => `/api/videos/${id}/thumbnail`,
}
