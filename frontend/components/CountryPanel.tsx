import type { CountryBranch, OutletNode } from '@/lib/globeData'
import { bandFor, DRIFT_COLORS } from '@/lib/globeData'

type Props = {
  branch: CountryBranch | null
}

const BAND_TEXT: Record<'low' | 'mid' | 'high', string> = {
  low:  'text-secondary',
  mid:  'text-tertiary',
  high: 'text-error',
}

const BAND_BORDER: Record<'low' | 'mid' | 'high', string> = {
  low:  'border-secondary',
  mid:  'border-tertiary',
  high: 'border-error',
}

const BAND_BAR: Record<'low' | 'mid' | 'high', string> = {
  low:  'bg-secondary',
  mid:  'bg-tertiary',
  high: 'bg-error',
}

// Placeholder string the legacy DNA extractor wrote when LLM extraction failed.
// Existing tree JSON in stories.tree may still contain it; treat as empty so the
// headline fallback fires.
const LEGACY_SUMMARY_PLACEHOLDER = 'Summary unavailable for this article.'

function cleanSummary(s?: string): string {
  const trimmed = s?.trim() ?? ''
  return trimmed === LEGACY_SUMMARY_PLACEHOLDER ? '' : trimmed
}

// Branch summaries are built by joining outlet entries ("Outlet: detail. ..."),
// so the placeholder may appear inline. Strip those fragments too.
function cleanBranchSummary(s?: string): string {
  if (!s) return ''
  const cleaned = s.replace(new RegExp(LEGACY_SUMMARY_PLACEHOLDER, 'g'), '').trim()
  return cleaned === '' ? '' : cleaned
}

export default function CountryPanel({ branch }: Props) {
  if (!branch) {
    return (
      <div className="bg-surface-container/70 backdrop-blur border border-outline-variant rounded-xl p-6 flex flex-col items-center justify-center text-center min-h-[600px]">
        <span className="material-symbols-outlined text-outline text-[48px]">public</span>
        <p className="mt-4 text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">
          Select a country
        </p>
        <p className="mt-2 text-xs text-outline max-w-xs">
          Click a pin on the globe to inspect outlet-level drift for that region.
        </p>
      </div>
    )
  }

  const band = bandFor(branch.drift_score)
  const outlets = (branch.children ?? []).slice().sort((a, b) => (b.drift_score ?? 0) - (a.drift_score ?? 0))

  return (
    <div className="bg-surface-container/70 backdrop-blur border border-outline-variant rounded-xl p-6 flex flex-col gap-6 min-h-[600px]">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-xl font-semibold text-on-surface truncate">{branch.country}</h3>
          <p className="text-[11px] font-mono uppercase tracking-wider text-outline mt-1">
            Regional Node Analysis
          </p>
        </div>
        <div className="text-right shrink-0">
          <div className={`text-2xl font-bold ${BAND_TEXT[band]}`}>{branch.drift_score}/100</div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-outline">
            Drift Score
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {outlets.length === 0 && (
          <p className="text-xs text-outline">No outlets recorded for this country.</p>
        )}
        {outlets.map((outlet, i) => (
          <OutletCard key={`${outlet.outlet ?? 'outlet'}-${i}`} outlet={outlet} />
        ))}
      </div>

      <div className="mt-auto pt-4 border-t border-outline-variant">
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-outline block mb-2">
          Narrative Summary
        </span>
        <p className="text-sm text-on-surface italic leading-relaxed">
          {cleanBranchSummary(branch.summary) || 'No summary available for this country.'}
        </p>
      </div>
    </div>
  )
}

function OutletCard({ outlet }: { outlet: OutletNode }) {
  const score = outlet.drift_score ?? 0
  const band = bandFor(score)
  // DNA summary is the canonical field; fall back to outlet.summary (older trees)
  // then headline if everything else is empty.
  const detail =
    cleanSummary(outlet.dna?.summary) ||
    cleanSummary(outlet.summary) ||
    outlet.headline?.trim() ||
    'Coverage captured with limited details.'
  const alignmentPct = Math.max(2, 100 - score)

  return (
    <div className={`p-4 border-l-2 ${BAND_BORDER[band]} bg-surface-container-lowest rounded-r`}>
      <div className="flex justify-between items-center mb-2 gap-3">
        <span className={`text-[11px] font-mono font-bold uppercase tracking-wider truncate ${BAND_TEXT[band]}`}>
          {outlet.outlet ?? 'Unknown'}
        </span>
        <span className="text-[11px] font-mono text-on-surface-variant shrink-0">
          Drift: {String(score).padStart(2, '0')}
        </span>
      </div>
      <p className="text-sm text-on-surface-variant mb-3 line-clamp-3">{detail}</p>
      <div className="w-full h-1 bg-surface-container-highest rounded-full overflow-hidden">
        <div
          className={`h-full ${BAND_BAR[band]}`}
          style={{ width: `${alignmentPct}%`, backgroundColor: DRIFT_COLORS[band] }}
        />
      </div>
      {outlet.url && (
        <a
          href={outlet.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-1 text-[10px] font-mono text-outline hover:text-secondary truncate max-w-full"
        >
          <span className="material-symbols-outlined text-[12px]">link</span>
          <span className="truncate">{outlet.url.replace(/^https?:\/\//, '')}</span>
        </a>
      )}
    </div>
  )
}
