from typing import Dict, List, Optional, Any, AsyncIterator
import aiohttp
import logging
import json

# Import interfaces from published bruno packages
from bruno_core.interfaces import LLMInterface
from bruno_core.models import Message, MessageRole
from bruno_llm.base import BaseProvider

logger = logging.getLogger(__name__)

class OllamaClient(LLMInterface):
    """Client for Ollama LLM API implementing LLMInterface."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral:7b"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._system_prompt: Optional[str] = None
        logger.info(f"Initialized OllamaClient with base_url: {self.base_url}, model: {self.model}")

    # Implementation of LLMInterface methods
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate a text response from the LLM."""
        try:
            # Convert Message objects to dict format if needed
            message_dicts = []
            for msg in messages:
                if isinstance(msg, Message):
                    message_dicts.append({"role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role), "content": msg.content})
                else:
                    message_dicts.append(msg)
            
            # Use legacy generate_dict for backward compatibility
            response = await self.generate_dict(
                messages=message_dicts,
                model=kwargs.get('model', self.model),
                temperature=temperature or 0.7,
                max_tokens=max_tokens or 2000,
                stream=False
            )
            return response["content"]
        except Exception as e:
            logger.error(f"Error in generate: {str(e)}", exc_info=True)
            raise
    
    async def stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream text response from the LLM."""
        try:
            # Convert Message objects to dict format
            message_dicts = []
            for msg in messages:
                if isinstance(msg, Message):
                    message_dicts.append({"role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role), "content": msg.content})
                else:
                    message_dicts.append(msg)
            
            prompt = self._messages_to_prompt(message_dicts)
            
            payload = {
                "model": kwargs.get('model', self.model),
                "prompt": prompt,
                "temperature": temperature or 0.7,
                "options": {
                    "num_predict": max_tokens or 2000,
                },
                "stream": True
            }
            
            url = f"{self.base_url}/api/generate"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")
                    
                    async for line in response.content:
                        if line:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                yield data['response']
        except Exception as e:
            logger.error(f"Error in stream: {str(e)}", exc_info=True)
            raise
    
    def get_token_count(self, text: str) -> int:
        """Estimate token count for given text."""
        # Simple approximation: ~4 characters per token
        return len(text) // 4
    
    async def check_connection(self) -> bool:
        """Check if LLM service is accessible."""
        try:
            url = f"{self.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models from the provider."""
        try:
            url = f"{self.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to list models: {response.status}")
                    
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    logger.info(f"Available Ollama models: {models}")
                    return models
        except Exception as e:
            logger.error(f"Error listing Ollama models: {str(e)}", exc_info=True)
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model": self.model,
            "provider": "ollama",
            "base_url": self.base_url
        }
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set or update the system prompt."""
        self._system_prompt = prompt
        logger.info(f"System prompt set: {prompt[:50]}...")
    
    def get_system_prompt(self) -> Optional[str]:
        """Get the current system prompt."""
        return self._system_prompt    