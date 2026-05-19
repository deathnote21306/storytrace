'use client'
import { useState, useEffect, useMemo, use } from 'react'
import DriftTree from '@/components/DriftTree'
import DiffPanel from '@/components/DiffPanel'
import DriftLegend from '@/components/DriftLegend'
import ErrorBoundary from '@/components/ErrorBoundary'
import Globe from '@/components/Globe'
import CountryPanel from '@/components/CountryPanel'
import {
  extractCountryBranches,
  buildGlobePoints,
  computeGlobeStats,
  pickInitialCountry,
  type CountryBranch,
  type DriftBand,
} from '@/lib/globeData'

type TreeNode = {
  id?: string
  type?: 'root' | 'country_branch' | 'outlet'
  outlet?: string
  country?: string
  drift_score?: number
  headline?: string
  url?: string
  summary?: string
  parent_outlet?: string
  dna?: {
    facts_kept?: string[]
    facts_dropped?: string[]
    tone?: string
    framing?: string
    political_lean?: string
  }
  children?: TreeNode[]
}

type StoryState =
  | { status: 'processing'; message?: string }
  | { status: 'complete'; root: Record<string, unknown>; tree: TreeNode }
  | { status: 'error'; message: string }

function countOutlets(node: TreeNode | undefined): number {
  if (!node) return 0
  let count = node.outlet ? 1 : 0
  for (const child of node.children || []) {
    count += countOutlets(child)
  }
  return count
}

function collectLeaves(node: TreeNode, acc: TreeNode[] = []): TreeNode[] {
  const children = node.children || []
  if (children.length === 0 && node.outlet) {
    acc.push(node)
    return acc
  }
  for (const child of children) {
    collectLeaves(child, acc)
  }
  return acc
}

export default function StoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [story, setStory] = useState<StoryState | null>(null)
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
    return (
      <StorySkeleton
        message={story?.status === 'processing' ? story.message || 'Analyzing…' : 'Connecting…'}
      />
    )
  }

  if (story.status === 'error') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] gap-4 px-4 text-center">
        <span className="material-symbols-outlined text-error text-[48px]">error</span>
        <p className="text-error text-sm">{story.message}</p>
        <button
          onClick={retry}
          className="flex items-center gap-2 bg-primary-container text-on-primary-container px-6 py-3 rounded-lg text-[11px] font-mono font-bold uppercase tracking-wider hover:opacity-90 transition-opacity"
        >
          Retry
        </button>
      </div>
    )
  }

  const root = story.root as Record<string, string>
  const headline = root.headline || 'Story Analysis'
  const rootUrl = root.url || ''
  const outletCount = countOutlets(story.tree)
  const leaves = collectLeaves(story.tree)

  return (
    <ErrorBoundary>
      <StoryComplete
        id={id}
        story={story}
        headline={headline}
        rootUrl={rootUrl}
        root={root}
        outletCount={outletCount}
        leaves={leaves}
      />
    </ErrorBoundary>
  )
}

type CompleteState = { status: 'complete'; root: Record<string, unknown>; tree: TreeNode }

function StoryComplete({
  id,
  story,
  headline,
  rootUrl,
  root,
  outletCount,
  leaves,
}: {
  id: string
  story: CompleteState
  headline: string
  rootUrl: string
  root: Record<string, string>
  outletCount: number
  leaves: TreeNode[]
}) {
  const branches = useMemo<CountryBranch[]>(
    () => extractCountryBranches(story.tree as never),
    [story.tree],
  )
  const [filter, setFilter] = useState<Set<DriftBand>>(
    () => new Set<DriftBand>(['low', 'mid', 'high']),
  )
  const [selectedBranch, setSelectedBranch] = useState<CountryBranch | null>(
    () => pickInitialCountry(branches),
  )

  useEffect(() => {
    if (!selectedBranch && branches.length > 0) {
      setSelectedBranch(pickInitialCountry(branches))
    }
  }, [branches, selectedBranch])

  const points = useMemo(() => buildGlobePoints(branches, filter), [branches, filter])
  const stats = useMemo(() => computeGlobeStats(branches), [branches])

  function toggleBand(band: DriftBand) {
    setFilter(prev => {
      const next = new Set(prev)
      if (next.has(band)) next.delete(band)
      else next.add(band)
      return next
    })
  }

  const [selected, setSelected] = useState<TreeNode | null>(null)

  return (
    <ErrorBoundary>
      <div className="w-full min-h-[calc(100vh-4rem)] bg-background">
        <header className="bg-surface flex flex-col gap-2 px-4 md:px-10 py-6 border-b border-outline-variant">
          <div className="flex justify-between items-start gap-4">
            <div className="flex items-start gap-4 min-w-0">
              <span className="material-symbols-outlined text-secondary text-[32px] shrink-0">
                account_tree
              </span>
              <div className="min-w-0">
                <h1 className="text-xl md:text-2xl font-bold text-on-surface leading-snug truncate">
                  {headline}
                </h1>
                {rootUrl && (
                  <p className="text-sm text-outline flex items-center gap-2 mt-1 truncate">
                    <span className="material-symbols-outlined text-[14px] shrink-0">link</span>
                    <a
                      href={rootUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-secondary hover:underline truncate"
                    >
                      {rootUrl.replace(/^https?:\/\//, '')}
                    </a>
                  </p>
                )}
                <p className="text-[11px] font-mono text-outline mt-1">
                  Source: {root.outlet || 'Unknown'} · Job: {id.slice(0, 8)}…
                </p>
              </div>
            </div>
            <div className="flex gap-1 shrink-0">
              <IconButton icon="share" />
              <IconButton icon="bookmark" />
              <IconButton icon="code" />
            </div>
          </div>
        </header>

        <div className="px-4 md:px-10 w-full pb-12 pt-6 flex flex-col gap-10">
          {/* Globe section — drift by country */}
          <section className="flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-secondary text-[20px]">public</span>
                <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">
                  Active Trace: Regional Drift Map
                </span>
              </div>
              <TriageFilters filter={filter} onToggle={toggleBand} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-8 relative bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden canvas-bg">
                <div className="h-[600px] w-full">
                  <Globe
                    points={points}
                    onSelectCountry={setSelectedBranch}
                    selectedCountry={selectedBranch?.country ?? null}
                  />
                </div>
                <div className="absolute bottom-4 left-4 bg-surface-container/80 backdrop-blur border border-outline-variant rounded-xl p-4 flex flex-col gap-2 pointer-events-none">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-secondary text-[14px]">public</span>
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">
                      Outlets: {stats.outletCount}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-secondary text-[14px]">insights</span>
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">
                      Avg Drift: {stats.avgDrift}%
                    </span>
                  </div>
                </div>
              </div>

              <aside className="lg:col-span-4">
                <CountryPanel branch={selectedBranch} />
              </aside>
            </div>
          </section>

          {/* Tree section */}
          <div className="grid grid-cols-1 lg:grid-cols-10 gap-6">
            {/* Tree panel — 70% */}
            <section className="lg:col-span-7 flex flex-col gap-6">
              <div className="bg-surface-container-low border border-outline-variant rounded-xl overflow-hidden relative canvas-bg shadow-[0_0_0_1px_rgba(67,70,85,0.2)]">
                <div className="p-4 border-b border-outline-variant flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 bg-surface-container">
                  <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">
                    Narrative Mutation Trace: Wire-to-Outlet Map
                  </span>
                  <DriftLegend compact />
                </div>
                <div className="px-4 py-2 border-b border-outline-variant bg-surface-container-lowest">
                  <DriftLegend badges />
                </div>
                <div className="relative min-h-[500px] md:min-h-[700px] w-full overflow-x-auto p-4">
                  <DriftTree treeData={story.tree} onNodeClick={setSelected} />
                </div>
              </div>
            </section>

            {/* Side panel — 30% */}
            <aside className="lg:col-span-3 flex flex-col gap-6">
              <DiffPanel node={selected} root={story.root} />

              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <span className="material-symbols-outlined text-primary">public</span>
                  <h4 className="text-lg font-semibold text-on-surface">Distribution</h4>
                </div>
                <div className="aspect-video bg-surface-container-high rounded border border-outline-variant overflow-hidden relative canvas-bg">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-on-surface">{outletCount}</div>
                      <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-outline mt-1">
                        Outlets Linked
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-tertiary">history</span>
                    <h4 className="text-lg font-semibold text-on-surface">Trace Logs</h4>
                  </div>
                </div>
                <div className="space-y-3">
                  {leaves.slice(0, 5).map((leaf, i) => {
                    const score = leaf.drift_score ?? 0
                    const isHigh = score >= 67
                    const isMid = score >= 34 && score < 67
                    return (
                      <div
                        key={`${leaf.outlet}-${i}`}
                        className="flex flex-col font-mono text-sm py-2 border-b border-outline-variant/30"
                      >
                        <span className="text-outline text-[10px]">
                          {leaf.outlet} · drift {score}
                        </span>
                        <span
                          className={`mt-0.5 text-xs truncate ${
                            isHigh ? 'text-error' : isMid ? 'text-tertiary' : 'text-secondary'
                          }`}
                        >
                          {isHigh
                            ? `Alert: ${leaf.outlet} deviation ${score}%`
                            : `${leaf.outlet} verified (${score}% drift)`}
                        </span>
                      </div>
                    )
                  })}
                  <div className="flex flex-col font-mono text-sm py-2">
                    <span className="text-outline text-[10px]">Root</span>
                    <span className="text-primary mt-0.5 text-xs">
                      Source: {root.outlet || 'Wire'} — {headline.slice(0, 60)}
                      {headline.length > 60 ? '…' : ''}
                    </span>
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </div>
        <button
          type="button"
          className="fixed bottom-8 right-8 z-40 flex items-center gap-3 bg-secondary-container text-on-primary-container pl-6 pr-7 py-4 rounded-full shadow-2xl hover:scale-105 active:scale-95 transition-all"
          aria-label="Generate geopolitical forecast"
        >
          <span className="material-symbols-outlined">auto_awesome</span>
          <span className="text-[11px] font-mono font-bold uppercase tracking-widest">
            Generate Geopolitical Forecast
          </span>
        </button>
      </div>
    </ErrorBoundary>
  )
}

function TriageFilters({
  filter,
  onToggle,
}: {
  filter: Set<DriftBand>
  onToggle: (band: DriftBand) => void
}) {
  const bands: { band: DriftBand; label: string; dot: string; text: string }[] = [
    { band: 'low',  label: 'Low Drift',  dot: 'border-secondary', text: 'text-secondary' },
    { band: 'mid',  label: 'Mid Drift',  dot: 'border-tertiary',  text: 'text-tertiary' },
    { band: 'high', label: 'High Drift', dot: 'border-error',     text: 'text-error' },
  ]
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-outline mr-1">
        Technical Triage
      </span>
      {bands.map(b => {
        const active = filter.has(b.band)
        return (
          <button
            key={b.band}
            type="button"
            onClick={() => onToggle(b.band)}
            aria-pressed={active}
            className={`px-3 py-1.5 rounded-full border flex items-center gap-2 transition-all ${
              active
                ? 'border-outline bg-surface-variant'
                : 'border-outline-variant bg-surface-container opacity-50 hover:opacity-80'
            }`}
          >
            <span className={`w-2.5 h-2.5 rounded-full border-2 ${b.dot}`} />
            <span className={`text-[10px] font-mono font-bold uppercase tracking-wider ${active ? b.text : 'text-on-surface-variant'}`}>
              {b.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}

function IconButton({ icon }: { icon: string }) {
  return (
    <button
      type="button"
      className="p-2 text-outline hover:text-primary transition-colors"
      aria-label={icon}
    >
      <span className="material-symbols-outlined">{icon}</span>
    </button>
  )
}

function StorySkeleton({ message }: { message: string }) {
  return (
    <div className="w-full min-h-[calc(100vh-4rem)] bg-background">
      <header className="bg-surface px-4 md:px-10 py-6 border-b border-outline-variant">
        <div className="flex items-start gap-4">
          <div className="w-8 h-8 rounded skeleton-shimmer" />
          <div className="flex-1 space-y-3">
            <div className="h-7 w-2/3 rounded skeleton-shimmer" />
            <div className="h-4 w-1/2 rounded skeleton-shimmer" />
            <div className="h-3 w-1/3 rounded skeleton-shimmer" />
          </div>
        </div>
      </header>
      <div className="px-4 md:px-10 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-10 gap-6">
          <section className="lg:col-span-7">
            <div className="bg-surface-container-low border border-outline-variant rounded-xl overflow-hidden">
              <div className="p-4 border-b border-outline-variant h-12 skeleton-shimmer" />
              <div className="min-h-[500px] md:min-h-[700px] p-8 flex flex-col items-center justify-center canvas-bg">
                <div className="w-16 h-16 rounded-full bg-primary-container/20 border-4 border-primary-container flex items-center justify-center node-pulse">
                  <span className="material-symbols-outlined text-primary text-[32px] animate-spin">
                    progress_activity
                  </span>
                </div>
                <p className="mt-6 text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">
                  {message}
                </p>
                <p className="mt-2 text-xs text-outline">Crawling outlets · Extracting DNA · Scoring drift</p>
                <div className="w-full max-w-md mt-8 space-y-3">
                  <div className="h-3 rounded skeleton-shimmer w-full" />
                  <div className="h-3 rounded skeleton-shimmer w-4/5" />
                  <div className="h-3 rounded skeleton-shimmer w-3/5" />
                </div>
              </div>
            </div>
          </section>
          <aside className="lg:col-span-3 space-y-6">
            <div className="bg-surface-container border border-outline-variant rounded-xl p-6 space-y-4">
              <div className="h-6 w-1/2 rounded skeleton-shimmer" />
              <div className="h-20 rounded skeleton-shimmer" />
              <div className="h-20 rounded skeleton-shimmer" />
            </div>
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 h-40 skeleton-shimmer" />
          </aside>
        </div>
      </div>
    </div>
  )
}
