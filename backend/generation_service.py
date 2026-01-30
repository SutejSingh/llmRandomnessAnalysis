"""
Generation service for LLM number generation
"""
import json
import logging
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from models import PromptRequest
from llm_client import LLMClient

logger = logging.getLogger(__name__)


async def generate_numbers_service(
    request: PromptRequest,
    llm_client: LLMClient
) -> dict:
    """
    Generate random numbers from specified LLM provider
    
    Args:
        request: PromptRequest with generation parameters
        llm_client: LLMClient instance
        
    Returns:
        Dictionary with numbers and provider
    """
    logger.info(f"Received generate request: provider={request.provider}, count={request.count or 100}, has_api_key={bool(request.api_key)}, has_system_prompt={bool(request.system_prompt)}")
    if request.system_prompt:
        logger.info(f"System prompt received from frontend (full text): {request.system_prompt}")
        logger.debug(f"System prompt length: {len(request.system_prompt)} characters")
    else:
        logger.info("No system prompt provided, will use default prompt")
    try:
        numbers = await llm_client.generate_random_numbers(
            provider=request.provider,
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            count=request.count or 100,
            api_key=request.api_key
        )
        logger.info(f"Generated {len(numbers)} numbers for provider {request.provider}")
        logger.debug(f"Numbers: {numbers[:10]}..." if len(numbers) > 10 else f"Numbers: {numbers}")
        return {"numbers": numbers, "provider": request.provider}
    except Exception as e:
        logger.error(f"Error generating numbers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def generate_numbers_stream_service(
    request: PromptRequest,
    llm_client: LLMClient
) -> StreamingResponse:
    """
    Stream random numbers from specified LLM provider
    
    Args:
        request: PromptRequest with generation parameters
        llm_client: LLMClient instance
        
    Returns:
        StreamingResponse with SSE events
    """
    logger.info(f"Received stream request: provider={request.provider}, count={request.count or 100}, batch_mode={request.batch_mode}, has_api_key={bool(request.api_key)}, has_system_prompt={bool(request.system_prompt)}")
    if request.system_prompt:
        logger.info(f"System prompt received from frontend (full text): {request.system_prompt}")
        logger.info(f"System prompt length: {len(request.system_prompt)} characters")
    else:
        logger.info("No system prompt provided, will use default prompt")

    async def event_generator():
        numbers_generated = 0
        try:
            async for number in llm_client.generate_random_numbers_stream(
                provider=request.provider,
                system_prompt=request.system_prompt,
                user_prompt=request.user_prompt,
                count=request.count or 100,
                api_key=request.api_key,
                batch_mode=request.batch_mode or False
            ):
                numbers_generated += 1
                logger.debug(f"Streaming number {numbers_generated}: {number}")
                yield f"data: {json.dumps({'number': number, 'provider': request.provider})}\n\n"
            logger.info(f"Stream completed: generated {numbers_generated} numbers")
        except Exception as e:
            logger.error(f"Error in stream: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
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
