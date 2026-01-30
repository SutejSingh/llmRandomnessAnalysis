import { AreaChart, Area, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface DistributionSectionProps {
  analysis: any
  view: 'tests' | 'kde' | 'qq'
  onViewChange: (view: 'tests' | 'kde' | 'qq') => void
}

const DistributionSection = ({ analysis, view, onViewChange }: DistributionSectionProps) => {
  const kdeData = analysis.distribution?.kde?.x?.map((x: number, idx: number) => ({ x, y: analysis.distribution.kde.y[idx] })) || []
  const qqData = analysis.distribution?.qq_plot?.sample?.map((sample: number, idx: number) => ({ sample, theoretical: analysis.distribution.qq_plot.theoretical[idx] })) || []

  if (!analysis.distribution) return null

  return (
    <div className="stats-section">
      <h3>Distribution Shape Analysis</h3>
      <div className="sub-nav-buttons">
        <button onClick={() => onViewChange('tests')} className={view === 'tests' ? 'active' : ''}>Tests</button>
        <button onClick={() => onViewChange('kde')} className={view === 'kde' ? 'active' : ''}>KDE</button>
        <button onClick={() => onViewChange('qq')} className={view === 'qq' ? 'active' : ''}>Q-Q Plot</button>
      </div>

      {view === 'tests' && (
        <div className="test-results test-results--fit">
          <div className="test-card">
            <h4>Uniformity Test</h4>
            <p>Kolmogorov-Smirnov: p = {analysis.distribution.is_uniform.ks_p.toFixed(4)}</p>
            <p className={analysis.distribution.is_uniform.ks_p > 0.05 ? 'pass' : 'fail'}>
              {analysis.distribution.is_uniform.ks_p > 0.05 ? '✓ Likely Uniform' : '✗ Not Uniform'}
            </p>
          </div>
        </div>
      )}

      {view === 'kde' && (
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

      {view === 'qq' && (
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
          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>Points should lie along the diagonal line if uniformly distributed</p>
        </div>
      )}
    </div>
  )
}

export default DistributionSection
