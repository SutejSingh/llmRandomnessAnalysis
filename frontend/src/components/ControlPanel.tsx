import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import NumberStream from './NumberStream'
import './ControlPanel.css'

const API_BASE = 'http://localhost:8000'

interface ControlPanelProps {
  provider: string
  setProvider: (provider: string) => void
  systemPrompt: string
  setSystemPrompt: (prompt: string) => void
  count: number
  setCount: (count: number) => void
  batchMode: boolean
  setBatchMode: (mode: boolean) => void
  numRuns: number
  setNumRuns: (runs: number) => void
  onGenerate: () => void
  isStreaming: boolean
  numbers: number[]
  onDummyData?: () => void
  onCsvUpload?: (runs: number[][], numRuns: number, analysis: any) => void
}

const ControlPanel = ({
  provider,
  setProvider,
  systemPrompt,
  setSystemPrompt,
  count,
  setCount,
  batchMode,
  setBatchMode,
  numRuns,
  setNumRuns,
  onGenerate,
  isStreaming,
  numbers,
  onDummyData,
  onCsvUpload
}: ControlPanelProps) => {
  // Local state for input values to allow empty during typing
  const [countInput, setCountInput] = useState<string>(count.toString())
  const [numRunsInput, setNumRunsInput] = useState<string>(numRuns.toString())
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Sync local state when props change (but not during user typing)
  useEffect(() => {
    setCountInput(count.toString())
  }, [count])
  
  useEffect(() => {
    setNumRunsInput(numRuns.toString())
  }, [numRuns])

  const defaultPromptsOneByOne = {
    openai: "You are a random number generator. Generate a single random number between 0 and 1. Respond with ONLY the number, no explanation, no formatting, just the decimal number.",
    anthropic: "You are a random number generator. Generate a single random number between 0 and 1. Respond with ONLY the number, no explanation, no formatting, just the decimal number.",
    deepseek: "You are a random number generator. Generate a single random number between 0 and 1. Respond with ONLY the number, no explanation, no formatting, just the decimal number."
  }

  const getDefaultPromptBatch = (provider: string, count: number) => {
    return `You are a random number generator. Generate exactly ${count} random numbers between 0 and 1. Return them in CSV format, one number per line. Only return the numbers, no explanation, no formatting, no headers.`
  }

  const getDefaultPrompt = () => {
    if (batchMode) {
      return getDefaultPromptBatch(provider, count)
    }
    return defaultPromptsOneByOne[provider as keyof typeof defaultPromptsOneByOne] || defaultPromptsOneByOne.openai
  }

  const handleBatchModeChange = (newBatchMode: boolean) => {
    setBatchMode(newBatchMode)
    // Always reset system prompt to default when mode changes
    if (newBatchMode) {
      setSystemPrompt(getDefaultPromptBatch(provider, count))
    } else {
      setSystemPrompt(defaultPromptsOneByOne[provider as keyof typeof defaultPromptsOneByOne] || defaultPromptsOneByOne.openai)
    }
  }

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider)
    // Update system prompt to default for new provider
    if (!systemPrompt || systemPrompt === getDefaultPrompt()) {
      if (batchMode) {
        setSystemPrompt(getDefaultPromptBatch(newProvider, count))
      } else {
        setSystemPrompt(defaultPromptsOneByOne[newProvider as keyof typeof defaultPromptsOneByOne] || defaultPromptsOneByOne.openai)
      }
    }
  }

  const handleCountChange = (newCount: number) => {
    const oldCount = count
    setCount(newCount)
    // Update system prompt if in batch mode and using default prompt
    if (batchMode) {
      const currentDefault = getDefaultPromptBatch(provider, newCount)
      // Update if prompt is empty or matches the old default
      if (!systemPrompt || systemPrompt.includes(`${oldCount} random numbers`)) {
        setSystemPrompt(currentDefault)
      }
    }
  }

  const handleResetPrompt = () => {
    setSystemPrompt(getDefaultPrompt())
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.csv')) {
      setUploadError('Please select a CSV file (.csv extension)')
      return
    }

    setIsUploading(true)
    setUploadError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`${API_BASE}/upload/csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const { runs, num_runs, analysis } = response.data

      if (onCsvUpload) {
        onCsvUpload(runs, num_runs, analysis)
      }
    } catch (error) {
      console.error('CSV upload error:', error)
      if (axios.isAxiosError(error)) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to upload CSV'
        setUploadError(errorMessage)
      } else {
        setUploadError('Failed to upload CSV file')
      }
    } finally {
      setIsUploading(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  // Initialize prompt on mount and update when batch mode or count changes
  useEffect(() => {
    const currentDefault = getDefaultPrompt()
    // Initialize if empty
    if (!systemPrompt) {
      setSystemPrompt(currentDefault)
      return
    }
    
    // Auto-update if it's clearly a default prompt that needs updating
    if (batchMode) {
      // If switching to batch mode and prompt looks like default, update it
      const isOneByOneDefault = Object.values(defaultPromptsOneByOne).includes(systemPrompt)
      if (isOneByOneDefault || (systemPrompt.includes('random numbers') && !systemPrompt.includes(`${count}`))) {
        setSystemPrompt(currentDefault)
      }
    } else {
      // If switching to one-by-one and prompt is batch default, update it
      if (systemPrompt.includes(`${count} random numbers`) && systemPrompt.includes('comma-separated')) {
        setSystemPrompt(currentDefault)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [batchMode, count, provider])

  return (
    <div className="control-panel">
      <div className="control-section">
        <div className="control-group">
          <label className="control-label">
            <span className="label-icon">🤖</span>
            <strong>LLM Provider</strong>
          </label>
          <select
            value={provider}
            onChange={(e) => handleProviderChange(e.target.value)}
            disabled={isStreaming}
            className="styled-select"
          >
            <option value="openai">OpenAI (GPT-4)</option>
            <option value="anthropic">Anthropic (Claude)</option>
            <option value="deepseek">DeepSeek</option>
          </select>
        </div>

        <div className="control-group">
          <label className="control-label">
            <span className="label-icon">🔢</span>
            <strong>Number Count</strong>
          </label>
          <input
            type="number"
            value={countInput}
            onChange={(e) => {
              const value = e.target.value
              setCountInput(value) // Always update local state to allow typing
              const numValue = parseInt(value, 10)
              // Only update parent state if we have a valid number
              if (!isNaN(numValue) && value !== '') {
                handleCountChange(Math.max(10, Math.min(1000, numValue)))
              }
            }}
            onBlur={(e) => {
              const value = e.target.value
              const numValue = parseInt(value, 10)
              // If empty or invalid, set to default
              if (value === '' || isNaN(numValue) || numValue < 10 || numValue > 1000) {
                handleCountChange(100)
                setCountInput('100')
              }
            }}
            min="10"
            max="1000"
            disabled={isStreaming || batchMode}
            className="styled-input"
            title={batchMode ? "Number count is specified in the system prompt when using batch mode" : ""}
          />
        </div>

        <div className="control-group">
          <label className="control-label">
            <span className="label-icon">🔄</span>
            <strong>Number of Runs</strong>
          </label>
          <input
            type="number"
            value={numRunsInput}
            onChange={(e) => {
              const value = e.target.value
              setNumRunsInput(value) // Always update local state to allow typing
              const numValue = parseInt(value, 10)
              // Only update parent state if we have a valid number
              if (!isNaN(numValue) && value !== '') {
                setNumRuns(Math.max(1, Math.min(50, numValue)))
              }
            }}
            onBlur={(e) => {
              const value = e.target.value
              const numValue = parseInt(value, 10)
              // If empty or invalid, set to default
              if (value === '' || isNaN(numValue) || numValue < 1 || numValue > 50) {
                setNumRuns(1)
                setNumRunsInput('1')
              }
            }}
            min="1"
            max="50"
            disabled={isStreaming}
            className="styled-input"
            title="Number of independent runs to perform"
          />
        </div>

        <div className="control-group request-mode-group">
          <label className="control-label">
            <span className="label-icon">⚡</span>
            <strong>Request Mode</strong>
          </label>
          <div className="radio-group">
            <label className="radio-option">
              <input
                type="radio"
                name="requestMode"
                value="one-by-one"
                checked={!batchMode}
                onChange={() => handleBatchModeChange(false)}
                disabled={isStreaming}
              />
              <span className="radio-custom"></span>
              <span className="radio-label">
                <span className="radio-title">One Request Per Number</span>
                <span className="radio-description">More reliable, slower</span>
              </span>
            </label>
            <label className="radio-option">
              <input
                type="radio"
                name="requestMode"
                value="batch"
                checked={batchMode}
                onChange={() => handleBatchModeChange(true)}
                disabled={isStreaming}
              />
              <span className="radio-custom"></span>
              <span className="radio-label">
                <span className="radio-title">One Request For All</span>
                <span className="radio-description">Faster, single request</span>
              </span>
            </label>
          </div>
        </div>

        <div className="generate-button-container">
          <button
            onClick={onGenerate}
            disabled={isStreaming}
            className="generate-button"
          >
            <span className="button-icon">{isStreaming ? '⏳' : '🧮'}</span>
            <span>{isStreaming ? 'Generating...' : 'Generate Random Numbers'}</span>
          </button>
        </div>

        <div className="control-group" style={{ marginTop: '20px', paddingTop: '20px', borderTop: '2px solid #e0e0e0' }}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv"
            style={{ display: 'none' }}
            disabled={isStreaming || isUploading}
          />
          <button
            onClick={handleUploadClick}
            disabled={isStreaming || isUploading}
            className="generate-button"
            style={{ width: '100%', backgroundColor: '#4a90e2' }}
          >
            <span className="button-icon">{isUploading ? '⏳' : '📁'}</span>
            <span>{isUploading ? 'Uploading...' : 'Upload CSV File'}</span>
          </button>
          {uploadError && (
            <p style={{ fontSize: '12px', color: '#d32f2f', marginTop: '10px', textAlign: 'center' }}>
              {uploadError}
            </p>
          )}
          <div style={{ fontSize: '12px', color: '#666', marginTop: '10px', textAlign: 'center', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
            <strong>CSV Format Required:</strong>
            <br />
            Columns must be named: <code>run 1</code>, <code>run 2</code>, <code>run 3</code>, etc.
            <br />
            Each column should contain numeric values (one per row).
            <br />
            <em>Example:</em> <code>run 1,run 2,run 3</code>
          </div>
        </div>

        <div className="control-group" style={{ marginTop: '20px', paddingTop: '20px', borderTop: '2px solid #e0e0e0' }}>
          <button
            onClick={onDummyData}
            disabled={isStreaming || isUploading}
            className="generate-button"
            style={{ width: '100%', backgroundColor: '#666' }}
          >
            <span className="button-icon">📊</span>
            <span>{isStreaming ? 'Loading...' : 'Load Dummy Data for Testing'}</span>
          </button>
          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px', textAlign: 'center' }}>
            Loads test data from dummy_data.json file. Supports both single array [x,x,x] and multi-run [[x,x,x], [x,x,x]] formats.
          </p>
        </div>
      </div>

      <div className="prompt-section">
        <div className="prompt-editor">
          <label>
            <strong className="system-prompt-label">System Prompt:</strong>
            <textarea
              value={systemPrompt || getDefaultPrompt()}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="Enter custom system prompt..."
              rows={4}
              disabled={isStreaming}
            />
          </label>
          <button
            onClick={handleResetPrompt}
            disabled={isStreaming}
            className="reset-prompt-button"
          >
            Reset to Default
          </button>
        </div>

        <div className="number-stream-container">
          <NumberStream numbers={numbers} isStreaming={isStreaming} />
        </div>
      </div>
    </div>
  )
}

export default ControlPanel
