import { useState, useEffect, useRef } from 'react'
import '../styles/NumberStream.css'

interface NumberStreamProps {
  numbers: number[]
  isStreaming: boolean
  /** Total numbers expected (count * numRuns); used to show remaining during stream */
  expectedCount?: number
}

const NumberStream = ({ numbers, isStreaming, expectedCount }: NumberStreamProps) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [displayedNumbers, setDisplayedNumbers] = useState<number[]>([])
  const [recentNumbers, setRecentNumbers] = useState<Set<number>>(new Set())
  const containerRef = useRef<HTMLDivElement>(null)
  const lastCountRef = useRef(0)
  const animationTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Animate numbers appearing one by one (only when not expanded)
  useEffect(() => {
    if (isExpanded) {
      // When expanded, sync displayedNumbers with all numbers immediately
      if (displayedNumbers.length !== numbers.length) {
        setDisplayedNumbers(numbers)
      }
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
          
          // Remove highlight after animation
          setTimeout(() => {
            setRecentNumbers(prev => {
              const next = new Set(prev)
              next.delete(num)
              return next
            })
          }, 600)
          
          index++
          if (index < newNumbers.length) {
            animationTimeoutRef.current = setTimeout(addNumber, 100) // Add one number every 100ms
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
  }, [numbers, isExpanded])

  // Reset when streaming starts
  useEffect(() => {
    if (isStreaming && numbers.length === 0) {
      setDisplayedNumbers([])
      setRecentNumbers(new Set())
      lastCountRef.current = 0
    }
  }, [isStreaming, numbers.length])

  // When streaming ends, show all numbers immediately so "X more" / "X remaining" goes away
  useEffect(() => {
    if (!isStreaming && numbers.length > 0) {
      setDisplayedNumbers(numbers)
      lastCountRef.current = numbers.length
    }
  }, [isStreaming, numbers])

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
      <h2>Number Stream</h2>
      <div className="stream-info">
        <span>Count: {numbers.length}</span>
        {isStreaming && <span className="streaming-indicator">● Streaming</span>}
        {numbers.length > 0 && (
          <button 
            onClick={handleToggleExpand}
            className="expand-button"
          >
            {isExpanded ? '▼ Collapse' : '▶ Expand All'}
          </button>
        )}
      </div>
      <div 
        ref={containerRef}
        className={`stream-container ${isExpanded ? 'expanded' : ''} ${numbers.length === 0 ? 'empty' : ''}`}
      >
        {numbers.length === 0 ? (
          <div className="empty-stream">No numbers generated yet. Click "Generate Random Numbers" to start.</div>
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
                  title={isExpanded ? "Click to collapse" : "Click to expand full list"}
                >
                  {num.toFixed(4)}
                </span>
              )
            })}
            {!isExpanded && isStreaming && expectedCount != null && numbers.length < expectedCount && (
              <span className="more-indicator">... streaming ({expectedCount - numbers.length} remaining)</span>
            )}
            {!isExpanded && !isStreaming && numbers.length > displayedNumbers.length && (
              <span className="more-indicator">... and {numbers.length - displayedNumbers.length} more (click any number to expand)</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default NumberStream
