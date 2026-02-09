import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { t } from '../i18n'
import NumberStream from './NumberStream'
import '../styles/ControlPanel.css'

const API_BASE = 'http://localhost:8000'

interface ControlPanelProps {
  provider: string
  setProvider: (provider: string) => void
  systemPrompt: string
  setSystemPrompt: (prompt: string) => void
  userPrompt: string
  setUserPrompt: (prompt: string) => void
  count: number
  setCount: (count: number) => void
  batchMode: boolean
  setBatchMode: (mode: boolean) => void
  numRuns: number
  setNumRuns: (runs: number) => void
  apiKey: string
  setApiKey: (key: string) => void
  onGenerate: () => void
  isStreaming: boolean
  numbers: number[]
  onDummyData?: () => void
  onCsvUpload?: (runs: number[][], numRuns: number, analysis: any) => void
  analysisReady?: boolean
}

const ControlPanel = ({
  provider,
  setProvider,
  systemPrompt,
  setSystemPrompt,
  userPrompt,
  setUserPrompt,
  count,
  setCount,
  batchMode,
  setBatchMode,
  numRuns,
  setNumRuns,
  apiKey,
  setApiKey,
  onGenerate,
  isStreaming,
  numbers,
  onDummyData,
  onCsvUpload,
  analysisReady = false
}: ControlPanelProps) => {
  // Local state for input values to allow empty during typing
  const [countInput, setCountInput] = useState<string>(count.toString())
  const [numRunsInput, setNumRunsInput] = useState<string>(numRuns.toString())
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [showUserPromptSection, setShowUserPromptSection] = useState(false)
  const [showApiKeyValue, setShowApiKeyValue] = useState(false)
  
  // Sync local state when props change (but not during user typing)
  useEffect(() => {
    setCountInput(count.toString())
  }, [count])
  
  useEffect(() => {
    setNumRunsInput(numRuns.toString())
  }, [numRuns])

  // Auto-collapse when analysis is ready to present
  useEffect(() => {
    if (analysisReady) {
      setIsCollapsed(true)
    }
  }, [analysisReady])

  const defaultPromptsOneByOne = {
    openai: t('controlPanel.defaultPromptOneByOne'),
    anthropic: t('controlPanel.defaultPromptOneByOne'),
    deepseek: t('controlPanel.defaultPromptOneByOne')
  }

  const getDefaultPromptBatch = (count: number) => {
    return t('controlPanel.defaultPromptBatch', { count })
  }

  const getDefaultPrompt = () => {
    if (batchMode) {
      return getDefaultPromptBatch(count)
    }
    return defaultPromptsOneByOne[provider as keyof typeof defaultPromptsOneByOne] || defaultPromptsOneByOne.openai
  }

  const handleBatchModeChange = (newBatchMode: boolean) => {
    setBatchMode(newBatchMode)
    // Always reset system prompt to default when mode changes
    if (newBatchMode) {
      setSystemPrompt(getDefaultPromptBatch(count))
    } else {
      setSystemPrompt(defaultPromptsOneByOne[provider as keyof typeof defaultPromptsOneByOne] || defaultPromptsOneByOne.openai)
    }
  }

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider)
    // Update system prompt to default for new provider
    if (!systemPrompt || systemPrompt === getDefaultPrompt()) {
      if (batchMode) {
        setSystemPrompt(getDefaultPromptBatch(count))
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
      const currentDefault = getDefaultPromptBatch(newCount)
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
      setUploadError(t('controlPanel.pleaseSelectCsv'))
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
        const errorMessage = error.response?.data?.detail || error.message || t('controlPanel.failedToUploadCsv')
        setUploadError(errorMessage)
      } else {
        setUploadError(t('controlPanel.failedToUploadCsv'))
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
    <div className={`control-panel ${isCollapsed ? 'control-panel--collapsed' : ''}`}>
      <button
        type="button"
        className="control-panel__carat"
        onClick={() => setIsCollapsed((c) => !c)}
        title={isCollapsed ? t('controlPanel.expandControls') : t('controlPanel.collapseControls')}
        aria-label={isCollapsed ? t('controlPanel.expandControls') : t('controlPanel.collapseControls')}
      >
        <span className="control-panel__carat-icon" aria-hidden>
          {isCollapsed ? '▶' : '▼'}
        </span>
        {isCollapsed && <span className="control-panel__carat-label">{t('controlPanel.controls')}</span>}
      </button>
      <div className="control-panel__content">
      <div className="control-section">
        <div className="control-group">
          <label className="control-label">
            <span className="label-icon">🤖</span>
            <strong>{t('controlPanel.llmProvider')}</strong>
          </label>
          <select
            value={provider}
            onChange={(e) => handleProviderChange(e.target.value)}
            disabled={isStreaming}
            className="styled-select"
          >
            <option value="openai">{t('controlPanel.providerOpenai')}</option>
            <option value="anthropic">{t('controlPanel.providerAnthropic')}</option>
            <option value="deepseek">{t('controlPanel.providerDeepseek')}</option>
          </select>
        </div>

        <div className="control-group">
          <label className="control-label">
            <span className="label-icon">🔢</span>
            <strong>{t('controlPanel.numberCount')}</strong>
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
            title={batchMode ? t('controlPanel.numberCountBatchTitle') : ''}
          />
        </div>

        <div className="control-group">
          <label className="control-label">
            <span className="label-icon">🔄</span>
            <strong>{t('controlPanel.numberOfRuns')}</strong>
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
            title={t('controlPanel.numberOfRunsTitle')}
          />
        </div>

        <div className="control-group request-mode-group">
          <label className="control-label">
            <span className="label-icon">⚡</span>
            <strong>{t('controlPanel.requestMode')}</strong>
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
                <span className="radio-title">{t('controlPanel.oneRequestPerNumber')}</span>
                <span className="radio-description">{t('controlPanel.oneRequestPerNumberDesc')}</span>
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
                <span className="radio-title">{t('controlPanel.oneRequestForAll')}</span>
                <span className="radio-description">{t('controlPanel.oneRequestForAllDesc')}</span>
              </span>
            </label>
          </div>
        </div>

        <div className="generate-button-container">
          <div className="generate-upload-row">
            <div className="generate-button-cell">
              <button
                onClick={onGenerate}
                disabled={isStreaming}
                className="generate-button"
              >
                <span className="button-icon">{isStreaming ? '⏳' : '🧮'}</span>
                <span>{isStreaming ? t('controlPanel.generating') : t('controlPanel.generateRandomNumbers')}</span>
              </button>
            </div>
            <span className="generate-or-upload-or">{t('controlPanel.or')}</span>
            <div className="upload-button-cell">
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
                className="generate-button upload-csv-button"
                style={{ backgroundColor: '#4a90e2' }}
              >
                <span className="button-icon">{isUploading ? '⏳' : '📁'}</span>
                <span>{isUploading ? t('controlPanel.uploading') : t('controlPanel.uploadCsvFile')}</span>
              </button>
            </div>
          </div>
          {uploadError && (
            <p className="upload-error-message">
              {uploadError}
            </p>
          )}
          <div className="upload-csv-instructions">
            <strong>{t('controlPanel.csvFormatRequired')}</strong>
            <br />
            {t('controlPanel.csvColumnsInstruction')}
            <br />
            {t('controlPanel.csvNumericInstruction')}
            <br />
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
            <span>{isStreaming ? t('controlPanel.loading') : t('controlPanel.loadDummyData')}</span>
          </button>
          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px', textAlign: 'center' }}>
            {t('controlPanel.dummyDataHint')}
          </p>
        </div>
      </div>

      <div className="prompt-section">
        <div className="prompt-editor">
          <label>
            <strong className="system-prompt-label">{t('controlPanel.systemPrompt')}</strong>
            <textarea
              value={systemPrompt || getDefaultPrompt()}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder={t('controlPanel.systemPromptPlaceholder')}
              rows={4}
              disabled={isStreaming}
            />
          </label>
          <button
            onClick={handleResetPrompt}
            disabled={isStreaming}
            className="reset-prompt-button"
          >
            {t('controlPanel.resetToDefault')}
          </button>
        </div>

        <div className="api-key-section">
          <button
            type="button"
            onClick={() => setShowUserPromptSection(!showUserPromptSection)}
            className="toggle-api-key-button"
          >
            {showUserPromptSection ? t('controlPanel.hideUserPrompt') : t('controlPanel.userPromptOptional')}
          </button>
          {showUserPromptSection && (
            <div className="prompt-editor user-prompt-editor">
              <label>
                <strong className="system-prompt-label">{t('controlPanel.userPromptLabel')}</strong>
                <textarea
                  value={userPrompt}
                  onChange={(e) => setUserPrompt(e.target.value)}
                  placeholder={t('controlPanel.userPromptPlaceholder')}
                  rows={1}
                  disabled={isStreaming}
                />
              </label>
              <p style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                {t('controlPanel.userPromptHint')}
              </p>
            </div>
          )}
        </div>

        <div className="api-key-editor">
          <label>
            <strong className="system-prompt-label">{t('controlPanel.apiKeyLabel')}</strong>
          </label>
          <p style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
            {t('controlPanel.apiKeyHint')}
          </p>
          <div className="api-key-input-wrapper">
            <input
              type={showApiKeyValue ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={t('controlPanel.apiKeyPlaceholder')}
              disabled={isStreaming}
              className="api-key-input"
              autoComplete="off"
            />
            <button
              type="button"
              onClick={() => setShowApiKeyValue(!showApiKeyValue)}
              className="toggle-visibility-button"
              title={showApiKeyValue ? t('controlPanel.hide') : t('controlPanel.show')}
              tabIndex={-1}
            >
              {showApiKeyValue ? '🙈' : '👁'}
            </button>
          </div>
        </div>

        <div className="number-stream-container">
          <NumberStream numbers={numbers} isStreaming={isStreaming} />
        </div>
      </div>
      </div>
    </div>
  )
}

export default ControlPanel
