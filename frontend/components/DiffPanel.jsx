'use client'

function driftTextColor(score) {
  if (score >= 67) return 'text-error'
  if (score >= 34) return 'text-tertiary'
  return 'text-secondary'
}

export default function DiffPanel({ node, root }) {
  if (!node) {
    return (
      <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden flex flex-col">
        <div className="p-6 bg-surface-container-low border-b border-outline-variant text-center">
          <span className="material-symbols-outlined text-outline text-[32px]">touch_app</span>
          <p className="text-sm text-on-surface-variant mt-3">
            Click a node on the mutation tree to see forensic analysis
          </p>
        </div>
      </div>
    )
  }

  if (!node.dna) return null

  const rootFacts = new Set(root?.dna?.facts_kept || [])
  const nodeFacts = new Set(node.dna.facts_kept || [])
  const dropped = [...rootFacts].filter(f => !nodeFacts.has(f))
  const kept = [...nodeFacts].filter(f => rootFacts.has(f))
  const score = node.drift_score ?? 0
  const scoreColor = driftTextColor(score)
  const parentLabel = node.parent_outlet || root?.outlet || 'Wire'

  return (
    <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden flex flex-col">
      <div className="p-6 bg-surface-container-low border-b border-outline-variant">
        <div className="flex justify-between items-start mb-4 gap-4">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-on-surface truncate">
              {node.outlet} Analysis
            </h2>
            <p className="text-xs font-mono text-outline mt-1 truncate">
              Path:{' '}
              <span className="text-secondary">{parentLabel}</span>
              {' > '}
              <span className={scoreColor}>{node.outlet}</span>
            </p>
          </div>
          <div className="text-right shrink-0">
            <div className={`text-2xl font-bold leading-tight ${scoreColor}`}>
              {score}/100
            </div>
            <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-outline">
              Drift Score
            </div>
          </div>
        </div>

        {node.dna.framing && (
          <p className="text-sm text-on-surface-variant italic mb-4 leading-relaxed">
            {node.dna.framing}
          </p>
        )}

        <div className="flex flex-wrap gap-1.5">
          {node.dna.tone && (
            <Tag icon="psychology" label={node.dna.tone} />
          )}
          {node.dna.political_lean && (
            <Tag icon="balance" label={node.dna.political_lean} />
          )}
        </div>
      </div>

      <div className="p-6 space-y-6">
        <FactSection
          title="Facts Dropped"
          icon="remove_circle"
          colorClass="text-error"
          items={dropped}
          emptyLabel="None dropped"
          itemBg="bg-error-container/5 border-error/10 hover:bg-error-container/10"
          indexColor="text-error"
        />
        <FactSection
          title="Facts Kept"
          icon="check_circle"
          colorClass="text-secondary"
          items={kept}
          emptyLabel="None matched"
          itemBg="bg-secondary-container/5 border-secondary/10 hover:bg-secondary-container/10"
          indexColor="text-secondary"
        />
      </div>
    </div>
  )
}

function Tag({ icon, label }) {
  return (
    <span className="bg-surface-variant px-2 py-0.5 rounded text-[10px] font-mono text-on-surface-variant border border-outline-variant flex items-center gap-1">
      <span className="material-symbols-outlined text-[12px]">{icon}</span>
      {label}
    </span>
  )
}

function FactSection({ title, icon, colorClass, items, emptyLabel, itemBg, indexColor }) {
  return (
    <div>
      <h3 className={`text-[11px] font-mono font-bold uppercase tracking-wider ${colorClass} mb-3 flex items-center gap-2`}>
        <span className="material-symbols-outlined text-[16px]">{icon}</span>
        {title}
      </h3>
      <div className="space-y-2">
        {items.length === 0 ? (
          <p className="text-sm text-outline">{emptyLabel}</p>
        ) : (
          items.map((f, i) => (
            <div
              key={i}
              className={`p-2 border rounded flex gap-2 group transition-all ${itemBg}`}
            >
              <span className={`font-mono text-[10px] mt-0.5 ${indexColor}`}>
                {String(i + 1).padStart(2, '0')}
              </span>
              <p className="text-sm text-on-surface-variant text-[13px] leading-snug">{f}</p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
