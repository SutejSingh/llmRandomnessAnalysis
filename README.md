# LLM Random Number Analysis

A comprehensive application for generating random numbers using different LLM providers (OpenAI, Anthropic, DeepSeek) and performing detailed statistical analysis on the generated sequences.

## Features

- **Multi-LLM Support**: Query OpenAI, Anthropic, and DeepSeek for random number generation
- **Real-time Streaming**: Watch numbers generate in real-time
- **Customizable Prompts**: Modify system prompts to test different LLM behaviors
- **Comprehensive Statistical Analysis**:
  - Basic descriptive statistics (mean, median, variance, quantiles)
  - Distribution shape analysis (normality tests, uniformity tests, KDE, Q-Q plots)
  - Range & boundary behavior (ECDF, edge analysis)
  - Independence/correlation analysis (ACF, lag plots, time series)
  - Stationarity analysis (rolling statistics, chunked analysis)
  - Spectral analysis (FFT, periodogram)

## Project Structure

```
LLMRandomNumberGen/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── llm_client.py        # LLM integration clients
│   ├── stats_analyzer.py    # Statistical analysis engine
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── App.tsx          # Main app component
│   │   └── main.tsx         # Entry point
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite configuration
└── README.md
```

## Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the example:
```bash
cp .env.example .env
```

5. Add your API keys to `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DUMMY_DATA_FILENAME=dummy_data.json
```

**Note**: `DUMMY_DATA_FILENAME` is optional and defaults to `dummy_data.json`. You can set it to any JSON file in the `backend/data/` directory (e.g., `dummy_data_single_run.json` or `dummy_data_multiple_run.json`).

6. Run the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. **Select LLM Provider**: Choose from OpenAI, Anthropic, or DeepSeek
2. **Set Number Count**: Specify how many random numbers to generate (10-1000)
3. **Customize Prompt** (optional): Click "Show System Prompt Editor" to modify the system prompt
4. **Generate**: Click "Generate Random Numbers" to start streaming
5. **Analyze**: Statistics are automatically calculated and displayed in tabs:
   - **Basic**: Descriptive statistics and histograms
   - **Distribution**: Normality/uniformity tests, KDE, Q-Q plots
   - **Range**: Boundary behavior and ECDF
   - **Independence**: Autocorrelation, lag plots, time series
   - **Stationarity**: Rolling statistics and chunked analysis
   - **Spectral**: FFT and power spectrum analysis

## API Endpoints

- `POST /generate` - Generate random numbers (non-streaming)
- `POST /generate/stream` - Stream random numbers (Server-Sent Events)
- `POST /analyze` - Perform statistical analysis on number array
- `GET /providers` - Get list of available LLM providers

## Statistical Tests

The application performs various statistical tests to assess randomness quality:

- **Normality Tests**: Shapiro-Wilk, D'Agostino's test
- **Uniformity Test**: Kolmogorov-Smirnov test
- **Independence**: Autocorrelation function, lag-1 scatter plots
- **Stationarity**: Rolling mean/variance, chunked statistics
- **Spectral Analysis**: FFT to detect periodic patterns

## Notes

- API rate limiting: The application includes basic rate limiting (0.1s delay between requests)
- Large samples: For samples > 5000, D'Agostino's test is used instead of Shapiro-Wilk
- Real-time updates: Statistics are recalculated automatically as numbers stream in

## License

MIT
