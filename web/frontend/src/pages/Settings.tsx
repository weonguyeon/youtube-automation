import { useEffect, useState } from 'react'
import { api } from '../lib/api'

interface SettingsData {
  deploy_mode: string
  has_anthropic_key: boolean
  has_elevenlabs_key: boolean
  has_youtube_credentials: boolean
  has_flux_key: boolean
  has_pexels_key: boolean
  ffmpeg_path: string
  brand_color_preset: string
  default_language: string
  default_font: string
}

interface FormFields {
  deploy_mode: string
  anthropic_api_key: string
  elevenlabs_api_key: string
  elevenlabs_voice_id: string
  youtube_client_id: string
  youtube_client_secret: string
  flux_api_key: string
  pexels_api_key: string
  ffmpeg_path: string
  brand_color_preset: string
}

const INITIAL_FORM: FormFields = {
  deploy_mode: 'cli',
  anthropic_api_key: '',
  elevenlabs_api_key: '',
  elevenlabs_voice_id: '',
  youtube_client_id: '',
  youtube_client_secret: '',
  flux_api_key: '',
  pexels_api_key: '',
  ffmpeg_path: 'ffmpeg',
  brand_color_preset: 'midnight_navy',
}

export default function Settings() {
  const [current, setCurrent] = useState<SettingsData | null>(null)
  const [form, setForm] = useState<FormFields>(INITIAL_FORM)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)

  useEffect(() => {
    api.getSettings().then((data) => {
      setCurrent(data)
      setForm((prev) => ({
        ...prev,
        deploy_mode: data.deploy_mode,
        ffmpeg_path: data.ffmpeg_path,
        brand_color_preset: data.brand_color_preset,
      }))
    })
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)
    try {
      // 빈 문자열은 전송하지 않음 (기존 값 유지)
      const payload: Record<string, string> = {}
      for (const [key, value] of Object.entries(form)) {
        if (value) payload[key] = value
      }
      const updated = await api.updateSettings(payload)
      setCurrent(updated)
      // API 키 필드 초기화
      setForm((prev) => ({
        ...prev,
        anthropic_api_key: '',
        elevenlabs_api_key: '',
        elevenlabs_voice_id: '',
        youtube_client_id: '',
        youtube_client_secret: '',
        flux_api_key: '',
        pexels_api_key: '',
      }))
      setMessage({ type: 'ok', text: '설정이 저장되었습니다' })
    } catch (e) {
      setMessage({ type: 'err', text: e instanceof Error ? e.message : '저장에 실패했습니다' })
    } finally {
      setSaving(false)
    }
  }

  const set = (key: keyof FormFields, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-bold mb-6">설정</h2>

      {/* Status indicators */}
      {current && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-8">
          <StatusBadge label="Claude API" active={current.has_anthropic_key} />
          <StatusBadge label="ElevenLabs" active={current.has_elevenlabs_key} />
          <StatusBadge label="YouTube" active={current.has_youtube_credentials} />
          <StatusBadge label="Flux (Replicate)" active={current.has_flux_key} />
          <StatusBadge label="Pexels" active={current.has_pexels_key} />
          <StatusBadge label={`Mode: ${current.deploy_mode}`} active />
        </div>
      )}

      {/* Form */}
      <div className="space-y-6">
        <Section title="일반">
          <SelectField
            label="배포 모드"
            value={form.deploy_mode}
            options={[
              { value: 'cli', label: 'CLI (Claude MAX)' },
              { value: 'api', label: 'API' },
            ]}
            onChange={(v) => set('deploy_mode', v)}
          />
          <InputField
            label="FFmpeg 경로"
            value={form.ffmpeg_path}
            onChange={(v) => set('ffmpeg_path', v)}
          />
          <InputField
            label="브랜드 컬러 프리셋"
            value={form.brand_color_preset}
            onChange={(v) => set('brand_color_preset', v)}
          />
        </Section>

        <Section title="API 키">
          <SecretField
            label="Anthropic API Key"
            value={form.anthropic_api_key}
            configured={current?.has_anthropic_key}
            onChange={(v) => set('anthropic_api_key', v)}
          />
          <SecretField
            label="ElevenLabs API Key"
            value={form.elevenlabs_api_key}
            configured={current?.has_elevenlabs_key}
            onChange={(v) => set('elevenlabs_api_key', v)}
          />
          <SecretField
            label="Flux API Key (Replicate)"
            value={form.flux_api_key}
            configured={current?.has_flux_key}
            onChange={(v) => set('flux_api_key', v)}
          />
          <SecretField
            label="Pexels API Key"
            value={form.pexels_api_key}
            configured={current?.has_pexels_key}
            onChange={(v) => set('pexels_api_key', v)}
          />
        </Section>

        <Section title="유튜브 업로드">
          <SecretField
            label="Client ID"
            value={form.youtube_client_id}
            configured={current?.has_youtube_credentials}
            onChange={(v) => set('youtube_client_id', v)}
          />
          <SecretField
            label="Client Secret"
            value={form.youtube_client_secret}
            configured={current?.has_youtube_credentials}
            onChange={(v) => set('youtube_client_secret', v)}
          />
        </Section>
      </div>

      {/* Save */}
      <div className="mt-8 flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
        >
          {saving ? '저장 중...' : '설정 저장'}
        </button>
        {message && (
          <span className={`text-sm ${message.type === 'ok' ? 'text-green-400' : 'text-red-400'}`}>
            {message.text}
          </span>
        )}
      </div>
    </div>
  )
}

function StatusBadge({ label, active }: { label: string; active: boolean }) {
  return (
    <div
      className={`px-3 py-2 rounded-lg text-xs font-medium border ${
        active
          ? 'bg-green-900/30 text-green-400 border-green-800'
          : 'bg-gray-900 text-gray-500 border-gray-800'
      }`}
    >
      <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${active ? 'bg-green-400' : 'bg-gray-600'}`} />
      {label}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">{title}</h3>
      <div className="space-y-3">{children}</div>
    </div>
  )
}

function InputField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <label className="block">
      <span className="text-xs text-gray-400">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:border-gray-600 focus:outline-none"
      />
    </label>
  )
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: { value: string; label: string }[]
  onChange: (v: string) => void
}) {
  return (
    <label className="block">
      <span className="text-xs text-gray-400">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:border-gray-600 focus:outline-none"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  )
}

function SecretField({
  label,
  value,
  configured,
  onChange,
}: {
  label: string
  value: string
  configured?: boolean
  onChange: (v: string) => void
}) {
  return (
    <label className="block">
      <span className="text-xs text-gray-400">
        {label}
        {configured && <span className="ml-2 text-green-500">(설정됨)</span>}
      </span>
      <input
        type="password"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={configured ? '********' : '키를 입력하세요...'}
        className="mt-1 w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:border-gray-600 focus:outline-none placeholder:text-gray-700"
      />
    </label>
  )
}
