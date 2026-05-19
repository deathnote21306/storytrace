type Props = {
  compact?: boolean
  badges?: boolean
}

export default function DriftLegend({ compact, badges }: Props) {
  if (badges) {
    return (
      <div className="flex flex-wrap gap-3 items-center">
        <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-outline border-r border-outline-variant pr-4 mr-1">
          Technical Triage
        </span>
        <Badge iconColor="text-secondary" label="Low Drift" active />
        <Badge iconColor="text-tertiary" label="Mid Drift" />
        <Badge iconColor="text-error" label="High Drift" />
      </div>
    )
  }

  if (compact) {
    return (
      <div className="flex flex-wrap gap-4">
        <LegendDot color="bg-secondary" label="0-33 Stable" />
        <LegendDot color="bg-tertiary" label="34-66 Drifted" />
        <LegendDot color="bg-error" label="67-100 Altered" />
      </div>
    )
  }

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-outline">
      <span className="font-mono font-bold uppercase tracking-wider">Drift score:</span>
      <LegendDot color="bg-secondary" label="Low (0–33)" />
      <LegendDot color="bg-tertiary" label="Mid (34–66)" />
      <LegendDot color="bg-error" label="High (67–100)" />
    </div>
  )
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 font-mono text-xs">
      <span className={`w-2 h-2 rounded-full ${color} inline-block`} />
      {label}
    </span>
  )
}

function Badge({
  iconColor,
  label,
  active,
}: {
  iconColor: string
  label: string
  active?: boolean
}) {
  return (
    <div
      className={`flex items-center gap-2 px-3 py-1 rounded-full cursor-default transition-all ${
        active
          ? 'bg-surface-variant'
          : 'bg-surface-container-high hover:bg-surface-variant'
      }`}
    >
      <span className={`material-symbols-outlined ${iconColor} text-[16px]`}>circle</span>
      <span
        className={`text-[10px] font-mono font-bold uppercase tracking-wider ${
          active ? 'text-on-surface' : 'text-on-surface-variant'
        }`}
      >
        {label}
      </span>
    </div>
  )
}
