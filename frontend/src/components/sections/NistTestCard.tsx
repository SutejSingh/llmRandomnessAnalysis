import { ReactNode } from 'react'

interface NistTestCardProps {
  title: string
  error?: string
  children?: ReactNode
  passed?: boolean
}

const NistTestCard = ({ title, error, children, passed }: NistTestCardProps) => (
  <div className="test-card">
    <h4>{title}</h4>
    {error ? (
      <p className="fail">Error: {error}</p>
    ) : (
      <>
        {children}
        {passed !== undefined && (
          <p className={passed ? 'pass' : 'fail'}>
            {passed ? '✓ Test Passed (p > 0.01)' : '✗ Test Failed (p ≤ 0.01)'}
          </p>
        )}
      </>
    )}
  </div>
)

export default NistTestCard
