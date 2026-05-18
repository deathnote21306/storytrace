'use client'
import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

const driftColor = d3.scaleLinear()
  .domain([0, 50, 100])
  .range(['#27A06A', '#F59E0B', '#E8562A'])

export default function DriftTree({ treeData, onNodeClick }) {
  const svgRef = useRef()

  useEffect(() => {
    if (!treeData) return
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width  = 900
    const height = 600
    const margin = { top: 40, right: 40, bottom: 40, left: 40 }

    const root = d3.hierarchy(treeData)
    const treeLayout = d3.tree()
      .size([width - margin.left - margin.right, height - margin.top - margin.bottom])

    treeLayout(root)

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    g.selectAll('.link')
      .data(root.links())
      .join('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', '#CBD5E1')
      .attr('stroke-width', 2)
      .attr('d', d3.linkVertical()
        .x(d => d.x)
        .y(d => d.y))

    const node = g.selectAll('.node')
      .data(root.descendants())
      .join('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .style('cursor', 'pointer')
      .on('click', (event, d) => onNodeClick && onNodeClick(d.data))

    node.append('circle')
      .attr('r', 18)
      .attr('fill', d => driftColor(d.data.drift_score || 0))
      .attr('stroke', '#fff')
      .attr('stroke-width', 3)

    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#fff')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .text(d => d.data.drift_score !== undefined ? d.data.drift_score : '')

    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '2.5em')
      .attr('fill', '#1B3A6B')
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .text(d => d.data.outlet || d.data.country || '')

  }, [treeData])

  return (
    <div className="w-full overflow-x-auto bg-white rounded-lg shadow p-4">
      <svg ref={svgRef} width="100%" viewBox="0 0 900 600" />
    </div>
  )
}
