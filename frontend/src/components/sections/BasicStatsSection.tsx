import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import BoxPlot from '../charts/BoxPlot'

interface BasicStatsSectionProps {
  analysis: any
  view: 'stats' | 'histogram' | 'boxplot'
  onViewChange: (view: 'stats' | 'histogram' | 'boxplot') => void
}

const BasicStatsSection = ({ analysis, view, onViewChange }: BasicStatsSectionProps) => {
  const histogramData = analysis.distribution?.histogram?.edges?.slice(0, -1).map((edge: number, idx: number) => ({
    bin: edge.toFixed(4),
    count: analysis.distribution.histogram.counts[idx]
  })) || []

  if (!analysis.basic_stats) return null

  return (
    <div className="stats-section">
      <h3>Basic Descriptive Statistics</h3>
      <div className="sub-nav-buttons">
        <button onClick={() => onViewChange('stats')} className={view === 'stats' ? 'active' : ''}>Statistics</button>
        <button onClick={() => onViewChange('histogram')} className={view === 'histogram' ? 'active' : ''}>Histogram</button>
        <button onClick={() => onViewChange('boxplot')} className={view === 'boxplot' ? 'active' : ''}>Box Plot</button>
      </div>

      {view === 'stats' && (
        <div className="stats-grid">
          <div className="stat-card"><div className="stat-label">Mean</div><div className="stat-value">{analysis.basic_stats.mean.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Median</div><div className="stat-value">{analysis.basic_stats.median.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Std Dev</div><div className="stat-value">{analysis.basic_stats.std.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Variance</div><div className="stat-value">{analysis.basic_stats.variance.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Min</div><div className="stat-value">{analysis.basic_stats.min.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Max</div><div className="stat-value">{analysis.basic_stats.max.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Q25</div><div className="stat-value">{analysis.basic_stats.q25.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Q75</div><div className="stat-value">{analysis.basic_stats.q75.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Q95</div><div className="stat-value">{analysis.basic_stats.q95.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Skewness</div><div className="stat-value">{analysis.basic_stats.skewness.toFixed(4)}</div></div>
          <div className="stat-card"><div className="stat-label">Kurtosis</div><div className="stat-value">{analysis.basic_stats.kurtosis.toFixed(4)}</div></div>
        </div>
      )}

      {view === 'histogram' && (
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

      {view === 'boxplot' && (
        <div className="chart-container">
          <h4>Box Plot</h4>
          <BoxPlot min={analysis.basic_stats.min} q25={analysis.basic_stats.q25} median={analysis.basic_stats.median} q75={analysis.basic_stats.q75} max={analysis.basic_stats.max} />
        </div>
      )}
    </div>
  )
}

export default BasicStatsSection
