'use client'
import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!input.trim()) return
    setLoading(true)
    setError('')

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const isUrl = input.startsWith('http://') || input.startsWith('https://')
    const body = isUrl ? { url: input } : { topic: input }

    try {
      const res = await fetch(`${apiUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const { job_id } = await res.json()
      router.push(`/story/${job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 text-center">
      <h1 className="text-4xl font-bold text-[#1B3A6B] mb-4">Git for News</h1>
      <p className="text-lg text-gray-600 max-w-xl mb-8">
        Paste a news URL or topic — StoryTrace tracks how the story mutated across
        countries and outlets, visualized as a drift tree.
      </p>

      <form onSubmit={handleSubmit} className="w-full max-w-xl flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="e.g. Russia Ukraine war  or  https://reuters.com/..."
          className="flex-1 border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#2E5FA3]"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-[#1B3A6B] text-white px-6 py-3 rounded-lg text-sm font-semibold hover:bg-[#2E5FA3] disabled:opacity-50 transition-colors"
        >
          {loading ? 'Analyzing…' : 'Trace'}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
    </div>
  )
}
