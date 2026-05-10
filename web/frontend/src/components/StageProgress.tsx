import type { StageInfo } from '../lib/api'

const STAGE_LABELS: Record<string, string> = {
  script_generation: '대본',
  audio_generation: '오디오',
  visual_generation: '시각 에셋',
  assembly: '조립',
  upload: '업로드',
}

function getStageName(name: string): string {
  for (const [key, label] of Object.entries(STAGE_LABELS)) {
    if (name.toLowerCase().includes(key.replace('_', ' ')) || name.toLowerCase().includes(key)) {
      return label
    }
  }
  // visual_generation (ai_pipeline) 같은 형태 처리
  if (name.toLowerCase().includes('visual')) return '시각 에셋'
  if (name.toLowerCase().includes('script')) return '대본'
  if (name.toLowerCase().includes('audio')) return '오디오'
  if (name.toLowerCase().includes('assembly')) return '조립'
  return name
}

export default function StageProgress({
  stages,
  currentStage,
}: {
  stages: StageInfo[]
  currentStage?: string | null
}) {
  if (!stages.length && !currentStage) return null

  return (
    <div className="flex items-center gap-1 text-xs">
      {stages.map((stage, i) => (
        <div key={i} className="flex items-center gap-1">
          {i > 0 && <span className="text-gray-600">→</span>}
          <span
            className={`px-1.5 py-0.5 rounded ${
              stage.success
                ? 'bg-green-900/50 text-green-400'
                : stage.error
                  ? 'bg-red-900/50 text-red-400'
                  : 'bg-gray-800 text-gray-500'
            }`}
          >
            {getStageName(stage.name)}
            {stage.duration_sec > 0 && (
              <span className="ml-1 opacity-60">{stage.duration_sec.toFixed(1)}s</span>
            )}
          </span>
        </div>
      ))}
      {/* 현재 진행 중인 Stage 표시 */}
      {currentStage && (
        <div className="flex items-center gap-1">
          {stages.length > 0 && <span className="text-gray-600">&rarr;</span>}
          <span className="px-1.5 py-0.5 rounded bg-blue-900/50 text-blue-400 animate-pulse">
            {getStageName(currentStage)}...
          </span>
        </div>
      )}
    </div>
  )
}
