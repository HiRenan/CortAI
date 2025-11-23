import { useState, useEffect, useRef } from 'react'
import { Send, AlertCircle } from 'lucide-react'
import { useVideoStore } from '../store/useVideoStore'
import { HeroSection } from '../components/HeroSection'
import { StatsCards } from '../components/StatsCards'
import { VideoCard } from '../components/VideoCard'
import { EmptyState } from '../components/EmptyState'

const URL_REGEX = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|twitch\.tv|vimeo\.com)\/.+$/i

export function Dashboard() {
  const [url, setUrl] = useState('')
  const [maxHighlights, setMaxHighlights] = useState(5)
  const [urlError, setUrlError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { videos, isLoading, error, fetchVideos, addVideo, deleteVideo, checkStatus } = useVideoStore()
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Fetch videos on mount
  useEffect(() => {
    fetchVideos()
  }, [fetchVideos])

  // Polling for processing videos (2s interval)
  useEffect(() => {
    const processingVideos = videos.filter(v => v.status === 'processing')

    if (processingVideos.length > 0) {
      pollingIntervalRef.current = setInterval(() => {
        processingVideos.forEach(video => {
          checkStatus(video.id)
        })
      }, 2000)
    } else {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [videos, checkStatus])

  const validateUrl = (url: string): boolean => {
    if (!url.trim()) {
      setUrlError('Por favor, insira uma URL')
      return false
    }

    if (!URL_REGEX.test(url)) {
      setUrlError('URL inválida. Use YouTube, Twitch ou Vimeo')
      return false
    }

    setUrlError(null)
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateUrl(url)) return

    setIsSubmitting(true)
    await addVideo(url, maxHighlights)
    setIsSubmitting(false)
    setUrl('')
  }

  const handleDelete = async (id: number) => {
    if (confirm('Tem certeza que deseja deletar este vídeo?')) {
      await deleteVideo(id)
    }
  }

  return (
    <div className="space-y-8 pb-8">
      {/* Hero Section */}
      <HeroSection />

      {/* Upload Form */}
      <div className="bg-white rounded-lg shadow-md border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">
          Processar Novo Vídeo
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <div className="flex gap-3">
              <input
                type="text"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value)
                  setUrlError(null)
                }}
                placeholder="https://youtube.com/watch?v=..."
                className={`
                  flex-1 px-4 py-3 rounded-lg border transition-all
                  focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                  ${urlError ? 'border-red-300 bg-red-50' : 'border-slate-300'}
                `}
                disabled={isSubmitting}
              />
              <button
                type="submit"
                disabled={isSubmitting || !url.trim()}
                className="
                  px-6 py-3 bg-gradient-to-r from-indigo-600 to-teal-600 text-white
                  rounded-lg font-medium shadow-md hover:shadow-lg
                  transition-all hover:from-indigo-700 hover:to-teal-700
                  disabled:opacity-50 disabled:cursor-not-allowed
                  flex items-center gap-2
                "
              >
                <Send className="w-4 h-4" strokeWidth={2} />
                {isSubmitting ? 'Processando...' : 'Processar'}
              </button>
            </div>

            {urlError && (
              <div className="flex items-center gap-2 mt-2 text-sm text-red-600">
                <AlertCircle className="w-4 h-4" strokeWidth={2} />
                <span>{urlError}</span>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 mt-2 text-sm text-red-600">
                <AlertCircle className="w-4 h-4" strokeWidth={2} />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* Max Highlights Selector */}
          <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
            <label htmlFor="maxHighlights" className="text-sm font-medium text-slate-700">
              Número de highlights:
            </label>
            <input
              type="number"
              id="maxHighlights"
              min="1"
              max="20"
              value={maxHighlights}
              onChange={(e) => setMaxHighlights(Math.min(20, Math.max(1, parseInt(e.target.value) || 5)))}
              className="
                w-20 px-3 py-2 rounded-lg border border-slate-300
                focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                text-center font-semibold bg-white
              "
              disabled={isSubmitting}
            />
            <span className="text-sm text-slate-500">
              (Recomendado: 3-10 para melhores resultados)
            </span>
          </div>

          <p className="text-xs text-slate-500 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-teal-500 rounded-full"></span>
            Plataformas suportadas: YouTube, Twitch, Vimeo
          </p>
        </form>
      </div>

      {/* Stats Cards */}
      {!isLoading && videos.length > 0 && (
        <StatsCards videos={videos} />
      )}

      {/* Videos Grid or Empty State */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-slate-600 mt-4 font-medium">Carregando vídeos...</p>
          </div>
        </div>
      ) : videos.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-slate-900">
            Seus Vídeos ({videos.length})
          </h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {videos.map((video) => (
              <VideoCard
                key={video.id}
                video={video}
                onDelete={handleDelete}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
