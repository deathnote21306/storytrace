'use client'
import { useState, use } from 'react'
import DriftTree from '@/components/DriftTree'
import DiffPanel from '@/components/DiffPanel'

const MOCK_TREE = {
  id: 'root',
  outlet: 'Reuters',
  country: 'US',
  headline: 'Iran nuclear talks progress',
  drift_score: 0,
  parent_id: null,
  type: 'root',
  dna: {
    facts_kept: ['partial withdrawal', 'Fordow facility', 'IAEA inspection'],
    facts_dropped: [],
    tone: 'neutral',
    framing: 'Diplomatic progress in nuclear negotiations',
    political_lean: 'center',
  },
  children: [
    {
      id: 'branch-UK',
      country: 'UK',
      type: 'country_branch',
      drift_score: 18,
      children: [
        {
          id: 'node-BBC',
          outlet: 'BBC',
          country: 'UK',
          headline: 'Iran steps back from nuclear site',
          drift_score: 18,
          parent_id: 'root',
          dna: {
            facts_kept: ['partial withdrawal', 'Fordow facility'],
            facts_dropped: ['IAEA inspection'],
            tone: 'neutral',
            framing: 'Diplomatic de-escalation',
            political_lean: 'center',
          },
          children: [],
        },
      ],
    },
    {
      id: 'branch-Russia',
      country: 'Russia',
      type: 'country_branch',
      drift_score: 74,
      children: [
        {
          id: 'node-RT',
          outlet: 'RT',
          country: 'Russia',
          headline: 'West forces Iran out of nuclear program',
          drift_score: 74,
          parent_id: 'root',
          dna: {
            facts_kept: ['Fordow facility'],
            facts_dropped: ['partial withdrawal', 'IAEA inspection'],
            tone: 'alarming',
            framing: 'Western coercion narrative',
            political_lean: 'far-left',
          },
          children: [],
        },
      ],
    },
  ],
}

export default function StoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null)

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-[#1B3A6B] mb-1">{MOCK_TREE.headline}</h1>
      <p className="text-sm text-gray-400 mb-6">Job: {id}</p>
      <DriftTree treeData={MOCK_TREE} onNodeClick={setSelected} />
      {selected && (
        <DiffPanel node={selected} root={MOCK_TREE} />
      )}
    </div>
  )
}
