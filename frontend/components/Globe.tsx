'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import type { GlobePoint } from '@/lib/globeData'

const GlobeGl = dynamic(() => import('react-globe.gl'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center text-outline text-[11px] font-mono uppercase tracking-wider">
      Loading globe…
    </div>
  ),
})

type Props = {
  points: GlobePoint[]
  onSelectCountry: (branch: GlobePoint['branch']) => void
  selectedCountry: string | null
}

export default function Globe({ points, onSelectCountry, selectedCountry }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const globeRef = useRef<{ controls: () => { autoRotate: boolean; autoRotateSpeed: number } } | null>(null)
  const [size, setSize] = useState<{ w: number; h: number }>({ w: 0, h: 0 })

  useEffect(() => {
    if (!containerRef.current) return
    const el = containerRef.current
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        setSize({ w: Math.round(width), h: Math.round(height) })
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    const g = globeRef.current
    if (!g) return
    const controls = g.controls()
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.6
  }, [size.w])

  useEffect(() => {
    if (!selectedCountry) return
    const target = points.find(p => p.country === selectedCountry)
    if (!target) return
    const g = globeRef.current as unknown as { pointOfView?: (v: { lat: number; lng: number; altitude: number }, ms?: number) => void } | null
    g?.pointOfView?.({ lat: target.lat, lng: target.lng, altitude: 1.8 }, 1200)
  }, [selectedCountry, points])

  const tooltipFor = useMemo(
    () => (p: object) => {
      const point = p as GlobePoint
      return `
        <div style="background:#171f33;border:1px solid #434655;padding:8px 10px;border-radius:6px;font-family:'JetBrains Mono',monospace;font-size:11px;color:#dae2fd;min-width:140px;">
          <div style="font-weight:700;color:${point.color};letter-spacing:0.05em;text-transform:uppercase;">${point.country}</div>
          <div style="margin-top:4px;">Drift: <b>${point.drift_score}</b>/100</div>
          <div>Outlets: <b>${point.outletCount}</b></div>
        </div>
      `
    },
    [],
  )

  return (
    <div ref={containerRef} className="w-full h-full">
      {size.w > 0 && size.h > 0 && (
        <GlobeGl
          ref={globeRef as never}
          width={size.w}
          height={size.h}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl="//cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
          atmosphereColor="#4edea3"
          atmosphereAltitude={0.18}
          pointsData={points}
          pointLat={(p: object) => (p as GlobePoint).lat}
          pointLng={(p: object) => (p as GlobePoint).lng}
          pointColor={(p: object) => (p as GlobePoint).color}
          pointAltitude={(p: object) => 0.04 + ((p as GlobePoint).drift_score / 100) * 0.35}
          pointRadius={(p: object) =>
            selectedCountry && (p as GlobePoint).country === selectedCountry ? 0.7 : 0.45
          }
          pointResolution={16}
          pointLabel={tooltipFor as never}
          onPointClick={(p: object) => onSelectCountry((p as GlobePoint).branch)}
        />
      )}
    </div>
  )
}
