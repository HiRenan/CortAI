import { CheckCircle2, Loader2, Circle } from 'lucide-react'
import { useMemo } from 'react'
import type { ProgressStage } from '../types/api'

interface Step {
  id: string
  label: string
  description: string
}

interface ProgressStepperProps {
  currentStage: ProgressStage
  percentage: number
  message?: string
}

const STEPS: Step[] = [
  { id: 'transcribing', label: 'Transcrever', description: 'Download e áudio' },
  { id: 'analyzing', label: 'Analisar', description: 'Identificar momentos' },
  { id: 'editing', label: 'Editar', description: 'Cortar vídeo' }
]

export function ProgressStepper({
  currentStage,
  percentage,
  message
}: ProgressStepperProps) {

  // Calcula status de cada step (completed, active, pending)
  const getStepStatus = useMemo(() => {
    return (stepId: string) => {
      if (!currentStage) return 'pending'

      const stepIndex = STEPS.findIndex(s => s.id === stepId)
      const currentIndex = STEPS.findIndex(s => s.id === currentStage)

      if (currentIndex === -1) return 'pending'
      if (stepIndex < currentIndex) return 'completed'
      if (stepIndex === currentIndex) return 'active'
      return 'pending'
    }
  }, [currentStage])

  return (
    <div className="w-full space-y-4">
      {/* Barra de Progresso com Gradiente */}
      <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="absolute h-full bg-gradient-to-r from-purple-600 via-blue-500 to-cyan-400 transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Steps Horizontal */}
      <div className="flex justify-between items-start relative">
        {STEPS.map((step, index) => {
          const status = getStepStatus(step.id)

          return (
            <div key={step.id} className="flex flex-col items-center flex-1 relative">
              {/* Linha Conectora */}
              {index > 0 && (
                <div
                  className={`absolute top-5 right-1/2 w-full h-0.5 -z-10 transition-colors duration-300 ${
                    status === 'completed' ? 'bg-gradient-to-r from-purple-600 to-blue-500' : 'bg-gray-200'
                  }`}
                  style={{ transform: 'translateX(50%)' }}
                />
              )}

              {/* Ícone do Step */}
              <div className={`
                relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-2
                transition-all duration-300 shadow-lg
                ${status === 'completed' && 'bg-green-500 border-green-500 shadow-green-200'}
                ${status === 'active' && 'bg-purple-600 border-purple-600 shadow-purple-200'}
                ${status === 'pending' && 'bg-white border-gray-300'}
              `}>
                {status === 'completed' && <CheckCircle2 className="w-6 h-6 text-white" />}
                {status === 'active' && <Loader2 className="w-6 h-6 text-white animate-spin" />}
                {status === 'pending' && <Circle className="w-6 h-6 text-gray-300" />}
              </div>

              {/* Label e Descrição */}
              <div className="mt-3 text-center">
                <p className={`text-sm font-semibold transition-colors ${
                  status !== 'pending' ? 'text-gray-900' : 'text-gray-400'
                }`}>
                  {step.label}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">{step.description}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Mensagem Atual */}
      {message && (
        <div className="flex items-center justify-center gap-2 py-2">
          <div className="w-2 h-2 bg-purple-600 rounded-full animate-pulse" />
          <p className="text-sm text-center text-purple-700 font-medium">
            {message}
          </p>
        </div>
      )}
    </div>
  )
}
