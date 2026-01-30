"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class PromptRequest(BaseModel):
    """Request model for generating random numbers"""
    provider: str  # "openai", "anthropic", "deepseek"
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None  # User message sent to the model (e.g. "Generate a random number between 0 and 1.")
    count: Optional[int] = 100
    api_key: Optional[str] = None  # API key for the selected provider
    batch_mode: Optional[bool] = False  # True = one request for all numbers, False = one request per number


class NumberData(BaseModel):
    """Request model for single-run analysis"""
    numbers: List[float]
    provider: str


class MultiRunData(BaseModel):
    """Request model for multi-run analysis"""
    runs: List[List[float]]
    provider: str
    num_runs: int


class PDFDownloadRequest(BaseModel):
    """Request model for PDF download. Analysis contains all chart data; runs not required."""
    analysis: Dict[str, Any]


class CSVDownloadRequest(BaseModel):
    """Request model for CSV download. Sends runs in body to avoid URL length limits."""
    runs: List[List[float]]
    provider: str = "manual"
