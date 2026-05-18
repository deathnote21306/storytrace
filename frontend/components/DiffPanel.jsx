'use client'

export default function DiffPanel({ node, root }) {
  if (!node || !node.dna) return null

  const rootFacts = new Set(root?.dna?.facts_kept || [])
  const nodeFacts = new Set(node.dna.facts_kept || [])
  const dropped   = [...rootFacts].filter(f => !nodeFacts.has(f))
  const kept      = [...nodeFacts].filter(f => rootFacts.has(f))

  return (
    <div className="bg-white rounded-lg shadow p-4 mt-4">
      <h3 className="font-bold text-lg text-[#1B3A6B] mb-3">
        {node.outlet} — Drift Score:{' '}
        <span style={{ color: node.drift_score > 70 ? '#E8562A' : '#27A06A' }}>
          {node.drift_score}/100
        </span>
      </h3>
      <p className="text-sm text-gray-500 mb-4 italic">{node.dna.framing}</p>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="font-semibold text-red-600 mb-2">Facts Dropped</h4>
          {dropped.length === 0
            ? <p className="text-sm text-gray-400">None dropped</p>
            : dropped.map((f, i) => (
                <div key={i} className="text-sm bg-red-50 text-red-700 px-2 py-1 rounded mb-1">{f}</div>
              ))
          }
        </div>
        <div>
          <h4 className="font-semibold text-green-600 mb-2">Facts Kept</h4>
          {kept.length === 0
            ? <p className="text-sm text-gray-400">None matched</p>
            : kept.map((f, i) => (
                <div key={i} className="text-sm bg-green-50 text-green-700 px-2 py-1 rounded mb-1">{f}</div>
              ))
          }
        </div>
      </div>
      <div className="mt-3 flex gap-4 text-sm">
        <span className="bg-gray-100 px-2 py-1 rounded">Tone: <strong>{node.dna.tone}</strong></span>
        <span className="bg-gray-100 px-2 py-1 rounded">Lean: <strong>{node.dna.political_lean}</strong></span>
      </div>
    </div>
  )
}
