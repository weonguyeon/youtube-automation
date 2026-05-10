import { useState } from 'react'
import { api, type JobResponse, type StageInfo } from '../lib/api'
import { useJobSSE } from '../hooks/useJobSSE'
import StageProgress from './StageProgress'

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-yellow-900/50 text-yellow-400',
  running: 'bg-blue-900/50 text-blue-400',
  completed: 'bg-green-900/50 text-green-400',
  failed: 'bg-red-900/50 text-red-400',
}

const STATUS_LABELS: Record<string, string> = {
  pending: '대기 중',
  running: '진행 중',
  completed: '완료',
  failed: '실패',
}

export default function JobCard({
  job,
  onDelete,
  onJobUpdate,
}: {
  job: JobResponse
  onDelete: (id: string) => void
  onJobUpdate?: (jobId: string) => void
}) {
  const isActive = job.status === 'running' || job.status === 'pending'
  const [expanded, setExpanded] = useState(false)
  const { progress } = useJobSSE(
    isActive ? job.job_id : null,
    undefined,
    () => onJobUpdate?.(job.job_id),
  )

  // SSE에서 받은 실시간 stages가 있으면 우선 사용
  const liveStages: StageInfo[] = progress?.stages ?? job.stages
  const currentStage = progress?.current_stage ?? job.current_stage

  const canPlay = job.status === 'completed' && !!job.video_id

  return (
    <div
      className={`bg-gray-900 border rounded-xl p-4 transition-colors ${
        canPlay ? 'border-gray-800 hover:border-red-500/50 cursor-pointer' : 'border-gray-800 hover:border-gray-700'
      }`}
      onClick={() => canPlay && setExpanded((v) => !v)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[job.status]}`}
            >
              {STATUS_LABELS[job.status]}
              {job.status === 'running' && (
                <span className="ml-1 animate-pulse">...</span>
              )}
            </span>
            <span className="text-xs text-gray-500">
              패턴 {job.pattern} / {job.format}
            </span>
            {canPlay && (
              <span className="text-xs text-red-400">
                {expanded ? '▾ 닫기' : '▸ 영상 보기'}
              </span>
            )}
          </div>
          <h3 className="text-sm font-medium text-white truncate">{job.topic}</h3>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(job.created_at).toLocaleString('ko-KR')}
            {job.completed_at && (
              <span className="ml-2">
                → {new Date(job.completed_at).toLocaleString('ko-KR')}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete(job.job_id)
          }}
          className="text-gray-600 hover:text-red-400 transition-colors p-1"
          title="삭제"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {(liveStages.length > 0 || currentStage) && (
        <div className="mt-3">
          <StageProgress stages={liveStages} currentStage={currentStage} />
        </div>
      )}

      {job.errors.length > 0 && (
        <div className="mt-2 text-xs text-red-400 bg-red-900/20 rounded p-2">
          {job.errors[0]}
        </div>
      )}

      {canPlay && expanded && job.video_id && (
        <div className="mt-3" onClick={(e) => e.stopPropagation()}>
          <video
            src={api.getVideoStreamUrl(job.video_id)}
            controls
            autoPlay
            className="w-full max-h-[480px] bg-black rounded-lg"
          />
        </div>
      )}
    </div>
  )
}
