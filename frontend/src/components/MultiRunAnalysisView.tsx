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
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  AreaChart,
  Area
} from 'recharts'
import { OverlaidBoxPlots } from './charts'

const QQ_COLORS = ['#DC143C', '#228B22', '#1E90FF', '#FF8C00', '#9370DB', '#00CED1', '#FF1493', '#FFD700', '#8B4513', '#32CD32', '#000000']

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
  const [multiRunPage, setMultiRunPage] = useState<1 | 2 | 3>(1)
  const [overlaidView, setOverlaidView] = useState<'boxplot' | 'ecdf' | 'qq'>('boxplot')
  const [frequencyHistogramView, setFrequencyHistogramView] = useState<'histogram' | 'kde'>('histogram')
  const [qqSelectedRun, setQqSelectedRun] = useState<number | null>(null)
  const [ecdfSelectedRun, setEcdfSelectedRun] = useState<number | null>(null)
  const qqLegendRef = useRef<HTMLDivElement>(null)
  const ecdfLegendRef = useRef<HTMLDivElement>(null)

  const valueFrequencyHistogramData = computeValueFrequencyHistogram(allRuns)
  const allNumbersKdeData = computeAllNumbersKde(allRuns)

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
                <table className="stats-table" style={{ marginBottom: '30px' }}>
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
                {onSelectRun && <p style={{ fontSize: '12px', color: '#666', marginBottom: '20px', fontStyle: 'italic' }}>Click on a row to view detailed statistics for that run</p>}
              </div>
            )}
          </div>
          {analysis.autocorrelation_table && (
            <div className="chart-container">
              <h4>Autocorrelation Analysis by Run</h4>
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
                  <AreaChart data={allNumbersKdeData.map((d) => ({ x: d.x, density: d.density }))} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
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
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={unifiedData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="x" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                        <YAxis />
                        <Tooltip />
                        {(ecdfSelectedRun != null ? [...analysis.ecdf_all_runs].sort((a: any, b: any) => (a.run === ecdfSelectedRun ? 1 : 0) - (b.run === ecdfSelectedRun ? 1 : 0)) : analysis.ecdf_all_runs).map((runData: any, idx: number) => {
                          const origIdx = analysis.ecdf_all_runs.findIndex((r: any) => r.run === runData.run)
                          const color = QQ_COLORS[(origIdx >= 0 ? origIdx : idx) % QQ_COLORS.length]
                          const opacity = ecdfSelectedRun === null ? 0.6 : (ecdfSelectedRun === runData.run ? 1 : 0.08)
                          return <Line key={runData.run} type="monotone" dataKey={`y${runData.run}`} stroke={color} strokeWidth={ecdfSelectedRun === runData.run ? 2.5 : 1.5} strokeOpacity={opacity} dot={false} name={`Run ${runData.run}`} connectNulls />
                        })}
                      </LineChart>
                    </ResponsiveContainer>
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
                const allQqPoints: any[] = []
                analysis.individual_analyses.forEach((runAnalysis: any, runIdx: number) => {
                  if (runAnalysis.distribution?.qq_plot?.sample && runAnalysis.distribution?.qq_plot?.theoretical) {
                    runAnalysis.distribution.qq_plot.sample.forEach((sample: number, idx: number) => {
                      allQqPoints.push({ theoretical: runAnalysis.distribution.qq_plot.theoretical[idx], sample, run: runIdx + 1 })
                    })
                  }
                })
                const runsMap = new Map<number, any[]>()
                allQqPoints.forEach(point => { const run = point.run; if (!runsMap.has(run)) runsMap.set(run, []); runsMap.get(run)!.push({ theoretical: point.theoretical, sample: point.sample }) })
                const allTheoretical = Array.from(new Set(allQqPoints.map(p => p.theoretical))).sort((a, b) => a - b)
                const unifiedData = allTheoretical.map(theoretical => {
                  const point: any = { theoretical }
                  runsMap.forEach((points, run) => {
                    let sampleValue: number | null = null
                    for (const p of points) { if (Math.abs(p.theoretical - theoretical) < 0.0001) { sampleValue = p.sample; break } }
                    if (sampleValue === null && points.length > 0) {
                      let closestIdx = 0, minDist = Math.abs(points[0].theoretical - theoretical)
                      for (let i = 1; i < points.length; i++) { const dist = Math.abs(points[i].theoretical - theoretical); if (dist < minDist) { minDist = dist; closestIdx = i } }
                      sampleValue = points[closestIdx].sample
                    }
                    point[`sample${run}`] = sampleValue
                  })
                  return point
                })
                const runKeys = Array.from(runsMap.keys()).sort((a, b) => a - b)
                return (
                  <>
                    <ResponsiveContainer width="100%" height={400}>
                      <ScatterChart data={unifiedData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="theoretical" name="Theoretical" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
                        <YAxis name="Sample" />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                        {(qqSelectedRun != null ? [...runKeys].sort((a, b) => (a === qqSelectedRun ? 1 : 0) - (b === qqSelectedRun ? 1 : 0) || a - b) : runKeys).map((run: number) => {
                          const origIdx = runKeys.indexOf(run)
                          const color = QQ_COLORS[origIdx % QQ_COLORS.length]
                          const opacity = qqSelectedRun === null ? 0.6 : (qqSelectedRun === run ? 1 : 0.08)
                          return <Scatter key={run} dataKey={`sample${run}`} fill={color} fillOpacity={opacity} stroke={color} strokeWidth={qqSelectedRun === run ? 2 : 1} name={`Run ${run}`} />
                        })}
                        <Line type="linear" dataKey="theoretical" stroke="#000" strokeWidth={2} strokeDasharray="5 5" dot={false} name="y=x" />
                      </ScatterChart>
                    </ResponsiveContainer>
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
    </div>
  )
}

export default MultiRunAnalysisView
