"""
Application configuration and setup
"""
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llm_client import LLMClient
from stats_analyzer import StatsAnalyzer
from latex_pdf_generator import LatexGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("Environment variables loaded")

# Get dummy data filename from environment variable, default to dummy_data.json
DUMMY_DATA_FILENAME = os.getenv("DUMMY_DATA_FILENAME", "dummy_data.json")
logger.info(f"Dummy data file: {DUMMY_DATA_FILENAME}")

# Log which API keys are available (without exposing the keys)
env_vars = {
    "OPENAI_API_KEY": "✓" if os.getenv("OPENAI_API_KEY") else "✗",
    "ANTHROPIC_API_KEY": "✓" if os.getenv("ANTHROPIC_API_KEY") else "✗",
    "DEEPSEEK_API_KEY": "✓" if os.getenv("DEEPSEEK_API_KEY") else "✗"
}
logger.info(f"API Keys status: {env_vars}")

# Initialize FastAPI app
app = FastAPI(title="LLM Random Number Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_client = LLMClient()
stats_analyzer = StatsAnalyzer()
latex_generator = LatexGenerator()  # Global PDF generator instance
current_runs_data = []  # Store current runs data for PDF generation
