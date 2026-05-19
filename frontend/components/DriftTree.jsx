'use client'
import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

const driftColor = d3.scaleLinear()
  .domain([0, 50, 100])
  .range(['#4edea3', '#ffb596', '#ffb4ab'])

export default function DriftTree({ treeData, onNodeClick }) {
  const svgRef = useRef()

  useEffect(() => {
    if (!treeData) return
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = 900
    const height = 600
    const margin = { top: 40, right: 40, bottom: 40, left: 40 }

    const root = d3.hierarchy(treeData)
    const treeLayout = d3
      .tree()
      .size([width - margin.left - margin.right, height - margin.top - margin.bottom])

    treeLayout(root)

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    g.selectAll('.link')
      .data(root.links())
      .join('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', '#434655')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '4')
      .attr('d', d3.linkVertical().x(d => d.x).y(d => d.y))

    const node = g
      .selectAll('.node')
      .data(root.descendants())
      .join('g')
      .attr('class', 'node drift-node')
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .style('cursor', d => (d.depth === 0 ? 'default' : 'pointer'))
      .on('click', (event, d) => {
        if (d.depth === 0) return
        onNodeClick && onNodeClick(d.data)
      })

    node
      .append('circle')
      .attr('r', d => {
        if (d.depth === 0) return 20
        if (d.data.type === 'country_branch') return 15
        return 12
      })
      .attr('fill', d => driftColor(d.data.drift_score || 0))
      .attr('stroke', '#0b1326')
      .attr('stroke-width', 3)
      .attr('opacity', d => (d.depth === 0 ? 0.95 : 1))

    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#0b1326')
      .attr('font-size', d => (d.depth === 0 ? '12px' : '9px'))
      .attr('font-weight', 'bold')
      .attr('font-family', 'var(--font-jetbrains), monospace')
      .text(d => {
        if (d.depth === 0) return 'R'
        return d.data.drift_score !== undefined ? d.data.drift_score : ''
      })

    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', d => (d.data.type === 'country_branch' ? '2.2em' : '2.5em'))
      .attr('fill', '#dae2fd')
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .attr('font-family', 'var(--font-hanken), sans-serif')
      .text(d => {
        if (d.depth === 0) return `WIRE: ${d.data.outlet || 'ROOT'}`
        return d.data.outlet || d.data.country || ''
      })

    node.append('title').text(d => {
      if (d.depth === 0) return d.data.headline || 'Root story'
      return d.data.summary || d.data.headline || d.data.outlet || d.data.country || 'Node'
    })
  }, [treeData, onNodeClick])

  return (
    <div className="w-full min-w-[600px]">
      <svg ref={svgRef} width="100%" viewBox="0 0 900 600" className="block" />
    </div>
  )
}
