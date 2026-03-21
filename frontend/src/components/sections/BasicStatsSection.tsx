import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { t } from '../../i18n'
import { formatFixed } from '../../utils/formatStat'
import BoxPlot from '../charts/BoxPlot'

interface BasicStatsSectionProps {
  analysis: any
  view: 'stats' | 'histogram' | 'boxplot'
  onViewChange: (view: 'stats' | 'histogram' | 'boxplot') => void
}

const BasicStatsSection = ({ analysis, view, onViewChange }: BasicStatsSectionProps) => {
  const histogramData = analysis.distribution?.histogram?.edges?.slice(0, -1).map((edge: number, idx: number) => ({
    bin: formatFixed(edge, 4, ''),
    count: analysis.distribution.histogram.counts[idx]
  })) || []

  if (!analysis.basic_stats) return null

  const na = t('basicStats.na')
  return (
    <div className="stats-section">
      <h3>{t('basicStats.title')}</h3>
      <div className="sub-nav-buttons">
        <button onClick={() => onViewChange('stats')} className={view === 'stats' ? 'active' : ''}>{t('basicStats.statistics')}</button>
        <button onClick={() => onViewChange('histogram')} className={view === 'histogram' ? 'active' : ''}>{t('basicStats.histogram')}</button>
        <button onClick={() => onViewChange('boxplot')} className={view === 'boxplot' ? 'active' : ''}>{t('basicStats.boxPlot')}</button>
      </div>

      {view === 'stats' && (
        <div className="stats-grid">
          <div className="stat-card"><div className="stat-label">{t('basicStats.mean')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.mean, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.median')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.median, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.mode')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.mode, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.stdDev')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.std, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.variance')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.variance, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.min')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.min, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.max')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.max, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.q25')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.q25, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.q75')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.q75, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.q95')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.q95, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.skewness')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.skewness, 4, na)}</div></div>
          <div className="stat-card"><div className="stat-label">{t('basicStats.kurtosis')}</div><div className="stat-value">{formatFixed(analysis.basic_stats.kurtosis, 4, na)}</div></div>
        </div>
      )}

      {view === 'histogram' && (
        <div className="chart-container">
          <h4>{t('basicStats.histogramTitle')}</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={histogramData} margin={{ top: 10, right: 20, left: 60, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="bin"
                angle={-45}
                textAnchor="end"
                height={80}
                tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value}
                label={{ value: 'Value (bin start)', position: 'bottom', offset: 20 }}
              />
              <YAxis label={{ value: 'Frequency', angle: -90, position: 'left', offset: 40 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#000" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {view === 'boxplot' && (
        <div className="chart-container">
          <h4>{t('basicStats.boxPlotTitle')}</h4>
          <BoxPlot min={analysis.basic_stats.min} q25={analysis.basic_stats.q25} median={analysis.basic_stats.median} q75={analysis.basic_stats.q75} max={analysis.basic_stats.max} />
        </div>
      )}
    </div>
  )
}

export default BasicStatsSection
