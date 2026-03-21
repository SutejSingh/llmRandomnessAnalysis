import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { t } from '../../i18n'
import { formatFixed } from '../../utils/formatStat'

interface StationaritySectionProps {
  analysis: any
  view: 'rolling' | 'chunks'
  onViewChange: (view: 'rolling' | 'chunks') => void
  chartHeight?: number
}

const StationaritySection = ({ analysis, view, onViewChange, chartHeight = 250 }: StationaritySectionProps) => {
  const rollingData = analysis.stationarity?.rolling_mean?.index?.map((idx: number) => ({
    index: idx,
    mean: analysis.stationarity.rolling_mean.values[idx],
    std: analysis.stationarity.rolling_std.values[idx]
  })) || []

  if (!analysis.stationarity) return null

  const na = t('basicStats.na')

  return (
    <div className="stats-section">
      <h3>{t('stationaritySection.title')}</h3>
      <div className="sub-nav-buttons">
        <button onClick={() => onViewChange('rolling')} className={view === 'rolling' ? 'active' : ''}>{t('stationaritySection.rollingStats')}</button>
        <button onClick={() => onViewChange('chunks')} className={view === 'chunks' ? 'active' : ''}>{t('stationaritySection.chunks')}</button>
      </div>

      {view === 'rolling' && (
        <div className="chart-container">
          <h4>{t('stationaritySection.rollingMeanStd')}</h4>
          <ResponsiveContainer width="100%" height={chartHeight}>
            <LineChart data={rollingData} margin={{ top: 10, right: 60, left: 60, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="index"
                tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value}
                label={{ value: 'Index', position: 'bottom', offset: 20 }}
              />
              <YAxis yAxisId="left" label={{ value: 'Value', angle: -90, position: 'left', offset: 40 }} />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={false}
                axisLine={false}
                label={undefined}
              />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="mean" stroke="#000" strokeWidth={2} name={t('stationaritySection.rollingMean')} />
              <Line yAxisId="right" type="monotone" dataKey="std" stroke="#666" strokeWidth={2} name={t('stationaritySection.rollingStd')} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {view === 'chunks' && (
        <div className="chunks-container">
          <h4>{t('stationaritySection.chunkedStatistics')}</h4>
          <div className="chunks-grid">
            {analysis.stationarity.chunks.map((chunk: any) => (
              <div key={chunk.chunk} className="chunk-card">
                <h5>{t('stationaritySection.chunkN', { n: chunk.chunk })}</h5>
                <p>{t('basicStats.mean')}: {formatFixed(chunk.mean, 4, na)}</p>
                <p>{t('basicStats.stdDev')}: {formatFixed(chunk.std, 4, na)}</p>
                <p>{t('basicStats.min')}: {formatFixed(chunk.min, 4, na)}</p>
                <p>{t('basicStats.max')}: {formatFixed(chunk.max, 4, na)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default StationaritySection
