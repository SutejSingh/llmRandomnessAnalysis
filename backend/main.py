"""
FastAPI application - Route handlers only
All business logic is in service modules
"""
from fastapi import Request, Query, UploadFile, File, HTTPException
import json
import logging

# Import configuration and services
from config import app, llm_client, stats_analyzer, latex_generator, current_runs_data, DUMMY_DATA_FILENAME
from models import PromptRequest, PDFDownloadRequest

# Import service functions
from generation_service import generate_numbers_service, generate_numbers_stream_service
from analysis_service import analyze_numbers_service
from csv_service import generate_csv, parse_uploaded_csv
from pdf_service import download_pdf_service
from dummy_data_service import get_dummy_data_service, stream_dummy_data_service

logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    return {"message": "LLM Random Number Generator API"}


@app.post("/generate")
async def generate_numbers(request: PromptRequest):
    """Generate random numbers from specified LLM provider"""
    return await generate_numbers_service(request, llm_client)


@app.post("/generate/stream")
async def generate_numbers_stream(request: PromptRequest):
    """Stream random numbers from specified LLM provider"""
    return await generate_numbers_stream_service(request, llm_client)


@app.post("/analyze")
async def analyze_numbers(request: Request):
    """Perform comprehensive statistical analysis on generated numbers"""
    return await analyze_numbers_service(request, stats_analyzer, current_runs_data)


@app.get("/download/csv")
async def download_csv(
    runs: str = Query(..., description="JSON string of runs array"),
    provider: str = Query("manual", description="Provider name")
):
    """Download raw numbers as CSV file with columns run 1, run 2, etc."""
    runs_data = json.loads(runs)
    return generate_csv(runs_data, provider)


@app.post("/download/pdf")
async def download_pdf(request: PDFDownloadRequest):
    """Download full analysis report as PDF file with metrics, charts, and everything using LaTeX"""
    return await download_pdf_service(request.analysis, request.runs, latex_generator)


@app.get("/dummy-data")
async def get_dummy_data():
    """Get dummy data from file for testing"""
    return get_dummy_data_service(DUMMY_DATA_FILENAME)


@app.get("/dummy-data/stream")
async def stream_dummy_data():
    """Stream dummy data as SSE events to match LLM streaming format"""
    return await stream_dummy_data_service(DUMMY_DATA_FILENAME)


@app.get("/providers")
async def get_providers():
    """Get list of available LLM providers"""
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI"},
            {"id": "anthropic", "name": "Anthropic"},
            {"id": "deepseek", "name": "DeepSeek"}
        ]
    }


@app.get("/pdf/status")
async def get_pdf_status():
    """Get the current PDF generation status"""
    status = latex_generator.get_status()
    return {
        "status": status,
        "is_ready": latex_generator.is_ready(),
        "error": latex_generator.get_error()
    }


@app.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload and parse CSV file with runs data
    
    Expected format: CSV with columns "run 1", "run 2", "run 3", etc.
    Each column contains numeric values (floats)
    
    Returns:
        Parsed runs data and metadata
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file (.csv extension)")
        
        # Parse CSV
        runs_data, num_runs = await parse_uploaded_csv(file)
        
        # Store runs data for potential PDF generation
        current_runs_data.clear()
        current_runs_data.extend(runs_data)
        
        # Perform analysis on uploaded data
        provider = "uploaded"
        analysis = stats_analyzer.analyze_multi_run(runs_data, provider, num_runs)
        
        return {
            "runs": runs_data,
            "num_runs": num_runs,
            "provider": provider,
            "analysis": analysis,
            "message": f"Successfully uploaded and analyzed {num_runs} run(s)"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
