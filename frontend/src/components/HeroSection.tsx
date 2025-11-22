import { Sparkles, Zap } from 'lucide-react'

export function HeroSection() {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-600 via-blue-500 to-cyan-400 p-8 text-white shadow-2xl">
      {/* Animated background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-10 left-10 w-32 h-32 bg-white rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-10 right-10 w-40 h-40 bg-white rounded-full blur-3xl animate-pulse delay-700" />
      </div>

      {/* Content */}
      <div className="relative z-10 space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-8 h-8 animate-pulse" />
          <h1 className="text-4xl font-bold tracking-tight">
            Bem-vindo ao CortAI
          </h1>
        </div>

        <p className="text-lg text-white/90 max-w-2xl">
          Transforme seus vídeos longos em <strong>cortes virais</strong> automaticamente com inteligência artificial.
          Nossa plataforma analisa, identifica highlights e gera clips prontos para suas redes sociais.
        </p>

        <div className="flex items-center gap-2 text-sm text-white/80">
          <Zap className="w-4 h-4" />
          <span>Processamento rápido e inteligente</span>
        </div>
      </div>
    </div>
  )
}
