import { useCallback, useEffect, useState } from 'react'
import { api, type VideoInfo } from '../lib/api'
import StageProgress from '../components/StageProgress'

export default function VideoGallery() {
  const [videos, setVideos] = useState<VideoInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<string | null>(null)

  const fetchVideos = useCallback(async () => {
    try {
      const data = await api.listVideos()
      setVideos(data.videos)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchVideos()
    // 10초마다 자동 새로고침 (새 영상 자동 반영)
    const id = setInterval(fetchVideos, 10000)
    // 윈도우 포커스 복귀 시 즉시 새로고침
    const onFocus = () => fetchVideos()
    window.addEventListener('focus', onFocus)
    return () => {
      clearInterval(id)
      window.removeEventListener('focus', onFocus)
    }
  }, [fetchVideos])

  if (loading) {
    return <div className="text-center text-gray-500 py-12">불러오는 중...</div>
  }

  if (videos.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        <p className="text-lg mb-2">아직 영상이 없습니다</p>
        <p className="text-sm">첫 번째 영상을 생성하면 여기에 표시됩니다</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">
          영상 갤러리 <span className="text-gray-500 text-sm font-normal">({videos.length}개)</span>
        </h2>
        <button
          type="button"
          onClick={fetchVideos}
          className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg"
        >
          새로고침
        </button>
      </div>

      {/* Video player */}
      {selected && (
        <div className="mb-6 bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <video
            src={api.getVideoStreamUrl(selected)}
            controls
            autoPlay
            className="w-full max-h-[500px] bg-black"
          />
          <div className="p-3 flex justify-between items-center">
            <span className="text-sm text-gray-400">
              {videos.find((v) => v.video_id === selected)?.topic || selected}
            </span>
            <button
              onClick={() => setSelected(null)}
              className="text-xs text-gray-500 hover:text-white"
            >
              닫기
            </button>
          </div>
        </div>
      )}

      {/* Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {videos.map((video) => (
          <div
            key={video.video_id}
            onClick={() => setSelected(video.video_id)}
            className={`bg-gray-900 border rounded-xl overflow-hidden cursor-pointer transition-all hover:scale-[1.02] ${
              selected === video.video_id
                ? 'border-red-500 ring-1 ring-red-500/50'
                : 'border-gray-800 hover:border-gray-700'
            }`}
          >
            {/* Thumbnail */}
            <div className="aspect-[9/16] max-h-48 bg-gray-800 relative overflow-hidden">
              <img
                src={api.getThumbnailUrl(video.video_id)}
                alt=""
                className="w-full h-full object-cover"
                onError={(e) => {
                  ;(e.target as HTMLImageElement).style.display = 'none'
                }}
              />
              <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 hover:opacity-100 transition-opacity">
                <svg className="w-10 h-10 text-white/80" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              {video.format && (
                <span className="absolute top-2 right-2 px-1.5 py-0.5 bg-black/70 text-[10px] text-gray-300 rounded">
                  {video.format}
                </span>
              )}
            </div>

            {/* Info */}
            <div className="p-3">
              <p className="text-xs font-medium text-white truncate">
                {video.topic || video.video_id}
              </p>
              <div className="flex items-center justify-between mt-1">
                {video.pattern && (
                  <span className="text-[10px] text-gray-500">패턴 {video.pattern}</span>
                )}
                {video.created_at && (
                  <span className="text-[10px] text-gray-600">
                    {new Date(video.created_at).toLocaleDateString('ko-KR')}
                  </span>
                )}
              </div>
              {video.stages.length > 0 && (
                <div className="mt-2">
                  <StageProgress stages={video.stages} />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
