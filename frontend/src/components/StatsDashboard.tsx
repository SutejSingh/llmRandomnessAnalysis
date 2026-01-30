import { useState, useEffect } from 'react'
import '../styles/StatsDashboard.css'
import DashboardHeader from './DashboardHeader'
import MultiRunAnalysisView from './MultiRunAnalysisView'
import PerRunAnalysisView from './PerRunAnalysisView'
import {
  BasicStatsSection,
  DistributionSection,
  RangeSection,
  IndependenceSection,
  StationaritySection,
  SpectralSection,
  NistTestsSection
} from './sections'

interface StatsDashboardProps {
  analysis: any
  allRuns?: number[][]
}

const StatsDashboard = ({ analysis, allRuns = [] }: StatsDashboardProps) => {
  const isMultiRun = analysis && analysis.aggregate_stats !== undefined
  const [activeTab, setActiveTab] = useState(isMultiRun ? 'multi-run' : 'basic')
  const [selectedRun, setSelectedRun] = useState<number | null>(null)
  const [multiRunViewMode, setMultiRunViewMode] = useState<'multi-run' | 'per-run'>('multi-run')
  const [perRunTab, setPerRunTab] = useState('basic')
  const [isDownloadingPDF, setIsDownloadingPDF] = useState(false)

  const [basicView, setBasicView] = useState<'stats' | 'histogram' | 'boxplot'>('stats')
  const [distributionView, setDistributionView] = useState<'tests' | 'kde' | 'qq'>('tests')
  const [rangeView, setRangeView] = useState<'boundary' | 'ecdf'>('boundary')
  const [independenceView, setIndependenceView] = useState<'timeseries' | 'acf' | 'lag1'>('timeseries')
  const [stationarityView, setStationarityView] = useState<'rolling' | 'chunks'>('rolling')
  const [spectralView, setSpectralView] = useState<'magnitude' | 'power'>('magnitude')
  const [perRunIndependenceView, setPerRunIndependenceView] = useState<'timeseries' | 'acf' | 'lag1'>('timeseries')
  const [perRunSpectralView, setPerRunSpectralView] = useState<'magnitude' | 'power'>('magnitude')

  const API_BASE = 'http://localhost:8000'

  useEffect(() => {
    if (multiRunViewMode === 'per-run' && analysis?.individual_analyses?.length > 0) {
      const n = analysis.individual_analyses.length
      if (selectedRun == null || selectedRun < 1 || selectedRun > n) {
        setSelectedRun(1)
      }
    }
  }, [multiRunViewMode, analysis?.individual_analyses, selectedRun])

  const handleMultiRunViewModeChange = (mode: 'multi-run' | 'per-run') => {
    setMultiRunViewMode(mode)
    if (mode === 'per-run') setSelectedRun(1)
  }

  const getRunsToDownload = (): number[][] => {
    if (allRuns.length > 0) return allRuns
    if (analysis?.individual_analyses?.length > 0) {
      return analysis.individual_analyses.map((a: any) => a.raw_data || [])
    }
    if (analysis?.raw_data) return [analysis.raw_data]
    return []
  }

  const handleDownloadCSV = () => {
    const runsToDownload = getRunsToDownload()
    if (runsToDownload.length === 0) {
      alert('No data available to download')
      return
    }
    const runsJson = encodeURIComponent(JSON.stringify(runsToDownload))
    const provider = analysis.provider || 'manual'
    window.open(`${API_BASE}/download/csv?runs=${runsJson}&provider=${provider}`, '_blank')
  }

  const handleDownloadPDF = async () => {
    const runsToDownload = getRunsToDownload()
    if (runsToDownload.length === 0) {
      alert('No data available to download')
      return
    }
    setIsDownloadingPDF(true)
    try {
      const response = await fetch(`${API_BASE}/download/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis, runs: runsToDownload })
      })
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `analysis_report_${analysis.provider || 'unknown'}_${new Date().toISOString().replace(/[:.]/g, '-')}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading PDF:', error)
      alert('Error downloading PDF file. Please try again.')
    } finally {
      setIsDownloadingPDF(false)
    }
  }

  if (!analysis) return null

  return (
    <div className="stats-dashboard">
      <DashboardHeader
        isMultiRun={!!isMultiRun}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        multiRunViewMode={multiRunViewMode}
        onMultiRunViewModeChange={handleMultiRunViewModeChange}
        onDownloadCSV={handleDownloadCSV}
        onDownloadPDF={handleDownloadPDF}
        isDownloadingPDF={isDownloadingPDF}
      />

      {/* Single-run tabs (when !isMultiRun) */}
      {!isMultiRun && activeTab === 'basic' && <BasicStatsSection analysis={analysis} view={basicView} onViewChange={setBasicView} />}
      {!isMultiRun && activeTab === 'distribution' && <DistributionSection analysis={analysis} view={distributionView} onViewChange={setDistributionView} />}
      {!isMultiRun && activeTab === 'range' && <RangeSection analysis={analysis} view={rangeView} onViewChange={setRangeView} />}
      {!isMultiRun && activeTab === 'independence' && <IndependenceSection analysis={analysis} view={independenceView} onViewChange={setIndependenceView} />}
      {!isMultiRun && activeTab === 'stationarity' && <StationaritySection analysis={analysis} view={stationarityView} onViewChange={setStationarityView} />}
      {!isMultiRun && activeTab === 'spectral' && <SpectralSection analysis={analysis} view={spectralView} onViewChange={setSpectralView} />}
      {!isMultiRun && activeTab === 'nist' && <NistTestsSection analysis={analysis} />}

      {/* Multi-run: aggregate view */}
      {isMultiRun && multiRunViewMode === 'multi-run' && (
        <MultiRunAnalysisView
          analysis={analysis}
          allRuns={allRuns}
          onSelectRun={(runNumber) => {
            setSelectedRun(runNumber)
            setMultiRunViewMode('per-run')
            setPerRunTab('basic')
          }}
        />
      )}

      {/* Multi-run: per-run view */}
      {isMultiRun && multiRunViewMode === 'per-run' && (
        <PerRunAnalysisView
          analysis={analysis}
          selectedRun={selectedRun ?? 1}
          onSelectedRunChange={(r) => setSelectedRun(r)}
          perRunTab={perRunTab}
          onPerRunTabChange={setPerRunTab}
          basicView={basicView}
          onBasicViewChange={setBasicView}
          distributionView={distributionView}
          onDistributionViewChange={setDistributionView}
          rangeView={rangeView}
          onRangeViewChange={setRangeView}
          independenceView={perRunIndependenceView}
          onIndependenceViewChange={setPerRunIndependenceView}
          stationarityView={stationarityView}
          onStationarityViewChange={setStationarityView}
          spectralView={perRunSpectralView}
          onSpectralViewChange={setPerRunSpectralView}
        />
      )}
    </div>
  )
}

export default StatsDashboard
