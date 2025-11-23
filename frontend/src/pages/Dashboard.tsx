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
  const [maxHighlights] = useState(5)
  const [includeSubtitles, setIncludeSubtitles] = useState(true)
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
    await addVideo(url, maxHighlights, includeSubtitles)
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

      {/* Upload Form - Redesigned */}
      <div className="relative overflow-hidden bg-gradient-to-br from-white via-indigo-50/30 to-teal-50/30 rounded-xl shadow-lg border border-slate-200/60 p-8">
        {/* Subtle background pattern */}
        <div className="absolute inset-0 opacity-[0.03]">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, rgb(99 102 241) 1px, transparent 0)',
            backgroundSize: '32px 32px'
          }} />
        </div>

        <div className="relative">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-teal-500 shadow-md">
              <Send className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Processar Novo Vídeo
              </h2>
              <p className="text-sm text-slate-600">Transforme seu conteúdo em clips virais</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* URL Input */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                URL do Vídeo
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={url}
                  onChange={(e) => {
                    setUrl(e.target.value)
                    setUrlError(null)
                  }}
                  placeholder="https://youtube.com/watch?v=..."
                  className={`
                    w-full pl-4 pr-4 py-4 rounded-xl border-2 transition-all text-base
                    focus:outline-none focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500
                    ${urlError ? 'border-red-300 bg-red-50' : 'border-slate-200 bg-white hover:border-slate-300'}
                  `}
                  disabled={isSubmitting}
                />
              </div>

              {urlError && (
                <div className="flex items-center gap-2 mt-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" strokeWidth={2} />
                  <span>{urlError}</span>
                </div>
              )}

              {error && (
                <div className="flex items-center gap-2 mt-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" strokeWidth={2} />
                  <span>{error}</span>
                </div>
              )}
            </div>

            {/* Max Highlights removido */}

            {/* Subtitle Toggle */}
            <div className="bg-white/70 backdrop-blur-sm rounded-xl p-5 border border-slate-200/60 shadow-sm">
              <label className="flex items-center justify-between cursor-pointer group">
                <div className="flex-1">
                  <div className="text-sm font-medium text-slate-700 mb-1">
                  Legendas
                  </div>
                  <div className="text-xs text-slate-600">
                    Adiciona legendas diretamente no vídeo (estilo YouTube/TikTok)
                  </div>
                </div>
                <div className="relative ml-4">
                  <input
                    type="checkbox"
                    checked={includeSubtitles}
                    onChange={(e) => setIncludeSubtitles(e.target.checked)}
                    disabled={isSubmitting}
                    className="sr-only peer"
                  />
                  <div className="
                    w-14 h-8 bg-slate-200 rounded-full peer
                    peer-focus:ring-4 peer-focus:ring-indigo-500/20
                    peer-checked:bg-gradient-to-r peer-checked:from-indigo-600 peer-checked:to-teal-600
                    transition-all duration-300
                    peer-disabled:opacity-50 peer-disabled:cursor-not-allowed
                  "></div>
                  <div className="
                    absolute left-1 top-1 w-6 h-6 bg-white rounded-full shadow-md
                    peer-checked:translate-x-6 transition-transform duration-300
                  "></div>
                </div>
              </label>
            </div>

            {/* Platform Info */}
            <div className="flex items-center gap-2 text-sm text-slate-600 px-1">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 bg-teal-500 rounded-full animate-pulse"></span>
                <span className="font-medium">Plataformas:</span>
              </div>
              <span>YouTube • Twitch • Vimeo</span>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || !url.trim()}
              className="
                w-full relative group overflow-hidden
                px-8 py-4 bg-gradient-to-r from-indigo-600 to-teal-600 text-white
                rounded-xl font-semibold text-base shadow-lg hover:shadow-xl
                transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]
                disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
                flex items-center justify-center gap-3
              "
            >
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-700 to-teal-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <Send className="w-5 h-5 relative z-10 transition-transform group-hover:translate-x-1" strokeWidth={2.5} />
              <span className="relative z-10">
                {isSubmitting ? 'Processando Vídeo...' : 'Processar Vídeo'}
              </span>
            </button>
          </form>
        </div>
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
