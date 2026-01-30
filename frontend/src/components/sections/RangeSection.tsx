import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface RangeSectionProps {
  analysis: any
  view: 'boundary' | 'ecdf'
  onViewChange: (view: 'boundary' | 'ecdf') => void
}

const RangeSection = ({ analysis, view, onViewChange }: RangeSectionProps) => {
  const ecdfData = analysis.range_behavior?.ecdf?.x?.map((x: number, idx: number) => ({ x, y: analysis.range_behavior.ecdf.y[idx] })) || []

  if (!analysis.range_behavior) return null

  return (
    <div className="stats-section">
      <h3>Range & Boundary Behavior</h3>
      <div className="sub-nav-buttons">
        <button onClick={() => onViewChange('boundary')} className={view === 'boundary' ? 'active' : ''}>Boundary Stats</button>
        <button onClick={() => onViewChange('ecdf')} className={view === 'ecdf' ? 'active' : ''}>ECDF</button>
      </div>

      {view === 'boundary' && (
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

      {view === 'ecdf' && (
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
  )
}

export default RangeSection
