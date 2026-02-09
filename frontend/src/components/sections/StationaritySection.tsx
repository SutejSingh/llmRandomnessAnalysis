import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { t } from '../../i18n'

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
            <LineChart data={rollingData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="index" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
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
                <p>{t('basicStats.mean')}: {chunk.mean.toFixed(4)}</p>
                <p>{t('basicStats.stdDev')}: {chunk.std.toFixed(4)}</p>
                <p>{t('basicStats.min')}: {chunk.min.toFixed(4)}</p>
                <p>{t('basicStats.max')}: {chunk.max.toFixed(4)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default StationaritySection
