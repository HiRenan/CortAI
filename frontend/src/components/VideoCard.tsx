import { Video as VideoIcon, Download, ExternalLink, Trash2, AlertCircle, Clock, CheckCircle, XCircle } from 'lucide-react'
import { ProgressStepper } from './ProgressStepper'
import type { Video } from '../types/api'

interface VideoCardProps {
  video: Video
  onDelete?: (id: number) => void
}

export function VideoCard({ video, onDelete }: VideoCardProps) {
  const isProcessing = video.status === 'processing'
  const isCompleted = video.status === 'completed'
  const isFailed = video.status === 'failed'
  const canDelete = Boolean(onDelete)
  const showDownload = isCompleted

  const handleDownload = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        alert('Você precisa estar autenticado para baixar o clip')
        return
      }

      const response = await fetch(`http://localhost:8000/api/v1/videos/${video.id}/download`, {
        headers: {
          Authorization: `Bearer ${token}`,
        }
      })

      if (!response.ok) {
        throw new Error('Erro ao baixar o clip')
      }

      const contentDisposition = response.headers.get('Content-Disposition')
      const filenameMatch = contentDisposition?.match(/filename="(.+)"/)
      const filename = filenameMatch ? filenameMatch[1] : `clip_video_${video.id}.mp4`

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Erro ao baixar clip:', error)
      alert('Erro ao baixar o clip. Tente novamente.')
    }
  }

  // Badge styling based on status
  const statusConfig = {
    processing: {
      badge: 'bg-amber-100 text-amber-800 border-amber-200',
      card: 'border-indigo-200 bg-indigo-50/30',
      icon: Clock,
      label: 'Em Processamento'
    },
    completed: {
      badge: 'bg-teal-100 text-teal-800 border-teal-200',
      card: 'border-teal-200 bg-teal-50/30',
      icon: CheckCircle,
      label: 'Concluído'
    },
    failed: {
      badge: 'bg-red-100 text-red-800 border-red-200',
      card: 'border-red-200 bg-red-50/30',
      icon: XCircle,
      label: 'Falhou'
    }
  }

  const currentStatus = statusConfig[video.status]
  const StatusIcon = currentStatus.icon

  const getYoutubeThumb = (url: string) => {
    const matchId = url.match(/v=([A-Za-z0-9_-]{6,})/) || url.match(/youtu\.be\/([A-Za-z0-9_-]{6,})/)
    if (matchId && matchId[1]) {
      return `https://img.youtube.com/vi/${matchId[1]}/hqdefault.jpg`
    }
    return null
  }

  const poster = video.thumbnail_path || getYoutubeThumb(video.url)

  return (
    <div className={`
      overflow-hidden rounded-lg border transition-all duration-300
      hover:shadow-lg hover:-translate-y-0.5
      ${currentStatus.card}
    `}>
      {/* Thumbnail / Placeholder */}
      <div className="relative aspect-video w-full bg-gradient-to-br from-indigo-100 via-slate-100 to-teal-100 flex items-center justify-center overflow-hidden">
        {poster ? (
          <img
            src={poster}
            alt={video.title || 'Vídeo'}
            className="w-full h-full object-cover"
          />
        ) : (
          <VideoIcon className="h-20 w-20 text-indigo-300" strokeWidth={1.5} />
        )}

        {/* Status Badge Overlay */}
        <div className="absolute top-3 right-3 flex items-center gap-2">
          <span className={`
            inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold
            border backdrop-blur-sm shadow-sm
            ${currentStatus.badge}
          `}>
            <StatusIcon className="w-3.5 h-3.5" strokeWidth={2.5} />
            {currentStatus.label}
          </span>

          {onDelete && (
            <button
              onClick={() => onDelete(video.id)}
              className="flex items-center justify-center p-2 rounded-lg border border-slate-200 text-slate-600 bg-white/90 hover:border-red-400 hover:text-red-600 hover:bg-red-50 transition-all shadow-sm"
              title="Excluir vídeo"
            >
              <Trash2 className="w-4 h-4" strokeWidth={2} />
            </button>
          )}
        </div>
      </div>

      {/* Card Content */}
      <div className="p-4 space-y-3 bg-white">
        {/* Title */}
        <h3 className="font-semibold text-base text-gray-900 line-clamp-2 min-h-[3rem]">
          {video.title || (isCompleted ? 'Vídeo processado' : 'Processando...')}
        </h3>

        {/* URL */}
        <a
          href={video.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-slate-500 hover:text-indigo-600 transition-colors line-clamp-1"
        >
          <ExternalLink className="w-3 h-3 flex-shrink-0" strokeWidth={2} />
          <span className="truncate">{video.url}</span>
        </a>

        {/* Progress Stepper (only if processing) */}
        {isProcessing && video.progress_stage && (
          <div className="pt-2 border-t border-gray-100">
            <ProgressStepper
              currentStage={video.progress_stage}
              percentage={video.progress_percentage || 0}
              message={video.progress_message || undefined}
            />
          </div>
        )}

        {/* Error Message (if failed) */}
        {isFailed && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-xs font-medium text-red-800">Erro no processamento</p>
              <p className="text-xs text-red-600 mt-1">
                {video.progress_message || 'Ocorreu um erro durante o processamento'}
              </p>
            </div>
          </div>
        )}

        {/* Actions */}
        {(isCompleted || isProcessing || isFailed) && (showDownload || canDelete) && (
          <div className="flex gap-2 pt-2 border-t border-slate-100">
            {showDownload && (
              <button
                onClick={handleDownload}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-teal-600 text-white rounded-lg hover:from-indigo-700 hover:to-teal-700 transition-all font-medium text-sm shadow-md hover:shadow-lg"
              >
                <Download className="w-4 h-4" strokeWidth={2} />
                Baixar Corte
              </button>
            )}

            {/* delete button removido da barra inferior; agora apenas no topo */}
          </div>
        )}

        {/* Date */}
        <p className="text-xs text-gray-400 pt-2">
          {new Date(video.created_at).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </p>
      </div>
    </div>
  )
}
