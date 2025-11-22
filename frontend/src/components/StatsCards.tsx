import { useMemo } from 'react'
import { Video as VideoIcon, Loader2, CheckCircle2 } from 'lucide-react'
import type { Video } from '../types/api'

interface StatsCardsProps {
  videos: Video[]
}

export function StatsCards({ videos }: StatsCardsProps) {
  const stats = useMemo(() => {
    const total = videos.length
    const processing = videos.filter(v => v.status === 'processing').length
    const completed = videos.filter(v => v.status === 'completed').length

    return { total, processing, completed }
  }, [videos])

  const cards = [
    {
      label: 'Total de Vídeos',
      value: stats.total,
      icon: VideoIcon,
      bgColor: 'bg-purple-100',
      iconColor: 'text-purple-600',
      borderColor: 'border-purple-200'
    },
    {
      label: 'Em Processamento',
      value: stats.processing,
      icon: Loader2,
      bgColor: 'bg-yellow-100',
      iconColor: 'text-yellow-600',
      borderColor: 'border-yellow-200',
      animate: stats.processing > 0 ? 'animate-spin' : ''
    },
    {
      label: 'Concluídos',
      value: stats.completed,
      icon: CheckCircle2,
      bgColor: 'bg-green-100',
      iconColor: 'text-green-600',
      borderColor: 'border-green-200'
    }
  ]

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {cards.map((card) => {
        const Icon = card.icon
        return (
          <div
            key={card.label}
            className={`
              flex items-center gap-4 p-5 rounded-xl border-2
              bg-white shadow-sm hover:shadow-md transition-shadow
              ${card.borderColor}
            `}
          >
            <div className={`p-3 rounded-lg ${card.bgColor}`}>
              <Icon className={`w-6 h-6 ${card.iconColor} ${card.animate || ''}`} />
            </div>
            <div>
              <p className="text-sm text-gray-600 font-medium">{card.label}</p>
              <p className="text-2xl font-bold text-gray-900">{card.value}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
