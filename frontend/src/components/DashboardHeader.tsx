import { t } from '../i18n'

interface DashboardHeaderProps {
  isMultiRun: boolean
  activeTab: string
  onTabChange: (tab: string) => void
  multiRunViewMode: 'multi-run' | 'per-run'
  onMultiRunViewModeChange: (mode: 'multi-run' | 'per-run') => void
  onDownloadCSV: () => void
  onDownloadPDF: () => void
  isDownloadingPDF: boolean
}

const DashboardHeader = ({
  isMultiRun,
  activeTab,
  onTabChange,
  multiRunViewMode,
  onMultiRunViewModeChange,
  onDownloadCSV,
  onDownloadPDF,
  isDownloadingPDF
}: DashboardHeaderProps) => (
  <div className="dashboard-header">
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
      <h2>{t('dashboard.statisticalAnalysis')}</h2>
      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={onDownloadCSV}
          style={{ padding: '10px 20px', backgroundColor: '#000', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}
          title={t('dashboard.downloadCsvTitle')}
        >
          <span>📥</span>
          <span>{t('dashboard.downloadCsv')}</span>
        </button>
        <button
          onClick={onDownloadPDF}
          disabled={isDownloadingPDF}
          style={{
            padding: '10px 20px',
            backgroundColor: isDownloadingPDF ? '#999' : '#c41e3a',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: isDownloadingPDF ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            opacity: isDownloadingPDF ? 0.7 : 1
          }}
          title={isDownloadingPDF ? t('dashboard.preparingPdf') : t('dashboard.downloadPdfTitle')}
        >
          {isDownloadingPDF ? (
            <>
              <span style={{ display: 'inline-block', width: '16px', height: '16px', border: '2px solid #fff', borderTop: '2px solid transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
              <span>{t('dashboard.preparingPdf')}</span>
            </>
          ) : (
            <>
              <span>📄</span>
              <span>{t('dashboard.downloadPdf')}</span>
            </>
          )}
        </button>
      </div>
    </div>
    <div className="tab-buttons">
      {isMultiRun && (
        <div style={{ display: 'flex', gap: '0', marginBottom: '10px', border: '2px solid #000', borderRadius: '6px', overflow: 'hidden', width: 'fit-content' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', margin: 0, padding: 0 }}>
            <input type="radio" name="multiRunView" value="multi-run" checked={multiRunViewMode === 'multi-run'} onChange={(e) => onMultiRunViewModeChange(e.target.value as 'multi-run' | 'per-run')} style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }} />
            <button type="button" onClick={() => onMultiRunViewModeChange('multi-run')} className={multiRunViewMode === 'multi-run' ? 'active' : ''} style={{ cursor: 'pointer', borderRadius: 0, borderRight: '1px solid #000', margin: 0 }}>
              {t('dashboard.multiRunAnalysis')}
            </button>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', margin: 0, padding: 0 }}>
            <input type="radio" name="multiRunView" value="per-run" checked={multiRunViewMode === 'per-run'} onChange={(e) => { const mode = e.target.value as 'multi-run' | 'per-run'; onMultiRunViewModeChange(mode); }} style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }} />
            <button type="button" onClick={() => { onMultiRunViewModeChange('per-run'); }} className={multiRunViewMode === 'per-run' ? 'active' : ''} style={{ cursor: 'pointer', borderRadius: 0, margin: 0 }}>
              {t('dashboard.perRunAnalysis')}
            </button>
          </label>
        </div>
      )}
      {!isMultiRun && ['basic', 'distribution', 'range', 'independence', 'stationarity', 'spectral', 'nist'].map(tab => (
        <button key={tab} onClick={() => onTabChange(tab)} className={activeTab === tab ? 'active' : ''}>
          {tab === 'nist' ? t('dashboard.nistTests') : t(`dashboard.${tab}` as 'dashboard.basic')}
        </button>
      ))}
    </div>
  </div>
)

export default DashboardHeader
