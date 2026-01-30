import {
  BasicStatsSection,
  DistributionSection,
  RangeSection,
  IndependenceSection,
  StationaritySection,
  SpectralSection,
  NistTestsSection
} from './sections'

interface PerRunAnalysisViewProps {
  analysis: any
  selectedRun: number
  onSelectedRunChange: (run: number) => void
  perRunTab: string
  onPerRunTabChange: (tab: string) => void
  basicView: 'stats' | 'histogram' | 'boxplot'
  onBasicViewChange: (view: 'stats' | 'histogram' | 'boxplot') => void
  distributionView: 'tests' | 'kde' | 'qq'
  onDistributionViewChange: (view: 'tests' | 'kde' | 'qq') => void
  rangeView: 'boundary' | 'ecdf'
  onRangeViewChange: (view: 'boundary' | 'ecdf') => void
  independenceView: 'timeseries' | 'acf' | 'lag1'
  onIndependenceViewChange: (view: 'timeseries' | 'acf' | 'lag1') => void
  stationarityView: 'rolling' | 'chunks'
  onStationarityViewChange: (view: 'rolling' | 'chunks') => void
  spectralView: 'magnitude' | 'power'
  onSpectralViewChange: (view: 'magnitude' | 'power') => void
}

const PerRunAnalysisView = ({
  analysis,
  selectedRun,
  onSelectedRunChange,
  perRunTab,
  onPerRunTabChange,
  basicView,
  onBasicViewChange,
  distributionView,
  onDistributionViewChange,
  rangeView,
  onRangeViewChange,
  independenceView,
  onIndependenceViewChange,
  stationarityView,
  onStationarityViewChange,
  spectralView,
  onSpectralViewChange
}: PerRunAnalysisViewProps) => {
  const individualAnalyses = analysis.individual_analyses || []
  if (individualAnalyses.length === 0) return null

  const numRuns = individualAnalyses.length
  const currentRun = selectedRun >= 1 && selectedRun <= numRuns ? selectedRun : 1
  const runAnalysis = individualAnalyses[currentRun - 1]
  if (!runAnalysis) return null

  const setRun = (r: number) => {
    onSelectedRunChange(r)
    onPerRunTabChange('basic')
  }

  return (
    <>
      <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() => setRun(Math.max(1, currentRun - 1))}
          disabled={currentRun <= 1}
          title="Previous run"
          aria-label="Previous run"
          style={{ padding: '8px 12px', border: `2px solid ${currentRun <= 1 ? '#999' : '#000'}`, borderRadius: '6px', background: currentRun <= 1 ? '#eee' : '#fff', cursor: currentRun <= 1 ? 'not-allowed' : 'pointer', fontSize: '16px', lineHeight: 1 }}
        >
          ‹
        </button>
        <label style={{ marginRight: '8px', fontWeight: '600' }}>Run:</label>
        <select
          value={currentRun}
          onChange={(e) => setRun(parseInt(e.target.value, 10))}
          style={{ padding: '8px 12px', border: '2px solid #000', borderRadius: '6px', fontSize: '14px', cursor: 'pointer', minWidth: '120px' }}
        >
          {individualAnalyses.map((_: any, idx: number) => (
            <option key={idx + 1} value={idx + 1}>Run {idx + 1}</option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => setRun(Math.min(numRuns, currentRun + 1))}
          disabled={currentRun >= numRuns}
          title="Next run"
          aria-label="Next run"
          style={{ padding: '8px 12px', border: `2px solid ${currentRun >= numRuns ? '#999' : '#000'}`, borderRadius: '6px', background: currentRun >= numRuns ? '#eee' : '#fff', cursor: currentRun >= numRuns ? 'not-allowed' : 'pointer', fontSize: '16px', lineHeight: 1 }}
        >
          ›
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '10px', color: '#000' }}>Run {currentRun} Analysis</h3>
        <p style={{ color: '#666', fontSize: '14px' }}>
          Detailed statistical analysis for Run {currentRun} ({runAnalysis.count ?? analysis.count_per_run} numbers)
        </p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ marginBottom: '10px', color: '#000' }}>Analysis Information Display</h4>
        <div className="tab-buttons">
          {['basic', 'distribution', 'range', 'independence', 'stationarity', 'spectral', 'nist'].map(tab => (
            <button key={tab} onClick={() => onPerRunTabChange(tab)} className={perRunTab === tab ? 'active' : ''}>
              {tab === 'nist' ? 'NIST Tests' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {perRunTab === 'basic' && <BasicStatsSection analysis={runAnalysis} view={basicView} onViewChange={onBasicViewChange} />}
      {perRunTab === 'distribution' && <DistributionSection analysis={runAnalysis} view={distributionView} onViewChange={onDistributionViewChange} />}
      {perRunTab === 'range' && <RangeSection analysis={runAnalysis} view={rangeView} onViewChange={onRangeViewChange} />}
      {perRunTab === 'independence' && <IndependenceSection analysis={runAnalysis} view={independenceView} onViewChange={onIndependenceViewChange} chartHeight={300} />}
      {perRunTab === 'stationarity' && <StationaritySection analysis={runAnalysis} view={stationarityView} onViewChange={onStationarityViewChange} chartHeight={300} />}
      {perRunTab === 'spectral' && <SpectralSection analysis={runAnalysis} view={spectralView} onViewChange={onSpectralViewChange} chartHeight={300} />}
      {perRunTab === 'nist' && <NistTestsSection analysis={runAnalysis} />}
    </>
  )
}

export default PerRunAnalysisView
