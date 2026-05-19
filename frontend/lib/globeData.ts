import { COUNTRY_COORDS } from './countryCoords'

export type DriftBand = 'low' | 'mid' | 'high'

export const DRIFT_COLORS: Record<DriftBand, string> = {
  low:  '#4edea3',
  mid:  '#ffb596',
  high: '#ffb4ab',
}

export function bandFor(score: number): DriftBand {
  if (score >= 67) return 'high'
  if (score >= 34) return 'mid'
  return 'low'
}

export type OutletNode = {
  id?: string
  outlet?: string
  country?: string
  headline?: string
  url?: string
  summary?: string
  drift_score?: number
  dna?: {
    facts_kept?: string[]
    facts_dropped?: string[]
    tone?: string
    framing?: string
    summary?: string
    political_lean?: string
  }
  type?: string
}

export type CountryBranch = {
  id?: string
  country: string
  type: 'country_branch'
  summary?: string
  drift_score: number
  children: OutletNode[]
}

type TreeShape = {
  children?: Array<Partial<CountryBranch> & { type?: string }>
}

export function extractCountryBranches(tree: TreeShape | null | undefined): CountryBranch[] {
  if (!tree?.children) return []
  return tree.children.filter(
    (c): c is CountryBranch => c.type === 'country_branch' && typeof c.country === 'string',
  )
}

export type GlobePoint = {
  country: string
  lat: number
  lng: number
  drift_score: number
  outletCount: number
  color: string
  branch: CountryBranch
}

export function buildGlobePoints(
  branches: CountryBranch[],
  filter: Set<DriftBand>,
): GlobePoint[] {
  const points: GlobePoint[] = []
  for (const branch of branches) {
    const coord = COUNTRY_COORDS[branch.country]
    if (!coord) continue
    const band = bandFor(branch.drift_score)
    if (!filter.has(band)) continue
    points.push({
      country: branch.country,
      lat:     coord.lat,
      lng:     coord.lng,
      drift_score: branch.drift_score,
      outletCount: branch.children?.length ?? 0,
      color:   DRIFT_COLORS[band],
      branch,
    })
  }
  return points
}

export function computeGlobeStats(branches: CountryBranch[]): {
  outletCount: number
  avgDrift: number
} {
  const outlets = branches.flatMap(b => b.children ?? [])
  if (outlets.length === 0) return { outletCount: 0, avgDrift: 0 }
  const sum = outlets.reduce((acc, o) => acc + (o.drift_score ?? 0), 0)
  return {
    outletCount: outlets.length,
    avgDrift:    Math.round((sum / outlets.length) * 10) / 10,
  }
}

export function pickInitialCountry(branches: CountryBranch[]): CountryBranch | null {
  if (branches.length === 0) return null
  return branches.reduce((max, b) => (b.drift_score > max.drift_score ? b : max), branches[0])
}
