import { useState } from 'react'
import ToastContainer from './components/Toast'
import Dashboard from './pages/Dashboard'
import CreateVideo from './pages/CreateVideo'
import BatchVideos from './pages/BatchVideos'
import VideoGallery from './pages/VideoGallery'
import Settings from './pages/Settings'

type Page = 'dashboard' | 'create' | 'batch' | 'gallery' | 'settings'

const NAV_ITEMS: { id: Page; label: string }[] = [
  { id: 'dashboard', label: '대시보드' },
  { id: 'create', label: '영상 생성' },
  { id: 'batch', label: '배치' },
  { id: 'gallery', label: '갤러리' },
  { id: 'settings', label: '설정' },
]

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <h1 className="text-lg font-bold tracking-tight">
            <span className="text-red-500">YT</span> 자동화
          </h1>
          <nav className="flex gap-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setPage(item.id)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  page === item.id
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {page === 'dashboard' && <Dashboard onNavigate={setPage} />}
        {page === 'create' && <CreateVideo onCreated={() => setPage('dashboard')} />}
        {page === 'batch' && <BatchVideos />}
        {page === 'gallery' && <VideoGallery />}
        {page === 'settings' && <Settings />}
      </main>
      <ToastContainer />
    </div>
  )
}
