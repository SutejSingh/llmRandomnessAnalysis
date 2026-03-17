"""
Dummy data service for testing
"""
import json
import asyncio
import logging
import os
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


def get_dummy_data_service(dummy_data_filename: str) -> dict:
    """
    Get dummy data from file for testing
    
    Args:
        dummy_data_filename: Name of dummy data file
        
    Returns:
        Dictionary with dummy data information
    """
    try:
        dummy_file_path = os.path.join(os.path.dirname(__file__), "data", dummy_data_filename)
        if not os.path.exists(dummy_file_path):
            raise HTTPException(status_code=404, detail="Dummy data file not found")
        
        with open(dummy_file_path, 'r') as f:
            data = json.load(f)
        
        # Determine if it's single run or multi-run
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], list):
                # Multi-run format: [[x,x,x], [x,x,x]]
                return {
                    "data": data,
                    "is_multi_run": True,
                    "num_runs": len(data),
                    "count_per_run": len(data[0]) if data else 0
                }
            else:
                # Single run format: [x,x,x]
                return {
                    "data": [data],  # Wrap in array for consistency
                    "is_multi_run": False,
                    "num_runs": 1,
                    "count_per_run": len(data)
                }
        else:
            raise HTTPException(status_code=400, detail="Invalid dummy data format")
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing dummy data file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error parsing dummy data: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading dummy data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading dummy data: {str(e)}")


async def stream_dummy_data_service(dummy_data_filename: str) -> StreamingResponse:
    """
    Stream dummy data as SSE events to match LLM streaming format
    
    Args:
        dummy_data_filename: Name of dummy data file
        
    Returns:
        StreamingResponse with SSE events
    """
    dummy_file_path = os.path.join(os.path.dirname(__file__), "data", dummy_data_filename)
    
    if not os.path.exists(dummy_file_path):
        async def error_generator():
            yield f"data: {json.dumps({'error': 'Dummy data file not found'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    async def event_generator():
        try:
            with open(dummy_file_path, 'r') as f:
                data = json.load(f)
            
            # Determine format
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], list):
                    # Multi-run: stream all runs, with [DONE] between runs
                    for run_idx, run in enumerate(data):
                        for number in run:
                            yield f"data: {json.dumps({'number': number, 'provider': 'dummy'})}\n\n"
                            await asyncio.sleep(0.01)  # Small delay to simulate streaming
                        # Send [DONE] after each run (except the last one)
                        if run_idx < len(data) - 1:
                            yield "data: [DONE]\n\n"
                else:
                    # Single run: stream the array
                    for number in data:
                        yield f"data: {json.dumps({'number': number, 'provider': 'dummy'})}\n\n"
                        await asyncio.sleep(0.01)  # Small delay to simulate streaming
            # Final [DONE] to signal end of all data
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Error in dummy data stream: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
