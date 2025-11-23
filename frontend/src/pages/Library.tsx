import { useState, useEffect, type FormEvent } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Video, Clock, CheckCircle, XCircle, Loader2, Play, Cast, Scissors, Signal } from 'lucide-react'
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
  const [liveUrl, setLiveUrl] = useState('')
  const [liveMaxDuration, setLiveMaxDuration] = useState(300)
  const [liveSegmentDuration, setLiveSegmentDuration] = useState(60)
  const [liveMaxHighlights, setLiveMaxHighlights] = useState(5)
  const [liveIncludeSubtitles, setLiveIncludeSubtitles] = useState(true)
  const [liveSubmitting, setLiveSubmitting] = useState(false)
  const [liveError, setLiveError] = useState<string | null>(null)

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

    // Cleanup apenas no unmount
    return () => {
      cancelled = true
      Object.values(previewUrls).forEach((url) => URL.revokeObjectURL(url))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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

  const handleLiveSubmit = async (e: FormEvent) => {
    e.preventDefault()

    if (!liveUrl.trim()) {
      setLiveError('Informe a URL da live que deseja gravar')
      return
    }

    setLiveSubmitting(true)
    setLiveError(null)

    try {
      const newVideo = await videoService.processVideo({
        url: liveUrl.trim(),
        max_highlights: liveMaxHighlights,
        include_subtitles: liveIncludeSubtitles,
        subtitle_style: 'youtube',
        use_stream_collector: true,
        stream_segment_duration: liveSegmentDuration,
        stream_max_duration: liveMaxDuration
      })

      setVideos((prev) => [newVideo, ...prev])
      setLiveUrl('')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erro ao iniciar captura da live'
      setLiveError(msg)
    } finally {
      setLiveSubmitting(false)
    }
  }

  const renderLiveCapture = () => (
    <Card className="border-indigo-100 shadow-sm">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
            <Cast className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-lg">Capturar Live e Gerar Clips</CardTitle>
            <CardDescription>Grave alguns minutos de uma live (HLS, RTMP, YouTube/Twitch ao vivo) e gere cortes automaticamente.</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleLiveSubmit}>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            <div className="md:col-span-2 lg:col-span-2">
              <label className="text-sm font-medium text-slate-700 mb-2 block">URL da live</label>
              <input
                type="text"
                value={liveUrl}
                onChange={(e) => setLiveUrl(e.target.value)}
                placeholder="https://twitch.tv/..."
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
                disabled={liveSubmitting}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 mb-2 block">Tempo total (s)</label>
              <input
                type="number"
                min={30}
                max={3600}
                value={liveMaxDuration}
                onChange={(e) => setLiveMaxDuration(Math.min(3600, Math.max(30, Number(e.target.value) || 300)))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
                disabled={liveSubmitting}
              />
              <p className="text-xs text-slate-500 mt-1">Quanto tempo gravar da live.</p>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 mb-2 block">Segmento (s)</label>
              <input
                type="number"
                min={10}
                max={600}
                value={liveSegmentDuration}
                onChange={(e) => setLiveSegmentDuration(Math.min(600, Math.max(10, Number(e.target.value) || 60)))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
                disabled={liveSubmitting}
              />
              <p className="text-xs text-slate-500 mt-1">Tamanho de cada corte bruto baixado.</p>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 mb-2 block">Highlights</label>
              <input
                type="number"
                min={1}
                max={20}
                value={liveMaxHighlights}
                onChange={(e) => setLiveMaxHighlights(Math.min(20, Math.max(1, Number(e.target.value) || 5)))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
                disabled={liveSubmitting}
              />
              <p className="text-xs text-slate-500 mt-1">Quantidade de clipes finais desejados.</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <label className="inline-flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={liveIncludeSubtitles}
                onChange={(e) => setLiveIncludeSubtitles(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                disabled={liveSubmitting}
              />
              Incluir legendas queimadas
            </label>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Signal className="h-4 w-4 text-indigo-500" />
              Captura usa FFmpeg + yt-dlp com segmentação automática.
            </div>
          </div>

          {liveError && (
            <p className="text-sm text-red-600">{liveError}</p>
          )}

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={liveSubmitting}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
            >
              {liveSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Gravando live...
                </>
              ) : (
                <>
                  <Scissors className="h-4 w-4" />
                  Gravar e gerar clipes
                </>
              )}
            </button>
            <p className="text-xs text-slate-500">
              O clipe final aparecerá na lista abaixo quando o processamento terminar.
            </p>
          </div>
        </form>
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Biblioteca</h1>
          <p className="text-gray-500 mt-2">Seus vídeos processados.</p>
        </div>
        {renderLiveCapture()}
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
        {renderLiveCapture()}
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
        {renderLiveCapture()}
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

      {renderLiveCapture()}

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
