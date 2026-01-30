import { useState, useEffect } from 'react'
import axios from 'axios'
import ControlPanel from './components/ControlPanel'
import StatsDashboard from './components/StatsDashboard'
import './styles/App.css'

const API_BASE = 'http://localhost:8000'

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
  const [systemPrompt, setSystemPrompt] = useState('')
  const [userPrompt, setUserPrompt] = useState('')
  const [count, setCount] = useState(100)
  const [batchMode, setBatchMode] = useState(false)
  const [numRuns, setNumRuns] = useState(1)
  const [allRuns, setAllRuns] = useState<number[][]>([])

  const handleGenerate = async () => {
    setNumbers([])
    setAnalysis(null)
    setAllRuns([])
    setIsStreaming(true)

    const runs: number[][] = []
    let currentRun: number[] = []

    try {
      for (let runIndex = 0; runIndex < numRuns; runIndex++) {
        currentRun = []
        const response = await fetch(`${API_BASE}/generate/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            provider,
            count,
            system_prompt: systemPrompt && systemPrompt.trim() ? systemPrompt.trim() : undefined,
            user_prompt: userPrompt && userPrompt.trim() ? userPrompt.trim() : undefined,
            batch_mode: batchMode
          })
        })

        if (!response.body) {
          throw new Error('No response body')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6)
              if (dataStr === '[DONE]') {
                break
              }
              try {
                const data = JSON.parse(dataStr)
                if (data.error) {
                  console.error('Error:', data.error)
                  throw new Error(data.error)
                }
                if (data.number !== undefined) {
                  currentRun.push(data.number)
                  setNumbers((prev) => [...prev, data.number])
                }
              } catch (e) {
                // Skip invalid JSON
              }
            }
          }
        }
        
        runs.push([...currentRun])
        setAllRuns([...runs])
      }

      setIsStreaming(false)
      
      // Trigger analysis after all runs are complete
      if (runs.length > 0 && runs.length === numRuns) {
        console.log(`All ${numRuns} runs complete. Run lengths:`, runs.map(r => r.length))
        
        // Validate runs have data
        const allRunsHaveData = runs.every(run => run && run.length > 0)
        if (!allRunsHaveData) {
          console.error('Some runs are empty:', runs.map((r, i) => `Run ${i + 1}: ${r.length} numbers`))
          setIsStreaming(false)
          return
        }
        
        // Analyze directly with the runs array
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
          if (axios.isAxiosError(error)) {
            console.error('Error details:', {
              status: error.response?.status,
              statusText: error.response?.statusText,
              data: error.response?.data,
              message: error.message
            })
          }
        }
      } else {
        console.warn(`Runs incomplete: ${runs.length}/${numRuns} runs collected`)
      }
    } catch (error) {
      console.error('Streaming error:', error)
      setIsStreaming(false)
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

  const handleDummyData = async () => {
    setNumbers([])
    setAnalysis(null)
    setAllRuns([])
    setIsStreaming(true)

    try {
      // First, get dummy data info to determine format
      const infoResponse = await axios.get(`${API_BASE}/dummy-data`)
      const dummyInfo = infoResponse.data
      
      const runs: number[][] = []
      let currentRun: number[] = []
      const totalRuns = dummyInfo.is_multi_run ? dummyInfo.num_runs : 1

      // Stream dummy data
      const response = await fetch(`${API_BASE}/dummy-data/stream`)
      
      if (!response.body) {
        throw new Error('No response body')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            if (dataStr === '[DONE]') {
              // End of current run
              if (currentRun.length > 0) {
                runs.push([...currentRun])
                setAllRuns([...runs])
                currentRun = []
              }
              // If we've collected all runs, break
              if (runs.length >= totalRuns) {
                break
              }
              continue
            }
            try {
              const data = JSON.parse(dataStr)
              if (data.error) {
                console.error('Error:', data.error)
                throw new Error(data.error)
              }
              if (data.number !== undefined) {
                currentRun.push(data.number)
                setNumbers((prev) => [...prev, data.number])
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
        
        // Break if we've collected all runs
        if (runs.length >= totalRuns) {
          break
        }
      }

      // Handle any remaining data
      if (currentRun.length > 0) {
        runs.push([...currentRun])
        setAllRuns([...runs])
      }

      setIsStreaming(false)
      setProvider('dummy')
      setNumRuns(dummyInfo.is_multi_run ? dummyInfo.num_runs : 1)

      // Trigger analysis after all runs are complete
      if (runs.length > 0) {
        console.log(`Dummy data loaded. Run lengths:`, runs.map(r => r.length))
        
        const allRunsHaveData = runs.every(run => run && run.length > 0)
        if (!allRunsHaveData) {
          console.error('Some runs are empty:', runs.map((r, i) => `Run ${i + 1}: ${r.length} numbers`))
          setIsStreaming(false)
          return
        }
        
        try {
          if (runs.length === 1) {
            console.log('Triggering single-run analysis for dummy data...')
            const response = await axios.post(`${API_BASE}/analyze`, {
              numbers: runs[0],
              provider: 'dummy'
            })
            console.log('Analysis response received:', response.data)
            setAnalysis(response.data)
          } else {
            console.log('Triggering multi-run analysis for dummy data...', { runsCount: runs.length })
            const response = await axios.post(`${API_BASE}/analyze`, {
              runs: runs,
              provider: 'dummy',
              num_runs: runs.length
            })
            console.log('Analysis response received:', response.data)
            setAnalysis(response.data)
          }
        } catch (error) {
          console.error('Analysis error:', error)
          if (axios.isAxiosError(error)) {
            console.error('Error details:', {
              status: error.response?.status,
              statusText: error.response?.statusText,
              data: error.response?.data,
              message: error.message
            })
          }
        }
      }
    } catch (error) {
      console.error('Dummy data error:', error)
      setIsStreaming(false)
      if (axios.isAxiosError(error)) {
        alert(`Error: ${error.response?.data?.detail || error.message}`)
      }
    }
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

  return (
    <div className="app">
      <header className="app-header">
        <h1>LLM Random Number Generator</h1>
      </header>

      <div className="app-content">
        <ControlPanel
          provider={provider}
          setProvider={setProvider}
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
          onGenerate={handleGenerate}
          isStreaming={isStreaming}
          numbers={numbers}
          onDummyData={handleDummyData}
          onCsvUpload={handleCsvUpload}
          analysisReady={!!analysis}
        />

        {analysis ? (
          <StatsDashboard analysis={analysis} allRuns={allRuns} />
        ) : (
          allRuns.length > 0 && !isStreaming && (
            <div style={{ padding: '20px', background: '#f5f5f5', borderRadius: '8px', marginTop: '20px' }}>
              <p>Numbers generated but analysis not available. Runs: {allRuns.length}/{numRuns}</p>
              <p>Run lengths: {allRuns.map((r, i) => `Run ${i + 1}: ${r.length}`).join(', ')}</p>
              <button onClick={handleAnalyze} style={{ marginTop: '10px', padding: '8px 16px' }}>
                Retry Analysis
              </button>
            </div>
          )
        )}
      </div>
    </div>
  )
}

export default App
