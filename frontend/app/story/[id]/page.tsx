'use client'
import { useState, useEffect, use } from 'react'
import DriftTree from '@/components/DriftTree'
import DiffPanel from '@/components/DiffPanel'

type StoryState =
  | { status: 'processing'; progress?: number; message?: string }
  | { status: 'complete'; root: Record<string, unknown>; tree: Record<string, unknown> }
  | { status: 'error'; message: string }

export default function StoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [story, setStory] = useState<StoryState | null>(null)
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    let timer: ReturnType<typeof setTimeout>

    async function poll() {
      try {
        const res = await fetch(`${apiUrl}/story/${id}`)
        if (!res.ok) {
          setStory({ status: 'error', message: `Server error: ${res.status}` })
          return
        }
        const data = await res.json()
        setStory(data)
        if (data.status === 'processing') {
          timer = setTimeout(poll, 3000)
        }
      } catch {
        setStory({ status: 'error', message: 'Could not reach the API' })
      }
    }

    poll()
    return () => clearTimeout(timer)
  }, [id])

  if (!story) {
    return <Spinner message="Connecting…" />
  }

  if (story.status === 'processing') {
    return (
      <Spinner
        message={story.message || 'Analyzing…'}
        progress={story.progress}
      />
    )
  }

  if (story.status === 'error') {
    return (
      <div className="flex items-center justify-center min-h-[80vh] text-red-500">
        {story.message}
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-[#1B3A6B] mb-1">
        {(story.root as Record<string, string>).headline}
      </h1>
      <p className="text-sm text-gray-400 mb-6">
        Source: {(story.root as Record<string, string>).outlet} · Job: {id}
      </p>
      <DriftTree treeData={story.tree} onNodeClick={setSelected} />
      {selected && <DiffPanel node={selected} root={story.root} />}
    </div>
  )
}

function Spinner({ message, progress }: { message: string; progress?: number }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] gap-4 text-gray-500">
      <div className="w-10 h-10 border-4 border-[#1B3A6B] border-t-transparent rounded-full animate-spin" />
      <p className="text-sm">{message}</p>
      {progress !== undefined && (
        <p className="text-xs text-gray-400">Step {progress} / 7</p>
      )}
    </div>
  )
}
