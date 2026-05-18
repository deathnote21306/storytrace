'use client'
import { useState, useEffect, use } from 'react'
import DriftTree from '@/components/DriftTree'
import DiffPanel from '@/components/DiffPanel'
import DriftLegend from '@/components/DriftLegend'
import ErrorBoundary from '@/components/ErrorBoundary'

type StoryState =
  | { status: 'processing'; message?: string }
  | { status: 'complete'; root: Record<string, unknown>; tree: Record<string, unknown> }
  | { status: 'error'; message: string }

export default function StoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [story, setStory] = useState<StoryState | null>(null)
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    let timer: ReturnType<typeof setTimeout>
    const controller = new AbortController()

    async function poll() {
      try {
        const res = await fetch(`${apiUrl}/story/${id}`, { signal: controller.signal })
        if (!res.ok) {
          setStory({ status: 'error', message: `Server error: ${res.status}` })
          return
        }
        const data = await res.json()
        setStory(data)
        if (data.status === 'processing') {
          timer = setTimeout(poll, 3000)
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setStory({ status: 'error', message: 'Could not reach the API' })
        }
      }
    }

    poll()
    return () => {
      controller.abort()
      clearTimeout(timer)
    }
  }, [id, retryCount])

  function retry() {
    setStory(null)
    setRetryCount(c => c + 1)
  }

  if (!story || story.status === 'processing') {
    return <SkeletonLoader message={story?.status === 'processing' ? (story.message || 'Analyzing…') : 'Connecting…'} />
  }

  if (story.status === 'error') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] gap-4 px-4 text-center">
        <p className="text-red-500 text-sm">{story.message}</p>
        <button
          onClick={retry}
          className="px-4 py-2 bg-[#1B3A6B] text-white rounded-lg text-sm font-semibold hover:bg-[#2E5FA3] transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-[#1B3A6B] mb-1 leading-snug">
          {(story.root as Record<string, string>).headline}
        </h1>
        <p className="text-sm text-gray-400 mb-2">
          Source: {(story.root as Record<string, string>).outlet} · Job: {id}
        </p>
        <DriftLegend />

        {/* overflow-x-auto lets the tree scroll horizontally on narrow screens */}
        <div className="overflow-x-auto mt-6">
          <DriftTree treeData={story.tree} onNodeClick={setSelected} />
        </div>

        <DiffPanel node={selected} root={story.root} />
      </div>
    </ErrorBoundary>
  )
}

function SkeletonLoader({ message }: { message: string }) {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="animate-pulse space-y-4">
        <div className="h-7 bg-gray-200 rounded w-2/3" />
        <div className="h-4 bg-gray-100 rounded w-1/3" />
        <div className="h-4 bg-gray-100 rounded w-24" />
        <div className="h-80 bg-gray-100 rounded-lg mt-6" />
        <div className="h-40 bg-gray-100 rounded-lg" />
      </div>
      <p className="text-xs text-gray-400 text-center mt-6">{message}</p>
    </div>
  )
}
