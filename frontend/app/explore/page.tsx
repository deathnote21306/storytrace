'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'

type RecentStory = {
  job_id: string
  topic: string
  headline: string
  outlet: string
  created_at: string
}

export default function ExplorePage() {
  const [stories, setStories] = useState<RecentStory[] | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${apiUrl}/story/recent`)
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then(setStories)
      .catch(() => setError(true))
  }, [])

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-[#1B3A6B] mb-6">Recent Stories</h1>

      {stories === null && !error && (
        <ul className="space-y-3 animate-pulse">
          {[1, 2, 3].map(i => (
            <li key={i} className="h-16 bg-gray-100 rounded-lg" />
          ))}
        </ul>
      )}

      {error && (
        <p className="text-gray-400 text-sm text-center py-16">
          Could not load recent stories — make sure the API is running.
        </p>
      )}

      {stories?.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-16">
          No completed stories yet.{' '}
          <Link href="/" className="text-[#2E5FA3] underline">
            Trace one now →
          </Link>
        </p>
      )}

      {stories && stories.length > 0 && (
        <ul className="space-y-3">
          {stories.map(s => (
            <li key={s.job_id}>
              <Link
                href={`/story/${s.job_id}`}
                className="block bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-[#2E5FA3] hover:shadow-sm transition-all"
              >
                <p className="font-medium text-[#1B3A6B] text-sm leading-snug">
                  {s.headline || s.topic}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {s.outlet} · {new Date(s.created_at).toLocaleDateString()}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
