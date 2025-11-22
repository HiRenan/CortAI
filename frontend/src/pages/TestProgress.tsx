import { useState } from 'react'
import { ProgressStepper } from '../components/ProgressStepper'
import type { ProgressStage } from '../types/api'

export function TestProgress() {
  const [stage, setStage] = useState<ProgressStage>('transcribing')
  const [percentage, setPercentage] = useState(25)
  const [message, setMessage] = useState('Transcrevendo áudio...')

  const presets = [
    { stage: 'transcribing' as ProgressStage, percentage: 5, message: 'Baixando vídeo...' },
    { stage: 'transcribing' as ProgressStage, percentage: 20, message: 'Transcrevendo áudio...' },
    { stage: 'transcribing' as ProgressStage, percentage: 33, message: 'Transcrição concluída' },
    { stage: 'analyzing' as ProgressStage, percentage: 40, message: 'Analisando transcrição...' },
    { stage: 'analyzing' as ProgressStage, percentage: 66, message: 'Análise concluída' },
    { stage: 'editing' as ProgressStage, percentage: 70, message: 'Cortando vídeo...' },
    { stage: 'editing' as ProgressStage, percentage: 95, message: 'Finalizando...' },
    { stage: null, percentage: 100, message: 'Concluído!' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Teste: ProgressStepper</h1>
          <p className="text-gray-600 mt-2">Componente de progresso com 3 etapas</p>
        </div>

        {/* Preview do Componente */}
        <div className="bg-white p-8 rounded-xl shadow-lg">
          <ProgressStepper
            currentStage={stage}
            percentage={percentage}
            message={message}
          />
        </div>

        {/* Controles Manuais */}
        <div className="bg-white p-6 rounded-xl shadow-lg space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Controles Manuais</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Stage: <span className="text-purple-600 font-mono">{stage || 'null'}</span>
            </label>
            <select
              value={stage || ''}
              onChange={(e) => setStage((e.target.value || null) as ProgressStage)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">Null (Concluído)</option>
              <option value="transcribing">Transcribing</option>
              <option value="analyzing">Analyzing</option>
              <option value="editing">Editing</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Percentage: <span className="text-purple-600 font-mono">{percentage}%</span>
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={percentage}
              onChange={(e) => setPercentage(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message:
            </label>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Digite uma mensagem..."
            />
          </div>
        </div>

        {/* Presets Rápidos */}
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Presets Rápidos</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {presets.map((preset, index) => (
              <button
                key={index}
                onClick={() => {
                  setStage(preset.stage)
                  setPercentage(preset.percentage)
                  setMessage(preset.message)
                }}
                className="px-4 py-3 text-sm font-medium text-purple-700 bg-purple-100 hover:bg-purple-200 rounded-lg transition-colors"
              >
                {preset.percentage}%
                <br />
                <span className="text-xs text-purple-600">{preset.stage || 'done'}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
