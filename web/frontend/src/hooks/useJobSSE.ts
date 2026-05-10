import { useEffect, useRef, useState } from 'react'
import type { StageInfo } from '../lib/api'

interface SSEProgress {
  type: 'progress' | 'done' | 'error'
  job_id: string
  status: string
  current_stage?: string | null
  stages: StageInfo[]
  message?: string
}

/**
 * SSE 훅 — running/pending 잡의 실시간 진행 상황 구독
 * 완료/실패 시 자동 종료, onDone 콜백 호출
 */
export function useJobSSE(
  jobId: string | null,
  onUpdate?: (data: SSEProgress) => void,
  onDone?: (data: SSEProgress) => void,
) {
  const [progress, setProgress] = useState<SSEProgress | null>(null)
  const [connected, setConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!jobId) return

    const es = new EventSource(`/api/jobs/${jobId}/sse`)
    eventSourceRef.current = es

    es.onopen = () => setConnected(true)

    es.onmessage = (event) => {
      try {
        const data: SSEProgress = JSON.parse(event.data)
        setProgress(data)
        onUpdate?.(data)

        if (data.type === 'done' || data.type === 'error') {
          onDone?.(data)
          es.close()
          setConnected(false)
        }
      } catch {
        // ignore parse errors
      }
    }

    es.onerror = () => {
      es.close()
      setConnected(false)
    }

    return () => {
      es.close()
      setConnected(false)
    }
    // jobId 변경 시에만 재구독
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId])

  return { progress, connected }
}
