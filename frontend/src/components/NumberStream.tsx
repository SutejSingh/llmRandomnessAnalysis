import { useState, useEffect, useRef } from 'react'
import { t } from '../i18n'
import '../styles/NumberStream.css'

interface NumberStreamProps {
  numbers: number[]
  isStreaming: boolean
}

const NumberStream = ({ numbers, isStreaming }: NumberStreamProps) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [displayedNumbers, setDisplayedNumbers] = useState<number[]>([])
  const [recentNumbers, setRecentNumbers] = useState<Set<number>>(new Set())
  const containerRef = useRef<HTMLDivElement>(null)
  const lastCountRef = useRef(0)
  const animationTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Animate numbers appearing one by one only when streaming; when not streaming show all immediately (e.g. CSV upload)
  useEffect(() => {
    if (isExpanded) {
      if (displayedNumbers.length !== numbers.length) {
        setDisplayedNumbers(numbers)
      }
      return
    }

    if (!isStreaming) {
      // CSV upload or non-streaming: show all numbers immediately, no "... pending" / "... more" text
      if (displayedNumbers.length !== numbers.length) {
        setDisplayedNumbers(numbers)
      }
      lastCountRef.current = numbers.length
      return
    }

    if (numbers.length > lastCountRef.current) {
      const newNumbers = numbers.slice(lastCountRef.current)
      let index = 0

      const addNumber = () => {
        if (index < newNumbers.length && !isExpanded) {
          const num = newNumbers[index]
          setDisplayedNumbers(prev => [...prev, num])
          setRecentNumbers(prev => new Set([...prev, num]))

          setTimeout(() => {
            setRecentNumbers(prev => {
              const next = new Set(prev)
              next.delete(num)
              return next
            })
          }, 600)

          index++
          if (index < newNumbers.length) {
            animationTimeoutRef.current = setTimeout(addNumber, 100)
          }
        }
      }

      addNumber()
      lastCountRef.current = numbers.length
    }

    return () => {
      if (animationTimeoutRef.current) {
        clearTimeout(animationTimeoutRef.current)
      }
    }
  }, [numbers, isExpanded, isStreaming])

  // Reset when streaming starts
  useEffect(() => {
    if (isStreaming && numbers.length === 0) {
      setDisplayedNumbers([])
      setRecentNumbers(new Set())
      lastCountRef.current = 0
    }
  }, [isStreaming, numbers.length])

  // Auto-scroll to bottom when new numbers arrive
  useEffect(() => {
    if (containerRef.current && !isExpanded) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [displayedNumbers, isExpanded])

  const handleToggleExpand = () => {
    setIsExpanded(!isExpanded)
  }

  const numbersToShow = isExpanded ? numbers : displayedNumbers

  return (
    <div className="number-stream">
      <h2>{t('numberStream.title')}</h2>
      <div className="stream-info">
        <span>{t('numberStream.count', { count: numbers.length })}</span>
        {isStreaming && <span className="streaming-indicator">{t('numberStream.streaming')}</span>}
        {numbers.length > 0 && (
          <button 
            onClick={handleToggleExpand}
            className="expand-button"
          >
            {isExpanded ? t('numberStream.collapse') : t('numberStream.expandAll')}
          </button>
        )}
      </div>
      <div 
        ref={containerRef}
        className={`stream-container ${isExpanded ? 'expanded' : ''} ${numbers.length === 0 ? 'empty' : ''}`}
      >
        {numbers.length === 0 ? (
          <div className="empty-stream">{t('numberStream.noNumbersYet')}</div>
        ) : (
          <div className="stream-numbers">
            {numbersToShow.map((num, idx) => {
              const isNew = recentNumbers.has(num)
              
              return (
                <span 
                  key={isExpanded ? `expanded-${idx}-${num}` : `stream-${idx}-${num}`}
                  className={`number-badge ${isNew ? 'new-number' : ''}`}
                  onClick={() => {
                    if (!isExpanded) {
                      handleToggleExpand()
                    }
                  }}
                  title={isExpanded ? t('numberStream.clickToCollapse') : t('numberStream.clickToExpandFullList')}
                >
                  {num.toFixed(4)}
                </span>
              )
            })}
            {!isExpanded && numbers.length > displayedNumbers.length && (
              <span className="more-indicator">{t('numberStream.streamingPending', { pending: numbers.length - displayedNumbers.length })}</span>
            )}
            {!isExpanded && !isStreaming && numbers.length > displayedNumbers.length && (
              <span className="more-indicator">{t('numberStream.andMore', { count: numbers.length - displayedNumbers.length })}</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default NumberStream
