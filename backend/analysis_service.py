"""
Analysis service for statistical analysis
"""
import json
import logging
from typing import Dict, Any
from fastapi import HTTPException, Request

from models import NumberData, MultiRunData
from stats_analyzer import StatsAnalyzer

logger = logging.getLogger(__name__)


async def analyze_numbers_service(
    request: Request,
    stats_analyzer: StatsAnalyzer
) -> Dict[str, Any]:
    """
    Perform comprehensive statistical analysis on generated numbers.
    Does not store runs; client sends analysis for PDF download.
    
    Args:
        request: FastAPI request object
        stats_analyzer: StatsAnalyzer instance
        
    Returns:
        Analysis results dictionary
    """
    try:
        body = await request.json()
        logger.info(f"Received analyze request. Keys in body: {list(body.keys())}")
        
        # Check if it's a multi-run request
        if 'runs' in body:
            runs_data = body.get('runs', [])
            logger.info(f"Multi-run analysis requested: {len(runs_data)} runs, num_runs={body.get('num_runs')}")
            if not runs_data:
                raise HTTPException(status_code=400, detail="'runs' array is empty")
            if not isinstance(runs_data, list):
                raise HTTPException(status_code=400, detail="'runs' must be an array")
            
            try:
                data = MultiRunData(**body)
                logger.info(f"Validated multi-run data: {len(data.runs)} runs, provider={data.provider}")
                # Log run lengths for debugging
                run_lengths = [len(run) for run in data.runs]
                logger.info(f"Run lengths: {run_lengths}")
                analysis = stats_analyzer.analyze_multi_run(data.runs, data.provider, data.num_runs)
                logger.info("Multi-run analysis completed successfully")
                
                return analysis
            except ValueError as e:
                logger.error(f"Validation error in multi-run analysis: {str(e)}", exc_info=True)
                raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
            except Exception as e:
                logger.error(f"Error in multi-run analysis: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Multi-run analysis error: {str(e)}")
        elif 'numbers' in body:
            # Single run analysis (backward compatibility)
            numbers_data = body.get('numbers', [])
            logger.info(f"Single-run analysis requested: {len(numbers_data)} numbers")
            if not numbers_data:
                raise HTTPException(status_code=400, detail="'numbers' array is empty")
            if not isinstance(numbers_data, list):
                raise HTTPException(status_code=400, detail="'numbers' must be an array")
            
            try:
                data = NumberData(**body)
                logger.info(f"Validated single-run data: {len(data.numbers)} numbers, provider={data.provider}")
                analysis = stats_analyzer.analyze(data.numbers, data.provider)
                logger.info("Single-run analysis completed successfully")
                
                return analysis
            except ValueError as e:
                logger.error(f"Validation error in single-run analysis: {str(e)}", exc_info=True)
                raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
            except Exception as e:
                logger.error(f"Error in single-run analysis: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Single-run analysis error: {str(e)}")
        else:
            logger.error(f"Invalid request body: missing 'runs' or 'numbers' key. Body keys: {list(body.keys())}")
            raise HTTPException(status_code=400, detail="Either 'runs' or 'numbers' must be provided")
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in analyze endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
