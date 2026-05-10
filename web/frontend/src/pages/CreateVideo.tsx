import { useEffect, useState } from 'react'
import {
  api,
  type ColorInfo,
  type EngineInfo,
  type FormatInfo,
  type PatternInfo,
  type PlatformInfo,
} from '../lib/api'
import { toast } from '../components/Toast'

export default function CreateVideo({ onCreated }: { onCreated: () => void }) {
  const [patterns, setPatterns] = useState<PatternInfo[]>([])
  const [formats, setFormats] = useState<FormatInfo[]>([])
  const [colors, setColors] = useState<ColorInfo[]>([])
  const [engines, setEngines] = useState<EngineInfo[]>([])
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([])

  const [topic, setTopic] = useState('')
  const [pattern, setPattern] = useState('B')
  const [format, setFormat] = useState('S15')
  const [colorPreset, setColorPreset] = useState('')
  const [engine, setEngine] = useState('')
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.getPatterns(),
      api.getFormats(),
      api.getColors(),
      api.getEngines(),
      api.getPlatforms().catch(() => [] as PlatformInfo[]),
    ]).then(([p, f, c, e, pl]) => {
      setPatterns(p)
      setFormats(f)
      setColors(c)
      setEngines(e)
      setPlatforms(pl)
    })
  }, [])

  const togglePlatform = (id: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim()) return

    setSubmitting(true)
    setError('')

    try {
      await api.createJob({
        topic: topic.trim(),
        pattern,
        format,
        color_preset: colorPreset || undefined,
        render_engine: engine || undefined,
        platforms: selectedPlatforms.length ? selectedPlatforms : undefined,
      })
      toast('success', '영상 생성 작업이 등록되었습니다!')
      onCreated()
    } catch (err) {
      const msg = err instanceof Error ? err.message : '영상 생성에 실패했습니다'
      setError(msg)
      toast('error', msg)
    } finally {
      setSubmitting(false)
    }
  }

  const difficultyStars = (n: number) => '★'.repeat(n) + '☆'.repeat(5 - n)

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-xl font-bold mb-6">새 영상 생성</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Topic */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">주제</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. 2026년 세계 GDP 순위 변화"
            className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-red-500 transition-colors"
            required
          />
        </div>

        {/* Pattern */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">패턴</label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {patterns.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setPattern(p.id)}
                className={`p-3 rounded-xl border text-left transition-colors ${
                  pattern === p.id
                    ? 'border-red-500 bg-red-500/10'
                    : 'border-gray-800 bg-gray-900 hover:border-gray-700'
                }`}
              >
                <div className="text-sm font-medium text-white">
                  {p.id}. {p.name}
                </div>
                <div className="text-xs text-gray-500 mt-1">{p.description}</div>
                <div className="text-xs text-yellow-500 mt-1">
                  {difficultyStars(p.difficulty)}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Format */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">포맷</label>
          <div className="flex flex-wrap gap-2">
            {formats.map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => setFormat(f.id)}
                className={`px-4 py-2 rounded-lg border text-sm transition-colors ${
                  format === f.id
                    ? 'border-red-500 bg-red-500/10 text-white'
                    : 'border-gray-800 bg-gray-900 text-gray-400 hover:border-gray-700'
                }`}
              >
                <span className="font-medium">{f.id}</span>
                <span className="ml-1 text-xs opacity-60">
                  {f.duration_sec < 60 ? `${f.duration_sec}s` : `${f.duration_sec / 60}m`}
                  {' '}({f.aspect_ratio})
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Color Preset */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            컬러 프리셋 <span className="text-gray-600">(선택사항)</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {colors.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setColorPreset(colorPreset === c.id ? '' : c.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-colors ${
                  colorPreset === c.id
                    ? 'border-red-500 bg-red-500/10'
                    : 'border-gray-800 bg-gray-900 hover:border-gray-700'
                }`}
              >
                <span
                  className="w-4 h-4 rounded-full border border-gray-700"
                  style={{ background: c.primary }}
                />
                <span className="text-gray-300">{c.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Engine */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            렌더 엔진 <span className="text-gray-600">(선택사항)</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {engines.map((eng) => (
              <button
                key={eng.id}
                type="button"
                onClick={() => setEngine(engine === eng.id ? '' : eng.id)}
                className={`px-4 py-2 rounded-lg border text-sm transition-colors ${
                  engine === eng.id
                    ? 'border-red-500 bg-red-500/10 text-white'
                    : 'border-gray-800 bg-gray-900 text-gray-400 hover:border-gray-700'
                }`}
              >
                <span className="font-medium">{eng.name}</span>
                <span className="ml-1 text-xs opacity-60">— {eng.description}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Multi-Platform Export */}
        {platforms.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              멀티플랫폼 익스포트 <span className="text-gray-600">(선택사항)</span>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {platforms.map((pl) => {
                const active = selectedPlatforms.includes(pl.id)
                return (
                  <button
                    key={pl.id}
                    type="button"
                    onClick={() => togglePlatform(pl.id)}
                    className={`p-3 rounded-xl border text-left transition-colors ${
                      active
                        ? 'border-red-500 bg-red-500/10'
                        : 'border-gray-800 bg-gray-900 hover:border-gray-700'
                    }`}
                  >
                    <div className="text-sm font-medium text-white">{pl.label}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {pl.width}×{pl.height}
                      {pl.max_duration_sec ? ` · 최대 ${pl.max_duration_sec}s` : ''}
                    </div>
                  </button>
                )
              })}
            </div>
            {selectedPlatforms.length > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                선택된 {selectedPlatforms.length}개 플랫폼 — 영상 생성 후 자동 변환됩니다.
              </p>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-sm text-red-400 bg-red-900/20 rounded-lg p-3">{error}</div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting || !topic.trim()}
          className="w-full py-3 bg-red-600 hover:bg-red-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl font-medium transition-colors"
        >
          {submitting ? '생성 중...' : '영상 생성하기'}
        </button>
      </form>
    </div>
  )
}
