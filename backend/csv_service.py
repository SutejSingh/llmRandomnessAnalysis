"""
CSV generation service
"""
import json
import logging
from typing import List
from datetime import datetime
from io import BytesIO
import pandas as pd
from fastapi import HTTPException
from fastapi.responses import Response

logger = logging.getLogger(__name__)


def generate_csv(runs_data: List[List[float]], provider: str) -> Response:
    """
    Generate CSV file from runs data
    
    Args:
        runs_data: List of runs (list of numbers)
        provider: Provider name for filename
        
    Returns:
        Response with CSV file
    """
    try:
        if not isinstance(runs_data, list) or len(runs_data) == 0:
            raise HTTPException(status_code=400, detail="Invalid runs data")
        
        # Create DataFrame with runs as columns
        max_len = max(len(run) for run in runs_data)
        data_dict = {}
        
        for i, run in enumerate(runs_data):
            col_name = f"run {i + 1}"
            # Pad shorter runs with empty strings
            padded_run = run + [""] * (max_len - len(run))
            data_dict[col_name] = padded_run
        
        df = pd.DataFrame(data_dict)
        
        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        filename = f"random_numbers_{provider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in runs parameter")
    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")
