import { t } from '../../i18n'
import NistTestCard from './NistTestCard'

interface NistTestsSectionProps {
  analysis: any
}

const NistTestsSection = ({ analysis }: NistTestsSectionProps) => {
  const nist = analysis.nist_tests
  if (!nist) return null

  return (
    <div className="stats-section">
      <h3>{t('nistSection.title')}</h3>
      <p style={{ marginBottom: '20px', color: '#666', fontSize: '14px' }}>
        {t('nistSection.binaryRepresentationNote')}
      </p>

      <div className="nist-tests-grid">
        <NistTestCard title={t('nistSection.frequencyTest')} error={nist.frequency_test?.error} passed={nist.frequency_test?.passed}>
          {!nist.frequency_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>{t('nistSection.pValue')}</td><td>{nist.frequency_test.p_value?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.monobitStatistic')}</td><td>{nist.frequency_test.statistic?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.ones')}</td><td>{nist.frequency_test.ones ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.zeros')}</td><td>{nist.frequency_test.zeros ?? t('basicStats.na')}</td></tr>
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title={t('nistSection.frequencyWithinBlockTest')} error={nist.frequency_within_block_test?.error} passed={nist.frequency_within_block_test?.passed}>
          {!nist.frequency_within_block_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>{t('nistSection.pValue')}</td><td>{nist.frequency_within_block_test.p_value?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.chiSquareStatistic')}</td><td>{nist.frequency_within_block_test.statistic?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.numberOfBlocks')}</td><td>{nist.frequency_within_block_test.num_blocks ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.blockSize')}</td><td>{nist.frequency_within_block_test.block_size ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.onesPerBlockMin')}</td><td>{nist.frequency_within_block_test.ones_per_block_summary?.min ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.onesPerBlockMax')}</td><td>{nist.frequency_within_block_test.ones_per_block_summary?.max ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.onesPerBlockMean')}</td><td>{nist.frequency_within_block_test.ones_per_block_summary?.mean?.toFixed(2) ?? t('basicStats.na')}</td></tr>
                {Array.isArray(nist.frequency_within_block_test.ones_per_block_summary?.preview) && nist.frequency_within_block_test.ones_per_block_summary.preview.length > 0 && (
                  <tr><td>{t('nistSection.onesPerBlockPreview')}</td><td>{nist.frequency_within_block_test.ones_per_block_summary.preview.join(', ')}</td></tr>
                )}
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title={t('nistSection.cumulativeSumsTest')} error={nist.cumulative_sums_test?.error} passed={nist.cumulative_sums_test?.passed}>
          {!nist.cumulative_sums_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>{t('nistSection.pValue')}</td><td>{nist.cumulative_sums_test.p_value?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.zStatistic')}</td><td>{nist.cumulative_sums_test.statistic?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.forwardPValue')}</td><td>{nist.cumulative_sums_test.p_value_forward?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.forwardZStatistic')}</td><td>{nist.cumulative_sums_test.z_forward?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.backwardPValue')}</td><td>{nist.cumulative_sums_test.p_value_backward?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.backwardZStatistic')}</td><td>{nist.cumulative_sums_test.z_backward?.toFixed(4) || t('basicStats.na')}</td></tr>
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title={t('nistSection.spectralTest')} error={nist.spectral_test?.error} passed={nist.spectral_test?.passed}>
          {!nist.spectral_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>{t('nistSection.pValue')}</td><td>{nist.spectral_test.p_value?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.spectralStatistic')}</td><td>{nist.spectral_test.statistic?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.spectralTau')}</td><td>{nist.spectral_test.tau?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.spectralExpectedPeaks')}</td><td>{nist.spectral_test.n0?.toFixed(2) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.spectralObservedPeaks')}</td><td>{nist.spectral_test.n1 ?? t('basicStats.na')}</td></tr>
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title={t('nistSection.runsTest')} error={nist.runs_test?.error} passed={nist.runs_test?.passed}>
          {!nist.runs_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>{t('nistSection.pValue')}</td><td>{nist.runs_test.p_value?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.zStatistic')}</td><td>{nist.runs_test.statistic?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.runsObserved')}</td><td>{nist.runs_test.runs ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.runsExpected')}</td><td>{nist.runs_test.expected_runs?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.ones')}</td><td>{nist.runs_test.ones ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.zeros')}</td><td>{nist.runs_test.zeros ?? t('basicStats.na')}</td></tr>
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title={t('nistSection.binaryMatrixRankTest')} error={nist.binary_matrix_rank_test?.error} passed={nist.binary_matrix_rank_test?.passed}>
          {!nist.binary_matrix_rank_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>{t('nistSection.pValue')}</td><td>{nist.binary_matrix_rank_test.p_value?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.chiSquareStatistic')}</td><td>{nist.binary_matrix_rank_test.statistic?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.numberOfMatrices')}</td><td>{nist.binary_matrix_rank_test.num_matrices ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.fullRankCount')}</td><td>{nist.binary_matrix_rank_test.full_rank_count ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.rankMinus1Count')}</td><td>{nist.binary_matrix_rank_test.rank_minus_1_count ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.rank0Count')}</td><td>{nist.binary_matrix_rank_test.rank_0_count ?? t('basicStats.na')}</td></tr>
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title={t('nistSection.longestRunOfOnesTest')} error={nist.longest_run_of_ones_test?.error} passed={nist.longest_run_of_ones_test?.passed}>
          {!nist.longest_run_of_ones_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>{t('nistSection.pValue')}</td><td>{nist.longest_run_of_ones_test.p_value?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.chiSquareStatistic')}</td><td>{nist.longest_run_of_ones_test.statistic?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.numberOfBlocks')}</td><td>{nist.longest_run_of_ones_test.num_blocks ?? t('basicStats.na')}</td></tr>
                {nist.longest_run_of_ones_test.run_counts && Object.entries(nist.longest_run_of_ones_test.run_counts).map(([length, count]: [string, any]) => (
                  <tr key={length}><td>{t('nistSection.lengthLe', { n: length })}</td><td>{count}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title={t('nistSection.approximateEntropyTest')} error={nist.approximate_entropy_test?.error} passed={nist.approximate_entropy_test?.passed}>
          {!nist.approximate_entropy_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>{t('nistSection.pValue')}</td><td>{nist.approximate_entropy_test.p_value?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.chiSquareStatistic')}</td><td>{nist.approximate_entropy_test.statistic?.toFixed(4) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.approximateEntropy')}</td><td>{nist.approximate_entropy_test.approximate_entropy?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.phiM')}</td><td>{nist.approximate_entropy_test.phi_m?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.phiM1')}</td><td>{nist.approximate_entropy_test.phi_m1?.toFixed(6) || t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.patternLengthM')}</td><td>{nist.approximate_entropy_test.pattern_length_m ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.patternLengthM1')}</td><td>{nist.approximate_entropy_test.pattern_length_m1 ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.uniquePatternsM')}</td><td>{nist.approximate_entropy_test.unique_patterns_m ?? t('basicStats.na')}</td></tr>
                <tr><td>{t('nistSection.uniquePatternsM1')}</td><td>{nist.approximate_entropy_test.unique_patterns_m1 ?? t('basicStats.na')}</td></tr>
              </tbody>
            </table>
          )}
        </NistTestCard>
      </div>

      <div className="chart-container" style={{ marginTop: '20px' }}>
        <h4>{t('nistSection.binarySequenceInfo')}</h4>
        <div className="info-card">
          <p>{t('nistSection.totalBinarySequenceLength', { n: nist.binary_sequence_length?.toLocaleString() ?? t('basicStats.na') })}</p>
          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
            {t('nistSection.ieee754Note')}
          </p>
        </div>
      </div>
    </div>
  )
}

export default NistTestsSection
