import { useEffect, useState } from 'react'

export interface ToastMessage {
  id: number
  type: 'success' | 'error' | 'info'
  text: string
}

let nextId = 0
let addToastFn: ((msg: Omit<ToastMessage, 'id'>) => void) | null = null

/** 글로벌 토스트 트리거 */
export function toast(type: ToastMessage['type'], text: string) {
  addToastFn?.({ type, text })
}

export default function ToastContainer() {
  const [messages, setMessages] = useState<ToastMessage[]>([])

  useEffect(() => {
    addToastFn = (msg) => {
      const id = ++nextId
      setMessages((prev) => [...prev, { ...msg, id }])
      setTimeout(() => setMessages((prev) => prev.filter((m) => m.id !== id)), 4000)
    }
    return () => { addToastFn = null }
  }, [])

  if (!messages.length) return null

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      {messages.map((m) => (
        <div
          key={m.id}
          className={`px-4 py-3 rounded-lg text-sm font-medium shadow-lg animate-[slideIn_0.2s_ease-out] ${
            m.type === 'success'
              ? 'bg-green-900/90 text-green-200 border border-green-700'
              : m.type === 'error'
                ? 'bg-red-900/90 text-red-200 border border-red-700'
                : 'bg-gray-800/90 text-gray-200 border border-gray-700'
          }`}
        >
          {m.text}
        </div>
      ))}
    </div>
  )
}
