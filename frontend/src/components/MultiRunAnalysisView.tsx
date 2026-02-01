import { useState, useEffect, useRef, type ComponentProps } from 'react'
import { createPortal } from 'react-dom'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ReferenceLine
} from 'recharts'
import { OverlaidBoxPlots } from './charts'

export type PinnedTooltip = { payload: Array<{ name?: string; value?: number; color?: string }>; label: unknown }

/** Recharts tooltip content: fixed bottom-right. When pinned, shows pinned data so user can scroll; otherwise follows hover. */
function AnchoredScrollableTooltip(props: {
  active?: boolean
  payload?: Array<{ name?: string; value?: number; color?: string }>
  label?: string
  labelFormatter?: (label: unknown) => string
  formatter?: (value: number) => [string, string]
  pinned?: PinnedTooltip | null
  onHover?: (payload: Array<{ name?: string; value?: number; color?: string }>, label: unknown) => void
}) {
  const { active, payload = [], label, labelFormatter, formatter, pinned, onHover } = props
  const showPinned = pinned?.payload?.length
  const showLive = active && payload?.length
  if (showLive && !showPinned && onHover) onHover(payload, label)
  const data = showPinned ? pinned! : (showLive ? { payload, label } : null)
  if (!data?.payload?.length) return null
  const labelStr = data.label != null && labelFormatter ? labelFormatter(data.label) : String(data.label ?? '')
  const content = (
    <div
      className="anchored-chart-tooltip"
      data-anchored-tooltip
      style={{
        position: 'fixed',
        right: 24,
        bottom: 24,
        zIndex: 1000,
        background: '#fff',
        border: '1px solid #ccc',
        borderRadius: 8,
        padding: '10px 14px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        maxHeight: 220,
        overflowY: 'auto',
        fontSize: 12,
      }}
    >
      {labelStr && <div style={{ marginBottom: 6, fontWeight: 600, color: '#333' }}>{labelStr}</div>}
      <ul style={{ margin: 0, paddingLeft: 16, listStyle: 'none' }}>
        {data.payload.map((entry, i) => {
          const formatted = formatter && entry.value != null ? formatter(entry.value) : null
          const displayValue = formatted != null ? formatted[0] : String(entry.value ?? '')
          const name = (formatted != null && formatted[1]) ? formatted[1] : (entry.name ?? '')
          return (
            <li key={i} style={{ marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: entry.color ?? '#888', flexShrink: 0 }} />
              <span style={{ color: '#666' }}>{name}:</span>
              <span style={{ fontFamily: 'monospace' }}>{displayValue}</span>
            </li>
          )
        })}
      </ul>
      <div style={{ marginTop: 6, fontSize: 11, color: '#999' }}>
        {showPinned ? 'Click chart or elsewhere to close' : 'Scroll if needed · click chart to pin'}
      </div>
    </div>
  )
  return createPortal(content, document.body)
}

const QQ_COLORS = ['#DC143C', '#228B22', '#1E90FF', '#FF8C00', '#9370DB', '#00CED1', '#FF1493', '#FFD700', '#8B4513', '#32CD32', '#000000']

// Cap overlaid Q-Q points to avoid browser crash (Recharts + heavy unifiedData build)
const MAX_QQ_DISPLAY_POINTS = 350

function downsampleQqForDisplay(sample: number[], theoretical: number[], maxPoints: number): { sample: number[]; theoretical: number[] } {
  const n = sample.length
  if (n <= maxPoints) return { sample: [...sample], theoretical: [...theoretical] }
  const outSample: number[] = []
  const outTheoretical: number[] = []
  const step = (n - 1) / (maxPoints - 1)
  for (let i = 0; i < maxPoints; i++) {
    const idx = i === maxPoints - 1 ? n - 1 : Math.min(Math.round(i * step), n - 1)
    outSample.push(sample[idx])
    outTheoretical.push(theoretical[idx])
  }
  return { sample: outSample, theoretical: outTheoretical }
}

/** Find index of closest value to x in sorted array (by value) */
function closestIndexSorted(sortedValues: number[], x: number): number {
  if (sortedValues.length === 0) return -1
  let lo = 0
  let hi = sortedValues.length - 1
  while (lo < hi - 1) {
    const mid = (lo + hi) >> 1
    if (sortedValues[mid]! <= x) lo = mid
    else hi = mid
  }
  return Math.abs(sortedValues[lo]! - x) <= Math.abs(sortedValues[hi]! - x) ? lo : hi
}

interface MultiRunAnalysisViewProps {
  analysis: any
  allRuns: number[][]
  onSelectRun?: (runNumber: number) => void
}

function computeValueFrequencyHistogram(allRuns: number[][]): { value: string; count: number }[] {
  const flat = allRuns.flat()
  if (flat.length === 0) return []
  const precision = 4
  const round = (x: number) => Math.round(x * Math.pow(10, precision)) / Math.pow(10, precision)
  const counts: Record<string, number> = {}
  flat.forEach((n) => {
    const key = round(n).toFixed(precision)
    counts[key] = (counts[key] ?? 0) + 1
  })
  return Object.entries(counts).map(([value, count]) => ({ value, count })).sort((a, b) => Number(a.value) - Number(b.value))
}

function computeAllNumbersKde(allRuns: number[][]): { x: number; density: number }[] {
  const flat = allRuns.flat()
  if (flat.length < 2) return []
  const n = flat.length
  const min = Math.min(...flat)
  const max = Math.max(...flat)
  const mean = flat.reduce((a, b) => a + b, 0) / n
  const variance = flat.reduce((a, b) => a + (b - mean) ** 2, 0) / n
  const sigma = Math.sqrt(variance) || 1
  const h = 1.06 * sigma * Math.pow(n, -0.2) || (max - min) / 50
  const gridPoints = 150
  const padding = (max - min) * 0.1 || 0.1
  const xMin = min - padding
  const xMax = max + padding
  const gaussian = (u: number) => (1 / Math.sqrt(2 * Math.PI)) * Math.exp(-0.5 * u * u)
  const data: { x: number; density: number }[] = []
  for (let i = 0; i <= gridPoints; i++) {
    const x = xMin + (xMax - xMin) * (i / gridPoints)
    let sum = 0
    for (let j = 0; j < flat.length; j++) sum += gaussian((x - flat[j]) / h)
    data.push({ x, density: sum / (n * h) })
  }
  return data
}

const toggleLabelStyle = (isActive: boolean) => ({
  display: 'flex' as const, alignItems: 'center' as const, gap: '8px', cursor: 'pointer', userSelect: 'none' as const,
  padding: '6px 12px', border: '2px solid #999', borderRadius: '4px', backgroundColor: isActive ? '#000' : 'white',
  transition: 'all 0.2s', boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
})

const MultiRunAnalysisView = ({ analysis, allRuns, onSelectRun }: MultiRunAnalysisViewProps) => {
  const [multiRunPage, setMultiRunPage] = useState<1 | 2 | 3 | 4>(1)
  const [overlaidView, setOverlaidView] = useState<'boxplot' | 'ecdf' | 'qq'>('boxplot')
  const [frequencyHistogramView, setFrequencyHistogramView] = useState<'histogram' | 'kde'>('histogram')
  const [qqSelectedRun, setQqSelectedRun] = useState<number | null>(null)
  const [ecdfSelectedRun, setEcdfSelectedRun] = useState<number | null>(null)
  const [ecdfPinned, setEcdfPinned] = useState<PinnedTooltip | null>(null)
  const [qqPinned, setQqPinned] = useState<PinnedTooltip | null>(null)
  const qqLegendRef = useRef<HTMLDivElement>(null)
  const ecdfLegendRef = useRef<HTMLDivElement>(null)
  const lastEcdfHoverRef = useRef<PinnedTooltip | null>(null)
  const lastQqHoverRef = useRef<PinnedTooltip | null>(null)
  const ecdfChartRef = useRef<HTMLDivElement>(null)
  const qqChartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node
      if (ecdfPinned && !ecdfChartRef.current?.contains(target) && !(target as Element).closest?.('[data-anchored-tooltip]')) setEcdfPinned(null)
      if (qqPinned && !qqChartRef.current?.contains(target) && !(target as Element).closest?.('[data-anchored-tooltip]')) setQqPinned(null)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [ecdfPinned, qqPinned])

  // Prefer backend frequency_histogram (Phase 6); fallback to client-side for legacy
  const valueFrequencyHistogramData =
    analysis.frequency_histogram?.bins?.length > 0
      ? analysis.frequency_histogram.bins.map((b: number, i: number) => ({
          value: String(b),
          count: analysis.frequency_histogram.frequencies[i] ?? 0
        }))
      : computeValueFrequencyHistogram(allRuns)
  // Prefer backend combined_kde (Phase 6 Option A); fallback to client-side for legacy
  const allNumbersKdeData =
    analysis.combined_kde?.x?.length > 0
      ? analysis.combined_kde.x.map((x: number, i: number) => ({
          x,
          density: analysis.combined_kde.y[i] ?? 0
        }))
      : computeAllNumbersKde(allRuns)

  useEffect(() => {
    const handle = (e: MouseEvent) => {
      if (qqLegendRef.current && !qqLegendRef.current.contains(e.target as Node) && qqSelectedRun !== null) setQqSelectedRun(null)
    }
    if (qqSelectedRun !== null) {
      document.addEventListener('mousedown', handle)
      return () => document.removeEventListener('mousedown', handle)
    }
  }, [qqSelectedRun])

  useEffect(() => {
    const handle = (e: MouseEvent) => {
      if (ecdfLegendRef.current && !ecdfLegendRef.current.contains(e.target as Node) && ecdfSelectedRun !== null) setEcdfSelectedRun(null)
    }
    if (ecdfSelectedRun !== null) {
      document.addEventListener('mousedown', handle)
      return () => document.removeEventListener('mousedown', handle)
    }
  }, [ecdfSelectedRun])

  const handleQqLegendClick = (runNumber: number, e: React.MouseEvent) => { e.stopPropagation(); setQqSelectedRun(qqSelectedRun === runNumber ? null : runNumber) }
  const handleEcdfLegendClick = (runNumber: number, e: React.MouseEvent) => { e.stopPropagation(); setEcdfSelectedRun(ecdfSelectedRun === runNumber ? null : runNumber) }

  const handleEcdfChartClick = () => {
    if (ecdfPinned) setEcdfPinned(null)
    else if (lastEcdfHoverRef.current?.payload?.length) setEcdfPinned(lastEcdfHoverRef.current)
  }
  const handleQqChartClick = () => {
    if (qqPinned) setQqPinned(null)
    else if (lastQqHoverRef.current?.payload?.length) setQqPinned(lastQqHoverRef.current)
  }

  return (
    <div className="stats-section">
      <h3>Multi-Run Statistical Analysis</h3>
      <p style={{ marginBottom: '15px', color: '#666' }}>
        Analysis across {analysis.num_runs} runs, {analysis.count_per_run} numbers per run
      </p>

      <div className="sub-nav-buttons" style={{ marginBottom: '20px' }}>
        <button onClick={() => setMultiRunPage(1)} className={multiRunPage === 1 ? 'active' : ''}>Test Results</button>
        <button onClick={() => setMultiRunPage(2)} className={multiRunPage === 2 ? 'active' : ''}>Tables</button>
        <button onClick={() => setMultiRunPage(3)} className={multiRunPage === 3 ? 'active' : ''}>Charts</button>
        <button onClick={() => setMultiRunPage(4)} className={multiRunPage === 4 ? 'active' : ''}>Deviation</button>
      </div>

      {multiRunPage === 1 && (
        <div className="chart-container">
          <h4>Test Results</h4>
          <div className="test-results">
            <div className="test-card"><h4>Kolmogorov-Smirnov Uniformity Test</h4><p className={analysis.test_results.ks_passed_count > 0 ? 'pass' : 'fail'}>{analysis.test_results.ks_uniformity_passed} runs passed (p &gt; 0.05)</p></div>
            <div className="test-card"><h4>NIST Runs Test</h4><p className={analysis.test_results.runs_test_passed_count > 0 ? 'pass' : 'fail'}>{analysis.test_results.runs_test_passed} runs passed (p &gt; 0.01)</p></div>
            <div className="test-card"><h4>NIST Binary Matrix Rank Test</h4><p className={analysis.test_results.binary_matrix_rank_test_passed_count > 0 ? 'pass' : 'fail'}>{analysis.test_results.binary_matrix_rank_test_passed} runs passed (p &gt; 0.01)</p></div>
            <div className="test-card"><h4>NIST Longest Run of Ones Test</h4><p className={analysis.test_results.longest_run_of_ones_test_passed_count > 0 ? 'pass' : 'fail'}>{analysis.test_results.longest_run_of_ones_test_passed} runs passed (p &gt; 0.01)</p></div>
            <div className="test-card"><h4>NIST Approximate Entropy Test</h4><p className={analysis.test_results.approximate_entropy_test_passed_count > 0 ? 'pass' : 'fail'}>{analysis.test_results.approximate_entropy_test_passed} runs passed (p &gt; 0.01)</p></div>
          </div>
        </div>
      )}

      {multiRunPage === 2 && (
        <>
          <div className="stats-tables-container">
            <div className="chart-container">
              <h4>Aggregate Statistics Across Runs</h4>
              <table className="stats-table">
                <thead><tr><th>Metric</th><th>Mean Across Runs</th><th>St.Dev Across Runs</th><th>Range</th></tr></thead>
                <tbody>
                  <tr><td><strong>Mean</strong></td><td>{analysis.aggregate_stats.mean?.mean?.toFixed(4) || 'N/A'}</td><td>{analysis.aggregate_stats.mean?.std_dev?.toFixed(4) || 'N/A'}</td><td>{analysis.aggregate_stats.mean?.range?.toFixed(4) || 'N/A'}</td></tr>
                  <tr><td><strong>Std Dev</strong></td><td>{analysis.aggregate_stats.std_dev?.mean?.toFixed(4) || 'N/A'}</td><td>{analysis.aggregate_stats.std_dev?.std_dev?.toFixed(4) || 'N/A'}</td><td>{analysis.aggregate_stats.std_dev?.range?.toFixed(4) || 'N/A'}</td></tr>
                  <tr><td><strong>Skewness</strong></td><td>{analysis.aggregate_stats.skewness?.mean?.toFixed(4) || 'N/A'}</td><td>{analysis.aggregate_stats.skewness?.std_dev?.toFixed(4) || 'N/A'}</td><td>{analysis.aggregate_stats.skewness?.range?.toFixed(4) || 'N/A'}</td></tr>
                  <tr><td><strong>Kurtosis</strong></td><td>{analysis.aggregate_stats.kurtosis?.mean?.toFixed(4) || 'N/A'}</td><td>{analysis.aggregate_stats.kurtosis?.std_dev?.toFixed(4) || 'N/A'}</td><td>{analysis.aggregate_stats.kurtosis?.range?.toFixed(4) || 'N/A'}</td></tr>
                </tbody>
              </table>
            </div>
            {analysis.individual_analyses?.length > 0 && (
              <div className="chart-container">
                <h4>Per-Run Statistics Summary</h4>
                <div className="table-scroll-wrapper table-scroll-wrapper--5-rows" style={{ marginBottom: '30px' }}>
                  <table className="stats-table">
                    <thead><tr><th>Run</th><th>Mean</th><th>Std Dev</th><th>Min</th><th>Max</th><th>Range</th><th>KS Test (p)</th></tr></thead>
                    <tbody>
                      {analysis.individual_analyses.map((runAnalysis: any, idx: number) => (
                        <tr
                          key={idx + 1}
                          onClick={() => onSelectRun?.(idx + 1)}
                          style={{ cursor: onSelectRun ? 'pointer' : undefined }}
                          onMouseEnter={(e) => onSelectRun && (e.currentTarget.style.background = '#f0f0f0')}
                          onMouseLeave={(e) => onSelectRun && (e.currentTarget.style.background = '')}
                        >
                          <td><strong>Run {idx + 1}</strong></td>
                          <td>{runAnalysis.basic_stats?.mean?.toFixed(4) || 'N/A'}</td>
                          <td>{runAnalysis.basic_stats?.std?.toFixed(4) || 'N/A'}</td>
                          <td>{runAnalysis.basic_stats?.min?.toFixed(4) || 'N/A'}</td>
                          <td>{runAnalysis.basic_stats?.max?.toFixed(4) || 'N/A'}</td>
                          <td>{runAnalysis.basic_stats ? (runAnalysis.basic_stats.max - runAnalysis.basic_stats.min).toFixed(4) : 'N/A'}</td>
                          <td>{runAnalysis.distribution?.is_uniform?.ks_p !== undefined ? `${runAnalysis.distribution.is_uniform.ks_p.toFixed(4)} ${runAnalysis.distribution.is_uniform.ks_p > 0.05 ? '✓' : '✗'}` : 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {onSelectRun && <p style={{ fontSize: '12px', color: '#666', marginBottom: '20px', fontStyle: 'italic' }}>Click on a row to view detailed statistics for that run</p>}
              </div>
            )}
          </div>
          {analysis.autocorrelation_table && (
            <div className="chart-container">
              <h4>Autocorrelation Analysis by Run</h4>
              <div className="table-scroll-wrapper table-scroll-wrapper--5-rows">
                <table className="stats-table">
                  <thead><tr><th>Run</th><th>Lags with Significant Correlation</th><th>Max |Correlation|</th></tr></thead>
                  <tbody>
                    {analysis.autocorrelation_table.map((row: any) => (
                      <tr key={row.run}>
                        <td>{row.run}</td>
                        <td>{Array.isArray(row.significant_lags) && row.significant_lags.length > 0 && row.significant_lags[0] !== 'None' ? row.significant_lags.join(', ') : 'None'}</td>
                        <td>{row.max_correlation.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {multiRunPage === 3 && (
        <>
          {analysis.frequency_histogram?.bins?.length > 0 && (
            <div className="chart-container">
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ marginBottom: '15px' }}>Frequency Histogram / KDE Across All Runs</h4>
                <p style={{ fontSize: '12px', color: '#666', marginBottom: '15px', fontStyle: 'italic' }}>Distribution of number frequencies across all {analysis.num_runs} runs</p>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  {(['histogram', 'kde'] as const).map((view) => (
                    <label key={view} onClick={(e) => { e.stopPropagation(); setFrequencyHistogramView(view) }} style={toggleLabelStyle(frequencyHistogramView === view)} onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'; e.currentTarget.style.transform = 'translateY(-2px)' }} onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'; e.currentTarget.style.transform = 'translateY(0)' }}>
                      <span style={{ fontSize: '12px', fontFamily: 'Courier New', color: frequencyHistogramView === view ? 'white' : '#000' }}>{view === 'histogram' ? 'Frequency Histogram' : 'KDE'}</span>
                    </label>
                  ))}
                </div>
              </div>
              {frequencyHistogramView === 'histogram' && valueFrequencyHistogramData.length > 0 && (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={valueFrequencyHistogramData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="value" angle={-45} textAnchor="end" height={80} interval={Math.max(0, Math.floor(valueFrequencyHistogramData.length / 30))} />
                    <YAxis label={{ value: 'Frequency', angle: -90, position: 'insideLeft' }} />
                    <Tooltip formatter={(value: any) => [value, 'Frequency']} labelFormatter={(label) => `Value: ${label}`} />
                    <Bar dataKey="count" fill="#1E90FF" />
                  </BarChart>
                </ResponsiveContainer>
              )}
              {frequencyHistogramView === 'kde' && allNumbersKdeData.length > 0 && (
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={allNumbersKdeData.map((d: { x: number; density: number }) => ({ x: d.x, density: d.density }))} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="x" type="number" domain={['dataMin', 'dataMax']} tickFormatter={(v) => typeof v === 'number' ? v.toFixed(3) : String(v)} />
                    <YAxis label={{ value: 'Density', angle: -90, position: 'insideLeft' }} />
                    <Tooltip formatter={(value: any) => [Number(value).toFixed(6), 'Density']} labelFormatter={(label) => `x: ${typeof label === 'number' ? label.toFixed(4) : label}`} />
                    <Area type="monotone" dataKey="density" stroke="#1E90FF" fill="#1E90FF" fillOpacity={0.4} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          )}

          {analysis.individual_analyses?.length > 0 && (
            <div className="chart-container">
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ marginBottom: '15px' }}>Overlaid Visualizations (All Runs)</h4>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  {(['boxplot', 'ecdf', 'qq'] as const).map((view) => (
                    <label key={view} onClick={(e) => { e.stopPropagation(); setOverlaidView(view) }} style={toggleLabelStyle(overlaidView === view)} onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'; e.currentTarget.style.transform = 'translateY(-2px)' }} onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'; e.currentTarget.style.transform = 'translateY(0)' }}>
                      <span style={{ fontSize: '12px', fontFamily: 'Courier New', color: overlaidView === view ? 'white' : '#000' }}>{view === 'boxplot' ? 'Box Plots' : view === 'ecdf' ? 'ECDF' : 'Q-Q Plot'}</span>
                    </label>
                  ))}
                </div>
              </div>

              {overlaidView === 'boxplot' && (
                <>
                  <OverlaidBoxPlots runs={analysis.individual_analyses.map((runAnalysis: any, idx: number) => ({ min: runAnalysis.basic_stats?.min || 0, q25: runAnalysis.basic_stats?.q25 || 0, median: runAnalysis.basic_stats?.median || 0, q75: runAnalysis.basic_stats?.q75 || 0, max: runAnalysis.basic_stats?.max || 0, runNumber: idx + 1 }))} />
                  <p style={{ fontSize: '12px', color: '#666', marginTop: '15px', fontStyle: 'italic' }}>Hover over a box plot to see detailed statistics for that run</p>
                </>
              )}

              {overlaidView === 'ecdf' && analysis.ecdf_all_runs && (() => {
                const allXValues = analysis.ecdf_all_runs.flatMap((r: any) => r.x)
                const minX = Math.min(...allXValues)
                const maxX = Math.max(...allXValues)
                const numPoints = 200
                const unifiedX = Array.from({ length: numPoints }, (_, i) => minX + (maxX - minX) * (i / (numPoints - 1)))
                const unifiedData = unifiedX.map((x: number) => {
                  const point: any = { x }
                  analysis.ecdf_all_runs.forEach((runData: any) => {
                    let ecdfValue = 0
                    if (x < runData.x[0]) ecdfValue = 0
                    else if (x > runData.x[runData.x.length - 1]) ecdfValue = 1
                    else {
                      for (let i = 0; i < runData.x.length; i++) {
                        if (runData.x[i] >= x) {
                          ecdfValue = i === 0 ? runData.y[0] : runData.y[i - 1] + (runData.y[i] - runData.y[i - 1]) * (x - runData.x[i - 1]) / (runData.x[i] - runData.x[i - 1])
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
                    <div ref={ecdfChartRef} onClick={handleEcdfChartClick} style={{ cursor: 'pointer' }} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleEcdfChartClick() } }} aria-label="Click to pin or unpin tooltip">
                      <ResponsiveContainer width="100%" height={400}>
<LineChart data={unifiedData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="x" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                        <YAxis />
                        <Tooltip content={(p: unknown) => <AnchoredScrollableTooltip {...(p as ComponentProps<typeof AnchoredScrollableTooltip>)} pinned={ecdfPinned} onHover={(payload, label) => { lastEcdfHoverRef.current = { payload, label } }} labelFormatter={(label) => `x: ${typeof label === 'number' ? label.toFixed(4) : label}`} />} />
                          {ecdfPinned?.label != null && <ReferenceLine x={Number(ecdfPinned.label)} stroke="#666" strokeDasharray="4 4" strokeWidth={1.5} />}
                          {(ecdfSelectedRun != null ? [...analysis.ecdf_all_runs].sort((a: any, b: any) => (a.run === ecdfSelectedRun ? 1 : 0) - (b.run === ecdfSelectedRun ? 1 : 0)) : analysis.ecdf_all_runs).map((runData: any, idx: number) => {
                          const origIdx = analysis.ecdf_all_runs.findIndex((r: any) => r.run === runData.run)
                          const color = QQ_COLORS[(origIdx >= 0 ? origIdx : idx) % QQ_COLORS.length]
                          const opacity = ecdfSelectedRun === null ? 0.6 : (ecdfSelectedRun === runData.run ? 1 : 0.08)
                          return <Line key={runData.run} type="monotone" dataKey={`y${runData.run}`} stroke={color} strokeWidth={ecdfSelectedRun === runData.run ? 2.5 : 1.5} strokeOpacity={opacity} dot={false} name={`Run ${runData.run}`} connectNulls isAnimationActive={false} />
                        })}
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    <div ref={ecdfLegendRef} style={{ marginTop: '15px', display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'center' }}>
                      {analysis.ecdf_all_runs.map((runData: any, idx: number) => {
                        const color = QQ_COLORS[idx % QQ_COLORS.length]
                        const isSelected = ecdfSelectedRun === runData.run
                        return (
                          <label key={runData.run} onClick={(e) => handleEcdfLegendClick(runData.run, e)} style={{ ...toggleLabelStyle(isSelected), color: isSelected ? 'white' : '#000' }} onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'; e.currentTarget.style.transform = 'translateY(-2px)' }} onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'; e.currentTarget.style.transform = 'translateY(0)' }}>
                            <div style={{ width: '20px', height: '12px', background: color, border: '1px solid #000' }} />
                            <span style={{ fontSize: '12px', fontFamily: 'Courier New', color: isSelected ? 'white' : '#000' }}>Run {runData.run}</span>
                          </label>
                        )
                      })}
                    </div>
                    <p style={{ fontSize: '12px', color: '#666', marginTop: '15px', fontStyle: 'italic' }}>Each line represents the ECDF for one run. For uniform distribution, lines should be close to the diagonal.</p>
                  </>
                )
              })()}

              {overlaidView === 'qq' && (() => {
                // Per-run: downsampled (theoretical, sample) sorted by theoretical for fast lookup
                const runPoints = new Map<number, { theoretical: number[]; sample: number[] }>()
                analysis.individual_analyses?.forEach((runAnalysis: any, runIdx: number) => {
                  const sample = runAnalysis.distribution?.qq_plot?.sample
                  const theoretical = runAnalysis.distribution?.qq_plot?.theoretical
                  if (sample?.length && theoretical?.length) {
                    const { sample: s, theoretical: t } = downsampleQqForDisplay(sample, theoretical, MAX_QQ_DISPLAY_POINTS)
                    const byTheoretical = t.map((th, i) => ({ th, sm: s[i]! })).sort((a, b) => a.th - b.th)
                    runPoints.set(runIdx + 1, {
                      theoretical: byTheoretical.map((x) => x.th),
                      sample: byTheoretical.map((x) => x.sm)
                    })
                  }
                })
                const runKeys = Array.from(runPoints.keys()).sort((a, b) => a - b)
                if (runKeys.length === 0) return null
                // Use first run's theoretical as grid (capped)
                const first = runPoints.get(runKeys[0]!)!
                let gridTheoretical = [...first.theoretical]
                if (gridTheoretical.length > MAX_QQ_DISPLAY_POINTS) {
                  const step = (gridTheoretical.length - 1) / (MAX_QQ_DISPLAY_POINTS - 1)
                  gridTheoretical = Array.from({ length: MAX_QQ_DISPLAY_POINTS }, (_, i) =>
                    gridTheoretical[i === MAX_QQ_DISPLAY_POINTS - 1 ? gridTheoretical.length - 1 : Math.round(i * step)]!
                  )
                }
                // Build unified data with binary-search lookup (avoids O(n²) scan)
                const unifiedData = gridTheoretical.map((theoretical) => {
                  const point: Record<string, number> = { theoretical }
                  runKeys.forEach((run) => {
                    const { theoretical: tArr, sample: sArr } = runPoints.get(run)! 
                    const idx = closestIndexSorted(tArr, theoretical)
                    point[`sample${run}`] = idx >= 0 ? sArr[idx]! : theoretical
                  })
                  return point
                })
                return (
                  <>
                    <div ref={qqChartRef} onClick={handleQqChartClick} style={{ cursor: 'pointer' }} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleQqChartClick() } }} aria-label="Click to pin or unpin tooltip">
                      <ResponsiveContainer width="100%" height={400}>
<LineChart data={unifiedData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="theoretical" name="Theoretical" type="number" tickFormatter={(v) => typeof v === 'number' ? v.toFixed(4) : String(v)} />
                          <YAxis name="Sample" type="number" tickFormatter={(v) => typeof v === 'number' ? v.toFixed(4) : String(v)} />
                          <Tooltip
                            content={(p: unknown) => (
                              <AnchoredScrollableTooltip
                                {...(p as ComponentProps<typeof AnchoredScrollableTooltip>)}
                                pinned={qqPinned}
                                onHover={(payload, label) => { lastQqHoverRef.current = { payload, label } }}
                                labelFormatter={(label) => `Theoretical: ${Number(label).toFixed(4)}`}
                                formatter={(value) => [value?.toFixed(6) ?? '', '']}
                              />
                            )}
                          />
                          {qqPinned?.label != null && <ReferenceLine x={Number(qqPinned.label)} stroke="#666" strokeDasharray="4 4" strokeWidth={1.5} />}
                          {(qqSelectedRun != null ? [...runKeys].sort((a, b) => (a === qqSelectedRun ? 1 : 0) - (b === qqSelectedRun ? 1 : 0) || a - b) : runKeys).map((run: number) => {
                          const origIdx = runKeys.indexOf(run)
                          const color = QQ_COLORS[origIdx % QQ_COLORS.length]
                          const opacity = qqSelectedRun === null ? 0.6 : (qqSelectedRun === run ? 1 : 0.08)
                          return <Line key={run} type="monotone" dataKey={`sample${run}`} stroke={color} strokeWidth={qqSelectedRun === run ? 2.5 : 1.5} strokeOpacity={opacity} dot={{ r: 2 }} connectNulls name={`Run ${run}`} isAnimationActive={false} />
                        })}
                        <Line type="monotone" dataKey="theoretical" stroke="#000" strokeWidth={2} strokeDasharray="5 5" dot={false} name="y=x" isAnimationActive={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    <div ref={qqLegendRef} style={{ marginTop: '15px', display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'center' }}>
                      {runKeys.map((run: number, idx: number) => {
                        const color = QQ_COLORS[idx % QQ_COLORS.length]
                        const isSelected = qqSelectedRun === run
                        return (
                          <label key={run} onClick={(e) => handleQqLegendClick(run, e)} style={toggleLabelStyle(isSelected)} onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'; e.currentTarget.style.transform = 'translateY(-2px)' }} onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'; e.currentTarget.style.transform = 'translateY(0)' }}>
                            <div style={{ width: '20px', height: '12px', background: color, border: '1px solid #000' }} />
                            <span style={{ fontSize: '12px', fontFamily: 'Courier New', color: isSelected ? 'white' : '#000' }}>Run {run}</span>
                          </label>
                        )
                      })}
                    </div>
                    <p style={{ fontSize: '12px', color: '#666', marginTop: '15px', fontStyle: 'italic' }}>Each color represents one run. Points should lie close to the diagonal line for uniform distribution.</p>
                  </>
                )
              })()}
            </div>
          )}
        </>
      )}

      {multiRunPage === 4 && analysis.distribution_deviation && (
        <div className="chart-container">
          <h4>Distribution Deviation Metrics</h4>
          <p style={{ fontSize: '12px', color: '#666', marginBottom: '20px', fontStyle: 'italic' }}>
            ECDF and Q-Q metrics across runs. Each run is normalized to [0, 1] before computing deviations against uniform.
          </p>

          <div className="stats-tables-container">
            <div className="chart-container">
              <h5 style={{ marginBottom: '12px' }}>ECDF Deviation (Uniformity)</h5>
              <table className="stats-table">
                <thead>
                  <tr><th>Metric</th><th>Mean</th><th>St. Dev</th><th>CV</th></tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Max vertical deviation (K-S statistic)</strong></td>
                    <td>{analysis.distribution_deviation.ecdf?.ks_statistic?.mean?.toFixed(4) ?? 'N/A'}</td>
                    <td>{analysis.distribution_deviation.ecdf?.ks_statistic?.std_dev?.toFixed(4) ?? 'N/A'}</td>
                    <td>{analysis.distribution_deviation.ecdf?.ks_statistic?.cv != null ? (analysis.distribution_deviation.ecdf.ks_statistic.cv * 100).toFixed(2) + '%' : 'N/A'}</td>
                  </tr>
                  <tr>
                    <td><strong>Mean absolute deviation (MAD)</strong></td>
                    <td>{analysis.distribution_deviation.ecdf?.mad?.mean?.toFixed(4) ?? 'N/A'}</td>
                    <td>{analysis.distribution_deviation.ecdf?.mad?.std_dev?.toFixed(4) ?? 'N/A'}</td>
                    <td>{analysis.distribution_deviation.ecdf?.mad?.cv != null ? (analysis.distribution_deviation.ecdf.mad.cv * 100).toFixed(2) + '%' : 'N/A'}</td>
                  </tr>
                </tbody>
              </table>
              <p style={{ fontSize: '11px', color: '#888', marginTop: '8px' }}>
                K-S captures worst-point deviation; MAD captures average deviation across the ECDF.
              </p>
            </div>

            {analysis.distribution_deviation.ecdf?.regional_deviation?.labels?.length > 0 && (
              <div className="chart-container">
                <h5 style={{ marginBottom: '12px' }}>Regional ECDF Deviation</h5>
                <table className="stats-table">
                  <thead>
                    <tr>
                      <th>Region</th>
                      <th>Mean deviation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.distribution_deviation.ecdf.regional_deviation.labels.map((label: string, i: number) => (
                      <tr key={label}>
                        <td><strong>{label}</strong></td>
                        <td>{(analysis.distribution_deviation.ecdf.regional_deviation.mean[i] ?? 0).toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="chart-container">
              <h5 style={{ marginBottom: '12px' }}>Q-Q Plot Deviation (vs diagonal y=x)</h5>
              <table className="stats-table">
                <thead>
                  <tr><th>Metric</th><th>Mean</th><th>St. Dev</th></tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>R² (coefficient of determination)</strong></td>
                    <td>{analysis.distribution_deviation.qq?.r_squared?.mean?.toFixed(4) ?? 'N/A'}</td>
                    <td>{analysis.distribution_deviation.qq?.r_squared?.std_dev?.toFixed(4) ?? 'N/A'}</td>
                  </tr>
                  <tr>
                    <td><strong>MSE from diagonal</strong></td>
                    <td>{analysis.distribution_deviation.qq?.mse_from_diagonal?.mean?.toFixed(6) ?? 'N/A'}</td>
                    <td>{analysis.distribution_deviation.qq?.mse_from_diagonal?.std_dev?.toFixed(6) ?? 'N/A'}</td>
                  </tr>
                </tbody>
              </table>
              <p style={{ fontSize: '11px', color: '#888', marginTop: '8px' }}>
                R² measures how well points follow the diagonal; higher is better. MSE is average squared distance from y=x.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MultiRunAnalysisView
