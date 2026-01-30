import NistTestCard from './NistTestCard'

interface NistTestsSectionProps {
  analysis: any
}

const NistTestsSection = ({ analysis }: NistTestsSectionProps) => {
  const nist = analysis.nist_tests
  if (!nist) return null

  return (
    <div className="stats-section">
      <h3>NIST Statistical Tests</h3>
      <p style={{ marginBottom: '20px', color: '#666', fontSize: '14px' }}>
        Tests performed on binary representation of numbers (IEEE 754 double precision)
      </p>

      <div className="nist-tests-grid">
        <NistTestCard title="Runs Test" error={nist.runs_test?.error} passed={nist.runs_test?.passed}>
          {!nist.runs_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>P-value</td><td>{nist.runs_test.p_value?.toFixed(6) || 'N/A'}</td></tr>
                <tr><td>Z-statistic</td><td>{nist.runs_test.statistic?.toFixed(4) || 'N/A'}</td></tr>
                <tr><td>Runs observed</td><td>{nist.runs_test.runs ?? 'N/A'}</td></tr>
                <tr><td>Runs expected</td><td>{nist.runs_test.expected_runs?.toFixed(4) || 'N/A'}</td></tr>
                <tr><td>Ones</td><td>{nist.runs_test.ones ?? 'N/A'}</td></tr>
                <tr><td>Zeros</td><td>{nist.runs_test.zeros ?? 'N/A'}</td></tr>
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title="Binary Matrix Rank Test" error={nist.binary_matrix_rank_test?.error} passed={nist.binary_matrix_rank_test?.passed}>
          {!nist.binary_matrix_rank_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>P-value</td><td>{nist.binary_matrix_rank_test.p_value?.toFixed(6) || 'N/A'}</td></tr>
                <tr><td>Chi-square statistic</td><td>{nist.binary_matrix_rank_test.statistic?.toFixed(4) || 'N/A'}</td></tr>
                <tr><td>Number of matrices</td><td>{nist.binary_matrix_rank_test.num_matrices ?? 'N/A'}</td></tr>
                <tr><td>Full rank count</td><td>{nist.binary_matrix_rank_test.full_rank_count ?? 'N/A'}</td></tr>
                <tr><td>Rank-1 count</td><td>{nist.binary_matrix_rank_test.rank_minus_1_count ?? 'N/A'}</td></tr>
                <tr><td>Rank-0 count</td><td>{nist.binary_matrix_rank_test.rank_0_count ?? 'N/A'}</td></tr>
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title="Longest Run of Ones Test" error={nist.longest_run_of_ones_test?.error} passed={nist.longest_run_of_ones_test?.passed}>
          {!nist.longest_run_of_ones_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>P-value</td><td>{nist.longest_run_of_ones_test.p_value?.toFixed(6) || 'N/A'}</td></tr>
                <tr><td>Chi-square statistic</td><td>{nist.longest_run_of_ones_test.statistic?.toFixed(4) || 'N/A'}</td></tr>
                <tr><td>Number of blocks</td><td>{nist.longest_run_of_ones_test.num_blocks ?? 'N/A'}</td></tr>
                {nist.longest_run_of_ones_test.run_counts && Object.entries(nist.longest_run_of_ones_test.run_counts).map(([length, count]: [string, any]) => (
                  <tr key={length}><td>Length ≤{length}</td><td>{count}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </NistTestCard>

        <NistTestCard title="Approximate Entropy Test" error={nist.approximate_entropy_test?.error} passed={nist.approximate_entropy_test?.passed}>
          {!nist.approximate_entropy_test?.error && (
            <table className="test-results-table">
              <tbody>
                <tr><td>P-value</td><td>{nist.approximate_entropy_test.p_value?.toFixed(6) || 'N/A'}</td></tr>
                <tr><td>Chi-square statistic</td><td>{nist.approximate_entropy_test.statistic?.toFixed(4) || 'N/A'}</td></tr>
                <tr><td>Approximate Entropy</td><td>{nist.approximate_entropy_test.approximate_entropy?.toFixed(6) || 'N/A'}</td></tr>
                <tr><td>Phi(m)</td><td>{nist.approximate_entropy_test.phi_m?.toFixed(6) || 'N/A'}</td></tr>
                <tr><td>Phi(m+1)</td><td>{nist.approximate_entropy_test.phi_m1?.toFixed(6) || 'N/A'}</td></tr>
                <tr><td>Pattern length m</td><td>{nist.approximate_entropy_test.pattern_length_m ?? 'N/A'}</td></tr>
                <tr><td>Pattern length m+1</td><td>{nist.approximate_entropy_test.pattern_length_m1 ?? 'N/A'}</td></tr>
                <tr><td>Unique patterns (m)</td><td>{nist.approximate_entropy_test.unique_patterns_m ?? 'N/A'}</td></tr>
                <tr><td>Unique patterns (m+1)</td><td>{nist.approximate_entropy_test.unique_patterns_m1 ?? 'N/A'}</td></tr>
              </tbody>
            </table>
          )}
        </NistTestCard>
      </div>

      <div className="chart-container" style={{ marginTop: '20px' }}>
        <h4>Binary Sequence Information</h4>
        <div className="info-card">
          <p>Total binary sequence length: {nist.binary_sequence_length?.toLocaleString() ?? 'N/A'} bits</p>
          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
            Each number is converted to its IEEE 754 double precision (64-bit) binary representation
          </p>
        </div>
      </div>
    </div>
  )
}

export default NistTestsSection
