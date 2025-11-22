import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { Video, VideoListResponse } from '../types/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface VideoStore {
  videos: Video[]
  isLoading: boolean
  error: string | null

  fetchVideos: () => Promise<void>
  addVideo: (url: string) => Promise<void>
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
          const token = localStorage.getItem('auth_token')
          const response = await fetch(`${API_URL}/api/v1/videos/`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })

          if (!response.ok) {
            throw new Error('Falha ao carregar vídeos')
          }

          const data: VideoListResponse = await response.json()
          set({ videos: data.videos, isLoading: false })
        } catch (error) {
          console.error('Erro ao carregar vídeos:', error)
          set({
            error: error instanceof Error ? error.message : 'Erro desconhecido',
            isLoading: false
          })
        }
      },

      addVideo: async (url) => {
        set({ error: null })

        try {
          const token = localStorage.getItem('auth_token')
          const response = await fetch(`${API_URL}/api/v1/videos/process`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ url }),
          })

          if (!response.ok) {
            throw new Error('Falha ao iniciar processamento')
          }

          const newVideo: Video = await response.json()

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
          const token = localStorage.getItem('auth_token')
          const response = await fetch(`${API_URL}/api/v1/videos/${id}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })

          if (!response.ok) {
            throw new Error('Falha ao deletar vídeo')
          }

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
          const token = localStorage.getItem('auth_token')
          const response = await fetch(`${API_URL}/api/v1/videos/status/${video.task_id}`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })

          if (!response.ok) {
            throw new Error('Falha ao verificar status')
          }

          const data = await response.json()

          // Update video with progress tracking data
          set((state) => ({
            videos: state.videos.map((v) =>
              v.id === id ? {
                ...v,
                status: data.status === 'SUCCESS' ? 'completed' :
                        data.status === 'FAILURE' ? 'failed' : v.status,
                progress_stage: data.progress_stage,
                progress_percentage: data.progress_percentage,
                progress_message: data.progress_message
              } : v
            )
          }))
        } catch (error) {
          console.error('Erro ao checar status:', error)
        }
      }
    }),
    { name: 'CortAI-Store' }
  )
)
