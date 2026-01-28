"""
CSV generation and parsing service
"""
import json
import logging
import re
from typing import List, Tuple
from datetime import datetime
from io import BytesIO, StringIO
import pandas as pd
from fastapi import HTTPException, UploadFile
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


async def parse_uploaded_csv(file: UploadFile) -> Tuple[List[List[float]], int]:
    """
    Parse uploaded CSV file and validate format
    
    Expected format: CSV with columns "run 1", "run 2", "run 3", etc.
    Each column contains numeric values (floats)
    
    Args:
        file: Uploaded CSV file
        
    Returns:
        Tuple of (runs_data, num_runs) where:
        - runs_data: List of runs (list of numbers)
        - num_runs: Number of runs detected
        
    Raises:
        HTTPException: If CSV format is invalid
    """
    try:
        # Read file content
        contents = await file.read()
        file_content = contents.decode('utf-8')
        
        # Parse CSV
        df = pd.read_csv(StringIO(file_content))
        
        # Validate that columns follow the expected format (run 1, run 2, etc.)
        runs_data = []
        
        # Check for columns matching "run 1", "run 2", etc. (case-insensitive, with optional spaces)
        column_names = [col.strip() for col in df.columns]
        
        # Find all columns that match the pattern "run N" or "runN"
        run_pattern = re.compile(r'^run\s*(\d+)$', re.IGNORECASE)
        
        run_columns = []
        for col in column_names:
            match = run_pattern.match(col)
            if match:
                run_num = int(match.group(1))
                run_columns.append((run_num, col))
        
        if not run_columns:
            raise HTTPException(
                status_code=400,
                detail="CSV must have columns named 'run 1', 'run 2', 'run 3', etc. (case-insensitive)"
            )
        
        # Sort by run number
        run_columns.sort(key=lambda x: x[0])
        
        # Extract data for each run
        for run_num, col_name in run_columns:
            # Find the actual column name in the dataframe (preserving original case/spacing)
            actual_col = None
            for df_col in df.columns:
                if df_col.strip().lower() == col_name.lower():
                    actual_col = df_col
                    break
            
            if actual_col is None:
                continue
            
            # Extract numbers from this column, filtering out empty/NaN values
            run_values = []
            for value in df[actual_col]:
                if pd.isna(value) or value == '':
                    continue
                try:
                    num = float(value)
                    run_values.append(num)
                except (ValueError, TypeError):
                    # Skip non-numeric values
                    logger.warning(f"Skipping non-numeric value '{value}' in {col_name}")
                    continue
            
            if len(run_values) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Column '{col_name}' contains no valid numeric values"
                )
            
            runs_data.append(run_values)
        
        if len(runs_data) == 0:
            raise HTTPException(
                status_code=400,
                detail="No valid run data found in CSV. Ensure columns are named 'run 1', 'run 2', etc."
            )
        
        num_runs = len(runs_data)
        logger.info(f"Successfully parsed CSV: {num_runs} runs, lengths: {[len(run) for run in runs_data]}")
        
        return runs_data, num_runs
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except Exception as e:
        logger.error(f"Error parsing CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error parsing CSV: {str(e)}")
