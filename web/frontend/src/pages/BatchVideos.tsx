import { useEffect, useState } from 'react'
import {
  api,
  type BatchSummary,
  type ColorInfo,
  type FormatInfo,
  type PatternInfo,
  type PlatformInfo,
} from '../lib/api'
import { toast } from '../components/Toast'

interface DraftJob {
  topic: string
}

export default function BatchVideos() {
  const [patterns, setPatterns] = useState<PatternInfo[]>([])
  const [formats, setFormats] = useState<FormatInfo[]>([])
  const [colors, setColors] = useState<ColorInfo[]>([])
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([])
  const [batches, setBatches] = useState<BatchSummary[]>([])

  const [defaultPattern, setDefaultPattern] = useState('B')
  const [defaultFormat, setDefaultFormat] = useState('S15')
  const [defaultColor, setDefaultColor] = useState('')
  const [defaultPlatforms, setDefaultPlatforms] = useState<string[]>([])

  const [draftRows, setDraftRows] = useState<DraftJob[]>([{ topic: '' }, { topic: '' }])
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    Promise.all([
      api.getPatterns(),
      api.getFormats(),
      api.getColors(),
      api.getPlatforms().catch(() => [] as PlatformInfo[]),
      api.listBatches().catch(() => ({ batches: [] as BatchSummary[], total: 0 })),
    ]).then(([p, f, c, pl, bl]) => {
      setPatterns(p)
      setFormats(f)
      setColors(c)
      setPlatforms(pl)
      setBatches(bl.batches)
    })
  }, [])

  const refreshBatches = async () => {
    try {
      const data = await api.listBatches()
      setBatches(data.batches)
    } catch {
      // ignore
    }
  }

  const updateRow = (i: number, topic: string) => {
    setDraftRows((prev) => {
      const next = [...prev]
      next[i] = { topic }
      return next
    })
  }

  const addRow = () => setDraftRows((prev) => [...prev, { topic: '' }])
  const removeRow = (i: number) =>
    setDraftRows((prev) => prev.filter((_, idx) => idx !== i))

  const togglePlatform = (id: string) => {
    setDefaultPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    )
  }

  const handleSubmit = async () => {
    const validJobs = draftRows.filter((r) => r.topic.trim().length > 0)
    if (validJobs.length === 0) {
      toast('error', '주제를 1개 이상 입력하세요')
      return
    }

    setSubmitting(true)
    try {
      const result = await api.createBatch({
        defaults: {
          pattern: defaultPattern,
          format: defaultFormat,
          color_preset: defaultColor || undefined,
          platforms: defaultPlatforms.length ? defaultPlatforms : undefined,
        },
        jobs: validJobs.map((r) => ({ topic: r.topic.trim() })),
      })
      toast('success', `배치 ${result.batch_id} 등록 — ${result.total}개 영상 큐잉`)
      setDraftRows([{ topic: '' }, { topic: '' }])
      await refreshBatches()
    } catch (err) {
      const msg = err instanceof Error ? err.message : '배치 등록 실패'
      toast('error', msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold mb-2">배치 영상 생성</h2>
        <p className="text-sm text-gray-500">
          여러 영상을 한 번에 큐잉합니다. defaults 가 각 잡에 자동 적용됩니다.
        </p>
      </div>

      {/* Defaults */}
      <section className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-gray-300">기본값 (defaults)</h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">패턴</label>
            <select
              value={defaultPattern}
              onChange={(e) => setDefaultPattern(e.target.value)}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm"
            >
              {patterns.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.id}. {p.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">포맷</label>
            <select
              value={defaultFormat}
              onChange={(e) => setDefaultFormat(e.target.value)}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm"
            >
              {formats.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.id} ({f.duration_sec}s, {f.aspect_ratio})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">컬러 프리셋</label>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setDefaultColor('')}
              className={`px-3 py-1.5 rounded-lg border text-xs transition-colors ${
                defaultColor === ''
                  ? 'border-red-500 bg-red-500/10 text-white'
                  : 'border-gray-800 bg-gray-950 text-gray-400'
              }`}
            >
              자동
            </button>
            {colors.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setDefaultColor(c.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs transition-colors ${
                  defaultColor === c.id
                    ? 'border-red-500 bg-red-500/10 text-white'
                    : 'border-gray-800 bg-gray-950 text-gray-400'
                }`}
              >
                <span
                  className="w-3 h-3 rounded-full border border-gray-700"
                  style={{ background: c.primary }}
                />
                {c.name}
              </button>
            ))}
          </div>
        </div>

        {platforms.length > 0 && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">멀티플랫폼 익스포트</label>
            <div className="flex flex-wrap gap-2">
              {platforms.map((pl) => {
                const active = defaultPlatforms.includes(pl.id)
                return (
                  <button
                    key={pl.id}
                    type="button"
                    onClick={() => togglePlatform(pl.id)}
                    className={`px-3 py-1.5 rounded-lg border text-xs transition-colors ${
                      active
                        ? 'border-red-500 bg-red-500/10 text-white'
                        : 'border-gray-800 bg-gray-950 text-gray-400'
                    }`}
                  >
                    {pl.label}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </section>

      {/* Job topics */}
      <section className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-300">주제 목록</h3>
          <button
            type="button"
            onClick={addRow}
            className="px-3 py-1 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg"
          >
            + 행 추가
          </button>
        </div>
        <div className="space-y-2">
          {draftRows.map((row, i) => (
            <div key={i} className="flex gap-2">
              <span className="w-6 text-xs text-gray-600 pt-2 text-right">{i + 1}</span>
              <input
                type="text"
                value={row.topic}
                onChange={(e) => updateRow(i, e.target.value)}
                placeholder="영상 주제"
                className="flex-1 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500"
              />
              <button
                type="button"
                onClick={() => removeRow(i)}
                disabled={draftRows.length === 1}
                className="text-gray-600 hover:text-red-400 disabled:opacity-30 px-2"
                title="삭제"
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full mt-2 py-3 bg-red-600 hover:bg-red-500 disabled:bg-gray-700 text-white rounded-xl font-medium transition-colors"
        >
          {submitting ? '등록 중...' : `배치 등록 (${draftRows.filter((r) => r.topic.trim()).length}개)`}
        </button>
      </section>

      {/* Recent batches */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-300">최근 배치</h3>
          <button
            type="button"
            onClick={refreshBatches}
            className="text-xs text-gray-500 hover:text-gray-300"
          >
            새로고침
          </button>
        </div>
        {batches.length === 0 ? (
          <div className="text-sm text-gray-600 py-6 text-center">아직 배치가 없습니다</div>
        ) : (
          <div className="space-y-2">
            {batches.map((b) => (
              <div
                key={b.batch_id}
                className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between"
              >
                <div>
                  <p className="text-sm font-medium text-white">#{b.batch_id}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(b.created_at).toLocaleString('ko-KR')}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">
                    완료 {b.done}/{b.total}
                  </p>
                  <p className="text-xs">
                    <span className="text-green-400">{b.success}</span> /{' '}
                    <span className="text-red-400">{b.failed}</span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
