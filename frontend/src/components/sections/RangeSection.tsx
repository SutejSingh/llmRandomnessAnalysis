import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { t } from '../../i18n'
import { formatFixed } from '../../utils/formatStat'

interface RangeSectionProps {
  analysis: any
  view: 'boundary' | 'ecdf'
  onViewChange: (view: 'boundary' | 'ecdf') => void
}

const RangeSection = ({ analysis, view, onViewChange }: RangeSectionProps) => {
  const ecdfData = analysis.range_behavior?.ecdf?.x?.map((x: number, idx: number) => ({ x, y: analysis.range_behavior.ecdf.y[idx] })) || []

  if (!analysis.range_behavior) return null

  const na = t('basicStats.na')
  const b = analysis.range_behavior.boundaries

  return (
    <div className="stats-section">
      <h3>{t('rangeSection.title')}</h3>
      <div className="sub-nav-buttons">
        <button onClick={() => onViewChange('boundary')} className={view === 'boundary' ? 'active' : ''}>{t('rangeSection.boundaryStats')}</button>
        <button onClick={() => onViewChange('ecdf')} className={view === 'ecdf' ? 'active' : ''}>{t('rangeSection.ecdf')}</button>
      </div>

      {view === 'boundary' && (
        <div className="boundary-info">
          <div className="info-card">
            <h4>{t('rangeSection.boundaryStatistics')}</h4>
            <p>{t('basicStats.min')}: {formatFixed(b.min, 4, na)}</p>
            <p>{t('basicStats.max')}: {formatFixed(b.max, 4, na)}</p>
            <p>{t('rangeSection.nearMin', { count: b.near_min_count, pct: formatFixed(b.near_min_pct, 4, na) })}</p>
            <p>{t('rangeSection.nearMax', { count: b.near_max_count, pct: formatFixed(b.near_max_pct, 4, na) })}</p>
          </div>
        </div>
      )}

      {view === 'ecdf' && (
        <div className="chart-container">
          <h4>{t('rangeSection.ecdfTitle')}</h4>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={ecdfData} margin={{ top: 10, right: 20, left: 60, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="x"
                tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value}
                label={{ value: 'Value', position: 'bottom', offset: 20 }}
              />
              <YAxis label={{ value: 'Cumulative probability', angle: -90, position: 'left', offset: 45 }} />
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
