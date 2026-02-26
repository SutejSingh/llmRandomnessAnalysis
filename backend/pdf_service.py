"""
PDF download service
"""
import logging
import tempfile
import shutil
import os
from typing import Dict, Any, List
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import Response

from reporting import LatexGenerator

logger = logging.getLogger(__name__)


async def download_pdf_service(
    analysis: Dict[str, Any],
    latex_generator: LatexGenerator
) -> Response:
    """
    Handle PDF download request. PDF is generated from analysis only (no runs_data).
    
    Args:
        analysis: Analysis data dictionary (contains all chart data)
        latex_generator: LatexGenerator instance
        
    Returns:
        Response with PDF file
    """
    # Generate PDF synchronously when button is pressed
    temp_dir = None
    try:
        logger.info("Generating PDF synchronously")
        # Create temporary directory for LaTeX compilation
        temp_dir = tempfile.mkdtemp()
        
        # Generate PDF using LaTeX (analysis-only; chart data is in analysis)
        temp_generator = LatexGenerator()
        pdf_bytes = temp_generator._generate_latex_pdf(analysis, None, temp_dir)
        temp_generator.cleanup()
        
        filename = f"LLM_Randomness_Evaluation_Report_{analysis.get('provider', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
