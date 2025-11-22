import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Video, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import videoService from '../services/videoService'
import type { Video as VideoType } from '../types/api'

export function Library() {
  const [videos, setVideos] = useState<VideoType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
    }
  }, [])

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
            <div className="aspect-video w-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
              <Video className="h-12 w-12 text-gray-400" />
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
                <p className="text-xs text-green-600 mt-2 truncate">
                  📁 {video.output_path}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
