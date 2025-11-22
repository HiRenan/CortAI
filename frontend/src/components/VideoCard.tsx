import { Video as VideoIcon, Download, ExternalLink, Trash2, AlertCircle } from 'lucide-react'
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

  // Badge color based on status
  const badgeColors = {
    processing: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    completed: 'bg-green-100 text-green-800 border-green-200',
    failed: 'bg-red-100 text-red-800 border-red-200'
  }

  // Card border color based on status
  const cardBorderColors = {
    processing: 'border-purple-200 bg-purple-50/30',
    completed: 'border-green-200 bg-green-50/30',
    failed: 'border-red-200 bg-red-50/30'
  }

  return (
    <div className={`
      overflow-hidden rounded-xl border-2 transition-all duration-300
      hover:shadow-xl hover:-translate-y-1
      ${cardBorderColors[video.status]}
    `}>
      {/* Thumbnail / Placeholder */}
      <div className="relative aspect-video w-full bg-gradient-to-br from-purple-100 via-blue-100 to-cyan-100 flex items-center justify-center overflow-hidden">
        {video.output_path ? (
          <img
            src={video.output_path}
            alt={video.title || 'Vídeo'}
            className="w-full h-full object-cover"
          />
        ) : (
          <VideoIcon className="h-20 w-20 text-purple-300" />
        )}

        {/* Status Badge Overlay */}
        <div className="absolute top-3 right-3">
          <span className={`
            inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold
            border backdrop-blur-sm
            ${badgeColors[video.status]}
          `}>
            {isProcessing && '⏳ Em Processamento'}
            {isCompleted && '✅ Concluído'}
            {isFailed && '❌ Falhou'}
          </span>
        </div>
      </div>

      {/* Card Content */}
      <div className="p-4 space-y-3 bg-white">
        {/* Title */}
        <h3 className="font-semibold text-base text-gray-900 line-clamp-2 min-h-[3rem]">
          {video.title || 'Processando...'}
        </h3>

        {/* URL */}
        <a
          href={video.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-purple-600 transition-colors line-clamp-1"
        >
          <ExternalLink className="w-3 h-3 flex-shrink-0" />
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

        {/* Actions (if completed) */}
        {isCompleted && (
          <div className="flex gap-2 pt-2 border-t border-gray-100">
            <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all font-medium text-sm shadow-md hover:shadow-lg">
              <Download className="w-4 h-4" />
              Baixar Corte
            </button>
            {onDelete && (
              <button
                onClick={() => onDelete(video.id)}
                className="px-3 py-2 border-2 border-gray-300 text-gray-700 rounded-lg hover:border-red-500 hover:text-red-600 hover:bg-red-50 transition-all"
                title="Deletar vídeo"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
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
