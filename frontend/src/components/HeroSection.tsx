import { Sparkles, Zap, Video } from 'lucide-react'
import mascoteImg from '../assets/mascote.png'

export function HeroSection() {
  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-teal-600 p-10 text-white shadow-xl">
      {/* Modern geometric pattern background */}
      <div className="absolute inset-0 opacity-[0.07]">
        <svg className="absolute inset-0 h-full w-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid-pattern" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.5" />
            </pattern>
            <pattern id="dots-pattern" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="1" fill="currentColor" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid-pattern)" />
          <rect width="100%" height="100%" fill="url(#dots-pattern)" />
        </svg>
      </div>

      {/* Animated gradient orbs (subtle, modern) */}
      <div className="absolute -top-24 -right-24 w-64 h-64 bg-teal-400/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }} />
      <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-indigo-400/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '10s', animationDelay: '2s' }} />

      {/* Content */}
      <div className="relative z-10 space-y-6">
        {/* Header with mascot badge */}
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center w-14 h-14 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 shadow-lg p-2">
            <img src={mascoteImg} alt="CortAI Mascote" className="w-full h-full object-contain" />
          </div>
          <div>
            <h1 className="text-4xl font-bold tracking-tight leading-tight">
              Bem-vindo ao CortAI
            </h1>
          </div>
        </div>

        {/* Description */}
        <p className="text-lg text-white/90 max-w-3xl leading-relaxed">
          Transforme seus vídeos longos em <span className="font-semibold text-teal-300">cortes virais</span> automaticamente com inteligência artificial.
          Nossa plataforma analisa, identifica highlights e gera clips prontos para suas redes sociais.
        </p>

        {/* Features badges */}
        <div className="flex flex-wrap items-center gap-3 pt-2">
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 backdrop-blur-sm border border-white/20 text-sm font-medium">
            <Zap className="w-4 h-4 text-yellow-300" strokeWidth={2.5} />
            <span>Processamento Rápido</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 backdrop-blur-sm border border-white/20 text-sm font-medium">
            <Video className="w-4 h-4 text-teal-300" strokeWidth={2.5} />
            <span>Cortes Automáticos</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 backdrop-blur-sm border border-white/20 text-sm font-medium">
            <Sparkles className="w-4 h-4 text-purple-300" strokeWidth={2.5} />
            <span>Análise Multimodal</span>
          </div>
        </div>
      </div>
    </div>
  )
}
