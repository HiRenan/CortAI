import { Video, ArrowUp } from 'lucide-react'

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="relative">
        {/* Animated icon */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-400/20 via-blue-400/20 to-cyan-400/20 rounded-full blur-2xl animate-pulse" />
        <div className="relative bg-gradient-to-br from-purple-100 via-blue-100 to-cyan-100 p-8 rounded-full">
          <Video className="w-16 h-16 text-purple-600" />
        </div>
      </div>

      <h3 className="mt-6 text-xl font-semibold text-gray-900">
        Nenhum vídeo processado ainda
      </h3>

      <p className="mt-2 text-center text-gray-600 max-w-md">
        Comece enviando a URL de um vídeo do YouTube ou outra plataforma.
        Nossa IA irá analisar e gerar cortes automaticamente!
      </p>

      <div className="mt-6 flex items-center gap-2 text-sm text-purple-600 font-medium">
        <ArrowUp className="w-4 h-4 animate-bounce" />
        <span>Cole a URL do vídeo no formulário acima</span>
      </div>
    </div>
  )
}
