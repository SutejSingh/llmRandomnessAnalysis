import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { t } from '../../i18n'

interface IndependenceSectionProps {
  analysis: any
  view: 'timeseries' | 'acf' | 'lag1'
  onViewChange: (view: 'timeseries' | 'acf' | 'lag1') => void
  chartHeight?: number
}

const IndependenceSection = ({ analysis, view, onViewChange, chartHeight = 250 }: IndependenceSectionProps) => {
  const timeSeriesData = analysis.independence?.time_series?.index?.map((idx: number) => ({ index: idx, value: analysis.independence.time_series.values[idx] })) || []
  const acfData = analysis.independence?.autocorrelation?.lags?.map((lag: number, idx: number) => ({ lag, correlation: analysis.independence.autocorrelation.values[idx] })) || []
  const lag1Data = analysis.independence?.lag1_scatter?.x?.map((x: number, idx: number) => ({ x, y: analysis.independence.lag1_scatter.y[idx] })) || []

  if (!analysis.independence) return null

  return (
    <div className="stats-section">
      <h3>{t('independenceSection.title')}</h3>
      <div className="sub-nav-buttons">
        <button onClick={() => onViewChange('timeseries')} className={view === 'timeseries' ? 'active' : ''}>{t('independenceSection.timeSeries')}</button>
        <button onClick={() => onViewChange('acf')} className={view === 'acf' ? 'active' : ''}>{t('independenceSection.acf')}</button>
        <button onClick={() => onViewChange('lag1')} className={view === 'lag1' ? 'active' : ''}>{t('independenceSection.lag1Scatter')}</button>
      </div>

      {view === 'timeseries' && (
        <div className="chart-container">
          <h4>{t('independenceSection.timeSeriesTitle')}</h4>
          <ResponsiveContainer width="100%" height={chartHeight}>
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

      {view === 'acf' && (
        <div className="chart-container">
          <h4>{t('independenceSection.acfTitle')}</h4>
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart data={acfData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="lag" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
              <YAxis domain={[-1, 1]} />
              <Tooltip />
              <Bar dataKey="correlation" fill="#000" />
            </BarChart>
          </ResponsiveContainer>
          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>{t('independenceSection.acfNote')}</p>
        </div>
      )}

      {view === 'lag1' && (
        <div className="chart-container">
          <h4>{t('independenceSection.lag1ScatterTitle')}</h4>
          <ResponsiveContainer width="100%" height={chartHeight}>
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
  )
}

export default IndependenceSection
