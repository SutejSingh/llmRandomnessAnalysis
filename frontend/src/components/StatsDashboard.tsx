import { useState, useEffect, useRef } from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  AreaChart,
  Area
} from 'recharts'
import './StatsDashboard.css'

interface StatsDashboardProps {
  analysis: any
  allRuns?: number[][]
}

// Overlaid Box Plots Component for Multi-Run Analysis
const OverlaidBoxPlots = ({ runs }: { runs: Array<{ min: number; q25: number; median: number; q75: number; max: number; runNumber: number }> }) => {
  const width = 600
  const height = 200
  const padding = 80
  const plotWidth = width - 2 * padding
  const plotHeight = height - 2 * padding
  
  // Find global min and max across all runs for consistent scaling
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
  
  // Color palette for different runs - easily distinguishable colors (black is last, only used after other colors are exhausted)
  const colors = [
    '#DC143C', // Crimson Red
    '#228B22', // Forest Green
    '#1E90FF', // Dodger Blue
    '#FF8C00', // Dark Orange
    '#9370DB', // Medium Purple
    '#00CED1', // Dark Turquoise
    '#FF1493', // Deep Pink
    '#FFD700', // Gold
    '#8B4513', // Saddle Brown
    '#32CD32', // Lime Green
    '#000000'  // Black (last)
  ]
  
  const [hoveredRun, setHoveredRun] = useState<number | null>(null)
  const [selectedRun, setSelectedRun] = useState<number | null>(null)
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null)
  const legendRef = useRef<HTMLDivElement>(null)
  
  // Handle clicks outside the legend to deselect
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (legendRef.current && !legendRef.current.contains(event.target as Node) && selectedRun !== null) {
        setSelectedRun(null)
      }
    }
    
    if (selectedRun !== null) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [selectedRun])
  
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }
  
  const handleMouseLeave = () => {
    setHoveredRun(null)
    setTooltipPos(null)
  }
  
  const handleLegendClick = (runNumber: number, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent event from bubbling up
    // Toggle behavior: if clicking the same run, deselect it; otherwise select the new one
    setSelectedRun(selectedRun === runNumber ? null : runNumber)
  }
  
  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px 0', position: 'relative' }}>
      <svg 
        width={width} 
        height={height} 
        style={{ border: '1px solid #e0e0e0', borderRadius: '6px', background: 'white' }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        {/* Horizontal axis line */}
        <line x1={padding} y1={whiskerY} x2={width - padding} y2={whiskerY} stroke="#000" strokeWidth="2" />
        
        {/* Draw all box plots */}
        {runs.map((run, idx) => {
          const xMin = scale(run.min)
          const xQ25 = scale(run.q25)
          const xMedian = scale(run.median)
          const xQ75 = scale(run.q75)
          const xMax = scale(run.max)
          const color = colors[idx % colors.length]
          
          // Priority: selectedRun > hoveredRun > default
          let opacity: number
          let strokeWidth: number
          if (selectedRun !== null) {
            // If a run is selected, only highlight that one
            opacity = selectedRun === run.runNumber ? 1 : 0.2
            strokeWidth = selectedRun === run.runNumber ? 3 : 2
          } else {
            // If no run is selected, use hover behavior
            opacity = hoveredRun === null ? 0.6 : (hoveredRun === run.runNumber ? 1 : 0.2)
            strokeWidth = hoveredRun === run.runNumber ? 3 : 2
          }
          
          return (
            <g 
              key={run.runNumber}
              onMouseEnter={() => setHoveredRun(run.runNumber)}
              style={{ cursor: 'pointer' }}
            >
              {/* Left whisker (min to Q25) */}
              <line x1={xMin} y1={whiskerY - 10} x2={xMin} y2={whiskerY + 10} stroke={color} strokeWidth={strokeWidth} opacity={opacity} />
              <line x1={xMin} y1={whiskerY} x2={xQ25} y2={whiskerY} stroke={color} strokeWidth={strokeWidth - 1} strokeDasharray="3,3" opacity={opacity} />
              
              {/* Box (Q25 to Q75) */}
              <rect 
                x={Math.min(xQ25, xQ75)} 
                y={boxY} 
                width={Math.abs(xQ75 - xQ25) || 2} 
                height={boxHeight} 
                fill={color} 
                stroke={color} 
                strokeWidth={strokeWidth} 
                opacity={opacity}
              />
              
              {/* Median line */}
              <line x1={xMedian} y1={boxY} x2={xMedian} y2={boxY + boxHeight} stroke="#fff" strokeWidth={strokeWidth + 1} opacity={opacity} />
              
              {/* Right whisker (Q75 to max) */}
              <line x1={xMax} y1={whiskerY - 10} x2={xMax} y2={whiskerY + 10} stroke={color} strokeWidth={strokeWidth} opacity={opacity} />
              <line x1={xQ75} y1={whiskerY} x2={xMax} y2={whiskerY} stroke={color} strokeWidth={strokeWidth - 1} strokeDasharray="3,3" opacity={opacity} />
            </g>
          )
        })}
        
        {/* Labels */}
        <text x={padding} y={boxY + boxHeight + 25} textAnchor="start" fontSize="11" fill="#666" fontFamily="Courier New">
          Min: {globalMin.toFixed(4)}
        </text>
        <text x={width - padding} y={boxY + boxHeight + 25} textAnchor="end" fontSize="11" fill="#666" fontFamily="Courier New">
          Max: {globalMax.toFixed(4)}
        </text>
      </svg>
      
      {/* Tooltip */}
      {(hoveredRun !== null || selectedRun !== null) && tooltipPos && (() => {
        const runToShow = selectedRun !== null ? selectedRun : hoveredRun
        const run = runs.find(r => r.runNumber === runToShow)
        if (!run) return null
        
        // Calculate tooltip position relative to container
        const tooltipX = Math.min(tooltipPos.x + 20, width - 200)
        const tooltipY = Math.max(tooltipPos.y - 100, 10)
        
        return (
          <div
            style={{
              position: 'absolute',
              left: `${tooltipX}px`,
              top: `${tooltipY}px`,
              background: 'rgba(0, 0, 0, 0.9)',
              color: 'white',
              padding: '12px',
              borderRadius: '6px',
              fontSize: '12px',
              fontFamily: 'Courier New',
              pointerEvents: 'none',
              zIndex: 1000,
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
              minWidth: '180px'
            }}
          >
            <div style={{ fontWeight: 'bold', marginBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.3)', paddingBottom: '4px' }}>
              Run {run.runNumber}
            </div>
            <div style={{ marginBottom: '4px' }}>Min: {run.min.toFixed(4)}</div>
            <div style={{ marginBottom: '4px' }}>Q25: {run.q25.toFixed(4)}</div>
            <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>Median: {run.median.toFixed(4)}</div>
            <div style={{ marginBottom: '4px' }}>Q75: {run.q75.toFixed(4)}</div>
            <div>Max: {run.max.toFixed(4)}</div>
          </div>
        )
      })()}
      
      {/* Legend */}
      <div 
        ref={legendRef}
        style={{ marginTop: '15px', display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'center' }}
      >
        {runs.map((run, idx) => {
          const color = colors[idx % colors.length]
          const isSelected = selectedRun === run.runNumber
          return (
            <label
              key={run.runNumber}
              onClick={(e) => handleLegendClick(run.runNumber, e)}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                cursor: 'pointer',
                userSelect: 'none',
                padding: '6px 12px',
                border: '2px solid #999',
                borderRadius: '4px',
                backgroundColor: isSelected ? '#000' : 'white',
                transition: 'all 0.2s',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'
                e.currentTarget.style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
            >
              {/* Color box */}
              <div style={{ width: '20px', height: '12px', background: color, border: '1px solid #000' }}></div>
              <span style={{ 
                fontSize: '12px', 
                fontFamily: 'Courier New',
                color: isSelected ? 'white' : '#000'
              }}>Run {run.runNumber}</span>
            </label>
          )
        })}
      </div>
    </div>
  )
}

// Box Plot Component
const BoxPlot = ({ min, q25, median, q75, max }: { min: number; q25: number; median: number; q75: number; max: number }) => {
  const width = 600
  const height = 200
  const padding = 80
  const plotWidth = width - 2 * padding
  const plotHeight = height - 2 * padding
  
  // Normalize values to plot coordinates
  const range = max - min || 1 // Avoid division by zero
  const scale = (value: number) => {
    if (range === 0) return padding + plotWidth / 2
    return ((value - min) / range) * plotWidth + padding
  }
  
  const xMin = scale(min)
  const xQ25 = scale(q25)
  const xMedian = scale(median)
  const xQ75 = scale(q75)
  const xMax = scale(max)
  
  const boxY = padding + plotHeight / 2 - 30
  const boxHeight = 60
  const whiskerY = boxY + boxHeight / 2
  
  // Check if labels would overlap - use two rows if needed
  const minLabelX = Math.max(padding, xMin - 40)
  const q25LabelX = Math.max(xQ25 - 30, minLabelX + 80)
  const q75LabelX = Math.min(xQ75 + 30, width - padding - 80)
  const maxLabelX = Math.min(width - padding, xMax + 40)
  
  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px 0' }}>
      <svg width={width} height={height} style={{ border: '1px solid #e0e0e0', borderRadius: '6px', background: 'white' }}>
        {/* Horizontal axis line */}
        <line x1={padding} y1={whiskerY} x2={width - padding} y2={whiskerY} stroke="#000" strokeWidth="2" />
        
        {/* Left whisker (min to Q25) */}
        <line x1={xMin} y1={whiskerY - 10} x2={xMin} y2={whiskerY + 10} stroke="#000" strokeWidth="2" />
        <line x1={xMin} y1={whiskerY} x2={xQ25} y2={whiskerY} stroke="#000" strokeWidth="1" strokeDasharray="3,3" />
        
        {/* Box (Q25 to Q75) */}
        <rect x={Math.min(xQ25, xQ75)} y={boxY} width={Math.abs(xQ75 - xQ25) || 2} height={boxHeight} fill="#f0f0f0" stroke="#000" strokeWidth="2" />
        
        {/* Median line */}
        <line x1={xMedian} y1={boxY} x2={xMedian} y2={boxY + boxHeight} stroke="#000" strokeWidth="3" />
        
        {/* Right whisker (Q75 to max) */}
        <line x1={xMax} y1={whiskerY - 10} x2={xMax} y2={whiskerY + 10} stroke="#000" strokeWidth="2" />
        <line x1={xQ75} y1={whiskerY} x2={xMax} y2={whiskerY} stroke="#000" strokeWidth="1" strokeDasharray="3,3" />
        
        {/* Labels - first row (below plot) */}
        <text x={minLabelX} y={boxY + boxHeight + 25} textAnchor="middle" fontSize="11" fill="#666" fontFamily="Courier New">
          Min
        </text>
        <text x={q25LabelX} y={boxY + boxHeight + 25} textAnchor="middle" fontSize="11" fill="#666" fontFamily="Courier New">
          Q25
        </text>
        <text x={xMedian} y={boxY - 15} textAnchor="middle" fontSize="12" fill="#000" fontFamily="Courier New" fontWeight="bold">
          Median
        </text>
        <text x={q75LabelX} y={boxY + boxHeight + 25} textAnchor="middle" fontSize="11" fill="#666" fontFamily="Courier New">
          Q75
        </text>
        <text x={maxLabelX} y={boxY + boxHeight + 25} textAnchor="middle" fontSize="11" fill="#666" fontFamily="Courier New">
          Max
        </text>
        
        {/* Values - second row (further below) */}
        <text x={minLabelX} y={boxY + boxHeight + 40} textAnchor="middle" fontSize="10" fill="#666" fontFamily="Courier New">
          {min.toFixed(4)}
        </text>
        <text x={q25LabelX} y={boxY + boxHeight + 40} textAnchor="middle" fontSize="10" fill="#666" fontFamily="Courier New">
          {q25.toFixed(4)}
        </text>
        <text x={xMedian} y={boxY - 2} textAnchor="middle" fontSize="10" fill="#000" fontFamily="Courier New" fontWeight="bold">
          {median.toFixed(4)}
        </text>
        <text x={q75LabelX} y={boxY + boxHeight + 40} textAnchor="middle" fontSize="10" fill="#666" fontFamily="Courier New">
          {q75.toFixed(4)}
        </text>
        <text x={maxLabelX} y={boxY + boxHeight + 40} textAnchor="middle" fontSize="10" fill="#666" fontFamily="Courier New">
          {max.toFixed(4)}
        </text>
      </svg>
      
      {/* Text summary below the plot */}
      <div style={{ 
        marginTop: '20px', 
        padding: '15px', 
        background: '#f9f9f9', 
        borderRadius: '6px', 
        border: '1px solid #e0e0e0',
        width: '100%',
        maxWidth: width
      }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
          gap: '10px',
          fontFamily: 'Courier New',
          fontSize: '13px'
        }}>
          <div><strong>Minimum:</strong> {min.toFixed(4)}</div>
          <div><strong>First Quartile (Q25):</strong> {q25.toFixed(4)}</div>
          <div><strong>Median:</strong> {median.toFixed(4)}</div>
          <div><strong>Third Quartile (Q75):</strong> {q75.toFixed(4)}</div>
          <div><strong>Maximum:</strong> {max.toFixed(4)}</div>
        </div>
      </div>
    </div>
  )
}

const StatsDashboard = ({ analysis, allRuns = [] }: StatsDashboardProps) => {
  const isMultiRun = analysis && analysis.aggregate_stats !== undefined
  const [activeTab, setActiveTab] = useState(isMultiRun ? 'multi-run' : 'basic')
  const [selectedRun, setSelectedRun] = useState<number | null>(null)
  const [multiRunViewMode, setMultiRunViewMode] = useState<'multi-run' | 'per-run'>('multi-run')
  const [perRunTab, setPerRunTab] = useState('basic')
  const [isDownloadingPDF, setIsDownloadingPDF] = useState(false)
  
  // Sub-navigation state for each tab
  const [basicView, setBasicView] = useState<'stats' | 'histogram' | 'boxplot'>('stats')
  const [distributionView, setDistributionView] = useState<'tests' | 'kde' | 'qq'>('tests')
  const [rangeView, setRangeView] = useState<'boundary' | 'ecdf'>('boundary')
  const [independenceView, setIndependenceView] = useState<'timeseries' | 'acf' | 'lag1'>('timeseries')
  const [stationarityView, setStationarityView] = useState<'rolling' | 'chunks'>('rolling')
  const [spectralView, setSpectralView] = useState<'magnitude' | 'power'>('magnitude')
  const [overlaidView, setOverlaidView] = useState<'boxplot' | 'ecdf' | 'qq'>('boxplot')
  const [qqSelectedRun, setQqSelectedRun] = useState<number | null>(null)
  const qqLegendRef = useRef<HTMLDivElement>(null)
  const [ecdfSelectedRun, setEcdfSelectedRun] = useState<number | null>(null)
  const ecdfLegendRef = useRef<HTMLDivElement>(null)

  const API_BASE = 'http://localhost:8000'
  
  // Color palette for Q-Q plot and ECDF (same as box plot)
  const qqColors = [
    '#DC143C', // Crimson Red
    '#228B22', // Forest Green
    '#1E90FF', // Dodger Blue
    '#FF8C00', // Dark Orange
    '#9370DB', // Medium Purple
    '#00CED1', // Dark Turquoise
    '#FF1493', // Deep Pink
    '#FFD700', // Gold
    '#8B4513', // Saddle Brown
    '#32CD32', // Lime Green
    '#000000'  // Black (last)
  ]
  
  // Handle clicks outside Q-Q plot legend to deselect
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (qqLegendRef.current && !qqLegendRef.current.contains(event.target as Node) && qqSelectedRun !== null) {
        setQqSelectedRun(null)
      }
    }
    
    if (qqSelectedRun !== null) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [qqSelectedRun])
  
  // Handle clicks outside ECDF plot legend to deselect
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ecdfLegendRef.current && !ecdfLegendRef.current.contains(event.target as Node) && ecdfSelectedRun !== null) {
        setEcdfSelectedRun(null)
      }
    }
    
    if (ecdfSelectedRun !== null) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [ecdfSelectedRun])
  
  const handleQqLegendClick = (runNumber: number, e: React.MouseEvent) => {
    e.stopPropagation()
    // Toggle behavior: if clicking the same run, deselect it; otherwise select the new one
    setQqSelectedRun(qqSelectedRun === runNumber ? null : runNumber)
  }
  
  const handleEcdfLegendClick = (runNumber: number, e: React.MouseEvent) => {
    e.stopPropagation()
    // Toggle behavior: if clicking the same run, deselect it; otherwise select the new one
    setEcdfSelectedRun(ecdfSelectedRun === runNumber ? null : runNumber)
  }

  const handleDownloadCSV = () => {
    let runsToDownload = allRuns
    
    if (runsToDownload.length === 0) {
      // Fallback: try to get runs from analysis
      if (analysis.individual_analyses && analysis.individual_analyses.length > 0) {
        runsToDownload = analysis.individual_analyses.map((a: any) => a.raw_data || [])
      }
      // If still no data, try single run
      if (runsToDownload.length === 0 && analysis.raw_data) {
        runsToDownload = [analysis.raw_data]
      }
    }
    
    if (runsToDownload.length === 0) {
      alert('No data available to download')
      return
    }
    
    const runsJson = encodeURIComponent(JSON.stringify(runsToDownload))
    const provider = analysis.provider || 'manual'
    window.open(`${API_BASE}/download/csv?runs=${runsJson}&provider=${provider}`, '_blank')
  }

  const handleDownloadXLSX = async () => {
    let runsToDownload = allRuns
    
    if (runsToDownload.length === 0) {
      // Fallback: try to get runs from analysis
      if (analysis.individual_analyses && analysis.individual_analyses.length > 0) {
        runsToDownload = analysis.individual_analyses.map((a: any) => a.raw_data || [])
      }
      // If still no data, try single run
      if (runsToDownload.length === 0 && analysis.raw_data) {
        runsToDownload = [analysis.raw_data]
      }
    }
    
    if (runsToDownload.length === 0) {
      alert('No data available to download')
      return
    }
    
    try {
      const response = await fetch(`${API_BASE}/download/xlsx`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis: analysis,
          runs: runsToDownload
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `analysis_report_${analysis.provider || 'unknown'}_${new Date().toISOString().replace(/[:.]/g, '-')}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading XLSX:', error)
      alert('Error downloading Excel file. Please try again.')
    }
  }

  const handleDownloadPDF = async () => {
    let runsToDownload = allRuns
    
    if (runsToDownload.length === 0) {
      // Fallback: try to get runs from analysis
      if (analysis.individual_analyses && analysis.individual_analyses.length > 0) {
        runsToDownload = analysis.individual_analyses.map((a: any) => a.raw_data || [])
      }
      // If still no data, try single run
      if (runsToDownload.length === 0 && analysis.raw_data) {
        runsToDownload = [analysis.raw_data]
      }
    }
    
    if (runsToDownload.length === 0) {
      alert('No data available to download')
      return
    }
    
    setIsDownloadingPDF(true)
    try {
      const response = await fetch(`${API_BASE}/download/pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis: analysis,
          runs: runsToDownload
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `analysis_report_${analysis.provider || 'unknown'}_${new Date().toISOString().replace(/[:.]/g, '-')}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading PDF:', error)
      alert('Error downloading PDF file. Please try again.')
    } finally {
      setIsDownloadingPDF(false)
    }
  }

  if (!analysis) return null

  // Prepare histogram data (only if distribution exists)
  const histogramData = analysis.distribution?.histogram?.edges?.slice(0, -1).map((edge: number, idx: number) => ({
    bin: edge.toFixed(4),
    count: analysis.distribution.histogram.counts[idx]
  })) || []

  // Prepare KDE data
  const kdeData = analysis.distribution?.kde?.x?.map((x: number, idx: number) => ({
    x: x,
    y: analysis.distribution.kde.y[idx]
  })) || []

  // Prepare Q-Q plot data
  const qqData = analysis.distribution?.qq_plot?.sample?.map((sample: number, idx: number) => ({
    sample: sample,
    theoretical: analysis.distribution.qq_plot.theoretical[idx]
  })) || []

  // Prepare ACF data
  const acfData = analysis.independence?.autocorrelation?.lags?.map((lag: number, idx: number) => ({
    lag: lag,
    correlation: analysis.independence.autocorrelation.values[idx]
  })) || []

  // Prepare lag-1 scatter data
  const lag1Data = analysis.independence?.lag1_scatter?.x?.map((x: number, idx: number) => ({
    x: x,
    y: analysis.independence.lag1_scatter.y[idx]
  })) || []

  // Prepare time series data
  const timeSeriesData = analysis.independence?.time_series?.index?.map((idx: number) => ({
    index: idx,
    value: analysis.independence.time_series.values[idx]
  })) || []

  // Prepare rolling stats data
  const rollingData = analysis.stationarity?.rolling_mean?.index?.map((idx: number) => ({
    index: idx,
    mean: analysis.stationarity.rolling_mean.values[idx],
    std: analysis.stationarity.rolling_std.values[idx]
  })) || []

  // Prepare ECDF data
  const ecdfData = analysis.range_behavior?.ecdf?.x?.map((x: number, idx: number) => ({
    x: x,
    y: analysis.range_behavior.ecdf.y[idx]
  })) || []

  // Prepare spectral data
  const spectralData = analysis.spectral?.frequencies?.map((freq: number, idx: number) => ({
    frequency: freq,
    magnitude: analysis.spectral.magnitude[idx],
    power: analysis.spectral.power[idx]
  })) || []

  return (
    <div className="stats-dashboard">
      <div className="dashboard-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h2>Statistical Analysis</h2>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleDownloadCSV}
              style={{
                padding: '10px 20px',
                backgroundColor: '#000',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
              title="Download raw numbers as CSV"
            >
              <span>📥</span>
              <span>Download CSV</span>
            </button>
            <button
              onClick={handleDownloadXLSX}
              style={{
                padding: '10px 20px',
                backgroundColor: '#000',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
              title="Download full analysis report as XLSX"
            >
              <span>📊</span>
              <span>Download XLSX</span>
            </button>
            <button
              onClick={handleDownloadPDF}
              disabled={isDownloadingPDF}
              style={{
                padding: '10px 20px',
                backgroundColor: isDownloadingPDF ? '#999' : '#c41e3a',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: isDownloadingPDF ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                opacity: isDownloadingPDF ? 0.7 : 1
              }}
              title={isDownloadingPDF ? "Preparing PDF..." : "Download full analysis report as PDF"}
            >
              {isDownloadingPDF ? (
                <>
                  <span style={{
                    display: 'inline-block',
                    width: '16px',
                    height: '16px',
                    border: '2px solid #fff',
                    borderTop: '2px solid transparent',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite'
                  }}></span>
                  <span>Preparing PDF...</span>
                </>
              ) : (
                <>
                  <span>📄</span>
                  <span>Download PDF</span>
                </>
              )}
            </button>
          </div>
        </div>
        <div className="tab-buttons">
          {isMultiRun && (
            <div style={{ 
              display: 'flex', 
              gap: '0', 
              marginBottom: '10px',
              border: '2px solid #000',
              borderRadius: '6px',
              overflow: 'hidden',
              width: 'fit-content'
            }}>
              <label style={{ 
                display: 'flex', 
                alignItems: 'center', 
                cursor: 'pointer',
                margin: 0,
                padding: 0
              }}>
                <input
                  type="radio"
                  name="multiRunView"
                  value="multi-run"
                  checked={multiRunViewMode === 'multi-run'}
                  onChange={(e) => setMultiRunViewMode(e.target.value as 'multi-run' | 'per-run')}
                  style={{ 
                    position: 'absolute',
                    opacity: 0,
                    width: 0,
                    height: 0
                  }}
                />
                <button
                  type="button"
                  onClick={() => setMultiRunViewMode('multi-run')}
                  className={multiRunViewMode === 'multi-run' ? 'active' : ''}
                  style={{ 
                    cursor: 'pointer',
                    borderRadius: 0,
                    borderRight: '1px solid #000',
                    margin: 0
                  }}
                >
                  Multi-Run Analysis
                </button>
              </label>
              <label style={{ 
                display: 'flex', 
                alignItems: 'center', 
                cursor: 'pointer',
                margin: 0,
                padding: 0
              }}>
                <input
                  type="radio"
                  name="multiRunView"
                  value="per-run"
                  checked={multiRunViewMode === 'per-run'}
                  onChange={(e) => setMultiRunViewMode(e.target.value as 'multi-run' | 'per-run')}
                  style={{ 
                    position: 'absolute',
                    opacity: 0,
                    width: 0,
                    height: 0
                  }}
                />
                <button
                  type="button"
                  onClick={() => setMultiRunViewMode('per-run')}
                  className={multiRunViewMode === 'per-run' ? 'active' : ''}
                  style={{ 
                    cursor: 'pointer',
                    borderRadius: 0,
                    margin: 0
                  }}
                >
                  Per-Run Analysis
                </button>
              </label>
            </div>
          )}
          {!isMultiRun && ['basic', 'distribution', 'range', 'independence', 'stationarity', 'spectral', 'nist'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={activeTab === tab ? 'active' : ''}
            >
              {tab === 'nist' ? 'NIST Tests' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'basic' && analysis.basic_stats && (
        <div className="stats-section">
          <h3>Basic Descriptive Statistics</h3>
          
          {/* Navigation buttons */}
          <div className="sub-nav-buttons">
            <button
              onClick={() => setBasicView('stats')}
              className={basicView === 'stats' ? 'active' : ''}
            >
              Statistics
            </button>
            <button
              onClick={() => setBasicView('histogram')}
              className={basicView === 'histogram' ? 'active' : ''}
            >
              Histogram
            </button>
            <button
              onClick={() => setBasicView('boxplot')}
              className={basicView === 'boxplot' ? 'active' : ''}
            >
              Box Plot
            </button>
          </div>

          {basicView === 'stats' && (
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Mean</div>
                <div className="stat-value">{analysis.basic_stats.mean.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Median</div>
                <div className="stat-value">{analysis.basic_stats.median.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Std Dev</div>
                <div className="stat-value">{analysis.basic_stats.std.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Variance</div>
                <div className="stat-value">{analysis.basic_stats.variance.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Min</div>
                <div className="stat-value">{analysis.basic_stats.min.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Max</div>
                <div className="stat-value">{analysis.basic_stats.max.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Q25</div>
                <div className="stat-value">{analysis.basic_stats.q25.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Q75</div>
                <div className="stat-value">{analysis.basic_stats.q75.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Q95</div>
                <div className="stat-value">{analysis.basic_stats.q95.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Skewness</div>
                <div className="stat-value">{analysis.basic_stats.skewness.toFixed(4)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Kurtosis</div>
                <div className="stat-value">{analysis.basic_stats.kurtosis.toFixed(4)}</div>
              </div>
            </div>
          )}

          {basicView === 'histogram' && (
            <div className="chart-container">
              <h4>Histogram</h4>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={histogramData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="bin" angle={-45} textAnchor="end" height={80} tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#000" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {basicView === 'boxplot' && (
            <div className="chart-container">
              <h4>Box Plot</h4>
              <BoxPlot
                min={analysis.basic_stats.min}
                q25={analysis.basic_stats.q25}
                median={analysis.basic_stats.median}
                q75={analysis.basic_stats.q75}
                max={analysis.basic_stats.max}
              />
            </div>
          )}
        </div>
      )}

      {activeTab === 'distribution' && analysis.distribution && (
        <div className="stats-section">
          <h3>Distribution Shape Analysis</h3>
          
          {/* Navigation buttons */}
          <div className="sub-nav-buttons">
            <button
              onClick={() => setDistributionView('tests')}
              className={distributionView === 'tests' ? 'active' : ''}
            >
              Tests
            </button>
            <button
              onClick={() => setDistributionView('kde')}
              className={distributionView === 'kde' ? 'active' : ''}
            >
              KDE
            </button>
            <button
              onClick={() => setDistributionView('qq')}
              className={distributionView === 'qq' ? 'active' : ''}
            >
              Q-Q Plot
            </button>
          </div>

          {distributionView === 'tests' && (
            <div className="test-results">
              <div className="test-card">
                <h4>Uniformity Test</h4>
                <p>Kolmogorov-Smirnov: p = {analysis.distribution.is_uniform.ks_p.toFixed(4)}</p>
                <p className={analysis.distribution.is_uniform.ks_p > 0.05 ? 'pass' : 'fail'}>
                  {analysis.distribution.is_uniform.ks_p > 0.05 ? '✓ Likely Uniform' : '✗ Not Uniform'}
                </p>
              </div>
            </div>
          )}

          {distributionView === 'kde' && (
            <div className="chart-container">
              <h4>Kernel Density Estimate (KDE)</h4>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={kdeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="x" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="y" stroke="#000" fill="#000" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {distributionView === 'qq' && (
            <div className="chart-container">
              <h4>Q-Q Plot (Uniform Distribution)</h4>
              <ResponsiveContainer width="100%" height={250}>
                <ScatterChart data={qqData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="theoretical" name="Theoretical" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis dataKey="sample" name="Sample" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter name="Q-Q" dataKey="sample" fill="#000" />
                </ScatterChart>
              </ResponsiveContainer>
              <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
                Points should lie along the diagonal line if uniformly distributed
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'range' && analysis.range_behavior && (
        <div className="stats-section">
          <h3>Range & Boundary Behavior</h3>
          
          {/* Navigation buttons */}
          <div className="sub-nav-buttons">
            <button
              onClick={() => setRangeView('boundary')}
              className={rangeView === 'boundary' ? 'active' : ''}
            >
              Boundary Stats
            </button>
            <button
              onClick={() => setRangeView('ecdf')}
              className={rangeView === 'ecdf' ? 'active' : ''}
            >
              ECDF
            </button>
          </div>

          {rangeView === 'boundary' && (
            <div className="boundary-info">
              <div className="info-card">
                <h4>Boundary Statistics</h4>
                <p>Min: {analysis.range_behavior.boundaries.min.toFixed(4)}</p>
                <p>Max: {analysis.range_behavior.boundaries.max.toFixed(4)}</p>
                <p>Near Min: {analysis.range_behavior.boundaries.near_min_count} ({analysis.range_behavior.boundaries.near_min_pct.toFixed(4)}%)</p>
                <p>Near Max: {analysis.range_behavior.boundaries.near_max_count} ({analysis.range_behavior.boundaries.near_max_pct.toFixed(4)}%)</p>
              </div>
            </div>
          )}

          {rangeView === 'ecdf' && (
            <div className="chart-container">
              <h4>Empirical Cumulative Distribution Function (ECDF)</h4>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={ecdfData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="x" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="y" stroke="#000" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {activeTab === 'independence' && analysis.independence && (
        <div className="stats-section">
          <h3>Independence & Correlation Analysis</h3>

          {/* Navigation buttons */}
          <div className="sub-nav-buttons">
            <button
              onClick={() => setIndependenceView('timeseries')}
              className={independenceView === 'timeseries' ? 'active' : ''}
            >
              Time Series
            </button>
            <button
              onClick={() => setIndependenceView('acf')}
              className={independenceView === 'acf' ? 'active' : ''}
            >
              ACF
            </button>
            <button
              onClick={() => setIndependenceView('lag1')}
              className={independenceView === 'lag1' ? 'active' : ''}
            >
              Lag-1 Scatter
            </button>
          </div>

          {independenceView === 'timeseries' && (
            <div className="chart-container">
              <h4>Time Series</h4>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="index" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#000" strokeWidth={1} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {independenceView === 'acf' && (
            <div className="chart-container">
              <h4>Autocorrelation Function (ACF)</h4>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={acfData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="lag" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis domain={[-1, 1]} />
                  <Tooltip />
                  <Bar dataKey="correlation" fill="#000" />
                </BarChart>
              </ResponsiveContainer>
              <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
                Values near zero indicate independence. Significant peaks suggest correlation.
              </p>
            </div>
          )}

          {independenceView === 'lag1' && (
            <div className="chart-container">
              <h4>Lag-1 Scatter Plot</h4>
              <ResponsiveContainer width="100%" height={250}>
                <ScatterChart data={lag1Data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="x" name="x_n" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis dataKey="y" name="x_{n+1}" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter name="Lag-1" dataKey="y" fill="#000" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {activeTab === 'stationarity' && analysis.stationarity && (
        <div className="stats-section">
          <h3>Stationarity Analysis</h3>

          {/* Navigation buttons */}
          <div className="sub-nav-buttons">
            <button
              onClick={() => setStationarityView('rolling')}
              className={stationarityView === 'rolling' ? 'active' : ''}
            >
              Rolling Stats
            </button>
            <button
              onClick={() => setStationarityView('chunks')}
              className={stationarityView === 'chunks' ? 'active' : ''}
            >
              Chunks
            </button>
          </div>

          {stationarityView === 'rolling' && (
            <div className="chart-container">
              <h4>Rolling Mean & Standard Deviation</h4>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={rollingData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="index" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="mean" stroke="#000" strokeWidth={2} name="Rolling Mean" />
                  <Line yAxisId="right" type="monotone" dataKey="std" stroke="#666" strokeWidth={2} name="Rolling Std" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {stationarityView === 'chunks' && (
            <div className="chunks-container">
              <h4>Chunked Statistics</h4>
              <div className="chunks-grid">
                {analysis.stationarity.chunks.map((chunk: any) => (
                  <div key={chunk.chunk} className="chunk-card">
                    <h5>Chunk {chunk.chunk}</h5>
                    <p>Mean: {chunk.mean.toFixed(4)}</p>
                    <p>Std: {chunk.std.toFixed(4)}</p>
                    <p>Min: {chunk.min.toFixed(4)}</p>
                    <p>Max: {chunk.max.toFixed(4)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'spectral' && analysis.spectral && (
        <div className="stats-section">
          <h3>Spectral Analysis</h3>

          {/* Navigation buttons */}
          <div className="sub-nav-buttons">
            <button
              onClick={() => setSpectralView('magnitude')}
              className={spectralView === 'magnitude' ? 'active' : ''}
            >
              FFT Magnitude
            </button>
            <button
              onClick={() => setSpectralView('power')}
              className={spectralView === 'power' ? 'active' : ''}
            >
              Power Spectrum
            </button>
          </div>

          {spectralView === 'magnitude' && (
            <div className="chart-container">
              <h4>FFT Magnitude</h4>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={spectralData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="frequency" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="magnitude" stroke="#000" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {spectralView === 'power' && (
            <div className="chart-container">
              <h4>Power Spectrum (Periodogram)</h4>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={spectralData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="frequency" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="power" stroke="#666" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {activeTab === 'nist' && analysis.nist_tests && (
        <div className="stats-section">
          <h3>NIST Statistical Tests</h3>
          <p style={{ marginBottom: '20px', color: '#666', fontSize: '14px' }}>
            Tests performed on binary representation of numbers (IEEE 754 double precision)
          </p>

          {/* Display all 4 tests in a row */}
          <div className="nist-tests-grid">
            {/* Runs Test */}
            <div className="test-card">
              <h4>Runs Test</h4>
              {analysis.nist_tests.runs_test.error ? (
                <p className="fail">Error: {analysis.nist_tests.runs_test.error}</p>
              ) : (
                <>
                  <table className="test-results-table">
                    <tbody>
                      <tr>
                        <td>P-value</td>
                        <td>{analysis.nist_tests.runs_test.p_value?.toFixed(6) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Z-statistic</td>
                        <td>{analysis.nist_tests.runs_test.statistic?.toFixed(4) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Runs observed</td>
                        <td>{analysis.nist_tests.runs_test.runs || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Runs expected</td>
                        <td>{analysis.nist_tests.runs_test.expected_runs?.toFixed(4) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Ones</td>
                        <td>{analysis.nist_tests.runs_test.ones || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Zeros</td>
                        <td>{analysis.nist_tests.runs_test.zeros || 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                  <p className={analysis.nist_tests.runs_test.passed ? 'pass' : 'fail'}>
                    {analysis.nist_tests.runs_test.passed ? '✓ Test Passed (p > 0.01)' : '✗ Test Failed (p ≤ 0.01)'}
                  </p>
                </>
              )}
            </div>

            {/* Binary Matrix Rank Test */}
            <div className="test-card">
              <h4>Binary Matrix Rank Test</h4>
              {analysis.nist_tests.binary_matrix_rank_test.error ? (
                <p className="fail">Error: {analysis.nist_tests.binary_matrix_rank_test.error}</p>
              ) : (
                <>
                  <table className="test-results-table">
                    <tbody>
                      <tr>
                        <td>P-value</td>
                        <td>{analysis.nist_tests.binary_matrix_rank_test.p_value?.toFixed(6) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Chi-square statistic</td>
                        <td>{analysis.nist_tests.binary_matrix_rank_test.statistic?.toFixed(4) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Number of matrices</td>
                        <td>{analysis.nist_tests.binary_matrix_rank_test.num_matrices || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Full rank count</td>
                        <td>{analysis.nist_tests.binary_matrix_rank_test.full_rank_count || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Rank-1 count</td>
                        <td>{analysis.nist_tests.binary_matrix_rank_test.rank_minus_1_count || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Rank-0 count</td>
                        <td>{analysis.nist_tests.binary_matrix_rank_test.rank_0_count || 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                  <p className={analysis.nist_tests.binary_matrix_rank_test.passed ? 'pass' : 'fail'}>
                    {analysis.nist_tests.binary_matrix_rank_test.passed ? '✓ Test Passed (p > 0.01)' : '✗ Test Failed (p ≤ 0.01)'}
                  </p>
                </>
              )}
            </div>

            {/* Longest Run of Ones Test */}
            <div className="test-card">
              <h4>Longest Run of Ones Test</h4>
              {analysis.nist_tests.longest_run_of_ones_test.error ? (
                <p className="fail">Error: {analysis.nist_tests.longest_run_of_ones_test.error}</p>
              ) : (
                <>
                  <table className="test-results-table">
                    <tbody>
                      <tr>
                        <td>P-value</td>
                        <td>{analysis.nist_tests.longest_run_of_ones_test.p_value?.toFixed(6) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Chi-square statistic</td>
                        <td>{analysis.nist_tests.longest_run_of_ones_test.statistic?.toFixed(4) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Number of blocks</td>
                        <td>{analysis.nist_tests.longest_run_of_ones_test.num_blocks || 'N/A'}</td>
                      </tr>
                      {analysis.nist_tests.longest_run_of_ones_test.run_counts && Object.entries(analysis.nist_tests.longest_run_of_ones_test.run_counts).map(([length, count]: [string, any]) => (
                        <tr key={length}>
                          <td>Length ≤{length}</td>
                          <td>{count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className={analysis.nist_tests.longest_run_of_ones_test.passed ? 'pass' : 'fail'}>
                    {analysis.nist_tests.longest_run_of_ones_test.passed ? '✓ Test Passed (p > 0.01)' : '✗ Test Failed (p ≤ 0.01)'}
                  </p>
                </>
              )}
            </div>

            {/* Approximate Entropy Test */}
            <div className="test-card">
              <h4>Approximate Entropy Test</h4>
              {analysis.nist_tests.approximate_entropy_test.error ? (
                <p className="fail">Error: {analysis.nist_tests.approximate_entropy_test.error}</p>
              ) : (
                <>
                  <table className="test-results-table">
                    <tbody>
                      <tr>
                        <td>P-value</td>
                        <td>{analysis.nist_tests.approximate_entropy_test.p_value?.toFixed(6) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Chi-square statistic</td>
                        <td>{analysis.nist_tests.approximate_entropy_test.statistic?.toFixed(4) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Approximate Entropy</td>
                        <td>{analysis.nist_tests.approximate_entropy_test.approximate_entropy?.toFixed(6) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Phi(m)</td>
                        <td>{analysis.nist_tests.approximate_entropy_test.phi_m?.toFixed(6) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Phi(m+1)</td>
                        <td>{analysis.nist_tests.approximate_entropy_test.phi_m1?.toFixed(6) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Pattern length m</td>
                        <td>{analysis.nist_tests.approximate_entropy_test.pattern_length_m || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Pattern length m+1</td>
                        <td>{analysis.nist_tests.approximate_entropy_test.pattern_length_m1 || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Unique patterns (m)</td>
                        <td>{analysis.nist_tests.approximate_entropy_test.unique_patterns_m || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Unique patterns (m+1)</td>
                        <td>{analysis.nist_tests.approximate_entropy_test.unique_patterns_m1 || 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                  <p className={analysis.nist_tests.approximate_entropy_test.passed ? 'pass' : 'fail'}>
                    {analysis.nist_tests.approximate_entropy_test.passed ? '✓ Test Passed (p > 0.01)' : '✗ Test Failed (p ≤ 0.01)'}
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Binary Sequence Information */}
          <div className="chart-container" style={{ marginTop: '20px' }}>
            <h4>Binary Sequence Information</h4>
            <div className="info-card">
              <p>Total binary sequence length: {analysis.nist_tests.binary_sequence_length?.toLocaleString() || 'N/A'} bits</p>
              <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
                Each number is converted to its IEEE 754 double precision (64-bit) binary representation
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'multi-run' && isMultiRun && (
        <div className="stats-section">
          {/* Multi-Run Aggregate View */}
          {multiRunViewMode === 'multi-run' && (
            <>
              <h3>Multi-Run Statistical Analysis</h3>
              <p style={{ marginBottom: '20px', color: '#666' }}>
                Analysis across {analysis.num_runs} runs, {analysis.count_per_run} numbers per run
              </p>

              {/* Test Results */}
              <div className="chart-container">
                <h4>Test Results</h4>
                <div className="test-results">
                  <div className="test-card">
                    <h4>Kolmogorov-Smirnov Uniformity Test</h4>
                    <p className={analysis.test_results.ks_passed_count > 0 ? 'pass' : 'fail'}>
                      {analysis.test_results.ks_uniformity_passed} runs passed (p &gt; 0.05)
                    </p>
                  </div>
                  <div className="test-card">
                    <h4>NIST Runs Test</h4>
                    <p className={analysis.test_results.runs_test_passed_count > 0 ? 'pass' : 'fail'}>
                      {analysis.test_results.runs_test_passed} runs passed (p &gt; 0.01)
                    </p>
                  </div>
                  <div className="test-card">
                    <h4>NIST Binary Matrix Rank Test</h4>
                    <p className={analysis.test_results.binary_matrix_rank_test_passed_count > 0 ? 'pass' : 'fail'}>
                      {analysis.test_results.binary_matrix_rank_test_passed} runs passed (p &gt; 0.01)
                    </p>
                  </div>
                  <div className="test-card">
                    <h4>NIST Longest Run of Ones Test</h4>
                    <p className={analysis.test_results.longest_run_of_ones_test_passed_count > 0 ? 'pass' : 'fail'}>
                      {analysis.test_results.longest_run_of_ones_test_passed} runs passed (p &gt; 0.01)
                    </p>
                  </div>
                  <div className="test-card">
                    <h4>NIST Approximate Entropy Test</h4>
                    <p className={analysis.test_results.approximate_entropy_test_passed_count > 0 ? 'pass' : 'fail'}>
                      {analysis.test_results.approximate_entropy_test_passed} runs passed (p &gt; 0.01)
                    </p>
                  </div>
                </div>
              </div>

              {/* Statistics Tables Side by Side */}
              <div className="stats-tables-container">
                {/* Aggregate Statistics Table */}
                <div className="chart-container">
                  <h4>Aggregate Statistics Across Runs</h4>
                  <table className="stats-table">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Mean Across Runs</th>
                        <th>St.Dev Across Runs</th>
                        <th>Range</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Mean</strong></td>
                        <td>{analysis.aggregate_stats.mean?.mean?.toFixed(4) || 'N/A'}</td>
                        <td>{analysis.aggregate_stats.mean?.std_dev?.toFixed(4) || 'N/A'}</td>
                        <td>{analysis.aggregate_stats.mean?.range?.toFixed(4) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td><strong>Std Dev</strong></td>
                        <td>{analysis.aggregate_stats.std_dev?.mean?.toFixed(4) || 'N/A'}</td>
                        <td>{analysis.aggregate_stats.std_dev?.std_dev?.toFixed(4) || 'N/A'}</td>
                        <td>{analysis.aggregate_stats.std_dev?.range?.toFixed(4) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td><strong>Skewness</strong></td>
                        <td>{analysis.aggregate_stats.skewness?.mean?.toFixed(4) || 'N/A'}</td>
                        <td>{analysis.aggregate_stats.skewness?.std_dev?.toFixed(4) || 'N/A'}</td>
                        <td>{analysis.aggregate_stats.skewness?.range?.toFixed(4) || 'N/A'}</td>
                      </tr>
                      <tr>
                        <td><strong>Kurtosis</strong></td>
                        <td>{analysis.aggregate_stats.kurtosis?.mean?.toFixed(4) || 'N/A'}</td>
                        <td>{analysis.aggregate_stats.kurtosis?.std_dev?.toFixed(4) || 'N/A'}</td>
                        <td>{analysis.aggregate_stats.kurtosis?.range?.toFixed(4) || 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Per-Run Statistics Summary */}
                {analysis.individual_analyses && analysis.individual_analyses.length > 0 && (
                  <div className="chart-container">
                    <h4>Per-Run Statistics Summary</h4>
                    <table className="stats-table" style={{ marginBottom: '30px' }}>
                      <thead>
                        <tr>
                          <th>Run</th>
                          <th>Mean</th>
                          <th>Std Dev</th>
                          <th>Min</th>
                          <th>Max</th>
                          <th>Range</th>
                          <th>KS Test (p)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysis.individual_analyses.map((runAnalysis: any, idx: number) => (
                          <tr 
                            key={idx + 1}
                            onClick={() => {
                              setSelectedRun(idx + 1)
                              setMultiRunViewMode('per-run')
                              setPerRunTab('basic') // Reset to basic tab when selecting a run
                            }}
                            style={{ cursor: 'pointer' }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = '#f0f0f0'
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = ''
                            }}
                          >
                            <td><strong>Run {idx + 1}</strong></td>
                            <td>{runAnalysis.basic_stats?.mean?.toFixed(4) || 'N/A'}</td>
                            <td>{runAnalysis.basic_stats?.std?.toFixed(4) || 'N/A'}</td>
                            <td>{runAnalysis.basic_stats?.min?.toFixed(4) || 'N/A'}</td>
                            <td>{runAnalysis.basic_stats?.max?.toFixed(4) || 'N/A'}</td>
                            <td>{runAnalysis.basic_stats ? (runAnalysis.basic_stats.max - runAnalysis.basic_stats.min).toFixed(4) : 'N/A'}</td>
                            <td>
                              {runAnalysis.distribution?.is_uniform?.ks_p !== undefined 
                                ? `${runAnalysis.distribution.is_uniform.ks_p.toFixed(4)} ${runAnalysis.distribution.is_uniform.ks_p > 0.05 ? '✓' : '✗'}`
                                : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <p style={{ fontSize: '12px', color: '#666', marginBottom: '20px', fontStyle: 'italic' }}>
                      Click on a row to view detailed statistics for that run
                    </p>
                  </div>
                )}
              </div>

          {/* Autocorrelation Table */}
          <div className="chart-container">
            <h4>Autocorrelation Analysis by Run</h4>
            <table className="stats-table">
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Lags with Significant Correlation</th>
                  <th>Max |Correlation|</th>
                </tr>
              </thead>
              <tbody>
                {analysis.autocorrelation_table.map((row: any) => (
                  <tr key={row.run}>
                    <td>{row.run}</td>
                    <td>
                      {Array.isArray(row.significant_lags) && row.significant_lags.length > 0 && row.significant_lags[0] !== "None"
                        ? row.significant_lags.join(', ')
                        : 'None'}
                    </td>
                    <td>{row.max_correlation.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

              {/* Frequency Histogram */}
              {analysis.frequency_histogram && analysis.frequency_histogram.bins && analysis.frequency_histogram.bins.length > 0 && (
                <div className="chart-container">
                  <h4>Frequency Histogram Across All Runs</h4>
                  <p style={{ fontSize: '12px', color: '#666', marginBottom: '15px', fontStyle: 'italic' }}>
                    Distribution of number frequencies across all {analysis.num_runs} runs
                  </p>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={analysis.frequency_histogram.bins.map((bin: number, idx: number) => ({
                        bin: bin.toFixed(4),
                        frequency: analysis.frequency_histogram.frequencies[idx]
                      }))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="bin" 
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        tickFormatter={(value) => typeof value === 'number' ? value.toFixed(3) : value}
                      />
                      <YAxis label={{ value: 'Frequency', angle: -90, position: 'insideLeft' }} />
                      <Tooltip 
                        formatter={(value: any) => [value, 'Frequency']}
                        labelFormatter={(label) => `Bin Center: ${label}`}
                      />
                      <Bar dataKey="frequency" fill="#1E90FF" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Overlaid Visualizations */}
              {analysis.individual_analyses && analysis.individual_analyses.length > 0 && (
                <div className="chart-container">
                  <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ marginBottom: '15px' }}>Overlaid Visualizations (All Runs)</h4>
                    {/* Radio buttons for view selection */}
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      {(['boxplot', 'ecdf', 'qq'] as const).map((view) => (
                        <label
                          key={view}
                          onClick={(e) => {
                            e.stopPropagation()
                            setOverlaidView(view)
                          }}
                          style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '8px',
                            cursor: 'pointer',
                            userSelect: 'none',
                            padding: '6px 12px',
                            border: '2px solid #999',
                            borderRadius: '4px',
                            backgroundColor: overlaidView === view ? '#000' : 'white',
                            transition: 'all 0.2s',
                            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'
                            e.currentTarget.style.transform = 'translateY(-2px)'
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'
                            e.currentTarget.style.transform = 'translateY(0)'
                          }}
                        >
                          <span style={{ 
                            fontSize: '12px', 
                            fontFamily: 'Courier New',
                            color: overlaidView === view ? 'white' : '#000'
                          }}>
                            {view === 'boxplot' ? 'Box Plots' : view === 'ecdf' ? 'ECDF' : 'Q-Q Plot'}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Overlaid Box Plots */}
                  {overlaidView === 'boxplot' && (
                    <>
                      <OverlaidBoxPlots
                        runs={analysis.individual_analyses.map((runAnalysis: any, idx: number) => ({
                          min: runAnalysis.basic_stats?.min || 0,
                          q25: runAnalysis.basic_stats?.q25 || 0,
                          median: runAnalysis.basic_stats?.median || 0,
                          q75: runAnalysis.basic_stats?.q75 || 0,
                          max: runAnalysis.basic_stats?.max || 0,
                          runNumber: idx + 1
                        }))}
                      />
                      <p style={{ fontSize: '12px', color: '#666', marginTop: '15px', fontStyle: 'italic' }}>
                        Hover over a box plot to see detailed statistics for that run
                      </p>
                    </>
                  )}

                  {/* Overlaid ECDF Plot */}
                  {overlaidView === 'ecdf' && (() => {
                    // Create unified dataset: find min/max x across all runs, create common x-axis
                    const allXValues = analysis.ecdf_all_runs.flatMap((r: any) => r.x)
                    const minX = Math.min(...allXValues)
                    const maxX = Math.max(...allXValues)
                    const numPoints = 200
                    const unifiedX = Array.from({ length: numPoints }, (_, i) => minX + (maxX - minX) * (i / (numPoints - 1)))
                    
                    // Create unified dataset with all runs interpolated at common x points
                    const unifiedData = unifiedX.map((x: number) => {
                      const point: any = { x: x }
                      analysis.ecdf_all_runs.forEach((runData: any) => {
                        // Find the ECDF value for this x by interpolation
                        let ecdfValue = 0
                        
                        // Handle edge cases
                        if (x < runData.x[0]) {
                          ecdfValue = 0
                        } else if (x > runData.x[runData.x.length - 1]) {
                          ecdfValue = 1
                        } else {
                          // Find the right interval
                          for (let i = 0; i < runData.x.length; i++) {
                            if (runData.x[i] >= x) {
                              if (i === 0) {
                                ecdfValue = runData.y[0]
                              } else {
                                // Linear interpolation
                                const x0 = runData.x[i - 1]
                                const x1 = runData.x[i]
                                const y0 = runData.y[i - 1]
                                const y1 = runData.y[i]
                                const t = (x - x0) / (x1 - x0)
                                ecdfValue = y0 + t * (y1 - y0)
                              }
                              break
                            }
                          }
                        }
                        point[`y${runData.run}`] = ecdfValue
                      })
                      return point
                    })
                    
                    return (
                      <>
                        <ResponsiveContainer width="100%" height={400}>
                          <LineChart data={unifiedData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="x" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                            <YAxis />
                            <Tooltip />
                            {analysis.ecdf_all_runs.map((runData: any, idx: number) => {
                              const color = qqColors[idx % qqColors.length]
                              // Priority: ecdfSelectedRun > default (show all)
                              const opacity = ecdfSelectedRun === null ? 0.6 : (ecdfSelectedRun === runData.run ? 1 : 0.2)
                              const strokeWidth = ecdfSelectedRun === runData.run ? 2.5 : 1.5
                              return (
                                <Line
                                  key={runData.run}
                                  type="monotone"
                                  dataKey={`y${runData.run}`}
                                  stroke={color}
                                  strokeWidth={strokeWidth}
                                  strokeOpacity={opacity}
                                  dot={false}
                                  name={`Run ${runData.run}`}
                                  connectNulls
                                />
                              )
                            })}
                          </LineChart>
                        </ResponsiveContainer>
                        
                        {/* Legend with Radio Buttons */}
                        <div 
                          ref={ecdfLegendRef}
                          style={{ marginTop: '15px', display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'center' }}
                        >
                          {analysis.ecdf_all_runs.map((runData: any, idx: number) => {
                            const color = qqColors[idx % qqColors.length]
                            const isSelected = ecdfSelectedRun === runData.run
                            return (
                              <label
                                key={runData.run}
                                onClick={(e) => handleEcdfLegendClick(runData.run, e)}
                                style={{ 
                                  display: 'flex', 
                                  alignItems: 'center', 
                                  gap: '8px',
                                  cursor: 'pointer',
                                  userSelect: 'none',
                                  padding: '6px 12px',
                                  border: '2px solid #999',
                                  borderRadius: '4px',
                                  backgroundColor: isSelected ? '#000' : 'white',
                                  transition: 'all 0.2s',
                                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'
                                  e.currentTarget.style.transform = 'translateY(-2px)'
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'
                                  e.currentTarget.style.transform = 'translateY(0)'
                                }}
                              >
                                {/* Color box */}
                                <div style={{ width: '20px', height: '12px', background: color, border: '1px solid #000' }}></div>
                                <span style={{ 
                                  fontSize: '12px', 
                                  fontFamily: 'Courier New',
                                  color: isSelected ? 'white' : '#000'
                                }}>Run {runData.run}</span>
                              </label>
                            )
                          })}
                        </div>
                        <p style={{ fontSize: '12px', color: '#666', marginTop: '15px', fontStyle: 'italic' }}>
                          Each line represents the ECDF for one run. For uniform distribution, lines should be close to the diagonal.
                        </p>
                      </>
                    )
                  })()}

                  {/* Overlaid Q-Q Plot */}
                  {overlaidView === 'qq' && (() => {
                    // Prepare Q-Q plot data for all runs - combine all points
                    const allQqPoints: any[] = []
                    
                    analysis.individual_analyses.forEach((runAnalysis: any, runIdx: number) => {
                      if (runAnalysis.distribution?.qq_plot?.sample && runAnalysis.distribution?.qq_plot?.theoretical) {
                        runAnalysis.distribution.qq_plot.sample.forEach((sample: number, idx: number) => {
                          allQqPoints.push({
                            theoretical: runAnalysis.distribution.qq_plot.theoretical[idx],
                            sample: sample,
                            run: runIdx + 1
                          })
                        })
                      }
                    })

                    // Group by run for separate scatter series
                    const runsMap = new Map<number, any[]>()
                    allQqPoints.forEach(point => {
                      const run = point.run
                      if (!runsMap.has(run)) {
                        runsMap.set(run, [])
                      }
                      runsMap.get(run)!.push({ theoretical: point.theoretical, sample: point.sample })
                    })

                    // Create unified dataset - use theoretical values from all runs
                    const allTheoretical = Array.from(new Set(allQqPoints.map(p => p.theoretical))).sort((a, b) => a - b)
                    const unifiedData = allTheoretical.map(theoretical => {
                      const point: any = { theoretical }
                      runsMap.forEach((points, run) => {
                        // Find closest point or interpolate
                        let sampleValue = null
                        for (const p of points) {
                          if (Math.abs(p.theoretical - theoretical) < 0.0001) {
                            sampleValue = p.sample
                            break
                          }
                        }
                        if (sampleValue === null && points.length > 0) {
                          // Interpolate
                          let closestIdx = 0
                          let minDist = Math.abs(points[0].theoretical - theoretical)
                          for (let i = 1; i < points.length; i++) {
                            const dist = Math.abs(points[i].theoretical - theoretical)
                            if (dist < minDist) {
                              minDist = dist
                              closestIdx = i
                            }
                          }
                          sampleValue = points[closestIdx].sample
                        }
                        point[`sample${run}`] = sampleValue
                      })
                      return point
                    })

                    return (
                      <>
                        <ResponsiveContainer width="100%" height={400}>
                          <ScatterChart data={unifiedData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="theoretical" name="Theoretical" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                            <YAxis name="Sample" />
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                            {Array.from(runsMap.keys()).sort((a, b) => a - b).map((run: number, idx: number) => {
                              const color = qqColors[idx % qqColors.length]
                              // Priority: qqSelectedRun > default (show all)
                              const opacity = qqSelectedRun === null ? 0.6 : (qqSelectedRun === run ? 1 : 0.2)
                              return (
                                <Scatter
                                  key={run}
                                  dataKey={`sample${run}`}
                                  fill={color}
                                  fillOpacity={opacity}
                                  stroke={color}
                                  strokeWidth={qqSelectedRun === run ? 2 : 1}
                                  name={`Run ${run}`}
                                />
                              )
                            })}
                            {/* Reference line y=x */}
                            <Line
                              type="linear"
                              dataKey="theoretical"
                              stroke="#000"
                              strokeWidth={2}
                              strokeDasharray="5 5"
                              dot={false}
                              name="y=x"
                            />
                          </ScatterChart>
                        </ResponsiveContainer>
                        
                        {/* Legend with Radio Buttons */}
                        <div 
                          ref={qqLegendRef}
                          style={{ marginTop: '15px', display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'center' }}
                        >
                          {Array.from(runsMap.keys()).sort((a, b) => a - b).map((run: number, idx: number) => {
                            const color = qqColors[idx % qqColors.length]
                            const isSelected = qqSelectedRun === run
                            return (
                              <label
                                key={run}
                                onClick={(e) => handleQqLegendClick(run, e)}
                                style={{ 
                                  display: 'flex', 
                                  alignItems: 'center', 
                                  gap: '8px',
                                  cursor: 'pointer',
                                  userSelect: 'none',
                                  padding: '6px 12px',
                                  border: '2px solid #999',
                                  borderRadius: '4px',
                                  backgroundColor: isSelected ? '#000' : 'white',
                                  transition: 'all 0.2s',
                                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'
                                  e.currentTarget.style.transform = 'translateY(-2px)'
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'
                                  e.currentTarget.style.transform = 'translateY(0)'
                                }}
                              >
                                {/* Color box */}
                                <div style={{ width: '20px', height: '12px', background: color, border: '1px solid #000' }}></div>
                                <span style={{ 
                                  fontSize: '12px', 
                                  fontFamily: 'Courier New',
                                  color: isSelected ? 'white' : '#000'
                                }}>Run {run}</span>
                              </label>
                            )
                          })}
                        </div>
                        <p style={{ fontSize: '12px', color: '#666', marginTop: '15px', fontStyle: 'italic'  }}>
                          Each color represents one run. Points should lie close to the diagonal line for uniform distribution.
                        </p>
                      </>
                    )
                  })()}
                </div>
              )}

            </>
          )}

          {/* Per-Run Analysis View */}
          {multiRunViewMode === 'per-run' && (
            <>
              {/* Run Selector */}
              {analysis.individual_analyses && analysis.individual_analyses.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ marginRight: '10px', fontWeight: '600' }}>Select Run to View:</label>
                  <select
                    value={selectedRun || ''}
                    onChange={(e) => {
                      const runNum = e.target.value ? parseInt(e.target.value) : null
                      setSelectedRun(runNum)
                      setPerRunTab('basic') // Reset to basic tab when changing runs
                    }}
                    style={{
                      padding: '8px 12px',
                      border: '2px solid #000',
                      borderRadius: '6px',
                      fontSize: '14px',
                      cursor: 'pointer',
                      minWidth: '150px'
                    }}
                  >
                    <option value="">-- Select a run --</option>
                    {analysis.individual_analyses.map((_run: any, idx: number) => (
                      <option key={idx + 1} value={idx + 1}>
                        Run {idx + 1}
                      </option>
                    ))}
                  </select>
                </div>
              )}

          {/* Per-Run Detailed Statistics with Tabs */}
          {analysis.individual_analyses && analysis.individual_analyses.length > 0 && selectedRun && selectedRun > 0 && selectedRun <= analysis.individual_analyses.length && (
            (() => {
              const runAnalysis = analysis.individual_analyses[selectedRun - 1]
              if (!runAnalysis) return null

              // Prepare data for this run (same as single-run analysis)
              const runHistogramData = runAnalysis.distribution?.histogram?.edges?.slice(0, -1).map((edge: number, idx: number) => ({
                bin: edge.toFixed(4),
                count: runAnalysis.distribution.histogram.counts[idx]
              })) || []

              const runKdeData = runAnalysis.distribution?.kde?.x?.map((x: number, idx: number) => ({
                x: x,
                y: runAnalysis.distribution.kde.y[idx]
              })) || []

              const runQqData = runAnalysis.distribution?.qq_plot?.sample?.map((sample: number, idx: number) => ({
                sample: sample,
                theoretical: runAnalysis.distribution.qq_plot.theoretical[idx]
              })) || []

              const runAcfData = runAnalysis.independence?.autocorrelation?.lags?.map((lag: number, idx: number) => ({
                lag: lag,
                correlation: runAnalysis.independence.autocorrelation.values[idx]
              })) || []

              const runLag1Data = runAnalysis.independence?.lag1_scatter?.x?.map((x: number, idx: number) => ({
                x: x,
                y: runAnalysis.independence.lag1_scatter.y[idx]
              })) || []

              const runTimeSeriesData = runAnalysis.independence?.time_series?.index?.map((idx: number) => ({
                index: idx,
                value: runAnalysis.independence.time_series.values[idx]
              })) || []

              const runRollingData = runAnalysis.stationarity?.rolling_mean?.index?.map((idx: number) => ({
                index: idx,
                mean: runAnalysis.stationarity.rolling_mean.values[idx],
                std: runAnalysis.stationarity.rolling_std.values[idx]
              })) || []

              const runEcdfData = runAnalysis.range_behavior?.ecdf?.x?.map((x: number, idx: number) => ({
                x: x,
                y: runAnalysis.range_behavior.ecdf.y[idx]
              })) || []

              const runSpectralData = runAnalysis.spectral?.frequencies?.map((freq: number, idx: number) => ({
                frequency: freq,
                magnitude: runAnalysis.spectral.magnitude[idx],
                power: runAnalysis.spectral.power[idx]
              })) || []

              return (
                <>
                  <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ marginBottom: '10px', color: '#000' }}>Run {selectedRun} Analysis</h3>
                    <p style={{ color: '#666', fontSize: '14px' }}>
                      Detailed statistical analysis for Run {selectedRun} ({runAnalysis.count || analysis.count_per_run} numbers)
                    </p>
                  </div>

                  {/* Analysis information display section */}
                  <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ marginBottom: '10px', color: '#000' }}>Analysis Information Display</h4>
                    <div className="tab-buttons">
                      {['basic', 'distribution', 'range', 'independence', 'stationarity', 'spectral', 'nist'].map(tab => (
                        <button
                          key={tab}
                          onClick={() => setPerRunTab(tab)}
                          className={perRunTab === tab ? 'active' : ''}
                        >
                          {tab === 'nist' ? 'NIST Tests' : tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>

                  {perRunTab === 'basic' && runAnalysis.basic_stats && (
                    <div className="stats-section">
                      <h3>Basic Descriptive Statistics</h3>
                      
                      {/* Navigation buttons */}
                      <div className="sub-nav-buttons">
                        <button
                          onClick={() => setBasicView('stats')}
                          className={basicView === 'stats' ? 'active' : ''}
                        >
                          Statistics
                        </button>
                        <button
                          onClick={() => setBasicView('histogram')}
                          className={basicView === 'histogram' ? 'active' : ''}
                        >
                          Histogram
                        </button>
                        <button
                          onClick={() => setBasicView('boxplot')}
                          className={basicView === 'boxplot' ? 'active' : ''}
                        >
                          Box Plot
                        </button>
                      </div>

                      {basicView === 'stats' && (
                        <div className="stats-grid">
                          <div className="stat-card">
                            <div className="stat-label">Mean</div>
                            <div className="stat-value">{runAnalysis.basic_stats.mean.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Median</div>
                            <div className="stat-value">{runAnalysis.basic_stats.median.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Std Dev</div>
                            <div className="stat-value">{runAnalysis.basic_stats.std.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Variance</div>
                            <div className="stat-value">{runAnalysis.basic_stats.variance.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Min</div>
                            <div className="stat-value">{runAnalysis.basic_stats.min.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Max</div>
                            <div className="stat-value">{runAnalysis.basic_stats.max.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Q25</div>
                            <div className="stat-value">{runAnalysis.basic_stats.q25.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Q75</div>
                            <div className="stat-value">{runAnalysis.basic_stats.q75.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Q95</div>
                            <div className="stat-value">{runAnalysis.basic_stats.q95.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Skewness</div>
                            <div className="stat-value">{runAnalysis.basic_stats.skewness.toFixed(4)}</div>
                          </div>
                          <div className="stat-card">
                            <div className="stat-label">Kurtosis</div>
                            <div className="stat-value">{runAnalysis.basic_stats.kurtosis.toFixed(4)}</div>
                          </div>
                        </div>
                      )}

                      {basicView === 'histogram' && (
                        <div className="chart-container">
                          <h4>Histogram</h4>
                          <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={runHistogramData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="bin" angle={-45} textAnchor="end" height={80} tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="count" fill="#000" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {basicView === 'boxplot' && (
                        <div className="chart-container">
                          <h4>Box Plot</h4>
                          <BoxPlot
                            min={runAnalysis.basic_stats.min}
                            q25={runAnalysis.basic_stats.q25}
                            median={runAnalysis.basic_stats.median}
                            q75={runAnalysis.basic_stats.q75}
                            max={runAnalysis.basic_stats.max}
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {perRunTab === 'distribution' && runAnalysis.distribution && (
                    <div className="stats-section">
                      <h3>Distribution Shape Analysis</h3>
                      
                      {/* Navigation buttons */}
                      <div className="sub-nav-buttons">
                        <button
                          onClick={() => setDistributionView('tests')}
                          className={distributionView === 'tests' ? 'active' : ''}
                        >
                          Tests
                        </button>
                        <button
                          onClick={() => setDistributionView('kde')}
                          className={distributionView === 'kde' ? 'active' : ''}
                        >
                          KDE
                        </button>
                        <button
                          onClick={() => setDistributionView('qq')}
                          className={distributionView === 'qq' ? 'active' : ''}
                        >
                          Q-Q Plot
                        </button>
                      </div>

                      {distributionView === 'tests' && (
                        <div className="test-results">
                          <div className="test-card">
                            <h4>Uniformity Test</h4>
                            <p>Kolmogorov-Smirnov: p = {runAnalysis.distribution.is_uniform.ks_p.toFixed(4)}</p>
                            <p className={runAnalysis.distribution.is_uniform.ks_p > 0.05 ? 'pass' : 'fail'}>
                              {runAnalysis.distribution.is_uniform.ks_p > 0.05 ? '✓ Likely Uniform' : '✗ Not Uniform'}
                            </p>
                          </div>
                        </div>
                      )}

                      {distributionView === 'kde' && (
                        <div className="chart-container">
                          <h4>Kernel Density Estimate (KDE)</h4>
                          <ResponsiveContainer width="100%" height={250}>
                            <AreaChart data={runKdeData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="x" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                              <YAxis />
                              <Tooltip />
                              <Area type="monotone" dataKey="y" stroke="#000" fill="#000" fillOpacity={0.3} />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {distributionView === 'qq' && (
                        <div className="chart-container">
                          <h4>Q-Q Plot (Uniform Distribution)</h4>
                          <ResponsiveContainer width="100%" height={250}>
                            <ScatterChart data={runQqData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="theoretical" name="Theoretical" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                              <YAxis dataKey="sample" name="Sample" />
                              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                              <Scatter name="Q-Q" dataKey="sample" fill="#000" />
                            </ScatterChart>
                          </ResponsiveContainer>
                          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
                            Points should lie along the diagonal line if uniformly distributed
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {perRunTab === 'range' && runAnalysis.range_behavior && (
                    <div className="stats-section">
                      <h3>Range & Boundary Behavior</h3>
                      
                      <div className="boundary-info">
                        <div className="info-card">
                          <h4>Boundary Statistics</h4>
                          <p>Min: {runAnalysis.range_behavior.boundaries.min.toFixed(4)}</p>
                          <p>Max: {runAnalysis.range_behavior.boundaries.max.toFixed(4)}</p>
                          <p>Near Min: {runAnalysis.range_behavior.boundaries.near_min_count} ({runAnalysis.range_behavior.boundaries.near_min_pct.toFixed(4)}%)</p>
                          <p>Near Max: {runAnalysis.range_behavior.boundaries.near_max_count} ({runAnalysis.range_behavior.boundaries.near_max_pct.toFixed(4)}%)</p>
                        </div>
                      </div>

                      <div className="chart-container">
                        <h4>Empirical Cumulative Distribution Function (ECDF)</h4>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={runEcdfData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="x" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                            <YAxis />
                            <Tooltip />
                            <Line type="monotone" dataKey="y" stroke="#000" strokeWidth={2} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {perRunTab === 'independence' && runAnalysis.independence && (
                    <div className="stats-section">
                      <h3>Independence & Correlation Analysis</h3>

                      <div className="chart-container">
                        <h4>Time Series</h4>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={runTimeSeriesData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="index" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                            <YAxis />
                            <Tooltip />
                            <Line type="monotone" dataKey="value" stroke="#000" strokeWidth={1} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>

                      <div className="chart-container">
                        <h4>Autocorrelation Function (ACF)</h4>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={runAcfData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="lag" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                            <YAxis domain={[-1, 1]} />
                            <Tooltip />
                            <Bar dataKey="correlation" fill="#000" />
                          </BarChart>
                        </ResponsiveContainer>
                        <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
                          Values near zero indicate independence. Significant peaks suggest correlation.
                        </p>
                      </div>

                      <div className="chart-container">
                        <h4>Lag-1 Scatter Plot</h4>
                        <ResponsiveContainer width="100%" height={300}>
                          <ScatterChart data={runLag1Data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="x" name="x_n" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                            <YAxis dataKey="y" name="x_{n+1}" />
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                            <Scatter name="Lag-1" dataKey="y" fill="#000" />
                          </ScatterChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {perRunTab === 'stationarity' && runAnalysis.stationarity && (
                    <div className="stats-section">
                      <h3>Stationarity Analysis</h3>

                      <div className="chart-container">
                        <h4>Rolling Mean & Standard Deviation</h4>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={runRollingData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="index" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                            <YAxis yAxisId="left" />
                            <YAxis yAxisId="right" orientation="right" />
                            <Tooltip />
                            <Legend />
                            <Line yAxisId="left" type="monotone" dataKey="mean" stroke="#000" strokeWidth={2} name="Rolling Mean" />
                            <Line yAxisId="right" type="monotone" dataKey="std" stroke="#666" strokeWidth={2} name="Rolling Std" />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>

                      <div className="chunks-container">
                        <h4>Chunked Statistics</h4>
                        <div className="chunks-grid">
                          {runAnalysis.stationarity.chunks.map((chunk: any) => (
                            <div key={chunk.chunk} className="chunk-card">
                              <h5>Chunk {chunk.chunk}</h5>
                              <p>Mean: {chunk.mean.toFixed(4)}</p>
                              <p>Std: {chunk.std.toFixed(4)}</p>
                              <p>Min: {chunk.min.toFixed(4)}</p>
                              <p>Max: {chunk.max.toFixed(4)}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {perRunTab === 'spectral' && runAnalysis.spectral && (
                    <div className="stats-section">
                      <h3>Spectral Analysis</h3>

                      <div className="chart-container">
                        <h4>FFT Magnitude</h4>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={runSpectralData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="frequency" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                            <YAxis />
                            <Tooltip />
                            <Line type="monotone" dataKey="magnitude" stroke="#000" strokeWidth={2} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>

                      <div className="chart-container">
                        <h4>Power Spectrum (Periodogram)</h4>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={runSpectralData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="frequency" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                            <YAxis />
                            <Tooltip />
                            <Line type="monotone" dataKey="power" stroke="#666" strokeWidth={2} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {perRunTab === 'nist' && runAnalysis.nist_tests && (
                    <div className="stats-section">
                      <h3>NIST Statistical Tests</h3>
                      <p style={{ marginBottom: '20px', color: '#666', fontSize: '14px' }}>
                        Tests performed on binary representation of numbers (IEEE 754 double precision)
                      </p>

                      {/* Display all 4 tests in a row */}
                      <div className="nist-tests-grid">
                        {/* Runs Test */}
                        <div className="test-card">
                          <h4>Runs Test</h4>
                          {runAnalysis.nist_tests.runs_test.error ? (
                            <p className="fail">Error: {runAnalysis.nist_tests.runs_test.error}</p>
                          ) : (
                            <>
                              <table className="test-results-table">
                                <tbody>
                                  <tr>
                                    <td>P-value</td>
                                    <td>{runAnalysis.nist_tests.runs_test.p_value?.toFixed(6) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Z-statistic</td>
                                    <td>{runAnalysis.nist_tests.runs_test.statistic?.toFixed(4) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Runs observed</td>
                                    <td>{runAnalysis.nist_tests.runs_test.runs || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Runs expected</td>
                                    <td>{runAnalysis.nist_tests.runs_test.expected_runs?.toFixed(4) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Ones</td>
                                    <td>{runAnalysis.nist_tests.runs_test.ones || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Zeros</td>
                                    <td>{runAnalysis.nist_tests.runs_test.zeros || 'N/A'}</td>
                                  </tr>
                                </tbody>
                              </table>
                              <p className={runAnalysis.nist_tests.runs_test.passed ? 'pass' : 'fail'}>
                                {runAnalysis.nist_tests.runs_test.passed ? '✓ Test Passed (p > 0.01)' : '✗ Test Failed (p ≤ 0.01)'}
                              </p>
                            </>
                          )}
                        </div>

                        {/* Binary Matrix Rank Test */}
                        <div className="test-card">
                          <h4>Binary Matrix Rank Test</h4>
                          {runAnalysis.nist_tests.binary_matrix_rank_test.error ? (
                            <p className="fail">Error: {runAnalysis.nist_tests.binary_matrix_rank_test.error}</p>
                          ) : (
                            <>
                              <table className="test-results-table">
                                <tbody>
                                  <tr>
                                    <td>P-value</td>
                                    <td>{runAnalysis.nist_tests.binary_matrix_rank_test.p_value?.toFixed(6) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Chi-square statistic</td>
                                    <td>{runAnalysis.nist_tests.binary_matrix_rank_test.statistic?.toFixed(4) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Number of matrices</td>
                                    <td>{runAnalysis.nist_tests.binary_matrix_rank_test.num_matrices || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Full rank count</td>
                                    <td>{runAnalysis.nist_tests.binary_matrix_rank_test.full_rank_count || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Rank-1 count</td>
                                    <td>{runAnalysis.nist_tests.binary_matrix_rank_test.rank_minus_1_count || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Rank-0 count</td>
                                    <td>{runAnalysis.nist_tests.binary_matrix_rank_test.rank_0_count || 'N/A'}</td>
                                  </tr>
                                </tbody>
                              </table>
                              <p className={runAnalysis.nist_tests.binary_matrix_rank_test.passed ? 'pass' : 'fail'}>
                                {runAnalysis.nist_tests.binary_matrix_rank_test.passed ? '✓ Test Passed (p > 0.01)' : '✗ Test Failed (p ≤ 0.01)'}
                              </p>
                            </>
                          )}
                        </div>

                        {/* Longest Run of Ones Test */}
                        <div className="test-card">
                          <h4>Longest Run of Ones Test</h4>
                          {runAnalysis.nist_tests.longest_run_of_ones_test.error ? (
                            <p className="fail">Error: {runAnalysis.nist_tests.longest_run_of_ones_test.error}</p>
                          ) : (
                            <>
                              <table className="test-results-table">
                                <tbody>
                                  <tr>
                                    <td>P-value</td>
                                    <td>{runAnalysis.nist_tests.longest_run_of_ones_test.p_value?.toFixed(6) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Chi-square statistic</td>
                                    <td>{runAnalysis.nist_tests.longest_run_of_ones_test.statistic?.toFixed(4) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Number of blocks</td>
                                    <td>{runAnalysis.nist_tests.longest_run_of_ones_test.num_blocks || 'N/A'}</td>
                                  </tr>
                                  {runAnalysis.nist_tests.longest_run_of_ones_test.run_counts && Object.entries(runAnalysis.nist_tests.longest_run_of_ones_test.run_counts).map(([length, count]: [string, any]) => (
                                    <tr key={length}>
                                      <td>Length ≤{length}</td>
                                      <td>{count}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                              <p className={runAnalysis.nist_tests.longest_run_of_ones_test.passed ? 'pass' : 'fail'}>
                                {runAnalysis.nist_tests.longest_run_of_ones_test.passed ? '✓ Test Passed (p > 0.01)' : '✗ Test Failed (p ≤ 0.01)'}
                              </p>
                            </>
                          )}
                        </div>

                        {/* Approximate Entropy Test */}
                        <div className="test-card">
                          <h4>Approximate Entropy Test</h4>
                          {runAnalysis.nist_tests.approximate_entropy_test.error ? (
                            <p className="fail">Error: {runAnalysis.nist_tests.approximate_entropy_test.error}</p>
                          ) : (
                            <>
                              <table className="test-results-table">
                                <tbody>
                                  <tr>
                                    <td>P-value</td>
                                    <td>{runAnalysis.nist_tests.approximate_entropy_test.p_value?.toFixed(6) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Chi-square statistic</td>
                                    <td>{runAnalysis.nist_tests.approximate_entropy_test.statistic?.toFixed(4) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Approximate Entropy</td>
                                    <td>{runAnalysis.nist_tests.approximate_entropy_test.approximate_entropy?.toFixed(6) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Phi(m)</td>
                                    <td>{runAnalysis.nist_tests.approximate_entropy_test.phi_m?.toFixed(6) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Phi(m+1)</td>
                                    <td>{runAnalysis.nist_tests.approximate_entropy_test.phi_m1?.toFixed(6) || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Pattern length m</td>
                                    <td>{runAnalysis.nist_tests.approximate_entropy_test.pattern_length_m || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Pattern length m+1</td>
                                    <td>{runAnalysis.nist_tests.approximate_entropy_test.pattern_length_m1 || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Unique patterns (m)</td>
                                    <td>{runAnalysis.nist_tests.approximate_entropy_test.unique_patterns_m || 'N/A'}</td>
                                  </tr>
                                  <tr>
                                    <td>Unique patterns (m+1)</td>
                                    <td>{runAnalysis.nist_tests.approximate_entropy_test.unique_patterns_m1 || 'N/A'}</td>
                                  </tr>
                                </tbody>
                              </table>
                              <p className={runAnalysis.nist_tests.approximate_entropy_test.passed ? 'pass' : 'fail'}>
                                {runAnalysis.nist_tests.approximate_entropy_test.passed ? '✓ Test Passed (p > 0.01)' : '✗ Test Failed (p ≤ 0.01)'}
                              </p>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="chart-container" style={{ marginTop: '20px' }}>
                        <h4>Binary Sequence Information</h4>
                        <div className="info-card">
                          <p>Total binary sequence length: {runAnalysis.nist_tests.binary_sequence_length?.toLocaleString() || 'N/A'} bits</p>
                          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
                            Each number is converted to its IEEE 754 double precision (64-bit) binary representation
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )
            })()
          )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default StatsDashboard
