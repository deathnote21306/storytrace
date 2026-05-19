'use client'
import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import VoiceInput from '@/components/VoiceInput'
import { getApiUrl } from '@/lib/apiUrl'

export default function Home() {
  const router = useRouter()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!input.trim()) {
      setError('Please enter a topic or URL')
      return
    }
    setLoading(true)
    setError('')

    const apiUrl = await getApiUrl()
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
    <div className="w-full min-h-[calc(100vh-4rem)] bg-background">
      <section className="relative px-4 md:px-10 py-12 md:py-20 max-w-5xl mx-auto">
        <div className="absolute inset-0 canvas-bg opacity-60 pointer-events-none rounded-xl" />
        <div className="relative z-10 flex flex-col items-center text-center gap-6">
          <div className="flex items-center gap-3 text-secondary">
            <span className="material-symbols-outlined text-[40px]">account_tree</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-on-surface tracking-tight leading-tight">
            Git for News
          </h1>
          <p className="text-base md:text-lg text-on-surface-variant max-w-2xl leading-relaxed">
            Paste a news URL or speak a topic — StoryTrace finds the original wire story,
            tracks how it mutated across outlets and countries, and visualizes the drift chain.
          </p>

          <form
            onSubmit={handleSubmit}
            className="w-full max-w-2xl mt-4 bg-surface-container-low border border-outline-variant rounded-xl overflow-hidden shadow-lg"
          >
            <div className="px-4 py-3 border-b border-outline-variant bg-surface-container flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">search</span>
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">
                Start a Narrative Trace
              </span>
            </div>
            <div className="p-4 md:p-6 flex flex-col sm:flex-row gap-3 items-stretch sm:items-center canvas-bg">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="e.g. Russia Ukraine war  or  https://reuters.com/..."
                className="flex-1 bg-surface-container-highest border border-outline-variant rounded-lg px-4 py-3 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary-container disabled:opacity-50 font-mono"
                disabled={loading}
              />
              <div className="flex items-center gap-2 justify-center sm:justify-end">
                <VoiceInput onTranscript={(t: string) => setInput(prev => (prev + ' ' + t).trim())} />
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 bg-primary-container text-on-primary-container px-6 py-3 rounded-lg text-[11px] font-mono font-bold uppercase tracking-wider hover:opacity-90 disabled:opacity-50 transition-all active:scale-95 whitespace-nowrap"
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {loading ? 'hourglass_top' : 'bolt'}
                  </span>
                  {loading ? 'Tracing…' : 'Trace'}
                </button>
              </div>
            </div>
          </form>

          {error && (
            <p className="text-sm text-error flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">error</span>
              {error}
            </p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-3xl mt-8 text-left">
            <FeatureCard
              icon="rss_feed"
              title="Wire Source"
              desc="GDELT + NewsAPI find the earliest root story"
            />
            <FeatureCard
              icon="public"
              title="15 Outlets"
              desc="RSS crawl across global news feeds"
            />
            <FeatureCard
              icon="analytics"
              title="Drift Score"
              desc="0–100 narrative mutation per outlet"
            />
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: string
  title: string
  desc: string
}) {
  return (
    <div className="bg-surface-container border border-outline-variant rounded-xl p-4 hover:border-outline transition-colors">
      <span className="material-symbols-outlined text-secondary text-[24px]">{icon}</span>
      <h3 className="text-sm font-semibold text-on-surface mt-2">{title}</h3>
      <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">{desc}</p>
    </div>
  )
}
