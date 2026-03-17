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

# Chunk size for streaming CSV parse (Option A: pd.read_csv with chunks)
CSV_CHUNK_SIZE = 10000


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
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in runs parameter")
    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")


async def parse_uploaded_csv(file: UploadFile) -> Tuple[List[List[float]], int]:
    """
    Parse uploaded CSV file using streaming (Option A: read in chunks, pd.read_csv with chunksize).
    Reads file in chunks from FastAPI UploadFile, then parses with pandas in chunked mode
    to avoid loading full DataFrame into memory at once.
    
    Expected format: CSV with columns "run 1", "run 2", "run 3", etc.
    Each column contains numeric values (floats)
    
    Args:
        file: Uploaded CSV file (streaming)
        
    Returns:
        Tuple of (runs_data, num_runs)
    """
    try:
        # Stream read: accumulate chunks from FastAPI upload
        chunks = []
        while True:
            chunk = await file.read(1024 * 1024)  # 1 MB per read
            if not chunk:
                break
            chunks.append(chunk)
        file_content = b"".join(chunks).decode("utf-8")
        
        # Get column names from file (header only)
        header_df = pd.read_csv(StringIO(file_content), nrows=0)
        column_names = [col.strip() for col in header_df.columns]
        run_pattern = re.compile(r"^run\s*(\d+)$", re.IGNORECASE)
        run_columns = []
        for col in column_names:
            match = run_pattern.match(col)
            if match:
                run_columns.append((int(match.group(1)), col))
        if not run_columns:
            raise HTTPException(
                status_code=400,
                detail="CSV must have columns named 'run 1', 'run 2', 'run 3', etc. (case-insensitive)"
            )
        run_columns.sort(key=lambda x: x[0])
        
        # Map (run_idx, actual_column_name) for each run column
        actual_col_names = list(header_df.columns)
        run_col_indices: List[Tuple[int, str]] = []
        for i, (_, col_name) in enumerate(run_columns):
            for ac in actual_col_names:
                if ac.strip().lower() == col_name.lower():
                    run_col_indices.append((i, ac))
                    break
        
        # Parse CSV in chunks to avoid full DataFrame in memory
        runs_data: List[List[float]] = [[] for _ in run_columns]
        chunk_iter = pd.read_csv(StringIO(file_content), chunksize=CSV_CHUNK_SIZE)
        for df_chunk in chunk_iter:
            for run_idx, actual_col in run_col_indices:
                if actual_col not in df_chunk.columns:
                    continue
                for value in df_chunk[actual_col]:
                    if pd.isna(value) or value == "":
                        continue
                    try:
                        runs_data[run_idx].append(float(value))
                    except (ValueError, TypeError):
                        logger.warning("Skipping non-numeric value in %s", actual_col)
                        continue
        
        # Validate we got data
        if all(len(r) == 0 for r in runs_data):
            raise HTTPException(
                status_code=400,
                detail="No valid run data found in CSV. Ensure columns are named 'run 1', 'run 2', etc."
            )
        num_runs = len(runs_data)
        logger.info(
            "Successfully parsed CSV (streaming): %s runs, lengths: %s",
            num_runs,
            [len(run) for run in runs_data],
        )
        return runs_data, num_runs
        
    except HTTPException:
        raise
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except Exception as e:
        logger.error("Error parsing CSV: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")
