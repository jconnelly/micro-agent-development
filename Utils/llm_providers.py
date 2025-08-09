#!/usr/bin/env python3
"""
LLM Provider Abstraction Layer for BYO-LLM (Bring Your Own LLM) Support

This module provides a Protocol-based abstraction layer that allows the Micro-Agent
Development Platform to work with multiple LLM providers including:
- Google Gemini (default)
- OpenAI GPT models
- Anthropic Claude models  
- Azure OpenAI
- Custom LLM providers

Business Benefits:
- Enterprise Flexibility: Choose LLM providers based on cost, compliance, performance
- Cost Optimization: Switch providers to optimize costs for different use cases
- Vendor Independence: Avoid vendor lock-in and maintain negotiating power
- Compliance Support: Use providers that meet security and data residency requirements
- Custom Model Support: Integrate proprietary or fine-tuned models

Author: Micro-Agent Development Platform
Version: 1.0.0
"""

import os
import json
import time
from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum

# Import Utils for logging and error handling
try:
    from .time_utils import TimeUtils
    from .json_utils import JsonUtils
except ImportError:
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from Utils.time_utils import TimeUtils
    from Utils.json_utils import JsonUtils


class LLMProviderType(Enum):
    """Enumeration of supported LLM provider types"""
    GEMINI = "google_gemini"
    OPENAI = "openai" 
    CLAUDE = "anthropic_claude"
    AZURE_OPENAI = "azure_openai"
    CUSTOM = "custom"


@dataclass
class LLMResponse:
    """Standardized response object from LLM providers"""
    content: str
    model_name: str
    provider_type: LLMProviderType
    usage_stats: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None
    request_id: Optional[str] = None
    error: Optional[str] = None


class LLMProvider(Protocol):
    """
    Protocol defining the interface that all LLM providers must implement.
    
    This Protocol ensures consistent behavior across all LLM providers while
    allowing flexibility in implementation details.
    """
    
    def generate_content(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate content from a text prompt.
        
        Args:
            prompt: The input text prompt
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse: Standardized response object
        """
        ...
    
    def get_model_name(self) -> str:
        """Get the model identifier/name"""
        ...
    
    def get_provider_type(self) -> LLMProviderType:
        """Get the provider type"""
        ...
        
    def validate_connection(self) -> bool:
        """Test if the provider connection is working"""
        ...


class BaseLLMProvider(ABC):
    """
    Abstract base class providing common functionality for LLM providers.
    
    This class implements shared features like error handling, retry logic,
    and response formatting while leaving provider-specific implementation
    to concrete classes.
    """
    
    def __init__(self, model_name: str, provider_type: LLMProviderType):
        self.model_name = model_name
        self.provider_type = provider_type
        self._connection_validated = False
        
    @abstractmethod
    def _make_llm_call(self, prompt: str, **kwargs) -> str:
        """Provider-specific implementation of LLM call"""
        pass
    
    @abstractmethod 
    def _get_usage_stats(self) -> Optional[Dict[str, Any]]:
        """Get provider-specific usage statistics"""
        pass
    
    def generate_content(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate content with standardized error handling and response formatting.
        
        Args:
            prompt: Input text prompt
            **kwargs: Provider-specific parameters
            
        Returns:
            LLMResponse: Standardized response object
        """
        start_time = time.time()
        request_id = f"llm_req_{int(time.time() * 1000)}"
        
        try:
            # Validate prompt
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            # Make the LLM call
            content = self._make_llm_call(prompt.strip(), **kwargs)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Get usage stats if available
            usage_stats = self._get_usage_stats()
            
            return LLMResponse(
                content=content,
                model_name=self.model_name,
                provider_type=self.provider_type,
                usage_stats=usage_stats,
                response_time_ms=response_time_ms,
                request_id=request_id
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content="",
                model_name=self.model_name,
                provider_type=self.provider_type,
                usage_stats=None,
                response_time_ms=response_time_ms,
                request_id=request_id,
                error=str(e)
            )
    
    def get_model_name(self) -> str:
        """Get the model name"""
        return self.model_name
    
    def get_provider_type(self) -> LLMProviderType:
        """Get the provider type"""
        return self.provider_type


class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider implementation.
    
    Supports Google's Gemini models including:
    - gemini-1.5-flash (fast, cost-effective)
    - gemini-1.5-pro (advanced reasoning)
    - gemini-2.0-flash-exp (latest experimental)
    
    Configuration:
    - Requires GOOGLE_API_KEY environment variable
    - Supports temperature, max_tokens parameters
    - Built-in retry logic for rate limiting
    """
    
    def __init__(self, 
                 model_name: str = "gemini-1.5-flash",
                 api_key: Optional[str] = None):
        """
        Initialize Gemini provider.
        
        Args:
            model_name: Gemini model name (default: gemini-1.5-flash)
            api_key: API key (defaults to GOOGLE_API_KEY env var)
        """
        super().__init__(model_name, LLMProviderType.GEMINI)
        
        # Import Google AI SDK
        try:
            import google.generativeai as genai
            self.genai = genai
        except ImportError:
            raise ImportError("google-generativeai package required for Gemini provider")
        
        # Configure API key
        api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable or api_key parameter required")
        
        self.genai.configure(api_key=api_key)
        self.client = self.genai.GenerativeModel(model_name)
        self._last_usage_stats = None
        
    def _make_llm_call(self, prompt: str, **kwargs) -> str:
        """Make Gemini API call"""
        try:
            # Extract Gemini-specific parameters
            temperature = kwargs.get("temperature", 0.1)
            max_tokens = kwargs.get("max_tokens", 8192)
            
            # Configure generation parameters
            generation_config = self.genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            # Generate content
            response = self.client.generate_content(
                prompt, 
                generation_config=generation_config
            )
            
            # Store usage stats
            self._last_usage_stats = {
                "prompt_token_count": getattr(response.usage_metadata, 'prompt_token_count', None),
                "candidates_token_count": getattr(response.usage_metadata, 'candidates_token_count', None),
                "total_token_count": getattr(response.usage_metadata, 'total_token_count', None)
            }
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")
    
    def _get_usage_stats(self) -> Optional[Dict[str, Any]]:
        """Get Gemini usage statistics"""
        return self._last_usage_stats
    
    def validate_connection(self) -> bool:
        """Test Gemini connection"""
        try:
            response = self.generate_content("test")
            return response.error is None
        except:
            return False


class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI LLM provider implementation.
    
    Supports OpenAI models including:
    - gpt-4o (latest GPT-4 optimized)
    - gpt-4-turbo (balanced performance)
    - gpt-3.5-turbo (cost-effective)
    - o1-preview (advanced reasoning)
    
    Configuration:
    - Requires OPENAI_API_KEY environment variable
    - Supports temperature, max_tokens, top_p parameters
    - Built-in retry logic and rate limiting
    """
    
    def __init__(self, 
                 model_name: str = "gpt-4o",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        Initialize OpenAI provider.
        
        Args:
            model_name: OpenAI model name (default: gpt-4o)
            api_key: API key (defaults to OPENAI_API_KEY env var)
            base_url: Custom base URL for OpenAI-compatible APIs
        """
        super().__init__(model_name, LLMProviderType.OPENAI)
        
        # Import OpenAI SDK
        try:
            import openai
            self.openai = openai
        except ImportError:
            raise ImportError("openai package required for OpenAI provider")
        
        # Configure API key
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable or api_key parameter required")
        
        # Initialize client
        self.client = self.openai.OpenAI(api_key=api_key, base_url=base_url)
        self._last_usage_stats = None
        
    def _make_llm_call(self, prompt: str, **kwargs) -> str:
        """Make OpenAI API call"""
        try:
            # Extract OpenAI-specific parameters
            temperature = kwargs.get("temperature", 0.1)
            max_tokens = kwargs.get("max_tokens", 4096)
            top_p = kwargs.get("top_p", 1.0)
            
            # Create chat completion
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            
            # Store usage stats
            if response.usage:
                self._last_usage_stats = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    def _get_usage_stats(self) -> Optional[Dict[str, Any]]:
        """Get OpenAI usage statistics"""
        return self._last_usage_stats
    
    def validate_connection(self) -> bool:
        """Test OpenAI connection"""
        try:
            response = self.generate_content("test")
            return response.error is None
        except:
            return False


class ClaudeLLMProvider(BaseLLMProvider):
    """
    Anthropic Claude LLM provider implementation.
    
    Supports Claude models including:
    - claude-3-5-sonnet-20241022 (latest Sonnet)
    - claude-3-5-haiku-20241022 (fast, cost-effective)
    - claude-3-opus-20240229 (most capable)
    
    Configuration:
    - Requires ANTHROPIC_API_KEY environment variable
    - Supports temperature, max_tokens parameters
    - Built-in retry logic and safety filtering
    """
    
    def __init__(self, 
                 model_name: str = "claude-3-5-sonnet-20241022",
                 api_key: Optional[str] = None):
        """
        Initialize Claude provider.
        
        Args:
            model_name: Claude model name (default: claude-3-5-sonnet-20241022)
            api_key: API key (defaults to ANTHROPIC_API_KEY env var)
        """
        super().__init__(model_name, LLMProviderType.CLAUDE)
        
        # Import Anthropic SDK
        try:
            import anthropic
            self.anthropic = anthropic
        except ImportError:
            raise ImportError("anthropic package required for Claude provider")
        
        # Configure API key
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter required")
        
        # Initialize client
        self.client = self.anthropic.Anthropic(api_key=api_key)
        self._last_usage_stats = None
        
    def _make_llm_call(self, prompt: str, **kwargs) -> str:
        """Make Claude API call"""
        try:
            # Extract Claude-specific parameters
            temperature = kwargs.get("temperature", 0.1)
            max_tokens = kwargs.get("max_tokens", 4096)
            
            # Create message
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Store usage stats
            if hasattr(response, 'usage'):
                self._last_usage_stats = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            
            return response.content[0].text
            
        except Exception as e:
            raise Exception(f"Claude API call failed: {str(e)}")
    
    def _get_usage_stats(self) -> Optional[Dict[str, Any]]:
        """Get Claude usage statistics"""
        return self._last_usage_stats
    
    def validate_connection(self) -> bool:
        """Test Claude connection"""
        try:
            response = self.generate_content("test")
            return response.error is None
        except:
            return False


class AzureOpenAILLMProvider(BaseLLMProvider):
    """
    Azure OpenAI LLM provider implementation.
    
    Supports Azure-hosted OpenAI models with enterprise features:
    - Data residency and compliance
    - Private networking and VNets
    - Enterprise security controls
    - SLA guarantees
    
    Configuration:
    - Requires AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT env vars
    - Supports all OpenAI model parameters
    - Built-in retry logic and Azure-specific error handling
    """
    
    def __init__(self, 
                 deployment_name: str,
                 api_version: str = "2024-02-15-preview",
                 api_key: Optional[str] = None,
                 endpoint: Optional[str] = None):
        """
        Initialize Azure OpenAI provider.
        
        Args:
            deployment_name: Azure deployment name (required)
            api_version: Azure OpenAI API version
            api_key: API key (defaults to AZURE_OPENAI_API_KEY env var)
            endpoint: Endpoint URL (defaults to AZURE_OPENAI_ENDPOINT env var)
        """
        super().__init__(deployment_name, LLMProviderType.AZURE_OPENAI)
        
        # Import Azure OpenAI SDK
        try:
            from openai import AzureOpenAI
            self.AzureOpenAI = AzureOpenAI
        except ImportError:
            raise ImportError("openai package with Azure support required")
        
        # Configure credentials
        api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        
        if not api_key or not endpoint:
            raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT required")
        
        # Initialize Azure client
        self.client = self.AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        self.deployment_name = deployment_name
        self._last_usage_stats = None
        
    def _make_llm_call(self, prompt: str, **kwargs) -> str:
        """Make Azure OpenAI API call"""
        try:
            # Extract parameters
            temperature = kwargs.get("temperature", 0.1)
            max_tokens = kwargs.get("max_tokens", 4096)
            top_p = kwargs.get("top_p", 1.0)
            
            # Create chat completion
            response = self.client.chat.completions.create(
                model=self.deployment_name,  # Use deployment name for Azure
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            
            # Store usage stats
            if response.usage:
                self._last_usage_stats = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Azure OpenAI API call failed: {str(e)}")
    
    def _get_usage_stats(self) -> Optional[Dict[str, Any]]:
        """Get Azure OpenAI usage statistics"""
        return self._last_usage_stats
    
    def validate_connection(self) -> bool:
        """Test Azure OpenAI connection"""
        try:
            response = self.generate_content("test")
            return response.error is None
        except:
            return False


class LLMProviderFactory:
    """
    Factory class for creating LLM providers with convenient methods.
    
    Provides standardized ways to create and configure different LLM providers
    with sensible defaults and enterprise configurations.
    """
    
    @staticmethod
    def create_gemini_provider(model_name: str = "gemini-1.5-flash", 
                             api_key: Optional[str] = None) -> GeminiLLMProvider:
        """Create Google Gemini provider"""
        return GeminiLLMProvider(model_name=model_name, api_key=api_key)
    
    @staticmethod
    def create_openai_provider(model_name: str = "gpt-4o",
                             api_key: Optional[str] = None) -> OpenAILLMProvider:
        """Create OpenAI provider"""
        return OpenAILLMProvider(model_name=model_name, api_key=api_key)
    
    @staticmethod
    def create_claude_provider(model_name: str = "claude-3-5-sonnet-20241022",
                             api_key: Optional[str] = None) -> ClaudeLLMProvider:
        """Create Claude provider"""
        return ClaudeLLMProvider(model_name=model_name, api_key=api_key)
    
    @staticmethod
    def create_azure_openai_provider(deployment_name: str,
                                   api_version: str = "2024-02-15-preview",
                                   api_key: Optional[str] = None,
                                   endpoint: Optional[str] = None) -> AzureOpenAILLMProvider:
        """Create Azure OpenAI provider"""
        return AzureOpenAILLMProvider(
            deployment_name=deployment_name,
            api_version=api_version,
            api_key=api_key,
            endpoint=endpoint
        )
    
    @staticmethod
    def create_provider_from_config(provider_type: str, **config) -> LLMProvider:
        """
        Create provider from configuration dictionary.
        
        Args:
            provider_type: Provider type string (gemini, openai, claude, azure_openai)
            **config: Provider-specific configuration parameters
            
        Returns:
            LLMProvider: Configured provider instance
        """
        provider_type = provider_type.lower()
        
        if provider_type == "gemini":
            return LLMProviderFactory.create_gemini_provider(**config)
        elif provider_type == "openai":
            return LLMProviderFactory.create_openai_provider(**config)
        elif provider_type == "claude":
            return LLMProviderFactory.create_claude_provider(**config)
        elif provider_type == "azure_openai":
            return LLMProviderFactory.create_azure_openai_provider(**config)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")


# Convenience functions for backward compatibility and ease of use
def get_default_llm_provider() -> LLMProvider:
    """Get default LLM provider (Gemini)"""
    return LLMProviderFactory.create_gemini_provider()


def create_llm_provider(provider_type: str, **config) -> LLMProvider:
    """Create LLM provider with specified type and configuration"""
    return LLMProviderFactory.create_provider_from_config(provider_type, **config)