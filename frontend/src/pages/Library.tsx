import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Video, Clock, CheckCircle, XCircle, Loader2, Play } from 'lucide-react'
import videoService from '../services/videoService'
import type { Video as VideoType } from '../types/api'
import { API_URL } from '../lib/axios'

export function Library() {
  const [videos, setVideos] = useState<VideoType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [previewUrls, setPreviewUrls] = useState<Record<number, string>>({})
  const [previewLoading, setPreviewLoading] = useState<Record<number, boolean>>({})
  const [previewErrors, setPreviewErrors] = useState<Record<number, string | null>>({})

  useEffect(() => {
    let cancelled = false

    async function fetchVideos() {
      try {
        setLoading(true)
        setError(null)

        const response = await videoService.listVideos()

        if (!cancelled) {
          setVideos(response.videos)
        }
      } catch (err) {
        if (!cancelled) {
          const errorMessage = err instanceof Error ? err.message : 'Erro ao carregar vídeos'
          setError(errorMessage)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchVideos()

    // Cleanup function
    return () => {
      cancelled = true
      Object.values(previewUrls).forEach((url) => URL.revokeObjectURL(url))
    }
  }, [previewUrls])

  const handlePreview = async (video: VideoType) => {
    if (!video.output_path) return
    setPreviewErrors((prev) => ({ ...prev, [video.id]: null }))
    setPreviewLoading((prev) => ({ ...prev, [video.id]: true }))

    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setPreviewErrors((prev) => ({ ...prev, [video.id]: 'Faça login para assistir' }))
        setPreviewLoading((prev) => ({ ...prev, [video.id]: false }))
        return
      }

      const res = await fetch(`${API_URL}/api/v1/videos/${video.id}/download`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (!res.ok) {
        throw new Error('Falha ao baixar o corte para reprodução')
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      setPreviewUrls((prev) => ({ ...prev, [video.id]: url }))
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erro ao preparar o player'
      setPreviewErrors((prev) => ({ ...prev, [video.id]: msg }))
    } finally {
      setPreviewLoading((prev) => ({ ...prev, [video.id]: false }))
    }
  }

  const getStatusIcon = (status: VideoType['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusText = (status: VideoType['status']) => {
    switch (status) {
      case 'completed':
        return 'Concluído'
      case 'failed':
        return 'Falhou'
      case 'processing':
        return 'Processando'
      default:
        return status
    }
  }

  const getStatusBadgeVariant = (status: VideoType['status']) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'failed':
        return 'destructive'
      case 'processing':
        return 'warning'
      default:
        return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getYoutubeThumb = (url: string) => {
    const matchId = url.match(/v=([A-Za-z0-9_-]{6,})/) || url.match(/youtu\.be\/([A-Za-z0-9_-]{6,})/)
    if (matchId && matchId[1]) {
      return `https://img.youtube.com/vi/${matchId[1]}/hqdefault.jpg`
    }
    return null
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Biblioteca</h1>
          <p className="text-gray-500 mt-2">Seus vídeos processados.</p>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
          <span className="ml-3 text-gray-600">Carregando vídeos...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Biblioteca</h1>
          <p className="text-gray-500 mt-2">Seus vídeos processados.</p>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex">
            <XCircle className="h-5 w-5 text-red-600" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Erro ao carregar vídeos</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (videos.length === 0) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Biblioteca</h1>
          <p className="text-gray-500 mt-2">Seus vídeos processados.</p>
        </div>
        <div className="text-center py-12">
          <Video className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">Nenhum vídeo processado</h3>
          <p className="mt-2 text-sm text-gray-500">
            Comece processando um vídeo no Dashboard.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Biblioteca</h1>
        <p className="text-gray-500 mt-2">
          {videos.length} {videos.length === 1 ? 'vídeo processado' : 'vídeos processados'}
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {videos.map((video) => (
          <Card key={video.id} className="overflow-hidden hover:shadow-lg transition-shadow">
            <div className="aspect-video w-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center overflow-hidden">
              {previewUrls[video.id] ? (
                <video
                  src={previewUrls[video.id]}
                  preload="metadata"
                  controls
                  className="w-full h-full object-cover"
                />
              ) : video.thumbnail_path || getYoutubeThumb(video.url) ? (
                <img
                  src={video.thumbnail_path || getYoutubeThumb(video.url) || undefined}
                  alt={video.title || 'Thumbnail'}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Video className="h-12 w-12 text-gray-400" />
              )}
            </div>
            <CardHeader className="p-4">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base line-clamp-2">
                  {video.title || 'Vídeo sem título'}
                </CardTitle>
                <Badge variant={getStatusBadgeVariant(video.status)} className="flex items-center gap-1 shrink-0">
                  {getStatusIcon(video.status)}
                  {getStatusText(video.status)}
                </Badge>
              </div>
              <CardDescription className="line-clamp-1 text-xs mt-2">
                {video.url}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="flex items-center text-xs text-gray-500">
                <Clock className="h-3 w-3 mr-1" />
                {formatDate(video.created_at)}
              </div>
              {video.output_path && (
                <div className="mt-3 space-y-2">
                  <button
                    onClick={() => handlePreview(video)}
                    disabled={previewLoading[video.id]}
                    className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {previewLoading[video.id] ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Preparando player...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4" />
                        Assistir corte
                      </>
                    )}
                  </button>
                  {previewErrors[video.id] && (
                    <p className="text-xs text-red-600">{previewErrors[video.id]}</p>
                  )}
                  {previewUrls[video.id] && (
                    <p className="text-xs text-green-600 truncate">
                      📁 {video.output_path}
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
