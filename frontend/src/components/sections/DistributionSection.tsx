import { AreaChart, Area, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { t } from '../../i18n'
import { formatFixed } from '../../utils/formatStat'

interface DistributionSectionProps {
  analysis: any
  view: 'tests' | 'kde' | 'qq'
  onViewChange: (view: 'tests' | 'kde' | 'qq') => void
}

const DistributionSection = ({ analysis, view, onViewChange }: DistributionSectionProps) => {
  const kdeData = analysis.distribution?.kde?.x?.map((x: number, idx: number) => ({ x, y: analysis.distribution.kde.y[idx] })) || []
  const qqData = analysis.distribution?.qq_plot?.sample?.map((sample: number, idx: number) => ({ sample, theoretical: analysis.distribution.qq_plot.theoretical[idx] })) || []

  if (!analysis.distribution) return null

  const na = t('basicStats.na')
  const ksP = analysis.distribution.is_uniform.ks_p
  const ksPass = typeof ksP === 'number' && Number.isFinite(ksP) && ksP > 0.05

  return (
    <div className="stats-section">
      <h3>{t('distributionSection.title')}</h3>
      <div className="sub-nav-buttons">
        <button onClick={() => onViewChange('tests')} className={view === 'tests' ? 'active' : ''}>{t('distributionSection.tests')}</button>
        <button onClick={() => onViewChange('kde')} className={view === 'kde' ? 'active' : ''}>{t('distributionSection.kde')}</button>
        <button onClick={() => onViewChange('qq')} className={view === 'qq' ? 'active' : ''}>{t('distributionSection.qqPlot')}</button>
      </div>

      {view === 'tests' && (
        <div className="test-results test-results--fit">
          <div className="test-card">
            <h4>{t('distributionSection.uniformityTest')}</h4>
            <p>{t('distributionSection.kolmogorovSmirnov', { p: formatFixed(ksP, 4, na) })}</p>
            <p className={ksPass ? 'pass' : 'fail'}>
              {ksPass ? t('distributionSection.likelyUniform') : t('distributionSection.notUniform')}
            </p>
          </div>
        </div>
      )}

      {view === 'kde' && (
        <div className="chart-container">
          <h4>{t('distributionSection.kernelDensityEstimate')}</h4>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={kdeData} margin={{ top: 10, right: 20, left: 60, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="x"
                tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value}
                label={{ value: 'Value', position: 'bottom', offset: 20 }}
              />
              <YAxis label={{ value: 'Density', angle: -90, position: 'left', offset: 40 }} />
              <Tooltip />
              <Area type="monotone" dataKey="y" stroke="#000" fill="#000" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {view === 'qq' && (
        <div className="chart-container">
          <h4>{t('distributionSection.qqPlotUniform')}</h4>
          <ResponsiveContainer width="100%" height={250}>
            <ScatterChart data={qqData} margin={{ top: 10, right: 20, left: 70, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="theoretical"
                name={t('distributionSection.theoretical')}
                tickFormatter={(value) => typeof value === 'number' ? value.toFixed(4) : value}
                label={{ value: 'Theoretical quantile (Uniform)', position: 'bottom', offset: 20 }}
              />
              <YAxis
                dataKey="sample"
                name={t('distributionSection.sample')}
                label={{ value: 'Sample quantile', angle: -90, position: 'left', offset: 45 }}
              />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Q-Q" dataKey="sample" fill="#000" />
            </ScatterChart>
          </ResponsiveContainer>
          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>{t('distributionSection.qqDiagonalNote')}</p>
        </div>
      )}
    </div>
  )
}

export default DistributionSection
