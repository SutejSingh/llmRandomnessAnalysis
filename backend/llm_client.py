import os
import json
import re
import asyncio
import logging
from typing import AsyncIterator, List, Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        # Default system prompts for each provider
        self.default_prompts = {
            "openai": "You are a random number generator. Generate a single random number between 0 and 1. Respond with ONLY the number, no explanation, no formatting, just the decimal number.",
            "anthropic": "You are a random number generator. Generate a single random number between 0 and 1. Respond with ONLY the number, no explanation, no formatting, just the decimal number.",
            "deepseek": "You are a random number generator. Generate a single random number between 0 and 1. Respond with ONLY the number, no explanation, no formatting, just the decimal number."
        }
    
    def _get_api_key(self, provider: str, provided_key: Optional[str] = None) -> Optional[str]:
        """Get API key from provided key or environment variable"""
        if provided_key and provided_key.strip():
            masked_key = provided_key[:8] + "..." + provided_key[-4:] if len(provided_key) > 12 else "***"
            logger.info(f"Using provided API key for {provider}: {masked_key}")
            return provided_key.strip()
        # Fallback to environment variable
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY"
        }
        env_var_name = key_map.get(provider, "")
        env_key = os.getenv(env_var_name)
        if env_key:
            masked_key = env_key[:8] + "..." + env_key[-4:] if len(env_key) > 12 else "***"
            logger.info(f"Using environment variable {env_var_name} for {provider}: {masked_key}")
        else:
            logger.warning(f"No API key found for {provider} (checked env var: {env_var_name})")
        return env_key
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract a number from LLM response text - returns number as-is without normalization"""
        logger.debug(f"Extracting number from text: {text[:100]}...")
        # Try to find a decimal number
        patterns = [
            r'(\d+\.\d+)',  # Decimal number
            r'(\d+)',       # Integer
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    num = float(matches[0])
                    logger.debug(f"Found number: {num} (raw match: {matches[0]}) - no normalization applied")
                    # Return number as-is to preserve custom ranges (e.g., if user asks for 1-10, return those values)
                    return num
                except ValueError as e:
                    logger.debug(f"ValueError converting {matches[0]}: {e}")
                    continue
        
        logger.warning(f"Could not extract number from text: {text}")
        return None
    
    def _extract_numbers_csv(self, text: str) -> List[float]:
        """Extract all numbers from CSV format (one number per line) - returns numbers as-is without normalization"""
        logger.debug(f"Extracting numbers from CSV text (first 500 chars): {text[:500]}...")
        numbers = []
        
        # Split by lines and extract numbers
        lines = text.strip().split('\n')
        logger.debug(f"Found {len(lines)} lines in CSV response")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Remove any CSV delimiters (comma, semicolon, tab) and extract first number
            # Handle both comma-separated values and single values per line
            parts = re.split(r'[,\t;]', line)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Try to extract a number from this part
                # Look for decimal numbers (e.g., 0.1234, .5678, 0.9, 5.2, 10)
                match = re.search(r'(\d*\.?\d+)', part)
                if match:
                    try:
                        num_str = match.group(1)
                        num = float(num_str)
                        
                        # Return numbers as-is without normalization to preserve custom ranges
                        # (e.g., if user asks for numbers between 1-10, we should return those, not normalize to 0-1)
                        numbers.append(num)
                        logger.debug(f"Line {line_num}: extracted {num} from '{part}' (no normalization applied)")
                        break  # Only take first number from each line
                    except ValueError as e:
                        logger.debug(f"Line {line_num}: ValueError converting '{part}': {e}")
                        continue
        
        logger.info(f"Extracted {len(numbers)} numbers from CSV format (from {len(lines)} lines)")
        if len(numbers) == 0:
            logger.warning(f"No numbers extracted from CSV. Full text: {text}")
        return numbers
    
    def _extract_numbers(self, text: str, expected_count: int) -> List[float]:
        """Extract multiple numbers from LLM response text"""
        logger.debug(f"Extracting {expected_count} numbers from text: {text[:200]}...")
        numbers = []
        
        # Try multiple patterns to find numbers
        # Pattern 1: Comma-separated numbers
        comma_pattern = r'\b(\d+\.?\d*)\b'
        # Pattern 2: Line-separated numbers
        line_pattern = r'^\s*(\d+\.?\d*)\s*$'
        # Pattern 3: Numbers in brackets or parentheses
        bracket_pattern = r'[\[\(](\d+\.?\d*)[\]\)]'
        
        # Try comma-separated first
        matches = re.findall(comma_pattern, text)
        if len(matches) >= expected_count:
            for match in matches[:expected_count]:
                try:
                    num = float(match)
                    if num > 1:
                        num = num / (10 ** len(str(int(num))))
                    numbers.append(num)
                except ValueError:
                    continue
            if len(numbers) >= expected_count:
                logger.info(f"Extracted {len(numbers)} numbers using comma pattern")
                return numbers[:expected_count]
        
        # Try line-by-line
        lines = text.split('\n')
        for line in lines:
            if len(numbers) >= expected_count:
                break
            match = re.search(r'(\d+\.?\d*)', line.strip())
            if match:
                try:
                    num = float(match.group(1))
                    if num > 1:
                        num = num / (10 ** len(str(int(num))))
                    numbers.append(num)
                except ValueError:
                    continue
        
        if len(numbers) >= expected_count:
            logger.info(f"Extracted {len(numbers)} numbers using line pattern")
            return numbers[:expected_count]
        
        # Fallback: extract all numbers found
        all_matches = re.findall(r'\b(\d+\.?\d*)\b', text)
        for match in all_matches[:expected_count]:
            try:
                num = float(match)
                if num > 1:
                    num = num / (10 ** len(str(int(num))))
                numbers.append(num)
            except ValueError:
                continue
        
        logger.info(f"Extracted {len(numbers)} numbers (expected {expected_count})")
        return numbers[:expected_count] if numbers else []
    
    async def _generate_openai(self, system_prompt: str, count: int, api_key: Optional[str] = None) -> List[float]:
        """Generate numbers using OpenAI"""
        logger.info(f"Starting OpenAI generation: count={count}, system_prompt length={len(system_prompt)}")
        logger.debug(f"System prompt being used: {system_prompt[:200]}...")
        api_key = self._get_api_key("openai", api_key)
        if not api_key:
            logger.error("OpenAI API key is required but not found")
            raise ValueError("OpenAI API key is required")
        
        client = AsyncOpenAI(api_key=api_key)
        numbers = []
        for i in range(count):
            try:
                logger.debug(f"OpenAI request {i+1}/{count} using system prompt")
                response = await client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "Generate a random number between 0 and 1."}
                    ],
                    temperature=1.0,
                    max_tokens=50
                )
                text = response.choices[0].message.content
                logger.debug(f"OpenAI response {i+1}: {text}")
                number = self._extract_number(text)
                if number is not None:
                    numbers.append(number)
                    logger.info(f"Successfully extracted number {i+1}/{count}: {number}")
                else:
                    logger.warning(f"Failed to extract number from response {i+1}: {text}")
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.error(f"OpenAI error on request {i+1}/{count}: {str(e)}", exc_info=True)
                continue
        logger.info(f"OpenAI generation complete: {len(numbers)}/{count} numbers generated")
        return numbers
    
    async def _generate_anthropic(self, system_prompt: str, count: int, api_key: Optional[str] = None) -> List[float]:
        """Generate numbers using Anthropic"""
        logger.info(f"Starting Anthropic generation: count={count}, system_prompt length={len(system_prompt)}")
        logger.debug(f"System prompt being used: {system_prompt[:200]}...")
        api_key = self._get_api_key("anthropic", api_key)
        if not api_key:
            logger.error("Anthropic API key is required but not found")
            raise ValueError("Anthropic API key is required")
        
        client = AsyncAnthropic(api_key=api_key)
        numbers = []
        for i in range(count):
            try:
                logger.debug(f"Anthropic request {i+1}/{count} using system prompt")
                response = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=50,
                    temperature=1.0,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": "Generate a random number between 0 and 1."}
                    ]
                )
                text = response.content[0].text
                logger.debug(f"Anthropic response {i+1}: {text}")
                number = self._extract_number(text)
                if number is not None:
                    numbers.append(number)
                    logger.info(f"Successfully extracted number {i+1}/{count}: {number}")
                else:
                    logger.warning(f"Failed to extract number from response {i+1}: {text}")
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.error(f"Anthropic error on request {i+1}/{count}: {str(e)}", exc_info=True)
                continue
        logger.info(f"Anthropic generation complete: {len(numbers)}/{count} numbers generated")
        return numbers
    
    async def _generate_deepseek(self, system_prompt: str, count: int, api_key: Optional[str] = None) -> List[float]:
        """Generate numbers using DeepSeek"""
        logger.info(f"Starting DeepSeek generation: count={count}, system_prompt length={len(system_prompt)}")
        logger.debug(f"System prompt being used: {system_prompt[:200]}...")
        api_key = self._get_api_key("deepseek", api_key)
        if not api_key:
            logger.error("DeepSeek API key is required but not found")
            raise ValueError("DeepSeek API key is required")
        
        numbers = []
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        for i in range(count):
            try:
                logger.debug(f"DeepSeek request {i+1}/{count} using system prompt")
                response = await client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "Generate a random number between 0 and 1."}
                    ],
                    temperature=1.0,
                    max_tokens=50
                )
                text = response.choices[0].message.content
                logger.debug(f"DeepSeek response {i+1}: {text}")
                number = self._extract_number(text)
                if number is not None:
                    numbers.append(number)
                    logger.info(f"Successfully extracted number {i+1}/{count}: {number}")
                else:
                    logger.warning(f"Failed to extract number from response {i+1}: {text}")
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.error(f"DeepSeek error on request {i+1}/{count}: {str(e)}", exc_info=True)
                continue
        logger.info(f"DeepSeek generation complete: {len(numbers)}/{count} numbers generated")
        return numbers
    
    async def _generate_openai_batch(self, system_prompt: str, count: int, api_key: Optional[str] = None) -> List[float]:
        """Generate multiple numbers in one request using OpenAI - expects CSV format (one number per line)"""
        logger.info(f"Starting OpenAI batch generation: single request, expecting CSV format")
        api_key = self._get_api_key("openai", api_key)
        if not api_key:
            logger.error("OpenAI API key is required but not found")
            raise ValueError("OpenAI API key is required")
        
        client = AsyncOpenAI(api_key=api_key)
        try:
            # Use the system prompt as-is (user's custom prompt or default)
            # Only append CSV instruction if not already present
            final_system_prompt = system_prompt
            if "CSV" not in system_prompt.upper() and "one per line" not in system_prompt.lower() and "comma-separated" not in system_prompt.lower():
                final_system_prompt = system_prompt + " Return the numbers in CSV format, one number per line."
                logger.debug("Appended CSV format instruction to system prompt")
            else:
                logger.debug("System prompt already contains CSV/format instructions, using as-is")
            
            user_prompt = "Generate the random numbers as specified in the system prompt."
            logger.info(f"OpenAI batch request - using system prompt (length: {len(final_system_prompt)})")
            logger.info(f"OpenAI batch request - FULL system prompt being sent to LLM: {final_system_prompt}")
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1.0,
                max_tokens=5000  # Allow enough tokens for many numbers
            )
            text = response.choices[0].message.content
            logger.debug(f"OpenAI batch response (first 500 chars): {text[:500]}...")
            logger.debug(f"OpenAI batch response (full length): {len(text)} characters")
            
            # Extract all numbers from CSV format
            numbers = self._extract_numbers_csv(text)
            logger.info(f"OpenAI batch generation complete: {len(numbers)} numbers extracted from CSV")
            return numbers
        except Exception as e:
            logger.error(f"OpenAI batch error: {str(e)}", exc_info=True)
            return []
    
    async def _generate_anthropic_batch(self, system_prompt: str, count: int, api_key: Optional[str] = None) -> List[float]:
        """Generate multiple numbers in one request using Anthropic - expects CSV format (one number per line)"""
        logger.info(f"Starting Anthropic batch generation: single request, expecting CSV format")
        api_key = self._get_api_key("anthropic", api_key)
        if not api_key:
            logger.error("Anthropic API key is required but not found")
            raise ValueError("Anthropic API key is required")
        
        client = AsyncAnthropic(api_key=api_key)
        try:
            # Use the system prompt as-is (user's custom prompt or default)
            # Only append CSV instruction if not already present
            final_system_prompt = system_prompt
            if "CSV" not in system_prompt.upper() and "one per line" not in system_prompt.lower() and "comma-separated" not in system_prompt.lower():
                final_system_prompt = system_prompt + " Return the numbers in CSV format, one number per line."
                logger.debug("Appended CSV format instruction to system prompt")
            else:
                logger.debug("System prompt already contains CSV/format instructions, using as-is")
            
            user_prompt = "Generate the random numbers as specified in the system prompt."
            logger.info(f"Anthropic batch request - using system prompt (length: {len(final_system_prompt)})")
            logger.info(f"Anthropic batch request - FULL system prompt being sent to LLM: {final_system_prompt}")
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=5000,
                temperature=1.0,
                system=final_system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            text = response.content[0].text
            logger.debug(f"Anthropic batch response (first 500 chars): {text[:500]}...")
            logger.debug(f"Anthropic batch response (full length): {len(text)} characters")
            
            # Extract all numbers from CSV format
            numbers = self._extract_numbers_csv(text)
            logger.info(f"Anthropic batch generation complete: {len(numbers)} numbers extracted from CSV")
            return numbers
        except Exception as e:
            logger.error(f"Anthropic batch error: {str(e)}", exc_info=True)
            return []
    
    async def _generate_deepseek_batch(self, system_prompt: str, count: int, api_key: Optional[str] = None) -> List[float]:
        """Generate multiple numbers in one request using DeepSeek - expects CSV format (one number per line)"""
        logger.info(f"Starting DeepSeek batch generation: single request, expecting CSV format")
        api_key = self._get_api_key("deepseek", api_key)
        if not api_key:
            logger.error("DeepSeek API key is required but not found")
            raise ValueError("DeepSeek API key is required")
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        try:
            # Use the system prompt as-is (user's custom prompt or default)
            # Only append CSV instruction if not already present
            final_system_prompt = system_prompt
            if "CSV" not in system_prompt.upper() and "one per line" not in system_prompt.lower() and "comma-separated" not in system_prompt.lower():
                final_system_prompt = system_prompt + " Return the numbers in CSV format, one number per line."
                logger.debug("Appended CSV format instruction to system prompt")
            else:
                logger.debug("System prompt already contains CSV/format instructions, using as-is")
            
            user_prompt = "Generate the random numbers as specified in the system prompt."
            logger.info(f"DeepSeek batch request - using system prompt (length: {len(final_system_prompt)})")
            logger.info(f"DeepSeek batch request - FULL system prompt being sent to LLM: {final_system_prompt}")
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1.0,
                max_tokens=5000
            )
            text = response.choices[0].message.content
            logger.debug(f"DeepSeek batch response (first 500 chars): {text[:500]}...")
            logger.debug(f"DeepSeek batch response (full length): {len(text)} characters")
            
            # Extract all numbers from CSV format
            numbers = self._extract_numbers_csv(text)
            logger.info(f"DeepSeek batch generation complete: {len(numbers)} numbers extracted from CSV")
            return numbers
        except Exception as e:
            logger.error(f"DeepSeek batch error: {str(e)}", exc_info=True)
            return []
    
    async def generate_random_numbers(
        self,
        provider: str,
        system_prompt: Optional[str] = None,
        count: int = 100,
        api_key: Optional[str] = None,
        batch_mode: bool = False
    ) -> List[float]:
        """Generate random numbers from specified provider"""
        logger.info(f"generate_random_numbers called: provider={provider}, count={count}, batch_mode={batch_mode}, has_custom_prompt={bool(system_prompt)}")
        if system_prompt and system_prompt.strip():
            prompt = system_prompt.strip()
            logger.info(f"Using user-provided system prompt (length: {len(prompt)})")
            logger.debug(f"User prompt content: {prompt}")
        else:
            prompt = self.default_prompts.get(provider, self.default_prompts["openai"])
            logger.info(f"Using default system prompt for {provider} (no user prompt provided)")
        logger.debug(f"Final prompt (first 200 chars): {prompt[:200]}...")
        
        if batch_mode:
            if provider == "openai":
                return await self._generate_openai_batch(prompt, count, api_key)
            elif provider == "anthropic":
                return await self._generate_anthropic_batch(prompt, count, api_key)
            elif provider == "deepseek":
                return await self._generate_deepseek_batch(prompt, count, api_key)
            else:
                logger.error(f"Unknown provider: {provider}")
                raise ValueError(f"Unknown provider: {provider}")
        else:
            if provider == "openai":
                return await self._generate_openai(prompt, count, api_key)
            elif provider == "anthropic":
                return await self._generate_anthropic(prompt, count, api_key)
            elif provider == "deepseek":
                return await self._generate_deepseek(prompt, count, api_key)
            else:
                logger.error(f"Unknown provider: {provider}")
                raise ValueError(f"Unknown provider: {provider}")
    
    async def generate_random_numbers_stream(
        self,
        provider: str,
        system_prompt: Optional[str] = None,
        count: int = 100,
        api_key: Optional[str] = None,
        batch_mode: bool = False
    ) -> AsyncIterator[float]:
        """Stream random numbers from specified provider"""
        if system_prompt and system_prompt.strip():
            prompt = system_prompt.strip()
            logger.info(f"Using user-provided system prompt in stream (length: {len(prompt)})")
            logger.info(f"User-provided system prompt (FULL TEXT): {prompt}")
        else:
            prompt = self.default_prompts.get(provider, self.default_prompts["openai"])
            logger.info(f"Using default system prompt for {provider} in stream (no user prompt provided)")
            logger.info(f"Default system prompt (FULL TEXT): {prompt}")
        
        if batch_mode:
            # In batch mode, generate all numbers at once and stream them
            if provider == "openai":
                numbers = await self._generate_openai_batch(prompt, count, api_key)
            elif provider == "anthropic":
                numbers = await self._generate_anthropic_batch(prompt, count, api_key)
            elif provider == "deepseek":
                numbers = await self._generate_deepseek_batch(prompt, count, api_key)
            else:
                raise ValueError(f"Unknown provider: {provider}")
            
            # Stream the numbers one by one with a small delay
            for num in numbers:
                yield num
                await asyncio.sleep(0.05)  # Small delay for streaming effect
        else:
            # One-by-one mode
            if provider == "openai":
                async for num in self._generate_openai_stream(prompt, count, api_key):
                    yield num
            elif provider == "anthropic":
                async for num in self._generate_anthropic_stream(prompt, count, api_key):
                    yield num
            elif provider == "deepseek":
                async for num in self._generate_deepseek_stream(prompt, count, api_key):
                    yield num
            else:
                raise ValueError(f"Unknown provider: {provider}")
    
    async def _generate_openai_stream(self, system_prompt: str, count: int, api_key: Optional[str] = None) -> AsyncIterator[float]:
        """Stream numbers using OpenAI"""
        logger.info(f"Starting OpenAI stream: count={count}, system_prompt length={len(system_prompt)}")
        logger.debug(f"System prompt being used in stream: {system_prompt[:200]}...")
        api_key = self._get_api_key("openai", api_key)
        if not api_key:
            logger.error("OpenAI API key is required but not found")
            raise ValueError("OpenAI API key is required")
        
        client = AsyncOpenAI(api_key=api_key)
        for i in range(count):
            try:
                logger.debug(f"OpenAI stream request {i+1}/{count} using system prompt")
                response = await client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "Generate a random number between 0 and 1."}
                    ],
                    temperature=1.0,
                    max_tokens=50
                )
                text = response.choices[0].message.content
                logger.debug(f"OpenAI stream response {i+1}: {text}")
                number = self._extract_number(text)
                if number is not None:
                    logger.info(f"Streaming number {i+1}/{count}: {number}")
                    yield number
                else:
                    logger.warning(f"Failed to extract number from stream response {i+1}: {text}")
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"OpenAI stream error on request {i+1}/{count}: {str(e)}", exc_info=True)
                continue
    
    async def _generate_anthropic_stream(self, system_prompt: str, count: int, api_key: Optional[str] = None) -> AsyncIterator[float]:
        """Stream numbers using Anthropic"""
        logger.info(f"Starting Anthropic stream: count={count}, system_prompt length={len(system_prompt)}")
        logger.debug(f"System prompt being used in stream: {system_prompt[:200]}...")
        api_key = self._get_api_key("anthropic", api_key)
        if not api_key:
            logger.error("Anthropic API key is required but not found")
            raise ValueError("Anthropic API key is required")
        
        client = AsyncAnthropic(api_key=api_key)
        for i in range(count):
            try:
                logger.debug(f"Anthropic stream request {i+1}/{count} using system prompt")
                response = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=50,
                    temperature=1.0,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": "Generate a random number between 0 and 1."}
                    ]
                )
                text = response.content[0].text
                logger.debug(f"Anthropic stream response {i+1}: {text}")
                number = self._extract_number(text)
                if number is not None:
                    logger.info(f"Streaming number {i+1}/{count}: {number}")
                    yield number
                else:
                    logger.warning(f"Failed to extract number from stream response {i+1}: {text}")
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Anthropic stream error on request {i+1}/{count}: {str(e)}", exc_info=True)
                continue
    
    async def _generate_deepseek_stream(self, system_prompt: str, count: int, api_key: Optional[str] = None) -> AsyncIterator[float]:
        """Stream numbers using DeepSeek"""
        logger.info(f"Starting DeepSeek stream: count={count}, system_prompt length={len(system_prompt)}")
        logger.debug(f"System prompt being used in stream: {system_prompt[:200]}...")
        api_key = self._get_api_key("deepseek", api_key)
        if not api_key:
            logger.error("DeepSeek API key is required but not found")
            raise ValueError("DeepSeek API key is required")
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        for i in range(count):
            try:
                logger.debug(f"DeepSeek stream request {i+1}/{count} using system prompt")
                response = await client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "Generate a random number between 0 and 1."}
                    ],
                    temperature=1.0,
                    max_tokens=50
                )
                text = response.choices[0].message.content
                logger.debug(f"DeepSeek stream response {i+1}: {text}")
                number = self._extract_number(text)
                if number is not None:
                    logger.info(f"Streaming number {i+1}/{count}: {number}")
                    yield number
                else:
                    logger.warning(f"Failed to extract number from stream response {i+1}: {text}")
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"DeepSeek stream error on request {i+1}/{count}: {str(e)}", exc_info=True)
                continue
