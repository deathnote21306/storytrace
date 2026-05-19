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
      .style('cursor', 'pointer')
      .on('click', (event, d) => onNodeClick && onNodeClick(d.data))

    node
      .append('circle')
      .attr('r', 18)
      .attr('fill', d => driftColor(d.data.drift_score || 0))
      .attr('stroke', '#0b1326')
      .attr('stroke-width', 3)

    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#0b1326')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .attr('font-family', 'var(--font-jetbrains), monospace')
      .text(d => (d.data.drift_score !== undefined ? d.data.drift_score : ''))

    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '2.5em')
      .attr('fill', '#dae2fd')
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .attr('font-family', 'var(--font-hanken), sans-serif')
      .text(d => d.data.outlet || d.data.country || '')
  }, [treeData, onNodeClick])

  return (
    <div className="w-full min-w-[600px]">
      <svg ref={svgRef} width="100%" viewBox="0 0 900 600" className="block" />
    </div>
  )
}
