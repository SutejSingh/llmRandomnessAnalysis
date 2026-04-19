# LLM Randomness Analysis

A full-stack application for **generating random numbers using LLMs** (OpenAI, Anthropic, DeepSeek) and **analyzing their statistical properties**. It supports single-run and **multi-run** workflows, **CSV upload/download**, and **PDF report generation** with comprehensive metrics and charts.

## Run locally

**Requirements:** Python 3 with `venv`, Node.js and npm.

There is **no required `.env` file**. The backend uses `python-dotenv` only to load `backend/.env` **if you create one**; otherwise set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and/or `DEEPSEEK_API_KEY` in your shell or IDE. Keys are only needed for live LLM generation—you can use **Dummy data** or **CSV upload** without any keys.

Optional env vars:

- **`DUMMY_DATA_FILENAME`** — JSON filename under `backend/data/` (create the folder if needed; default `dummy_data.json`).

1. **One command (from the repository root):**

```bash
./start.sh
```

This creates `backend/venv` if missing, installs backend dependencies, starts the API on **http://localhost:8000**, installs frontend dependencies if needed, and runs the Vite dev server on **http://localhost:3000**. Stop both with Ctrl+C.

2. **Manual setup** (alternative to `start.sh`):

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Frontend** (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api` to the backend (see `frontend/vite.config.ts`).

**Tests** (optional): from the repository root, with `backend/venv` activated (`source backend/venv/bin/activate`):

```bash
pytest
```

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

- **Dummy data**: Load pre-recorded single- or multi-run JSON from `backend/data/` for testing without API keys
- **Collapsible control panel**: Collapse after analysis to focus on results

## Project structure

```
llmRandomnessAnalysis/
├── backend/
│   ├── main.py                 # FastAPI app and routes
│   ├── config.py               # App config and service wiring
│   ├── models.py               # Pydantic request/response models
│   ├── model_ids.py            # LLM model id helpers
│   ├── generation_service.py   # LLM number generation (stream + non-stream)
│   ├── analysis_service.py     # Single- and multi-run analysis orchestration
│   ├── csv_service.py          # CSV export and upload parsing
│   ├── pdf_service.py          # PDF download endpoint
│   ├── llm_client.py           # OpenAI / Anthropic / DeepSeek clients
│   ├── dummy_data_service.py   # Dummy data from JSON under backend/data/
│   ├── stats/                  # Statistics and NIST tests (StatsAnalyzer)
│   │   ├── analyzer.py
│   │   ├── basic_stats.py
│   │   ├── distribution.py
│   │   ├── independence.py
│   │   ├── range_behavior.py
│   │   ├── stationarity.py
│   │   ├── spectral.py
│   │   ├── nist_tests.py
│   │   └── utils.py
│   ├── reporting/              # LaTeX → PDF report generation
│   │   ├── latex_generator.py
│   │   ├── latex_tables.py
│   │   ├── latex_charts.py
│   │   └── common.py
│   ├── test_data/              # Sample CSVs for tests or manual checks
│   ├── tests/                  # pytest suite (mirrors packages above)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── i18n.ts
│   │   ├── constants/          # e.g. llmModels.ts
│   │   ├── locales/            # en.json
│   │   ├── utils/
│   │   ├── components/
│   │   │   ├── ControlPanel.tsx
│   │   │   ├── DashboardHeader.tsx
│   │   │   ├── NumberStream.tsx
│   │   │   ├── StatsDashboard.tsx
│   │   │   ├── MultiRunAnalysisView.tsx
│   │   │   ├── PerRunAnalysisView.tsx
│   │   │   ├── ErrorModal.tsx
│   │   │   ├── sections/       # Basic, Distribution, Range, …
│   │   │   └── charts/         # BoxPlot, OverlaidBoxPlots
│   │   └── styles/
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── real_data/                  # Archived LLM output CSVs (by provider / range)
├── pytest.ini
├── prompts.txt
├── start.sh                    # Start backend + frontend from repo root
└── README.md
```

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
