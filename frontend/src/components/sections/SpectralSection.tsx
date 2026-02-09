import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { t } from '../../i18n'

interface SpectralSectionProps {
  analysis: any
  view: 'magnitude' | 'power'
  onViewChange: (view: 'magnitude' | 'power') => void
  chartHeight?: number
}

const SpectralSection = ({ analysis, view, onViewChange, chartHeight = 250 }: SpectralSectionProps) => {
  const spectralData = analysis.spectral?.frequencies?.map((freq: number, idx: number) => ({
    frequency: freq,
    magnitude: analysis.spectral.magnitude[idx],
    power: analysis.spectral.power[idx]
  })) || []

  if (!analysis.spectral) return null

  const toggleStyle = (isActive: boolean) => ({
    display: 'flex' as const,
    alignItems: 'center' as const,
    gap: '8px',
    cursor: 'pointer',
    userSelect: 'none' as const,
    padding: '6px 12px',
    border: '2px solid #999',
    borderRadius: '4px',
    backgroundColor: isActive ? '#000' : 'white',
    transition: 'all 0.2s',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
  })

  return (
    <div className="stats-section">
      <h3>{t('spectralSection.title')}</h3>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {([
            { id: 'magnitude' as const, label: t('spectralSection.fftMagnitude') },
            { id: 'power' as const, label: t('spectralSection.powerSpectrum') }
          ]).map(({ id, label }) => (
            <label
              key={id}
              onClick={(e) => { e.stopPropagation(); onViewChange(id) }}
              style={toggleStyle(view === id)}
              onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
              onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'; e.currentTarget.style.transform = 'translateY(0)' }}
            >
              <span style={{ fontSize: '12px', fontFamily: 'Courier New', color: view === id ? 'white' : '#000' }}>{label}</span>
            </label>
          ))}
        </div>
      </div>

      {view === 'magnitude' && (
        <div className="chart-container">
          <h4>{t('spectralSection.fftMagnitudeTitle')}</h4>
          <ResponsiveContainer width="100%" height={chartHeight}>
            <LineChart data={spectralData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="frequency" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="magnitude" stroke="#000" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {view === 'power' && (
        <div className="chart-container">
          <h4>{t('spectralSection.powerSpectrumTitle')}</h4>
          <ResponsiveContainer width="100%" height={chartHeight}>
            <LineChart data={spectralData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="frequency" tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="power" stroke="#666" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

export default SpectralSection
