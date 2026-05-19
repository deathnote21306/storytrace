'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getApiUrl } from '@/lib/apiUrl'

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
    getApiUrl()
      .then(apiUrl => fetch(`${apiUrl}/story/recent`))
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then(setStories)
      .catch(() => setError(true))
  }, [])

  return (
    <div className="max-w-3xl mx-auto px-4 md:px-10 py-8">
      <h1 className="text-2xl font-bold text-on-surface mb-6 flex items-center gap-3">
        <span className="material-symbols-outlined text-secondary">explore</span>
        Recent Stories
      </h1>

      {stories === null && !error && (
        <ul className="space-y-3">
          {[1, 2, 3].map(i => (
            <li key={i} className="h-16 rounded-xl skeleton-shimmer border border-outline-variant" />
          ))}
        </ul>
      )}

      {error && (
        <p className="text-outline text-sm text-center py-16">
          Could not load recent stories — make sure the API is running.
        </p>
      )}

      {stories?.length === 0 && (
        <p className="text-outline text-sm text-center py-16">
          No completed stories yet.{' '}
          <Link href="/" className="text-secondary hover:underline">
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
                className="block bg-surface-container border border-outline-variant rounded-xl px-4 py-3 hover:border-primary hover:bg-surface-container-high transition-all"
              >
                <p className="font-medium text-on-surface text-sm leading-snug">
                  {s.headline || s.topic}
                </p>
                <p className="text-xs font-mono text-outline mt-1">
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
