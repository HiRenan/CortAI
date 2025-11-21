import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface Video {
  id: string
  taskId?: string
  url: string
  status: 'processing' | 'completed' | 'failed'
  title?: string
  thumbnail?: string
}

interface VideoStore {
  videos: Video[]
  addVideo: (url: string) => Promise<void>
  checkStatus: (id: string) => Promise<void>
}

export const useVideoStore = create<VideoStore>()(
  devtools(
    (set, get) => ({
      videos: [],
      
      addVideo: async (url) => {
        // 1. Adiciona estado otimista
        const tempId = crypto.randomUUID()
        set((state) => ({
          videos: [
            {
              id: tempId,
              url,
              status: 'processing',
              title: 'Iniciando processamento...',
            },
            ...state.videos,
          ],
        }))

        try {
          // 2. Chama a API Real
          const response = await fetch(`${API_URL}/api/v1/videos/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
          })
          
          if (!response.ok) throw new Error('Falha ao iniciar processamento')
            
          const data = await response.json() // Espera { task_id, status }

          // 3. Atualiza com o ID da Task real
          set((state) => ({
            videos: state.videos.map((v) => 
              v.id === tempId ? { ...v, taskId: data.task_id } : v
            )
          }))
          
        } catch (error) {
          console.error(error)
          set((state) => ({
            videos: state.videos.map((v) => 
              v.id === tempId ? { ...v, status: 'failed', title: 'Erro ao conectar com API' } : v
            )
          }))
        }
      },

      checkStatus: async (id) => {
        const video = get().videos.find((v) => v.id === id)
        if (!video?.taskId || video.status === 'completed' || video.status === 'failed') return

        try {
          const response = await fetch(`${API_URL}/api/v1/videos/status/${video.taskId}`)
          const data = await response.json()
          
          if (data.status === 'SUCCESS') {
             set((state) => ({
              videos: state.videos.map((v) => 
                v.id === id ? { ...v, status: 'completed', title: 'Processamento Concluído!' } : v
              )
            }))
          } else if (data.status === 'FAILURE') {
             set((state) => ({
              videos: state.videos.map((v) => 
                v.id === id ? { ...v, status: 'failed', title: 'Falha no processamento' } : v
              )
            }))
          }
          // Se for PENDING ou STARTED, não faz nada, só espera
        } catch (error) {
          console.error('Erro ao checar status:', error)
        }
      }
    }),
    { name: 'CortAI-Store' }
  )
)
