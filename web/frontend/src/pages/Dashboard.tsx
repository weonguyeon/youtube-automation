import { useCallback, useEffect, useState } from 'react'
import { api, type JobResponse } from '../lib/api'
import JobCard from '../components/JobCard'
import { toast } from '../components/Toast'

export default function Dashboard({
  onNavigate,
}: {
  onNavigate: (page: 'create' | 'batch' | 'gallery' | 'settings' | 'dashboard') => void
}) {
  const [jobs, setJobs] = useState<JobResponse[]>([])
  const [loading, setLoading] = useState(true)

  const fetchJobs = useCallback(async () => {
    try {
      const data = await api.listJobs()
      setJobs(data.jobs)
    } catch (e) {
      toast('error', '작업 목록을 불러오지 못했습니다')
      console.error('Failed to fetch jobs:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchJobs()
    // 10초마다 자동 새로고침 (새 잡/완료 잡 자동 반영)
    const id = setInterval(fetchJobs, 10000)
    return () => clearInterval(id)
  }, [fetchJobs])

  // SSE에서 잡 완료 알림 받으면 목록 새로고침
  const handleJobUpdate = useCallback(() => {
    fetchJobs()
  }, [fetchJobs])

  const handleDelete = async (id: string) => {
    try {
      await api.deleteJob(id)
      setJobs((prev) => prev.filter((j) => j.job_id !== id))
    } catch (e) {
      toast('error', '작업 삭제에 실패했습니다')
      console.error('Failed to delete job:', e)
    }
  }

  const running = jobs.filter((j) => j.status === 'running' || j.status === 'pending')
  const completed = jobs.filter((j) => j.status === 'completed')
  const failed = jobs.filter((j) => j.status === 'failed')

  return (
    <div>
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <StatCard label="전체 작업" value={jobs.length} />
        <StatCard label="진행 중" value={running.length} color="blue" />
        <StatCard label="완료" value={completed.length} color="green" />
        <StatCard label="실패" value={failed.length} color="red" />
      </div>

      {/* Actions */}
      <div className="flex gap-3 mb-6">
        <button
          onClick={() => onNavigate('create')}
          className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          + 새 영상
        </button>
        <button
          onClick={() => onNavigate('gallery')}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm font-medium transition-colors"
        >
          갤러리 보기
        </button>
      </div>

      {/* Job List */}
      {loading ? (
        <div className="text-center text-gray-500 py-12">불러오는 중...</div>
      ) : jobs.length === 0 ? (
        <div className="text-center text-gray-500 py-12">
          <p className="text-lg mb-2">아직 작업이 없습니다</p>
          <p className="text-sm">첫 번째 영상을 생성해보세요</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <JobCard key={job.job_id} job={job} onDelete={handleDelete} onJobUpdate={handleJobUpdate} />
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color?: string
}) {
  const colorClass =
    color === 'blue'
      ? 'text-blue-400'
      : color === 'green'
        ? 'text-green-400'
        : color === 'red'
          ? 'text-red-400'
          : 'text-white'

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${colorClass}`}>{value}</p>
    </div>
  )
}
