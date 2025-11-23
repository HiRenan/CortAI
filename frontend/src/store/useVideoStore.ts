import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { isAxiosError } from 'axios'
import api from '../lib/axios'
import type { TaskStatusResponse, Video, VideoListResponse } from '../types/api'

interface VideoStore {
  videos: Video[]
  isLoading: boolean
  error: string | null

  fetchVideos: () => Promise<void>
  addVideo: (url: string, maxHighlights?: number, includeSubtitles?: boolean) => Promise<void>
  deleteVideo: (id: number) => Promise<void>
  checkStatus: (id: number) => Promise<void>
}

export const useVideoStore = create<VideoStore>()(
  devtools(
    (set, get) => ({
      videos: [],
      isLoading: false,
      error: null,

      fetchVideos: async () => {
        set({ isLoading: true, error: null })

        try {
          const response = await api.get<VideoListResponse>('/api/v1/videos/')
          set({ videos: response.data.videos, isLoading: false })
        } catch (error: unknown) {
          if (isAxiosError(error) && error.response?.status === 401) {
            set({
              error: 'Sessão expirada. Faça login novamente.',
              isLoading: false,
            })
            return
          }

          console.error('Erro ao carregar vídeos:', error)
          set({
            error: error instanceof Error ? error.message : 'Erro desconhecido',
            isLoading: false
          })
        }
      },

      addVideo: async (url, maxHighlights = 5, includeSubtitles = true) => {
        set({ error: null })

        try {
          const response = await api.post<Video>('/api/v1/videos/process', {
            url,
            max_highlights: maxHighlights,
            include_subtitles: includeSubtitles,
            subtitle_style: 'youtube'
          })
          const newVideo = response.data

          // Adiciona o novo vídeo no início da lista
          set((state) => ({
            videos: [newVideo, ...state.videos]
          }))

        } catch (error) {
          console.error('Erro ao adicionar vídeo:', error)
          set({
            error: error instanceof Error ? error.message : 'Erro ao adicionar vídeo'
          })
        }
      },

      deleteVideo: async (id) => {
        set({ error: null })

        try {
          await api.delete(`/api/v1/videos/${id}`)

          // Remove o vídeo da lista
          set((state) => ({
            videos: state.videos.filter((v) => v.id !== id)
          }))
        } catch (error) {
          console.error('Erro ao deletar vídeo:', error)
          set({
            error: error instanceof Error ? error.message : 'Erro ao deletar vídeo'
          })
        }
      },

      checkStatus: async (id) => {
        const video = get().videos.find((v) => v.id === id)
        if (!video?.task_id || video.status === 'completed' || video.status === 'failed') {
          return
        }

        try {
          const { data } = await api.get<TaskStatusResponse>(`/api/v1/videos/status/${video.task_id}`)

          const mappedStatus =
            data.video_status ||
            (data.status === 'SUCCESS' ? 'completed' :
             data.status === 'FAILURE' ? 'failed' : undefined)

          set((state) => ({
            videos: state.videos.map((v) =>
              v.id === id ? {
                ...v,
                status: mappedStatus || v.status,
                progress_stage: data.progress_stage,
                progress_percentage: data.progress_percentage,
                progress_message: data.progress_message,
                output_path: data.output_path ?? v.output_path,
              } : v
            )
          }))

          // Se completou, faz um refresh geral para pegar eventuais novos campos
          if (mappedStatus === 'completed') {
            const refreshed = await api.get<VideoListResponse>('/api/v1/videos/')
            set({ videos: refreshed.data.videos })
          }
        } catch (error) {
          console.error('Erro ao checar status:', error)
        }
      }
    }),
    { name: 'CortAI-Store' }
  )
)
