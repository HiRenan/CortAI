/**
 * Video processing service
 */
import api from '../lib/axios'
import type {
  Video,
  VideoCreateRequest,
  VideoListResponse,
  TaskStatusResponse,
} from '../types/api'

export const videoService = {
  /**
   * Start processing a new video
   */
  async processVideo(data: VideoCreateRequest): Promise<Video> {
    const response = await api.post<Video>('/api/v1/videos/process', data)
    return response.data
  },

  /**
   * List all videos for the authenticated user
   */
  async listVideos(): Promise<VideoListResponse> {
    const response = await api.get<VideoListResponse>('/api/v1/videos/')
    return response.data
  },

  /**
   * Get details of a specific video
   */
  async getVideo(videoId: number): Promise<Video> {
    const response = await api.get<Video>(`/api/v1/videos/${videoId}`)
    return response.data
  },

  /**
   * Get status of a processing task
   */
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const response = await api.get<TaskStatusResponse>(`/api/v1/videos/status/${taskId}`)
    return response.data
  },
}

export default videoService
