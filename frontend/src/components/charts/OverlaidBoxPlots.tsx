import { useState, useEffect, useRef } from 'react'

export interface BoxPlotRun {
  min: number
  q25: number
  median: number
  q75: number
  max: number
  runNumber: number
}

const COLORS = [
  '#DC143C', '#228B22', '#1E90FF', '#FF8C00', '#9370DB', '#00CED1',
  '#FF1493', '#FFD700', '#8B4513', '#32CD32', '#000000'
]

interface OverlaidBoxPlotsProps {
  runs: BoxPlotRun[]
}

const OverlaidBoxPlots = ({ runs }: OverlaidBoxPlotsProps) => {
  const width = 600
  const height = 200
  const padding = 80
  const plotWidth = width - 2 * padding
  const plotHeight = height - 2 * padding

  const globalMin = Math.min(...runs.map(r => r.min))
  const globalMax = Math.max(...runs.map(r => r.max))
  const range = globalMax - globalMin || 1

  const scale = (value: number) => {
    if (range === 0) return padding + plotWidth / 2
    return ((value - globalMin) / range) * plotWidth + padding
  }

  const boxY = padding + plotHeight / 2 - 30
  const boxHeight = 60
  const whiskerY = boxY + boxHeight / 2

  const [hoveredRun, setHoveredRun] = useState<number | null>(null)
  const [selectedRun, setSelectedRun] = useState<number | null>(null)
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null)
  const legendRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (legendRef.current && !legendRef.current.contains(event.target as Node) && selectedRun !== null) {
        setSelectedRun(null)
      }
    }
    if (selectedRun !== null) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [selectedRun])

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }

  const handleLegendClick = (runNumber: number, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedRun(selectedRun === runNumber ? null : runNumber)
  }

  const orderedRuns = selectedRun != null
    ? [...runs].sort((a, b) => (a.runNumber === selectedRun ? 1 : 0) - (b.runNumber === selectedRun ? 1 : 0))
    : runs

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px 0', position: 'relative' }}>
      <svg
        width={width}
        height={height}
        style={{ border: '1px solid #e0e0e0', borderRadius: '6px', background: 'white' }}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => { setHoveredRun(null); setTooltipPos(null) }}
      >
        <line x1={padding} y1={whiskerY} x2={width - padding} y2={whiskerY} stroke="#000" strokeWidth="2" />
        {orderedRuns.map((run) => {
          const idx = runs.findIndex(r => r.runNumber === run.runNumber)
          const xMin = scale(run.min)
          const xQ25 = scale(run.q25)
          const xMedian = scale(run.median)
          const xQ75 = scale(run.q75)
          const xMax = scale(run.max)
          const color = COLORS[idx % COLORS.length]
          let opacity: number
          let strokeWidth: number
          if (selectedRun !== null) {
            opacity = selectedRun === run.runNumber ? 1 : 0.08
            strokeWidth = selectedRun === run.runNumber ? 3 : 2
          } else {
            opacity = hoveredRun === null ? 0.6 : (hoveredRun === run.runNumber ? 1 : 0.15)
            strokeWidth = hoveredRun === run.runNumber ? 3 : 2
          }
          return (
            <g key={run.runNumber} onMouseEnter={() => setHoveredRun(run.runNumber)} style={{ cursor: 'pointer' }}>
              <line x1={xMin} y1={whiskerY - 10} x2={xMin} y2={whiskerY + 10} stroke={color} strokeWidth={strokeWidth} opacity={opacity} />
              <line x1={xMin} y1={whiskerY} x2={xQ25} y2={whiskerY} stroke={color} strokeWidth={strokeWidth - 1} strokeDasharray="3,3" opacity={opacity} />
              <rect x={Math.min(xQ25, xQ75)} y={boxY} width={Math.abs(xQ75 - xQ25) || 2} height={boxHeight} fill={color} stroke={color} strokeWidth={strokeWidth} opacity={opacity} />
              <line x1={xMedian} y1={boxY} x2={xMedian} y2={boxY + boxHeight} stroke="#fff" strokeWidth={strokeWidth + 1} opacity={opacity} />
              <line x1={xMax} y1={whiskerY - 10} x2={xMax} y2={whiskerY + 10} stroke={color} strokeWidth={strokeWidth} opacity={opacity} />
              <line x1={xQ75} y1={whiskerY} x2={xMax} y2={whiskerY} stroke={color} strokeWidth={strokeWidth - 1} strokeDasharray="3,3" opacity={opacity} />
            </g>
          )
        })}
        <text x={padding} y={boxY + boxHeight + 25} textAnchor="start" fontSize="11" fill="#666" fontFamily="Courier New">Min: {globalMin.toFixed(4)}</text>
        <text x={width - padding} y={boxY + boxHeight + 25} textAnchor="end" fontSize="11" fill="#666" fontFamily="Courier New">Max: {globalMax.toFixed(4)}</text>
      </svg>

      {(hoveredRun !== null || selectedRun !== null) && tooltipPos && (() => {
        const runToShow = selectedRun !== null ? selectedRun : hoveredRun!
        const run = runs.find(r => r.runNumber === runToShow)
        if (!run) return null
        const tooltipX = Math.min(tooltipPos.x + 20, width - 200)
        const tooltipY = Math.max(tooltipPos.y - 100, 10)
        return (
          <div style={{ position: 'absolute', left: `${tooltipX}px`, top: `${tooltipY}px`, background: 'rgba(0, 0, 0, 0.9)', color: 'white', padding: '12px', borderRadius: '6px', fontSize: '12px', fontFamily: 'Courier New', pointerEvents: 'none', zIndex: 1000, boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)', minWidth: '180px' }}>
            <div style={{ fontWeight: 'bold', marginBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.3)', paddingBottom: '4px' }}>Run {run.runNumber}</div>
            <div style={{ marginBottom: '4px' }}>Min: {run.min.toFixed(4)}</div>
            <div style={{ marginBottom: '4px' }}>Q25: {run.q25.toFixed(4)}</div>
            <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>Median: {run.median.toFixed(4)}</div>
            <div style={{ marginBottom: '4px' }}>Q75: {run.q75.toFixed(4)}</div>
            <div>Max: {run.max.toFixed(4)}</div>
          </div>
        )
      })()}

      <div ref={legendRef} style={{ marginTop: '15px', display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'center' }}>
        {runs.map((run, idx) => {
          const color = COLORS[idx % COLORS.length]
          const isSelected = selectedRun === run.runNumber
          return (
            <label
              key={run.runNumber}
              onClick={(e) => handleLegendClick(run.runNumber, e)}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', userSelect: 'none', padding: '6px 12px', border: '2px solid #999', borderRadius: '4px', backgroundColor: isSelected ? '#000' : 'white', transition: 'all 0.2s', boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)' }}
              onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
              onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'; e.currentTarget.style.transform = 'translateY(0)' }}
            >
              <div style={{ width: '20px', height: '12px', background: color, border: '1px solid #000' }} />
              <span style={{ fontSize: '12px', fontFamily: 'Courier New', color: isSelected ? 'white' : '#000' }}>Run {run.runNumber}</span>
            </label>
          )
        })}
      </div>
    </div>
  )
}

export default OverlaidBoxPlots
