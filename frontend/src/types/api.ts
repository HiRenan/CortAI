/**
 * API types matching backend Pydantic schemas
 */

// Auth types
export interface User {
  id: number
  email: string
  name: string
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  username: string // email
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

// Video types
export type VideoStatus = 'processing' | 'completed' | 'failed'

export interface Video {
  id: number
  user_id: number
  url: string
  title: string | null
  status: VideoStatus
  task_id: string | null
  output_path: string | null
  created_at: string
}

export interface VideoCreateRequest {
  url: string
}

export interface VideoListResponse {
  videos: Video[]
  total: number
}

export interface TaskStatusResponse {
  task_id: string
  status: string
  video_id: number | null
  result: Record<string, unknown> | null
}

// API Error type
export interface ApiError {
  detail: string
}
