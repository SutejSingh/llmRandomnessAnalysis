import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { t } from './i18n'
import ControlPanel from './components/ControlPanel'
import StatsDashboard from './components/StatsDashboard'
import ErrorModal from './components/ErrorModal'
import { getDefaultModelForProvider } from './constants/llmModels'
import './styles/App.css'

const API_BASE = 'http://localhost:8000'

/** How often to flush queued stream numbers to React state (reduces re-renders while staying responsive). */
const STREAM_UI_FLUSH_MS = 2000

/** Parse FastAPI-style JSON error body from a failed fetch */
async function parseFetchErrorMessage(response: Response): Promise<string> {
  const text = await response.text()
  let msg = `Request failed (${response.status} ${response.statusText || ''})`.trim()
  try {
    const j = JSON.parse(text) as { detail?: unknown }
    if (typeof j.detail === 'string') {
      return j.detail
    }
    if (Array.isArray(j.detail)) {
      return j.detail
        .map((item: unknown) => {
          if (item && typeof item === 'object' && 'msg' in item) {
            return String((item as { msg: string }).msg)
          }
          return JSON.stringify(item)
        })
        .join('; ')
    }
    if (j.detail != null) {
      return String(j.detail)
    }
  } catch {
    /* not JSON */
  }
  if (text.trim()) {
    return text.length > 2000 ? `${text.slice(0, 2000)}…` : text
  }
  return msg
}

interface AnalysisData {
  provider: string
  count?: number
  num_runs?: number
  count_per_run?: number
  basic_stats?: any
  distribution?: any
  range_behavior?: any
  independence?: any
  stationarity?: any
  spectral?: any
  raw_data?: number[]
  aggregate_stats?: any
  test_results?: any
  autocorrelation_table?: any[]
  ecdf_all_runs?: any[]
  individual_analyses?: any[]
}

function App() {
  const [numbers, setNumbers] = useState<number[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null)
  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState(() => getDefaultModelForProvider('openai'))
  const [systemPrompt, setSystemPrompt] = useState('')
  const [userPrompt, setUserPrompt] = useState('')
  const [count, setCount] = useState(100)
  const [batchMode, setBatchMode] = useState(false)
  const [numRuns, setNumRuns] = useState(1)
  const [apiKey, setApiKey] = useState('')
  const [allRuns, setAllRuns] = useState<number[][]>([])
  const [generationError, setGenerationError] = useState<string | null>(null)

  const clearGenerationError = useCallback(() => setGenerationError(null), [])

  const handleGenerate = async () => {
    setNumbers([])
    setAnalysis(null)
    setAllRuns([])
    setGenerationError(null)
    setIsStreaming(true)

    let runs: number[][] = []
    let streamFailed = false
    const pendingUi: number[] = []
    let flushInterval: ReturnType<typeof setInterval> | null = null

    const flushPendingToUi = () => {
      if (pendingUi.length === 0) return
      const batch = pendingUi.splice(0, pendingUi.length)
      setNumbers((prev) => [...prev, ...batch])
    }

    try {
      runs = []
      flushInterval = setInterval(flushPendingToUi, STREAM_UI_FLUSH_MS)
      let currentRun: number[] = []

      for (let runIndex = 0; runIndex < numRuns; runIndex++) {
        currentRun = []
        const response = await fetch(`${API_BASE}/generate/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            provider,
            model,
            count,
            system_prompt: systemPrompt && systemPrompt.trim() ? systemPrompt.trim() : undefined,
            user_prompt: userPrompt && userPrompt.trim() ? userPrompt.trim() : undefined,
            batch_mode: batchMode,
            api_key: apiKey && apiKey.trim() ? apiKey.trim() : undefined
          })
        })

        if (!response.ok) {
          const errMsg = await parseFetchErrorMessage(response)
          throw new Error(errMsg)
        }

        if (!response.body) {
          throw new Error('No response body from server')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const dataStr = line.slice(6).trim()
            if (dataStr === '[DONE]') {
              break
            }
            let data: { error?: string; number?: number }
            try {
              data = JSON.parse(dataStr) as { error?: string; number?: number }
            } catch {
              continue
            }
            if (data.error) {
              throw new Error(data.error)
            }
            if (data.number !== undefined) {
              const n = data.number
              currentRun.push(n)
              pendingUi.push(n)
            }
          }
        }
        runs.push([...currentRun])
        setAllRuns([...runs])
      }
    } catch (error) {
      console.error('Streaming error:', error)
      streamFailed = true
      pendingUi.length = 0
      setIsStreaming(false)
      setNumbers([])
      setAllRuns([])
      const msg =
        error instanceof Error ? error.message : typeof error === 'string' ? error : 'An unknown error occurred'
      setGenerationError(msg)
    } finally {
      if (flushInterval !== null) {
        clearInterval(flushInterval)
      }
      if (!streamFailed) {
        flushPendingToUi()
        setIsStreaming(false)
      }
    }

    if (streamFailed) {
      return
    }

    // Trigger analysis after all runs are complete
    if (runs.length > 0 && runs.length === numRuns) {
      console.log(`All ${numRuns} runs complete. Run lengths:`, runs.map((r) => r.length))

      const allRunsHaveData = runs.every((run) => run && run.length > 0)
      if (!allRunsHaveData) {
        console.error('Some runs are empty:', runs.map((r, i) => `Run ${i + 1}: ${r.length} numbers`))
        setNumbers([])
        setAllRuns([])
        setGenerationError(
          'No numbers were received from the model. Check your API key, model access, and provider status — or try again.'
        )
        return
      }

      try {
        if (numRuns === 1 && runs.length === 1) {
          console.log('Triggering single-run analysis...', { numbersCount: runs[0].length, provider })
          const response = await axios.post(`${API_BASE}/analyze`, {
            numbers: runs[0],
            provider
          })
          console.log('Analysis response received:', response.data)
          setAnalysis(response.data)
        } else {
          console.log('Triggering multi-run analysis...', { runsCount: runs.length, numRuns, provider })
          const response = await axios.post(`${API_BASE}/analyze`, {
            runs: runs,
            provider,
            num_runs: numRuns
          })
          console.log('Analysis response received:', response.data)
          setAnalysis(response.data)
        }
      } catch (error) {
        console.error('Analysis error:', error)
        let analysisMsg = 'Analysis request failed.'
        if (axios.isAxiosError(error)) {
          const d = error.response?.data
          if (d && typeof d === 'object' && 'detail' in d) {
            const det = (d as { detail: unknown }).detail
            analysisMsg =
              typeof det === 'string' ? det : Array.isArray(det) ? JSON.stringify(det) : String(det)
          } else if (error.message) {
            analysisMsg = error.message
          }
        } else if (error instanceof Error) {
          analysisMsg = error.message
        }
        setGenerationError(analysisMsg)
      }
    } else {
      console.warn(`Runs incomplete: ${runs.length}/${numRuns} runs collected`)
    }
  }

  const handleAnalyze = async () => {
    if (allRuns.length === 0) return

    try {
      // For single run, use backward compatible format
      if (numRuns === 1 && allRuns.length === 1) {
        const response = await axios.post(`${API_BASE}/analyze`, {
          numbers: allRuns[0],
          provider
        })
        setAnalysis(response.data)
      } else {
        // Multi-run analysis
        const response = await axios.post(`${API_BASE}/analyze`, {
          runs: allRuns,
          provider,
          num_runs: numRuns
        })
        setAnalysis(response.data)
      }
    } catch (error) {
      console.error('Analysis error:', error)
      let analysisMsg = 'Analysis request failed.'
      if (axios.isAxiosError(error)) {
        const d = error.response?.data
        if (d && typeof d === 'object' && 'detail' in d) {
          const det = (d as { detail: unknown }).detail
          analysisMsg =
            typeof det === 'string' ? det : Array.isArray(det) ? JSON.stringify(det) : String(det)
        } else if (error.message) {
          analysisMsg = error.message
        }
      } else if (error instanceof Error) {
        analysisMsg = error.message
      }
      setGenerationError(analysisMsg)
    }
  }

  const handleCsvUpload = (runs: number[][], numRuns: number, uploadedAnalysis: AnalysisData) => {
    // Update state with uploaded data
    setAllRuns(runs)
    setNumRuns(numRuns)
    setProvider('uploaded')
    
    // Flatten all runs for the numbers display
    const allNumbers = runs.flat()
    setNumbers(allNumbers)
    
    // Set the analysis from the backend
    setAnalysis(uploadedAnalysis)
  }

  // Fallback: trigger analysis when state updates (for cases where direct call doesn't work)
  useEffect(() => {
    if (allRuns.length === numRuns && !isStreaming && numRuns > 0 && allRuns.length > 0) {
      // Check if all runs have data (don't check exact count since batch mode might vary)
      const allHaveData = allRuns.every(run => run.length > 0)
      if (allHaveData) {
        // Only trigger if analysis is null (not already set)
        if (!analysis) {
          handleAnalyze()
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allRuns.length, isStreaming, numRuns])

  const hasNumbersToAnalyze =
    allRuns.length > 0 && allRuns.some((r) => r.length > 0) && !generationError

  return (
    <div className="app">
      {generationError && (
        <ErrorModal message={generationError} onClose={clearGenerationError} />
      )}
      <header className="app-header">
        <h1>{t('app.title')}</h1>
      </header>

      <div className="app-content">
        <ControlPanel
          provider={provider}
          setProvider={setProvider}
          model={model}
          setModel={setModel}
          systemPrompt={systemPrompt}
          setSystemPrompt={setSystemPrompt}
          userPrompt={userPrompt}
          setUserPrompt={setUserPrompt}
          count={count}
          setCount={setCount}
          batchMode={batchMode}
          setBatchMode={setBatchMode}
          numRuns={numRuns}
          setNumRuns={setNumRuns}
          apiKey={apiKey}
          setApiKey={setApiKey}
          onGenerate={handleGenerate}
          isStreaming={isStreaming}
          numbers={numbers}
          onCsvUpload={handleCsvUpload}
          analysisReady={!!analysis}
        />

        {analysis ? (
          <StatsDashboard analysis={analysis} allRuns={allRuns} />
        ) : (
          hasNumbersToAnalyze &&
          !isStreaming && (
            <div style={{ padding: '20px', background: '#f5f5f5', borderRadius: '8px', marginTop: '20px' }}>
              <p>{t('app.numbersGeneratedButAnalysisNotAvailable', { current: String(allRuns.length), total: String(numRuns) })}</p>
              <p>{t('app.runLengths', { list: allRuns.map((r, i) => `Run ${i + 1}: ${r.length}`).join(', ') })}</p>
              <button onClick={handleAnalyze} style={{ marginTop: '10px', padding: '8px 16px' }}>
                {t('app.retryAnalysis')}
              </button>
            </div>
          )
        )}
      </div>
    </div>
  )
}

export default App
