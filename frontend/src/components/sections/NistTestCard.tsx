import { ReactNode } from 'react'
import { t } from '../../i18n'

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
      <p className="fail">{t('nistSection.error', { message: error })}</p>
    ) : (
      <>
        {children}
        {passed !== undefined && (
          <p className={passed ? 'pass' : 'fail'}>
            {passed ? t('nistSection.testPassed') : t('nistSection.testFailed')}
          </p>
        )}
      </>
    )}
  </div>
)

export default NistTestCard
