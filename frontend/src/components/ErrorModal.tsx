import { useEffect } from 'react'
import { t } from '../i18n'
import '../styles/ErrorModal.css'

interface ErrorModalProps {
  message: string
  onClose: () => void
}

/**
 * Centered modal for generation / API errors (missing key, provider errors, etc.)
 */
export default function ErrorModal({ message, onClose }: ErrorModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="error-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="error-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="error-modal-box">
        <h2 id="error-modal-title" className="error-modal-title">
          {t('app.errorModalTitle')}
        </h2>
        <pre className="error-modal-message">{message}</pre>
        <div className="error-modal-actions">
          <button type="button" className="error-modal-close" onClick={onClose}>
            {t('app.errorModalClose')}
          </button>
        </div>
      </div>
    </div>
  )
}
