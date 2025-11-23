import { VideoCard } from '../components/VideoCard'
import type { Video } from '../types/api'

const mockVideos: Video[] = [
  {
    id: 1,
    user_id: 1,
    url: 'https://youtube.com/watch?v=example1',
    title: 'Vídeo em Processamento - Etapa de Transcrição',
    status: 'processing',
    task_id: 'task-123',
    output_path: null,
    created_at: new Date().toISOString(),
    progress_stage: 'transcribing',
    progress_percentage: 25,
    progress_message: 'Transcrevendo áudio...'
  },
  {
    id: 2,
    user_id: 1,
    url: 'https://youtube.com/watch?v=example2',
    title: 'Vídeo em Análise - Identificando Highlights',
    status: 'processing',
    task_id: 'task-456',
    output_path: null,
    created_at: new Date().toISOString(),
    progress_stage: 'analyzing',
    progress_percentage: 55,
    progress_message: 'Analisando transcrição...'
  },
  {
    id: 3,
    user_id: 1,
    url: 'https://youtube.com/watch?v=example3',
    title: 'Vídeo Editando - Cortando Highlights do Vídeo Original',
    status: 'processing',
    task_id: 'task-789',
    output_path: null,
    created_at: new Date().toISOString(),
    progress_stage: 'editing',
    progress_percentage: 85,
    progress_message: 'Cortando vídeo...'
  },
  {
    id: 4,
    user_id: 1,
    url: 'https://youtube.com/watch?v=example4',
    title: 'Vídeo Concluído - Pronto para Download',
    status: 'completed',
    task_id: 'task-complete',
    output_path: '/path/to/video.mp4',
    created_at: new Date().toISOString(),
    progress_stage: null,
    progress_percentage: 100,
    progress_message: 'Concluído!'
  },
  {
    id: 5,
    user_id: 1,
    url: 'https://youtube.com/watch?v=example5',
    title: 'Vídeo com Erro no Processamento',
    status: 'failed',
    task_id: 'task-error',
    output_path: null,
    created_at: new Date().toISOString(),
    progress_stage: null,
    progress_percentage: 0,
    progress_message: 'Erro: Falha ao baixar vídeo. Verifique a URL.'
  },
  {
    id: 6,
    user_id: 1,
    url: 'https://youtube.com/watch?v=example6-very-long-url-to-test-truncation',
    title: 'Título Muito Longo Para Testar o Line Clamp - Lorem Ipsum Dolor Sit Amet Consectetur Adipiscing Elit',
    status: 'processing',
    task_id: 'task-long',
    output_path: null,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    progress_stage: 'transcribing',
    progress_percentage: 10,
    progress_message: 'Baixando vídeo...'
  }
]

export function TestVideoCard() {
  const handleDelete = (id: number) => {
    alert(`Deletar vídeo ${id}`)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Teste: VideoCard</h1>
          <p className="text-gray-600 mt-2">Componente de card de vídeo com ProgressStepper integrado</p>
        </div>

        {/* Legend */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Estados Testados:</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-yellow-100 border-2 border-yellow-200 rounded-full"></span>
              <span><strong>Processing:</strong> Com ProgressStepper (3 exemplos)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-green-100 border-2 border-green-200 rounded-full"></span>
              <span><strong>Completed:</strong> Com botões de ação</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-red-100 border-2 border-red-200 rounded-full"></span>
              <span><strong>Failed:</strong> Com mensagem de erro</span>
            </div>
          </div>
        </div>

        {/* Video Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {mockVideos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              onDelete={handleDelete}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
