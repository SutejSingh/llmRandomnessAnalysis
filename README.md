# LLM Randomness Analysis

A full-stack application for **generating random numbers using LLMs** (OpenAI, Anthropic, DeepSeek) and **analyzing their statistical properties**. It supports single-run and **multi-run** workflows, **CSV upload/download**, and **PDF report generation** with comprehensive metrics and charts.

## Features

### Generation

- **Multi-LLM support**: Generate numbers via OpenAI, Anthropic, or DeepSeek
- **Request modes**:
  - **One request per number**: One API call per number (slower, more reliable)
  - **Batch**: One API call for many numbers in CSV-style output
- **Multi-run**: Generate 1–50 independent runs; each run is analyzed separately and in aggregate
- **Real-time streaming**: Watch numbers appear as they are generated (streaming UI hidden for CSV upload)
- **Custom prompts**: Edit system and optional user prompts per provider

### Data In / Out

- **CSV upload**: Upload a CSV with columns `run 1`, `run 2`, …; get immediate multi-run analysis (no streaming)
- **CSV download**: Download generated or analyzed runs as CSV
- **PDF report**: Download a full LaTeX-rendered report (metrics, tables, charts) for the current analysis

### Statistical Analysis

- **Single-run**: Full analysis for one sequence of numbers
- **Multi-run**:
  - **Statistics across all runs (combined stream)**: Mean, mode, median, std dev, variance, min, max, Q25/Q50/Q75, skewness, kurtosis computed on all numbers concatenated as one stream
  - **Aggregate statistics across runs**: Per-metric mean, std dev, and range across runs (mean, mode, std dev, skewness, kurtosis)
  - **Per-run summary**: Mean, mode, std dev, min, max, range, KS uniformity result per run
  - **Distribution deviation**: ECDF (K-S, MAD, regional) and Q-Q (R², MSE) vs uniform
  - **Autocorrelation**: Per-run significant lags and max |correlation|
- **NIST-style tests** (on binary representation of floats): Runs test, Binary Matrix Rank (32×32), Longest Run of Ones (block size 128), Approximate Entropy
- **Core analytics**: Basic stats (including mode), distribution (uniformity/K-S, histogram, KDE, Q-Q), range/ECDF/boundaries, independence (ACF, lag-1 scatter), stationarity (rolling mean/std, chunks), spectral (FFT, periodogram)

### Other

- **Dummy data**: Load pre-recorded single- or multi-run JSON for testing without API keys
- **Collapsible control panel**: Collapse after analysis to focus on results

## Project Structure

```
llmRandomnessAnalysis/
├── backend/
│   ├── main.py                 # FastAPI app and routes
│   ├── config.py               # App config and service wiring
│   ├── models.py               # Pydantic request/response models
│   ├── generation_service.py   # LLM number generation (stream + non-stream)
│   ├── analysis_service.py     # Single- and multi-run analysis orchestration
│   ├── stats_analyzer.py       # All statistics and NIST tests
│   ├── csv_service.py          # CSV export and upload parsing
│   ├── pdf_service.py          # PDF download endpoint
│   ├── latex_pdf_generator.py  # LaTeX report generation (tables, charts)
│   ├── llm_client.py           # OpenAI / Anthropic / DeepSeek clients
│   ├── dummy_data_service.py   # Dummy data from JSON files
│   ├── data/                   # Sample/dummy JSON and helpers
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # State, generate/upload/analyze/PDF flow
│   │   ├── components/
│   │   │   ├── ControlPanel.tsx    # Provider, count, runs, prompts, generate/upload
│   │   │   ├── NumberStream.tsx     # Number list (streaming or full)
│   │   │   ├── StatsDashboard.tsx # Tabs and multi vs per-run view
│   │   │   ├── MultiRunAnalysisView.tsx  # Multi-run tables and charts
│   │   │   ├── PerRunAnalysisView.tsx    # Single-run sections
│   │   │   ├── sections/       # BasicStats, Distribution, Range, Independence, Stationarity, Spectral, NIST
│   │   │   └── charts/         # BoxPlot, OverlaidBoxPlots
│   │   └── styles/
│   ├── package.json
│   └── vite.config.ts
├── start.sh                    # Start backend + frontend
└── README.md
```

## Setup

### Backend

1. Go to the backend directory and use a virtual environment (recommended):

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy environment template and add API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEEPSEEK_API_KEY=your_deepseek_key
```

Optional: `DUMMY_DATA_FILENAME` can point to a JSON file in `backend/data/` (e.g. `dummy_data_single_run.json`, `dummy_data_multiple_run.json`) for testing without keys.

3. Run the API:

```bash
python main.py
```

API base: **http://localhost:8000**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: **http://localhost:3000**

### One-command start

From the project root:

```bash
./start.sh
```

Starts backend and frontend; create `backend/.env` first if you use real API keys.

## Usage

1. **Provider**: Choose OpenAI, Anthropic, or DeepSeek (or use Dummy data).
2. **Count**: 10–1000 numbers per run (in batch mode this is in the system prompt).
3. **Number of runs**: 1–50; each run is generated then analyzed; multi-run views and PDF include aggregate and per-run stats.
4. **Request mode**: One request per number, or batch (one request for all numbers in a run).
5. **Prompts**: Optionally edit system and user prompts.
6. **Generate**: Click “Generate Random Numbers” to stream runs; analysis runs after all runs finish.
7. **Or upload CSV**: Use “Upload CSV” with columns `run 1`, `run 2`, …; analysis runs immediately (no streaming).
8. **Results**: Use the dashboard tabs (Basic, Distribution, Range, Independence, Stationarity, Spectral, NIST) and switch between **Multi-run** (overview + combined-stream stats, aggregate, per-run) and **Per-run** (drill into one run).
9. **Export**: Download numbers as CSV or the full report as PDF.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/providers` | List LLM providers |
| POST | `/generate` | Generate numbers (non-streaming) |
| POST | `/generate/stream` | Stream numbers (SSE) |
| POST | `/analyze` | Analyze `numbers` (single) or `runs` (multi-run) |
| POST | `/upload/csv` | Upload CSV; returns parsed runs + analysis |
| POST | `/download/csv` | Download runs as CSV (POST body: runs, provider) |
| POST | `/download/pdf` | Download analysis report as PDF (POST body: analysis) |
| GET | `/pdf/status` | PDF generation status |
| GET | `/dummy-data` | Get dummy data (single or multi-run) |
| GET | `/dummy-data/stream` | Stream dummy data as SSE |

## Statistical Notes

- **Basic stats**: Sample variance/std (ddof=1); mode = midpoint of histogram peak bin.
- **Combined-stream stats**: All runs concatenated into one series; same metrics as single-run basic stats.
- **NIST tests**: Applied to the IEEE 754 binary representation of the floats. Runs test, Binary Matrix Rank (32×32 only), Longest Run of Ones (block size 128 only), Approximate Entropy (NIST SP 800-22 formula).
- **Uniformity**: Kolmogorov–Smirnov test against uniform on the data range.

## License

MIT
