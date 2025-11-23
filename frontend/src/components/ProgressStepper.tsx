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
      <div className="relative h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          className="absolute h-full bg-gradient-to-r from-indigo-600 to-teal-500 transition-all duration-500 ease-out shadow-sm"
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
                    status === 'completed' ? 'bg-gradient-to-r from-indigo-500 to-teal-500' : 'bg-slate-200'
                  }`}
                  style={{ transform: 'translateX(50%)' }}
                />
              )}

              {/* Ícone do Step */}
              <div className={`
                relative z-10 flex items-center justify-center w-11 h-11 rounded-full border-2
                transition-all duration-300 shadow-md
                ${status === 'completed' && 'bg-teal-500 border-teal-500'}
                ${status === 'active' && 'bg-indigo-600 border-indigo-600'}
                ${status === 'pending' && 'bg-white border-slate-300'}
              `}>
                {status === 'completed' && <CheckCircle2 className="w-5 h-5 text-white" strokeWidth={2.5} />}
                {status === 'active' && <Loader2 className="w-5 h-5 text-white animate-spin" strokeWidth={2.5} />}
                {status === 'pending' && <Circle className="w-5 h-5 text-slate-300" strokeWidth={2} />}
              </div>

              {/* Label e Descrição */}
              <div className="mt-3 text-center">
                <p className={`text-sm font-semibold transition-colors ${
                  status !== 'pending' ? 'text-slate-900' : 'text-slate-400'
                }`}>
                  {step.label}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">{step.description}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Mensagem Atual */}
      {message && (
        <div className="flex items-center justify-center gap-2 py-2 px-3 bg-indigo-50 rounded-lg border border-indigo-100">
          <div className="w-2 h-2 bg-indigo-600 rounded-full animate-pulse" />
          <p className="text-sm text-center text-indigo-700 font-medium">
            {message}
          </p>
        </div>
      )}
    </div>
  )
}
