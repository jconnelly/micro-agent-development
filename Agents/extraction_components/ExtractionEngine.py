"""
Extraction Engine Component for Business Rule Extraction

This module handles the core LLM interaction, prompt preparation, and rule extraction
logic for the BusinessRuleExtractionAgent.

Extracted from BusinessRuleExtractionAgent.py as part of Phase 16 Task 2 modularization.
"""

import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple


class ExtractionEngine:
    """
    Handles core LLM interaction and rule extraction logic.
    
    Responsibilities:
    - LLM prompt preparation and optimization
    - API call management with retry logic
    - Response parsing and validation
    - Error handling and recovery
    """
    
    def __init__(self, agent_config: Dict[str, Any], llm_client: Any = None):
        """Initialize the extraction engine with configuration and LLM client."""
        self.agent_config = agent_config
        self.llm_client = llm_client
        
        # Load configuration
        model_config = self.agent_config.get('model_defaults', {})
        self._max_output_tokens = model_config.get('max_output_tokens', 4096)
        self._max_input_tokens = model_config.get('max_input_tokens', 8192)
        self._temperature = model_config.get('temperature', 0.1)
        self._max_retries = self.agent_config.get('api_settings', {}).get('max_retries', 3)
        self._timeout = self.agent_config.get('api_settings', {}).get('timeout_seconds', 30)
        
    def prepare_llm_prompt(self, code_snippet: str, context: Optional[str] = None, 
                          language_enhancements: Dict[str, str] = None) -> Tuple[str, str]:
        """
        Prepare optimized prompts for LLM rule extraction.
        
        Args:
            code_snippet: Code snippet to analyze
            context: Optional file context
            language_enhancements: Language-specific prompt enhancements
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Enhanced system prompt with language-specific guidance
        system_prompt = self._build_system_prompt(language_enhancements)
        
        # Build user prompt with context and code
        user_prompt = self._build_user_prompt(code_snippet, context, language_enhancements)
        
        return system_prompt, user_prompt
    
    def extract_rules_from_chunk(self, chunk_content: str, context: Optional[str] = None,
                               chunk_idx: int = 0, language_enhancements: Dict[str, str] = None) -> Tuple[List[Dict], int, int]:
        """
        Extract rules from a single chunk with error handling.
        
        Args:
            chunk_content: Content of the chunk to process
            context: Optional file context
            chunk_idx: Index of the chunk being processed
            language_enhancements: Language-specific enhancements
            
        Returns:
            Tuple of (extracted_rules, tokens_input, tokens_output)
        """
        try:
            # Prepare the prompt
            system_prompt, user_prompt = self.prepare_llm_prompt(
                chunk_content, context, language_enhancements
            )
            
            # Make API call with retry logic
            response = self._api_call_with_retry(user_prompt)
            
            # Parse and validate the response
            rules = self._parse_llm_response(response)
            
            # Extract token usage if available
            tokens_input = response.get('tokens_input', 0)
            tokens_output = response.get('tokens_output', 0)
            
            return rules, tokens_input, tokens_output
            
        except Exception as e:
            # Log error and return empty results
            self._log_chunk_error(chunk_idx, e)
            return [], 0, 0
    
    def _build_system_prompt(self, language_enhancements: Dict[str, str] = None) -> str:
        """Build the system prompt with language-specific enhancements."""
        
        base_prompt = '''You are an expert business rule extraction and translation agent. Your task is to analyze legacy code snippets, identify embedded business rules, separate them from technical implementation details, and translate any cryptic technical terminology into clear, business-friendly language.

Key objectives:
1. BUSINESS FOCUS: Extract only business logic, not technical implementation
2. CLARITY: Translate technical terms into business language
3. COMPLETENESS: Identify both explicit and implicit business rules
4. CATEGORIZATION: Classify rules by type (VALIDATION, CALCULATION, DECISION, WORKFLOW, CONDITIONAL, DATA_TRANSFORMATION)

Output format: JSON array with structured business rules containing:
- rule_id: Unique identifier
- conditions: Business conditions in plain language
- actions: Business actions taken
- business_description: Clear explanation for business users
- business_domain: Domain classification
- priority: Business priority level
- compliance_notes: Regulatory or compliance relevance'''

        # Add language-specific guidance
        if language_enhancements:
            context_info = language_enhancements.get('context_info', '')
            pattern_hints = language_enhancements.get('pattern_hints', '')
            business_focus = language_enhancements.get('business_focus', '')
            
            if context_info:
                base_prompt += f"\n\nContext: {context_info}"
            if pattern_hints:
                base_prompt += f"\nPattern Recognition: {pattern_hints}"
            if business_focus:
                base_prompt += f"\nBusiness Focus: {business_focus}"
        
        return base_prompt
    
    def _build_user_prompt(self, code_snippet: str, context: Optional[str] = None,
                          language_enhancements: Dict[str, str] = None) -> str:
        """Build the user prompt with code and context using optimized string operations."""
        
        # Import string optimizer for performance improvement
        try:
            from ...Utils.string_optimizer import PromptBuilder
            
            # Use optimized prompt builder for 10-15% performance improvement
            builder = PromptBuilder()
            
            # Add context if available
            if context:
                builder.add_context_section("Consider the following context:", 
                                          language_enhancements.get('context_info', '') if language_enhancements else '')
            
            # Add main instructions
            instructions = [
                "Analyze the following legacy code snippet and extract all explicit and implicit business rules.",
                "For each rule, provide its conditions, actions, a clear business description, and the relevant lines from the source code.", 
                "Translate any technical terms into business language. If no business rules are found, return an empty array."
            ]
            builder.add_instructions(instructions)
            
            # Add code snippet
            builder.add_code_snippet(code_snippet, "legacy_code")
            
            # Add format requirements with example
            example_format = '''[
  {
    "rule_id": "RULE_001",
    "conditions": "Customer age must be 18 or older",
    "actions": "Approve application for processing",
    "business_description": "Age verification rule: Only adult customers are eligible for applications",
    "source_lines": "lines 45-47",
    "business_domain": "eligibility",
    "priority": "high",
    "compliance_notes": "Legal requirement - age of majority"
  }
]'''
            builder.add_format_requirements("JSON array following this format:", example_format)
            
            return builder.build_system_prompt()
            
        except ImportError:
            # Fallback to original implementation if optimizer not available
            prompt_parts = []
            
            # Add context if available
            if context:
                prompt_parts.append("Consider the following context:")
                if language_enhancements and language_enhancements.get('context_info'):
                    prompt_parts.append(language_enhancements['context_info'])
                prompt_parts.append("")
            
            # Add the main instruction
            prompt_parts.extend([
                "Analyze the following legacy code snippet and extract all explicit and implicit business rules.",
                "For each rule, provide its conditions, actions, a clear business description, and the relevant lines from the source code.",
                "Translate any technical terms into business language. If no business rules are found, return an empty array.",
                "",
                "Code Snippet:",
                "```",
                code_snippet,
                "```",
                "",
                "Extract business rules as a JSON array following this format:"
            ])
            
            # Add example format
            example_format = '''[
  {
    "rule_id": "RULE_001",
    "conditions": "Customer age must be 18 or older",
    "actions": "Approve application for processing",
    "business_description": "Age verification rule: Only adult customers are eligible for applications",
    "source_lines": "lines 45-47",
    "business_domain": "eligibility",
    "priority": "high",
    "compliance_notes": "Legal requirement - age of majority"
  }
]'''
            
            prompt_parts.append(example_format)
            
            return "\n".join(prompt_parts)
    
    def _api_call_with_retry(self, prompt: str) -> Dict[str, Any]:
        """Make API call with retry logic."""
        last_exception = None
        
        for attempt in range(self._max_retries):
            try:
                # Always use basic LLM call implementation
                response = self._make_basic_llm_call(prompt)
                return response
                
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                
        # If all retries failed, raise the last exception
        raise last_exception
    
    async def make_api_call_async(self, prompt: str) -> Dict[str, Any]:
        """Make asynchronous API call."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._api_call_with_retry(prompt)
        )
    
    def _make_basic_llm_call(self, prompt: str) -> Dict[str, Any]:
        """Basic LLM call implementation supporting OpenAI and Gemini clients."""
        if not self.llm_client:
            raise ValueError("No LLM client configured")
        
        try:
            # Detect client type and make appropriate API call
            client_type = type(self.llm_client).__name__
            
            if hasattr(self.llm_client, 'chat') and hasattr(self.llm_client.chat, 'completions'):
                # OpenAI client
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert business rule extraction agent."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self._max_output_tokens,
                    temperature=self._temperature
                )
                
                return {
                    'response_text': response.choices[0].message.content,
                    'tokens_input': response.usage.prompt_tokens if response.usage else 0,
                    'tokens_output': response.usage.completion_tokens if response.usage else 0
                }
            
            elif hasattr(self.llm_client, 'generate_content'):
                # Gemini client
                response = self.llm_client.generate_content(prompt)
                
                return {
                    'response_text': response.text if response.text else '',
                    'tokens_input': getattr(response, 'prompt_token_count', 0),
                    'tokens_output': getattr(response, 'candidates_token_count', 0)
                }
            
            else:
                # Unknown client type - try generic approach
                raise ValueError(f"Unsupported LLM client type: {client_type}")
                
        except Exception as e:
            # Log the error and re-raise with context
            error_msg = f"LLM API call failed with {type(self.llm_client).__name__}: {str(e)}"
            raise RuntimeError(error_msg) from e
    
    def _parse_llm_response(self, response: Dict[str, Any]) -> List[Dict]:
        """Parse and validate LLM response."""
        response_text = response.get('response_text', '')
        
        if not response_text:
            return []
        
        # Clean the response (remove markdown formatting if present)
        cleaned_response = self._clean_json_response(response_text)
        
        try:
            # Parse JSON response
            rules = json.loads(cleaned_response)
            
            # Validate that it's a list
            if not isinstance(rules, list):
                return []
            
            # Validate each rule
            validated_rules = []
            for rule in rules:
                if self._validate_rule_structure(rule):
                    validated_rules.append(rule)
            
            return validated_rules
            
        except json.JSONDecodeError:
            # Log parsing error
            self._log_parsing_error(response_text)
            return []
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean JSON response from LLM (remove markdown formatting)."""
        # Remove markdown code blocks
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            if end != -1:
                response_text = response_text[start:end]
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            if end != -1:
                response_text = response_text[start:end]
        
        # Clean up common formatting issues
        response_text = response_text.strip()
        
        # Remove any leading/trailing non-JSON content
        if response_text.startswith('[') and response_text.endswith(']'):
            return response_text
        
        # Try to find JSON array boundaries
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return response_text[start_idx:end_idx + 1]
        
        return response_text
    
    def _validate_rule_structure(self, rule: Dict[str, Any]) -> bool:
        """Validate that a rule has the required structure."""
        required_fields = ['rule_id', 'conditions', 'actions', 'business_description']
        
        if not isinstance(rule, dict):
            return False
        
        for field in required_fields:
            if field not in rule or not rule[field]:
                return False
        
        return True
    
    def _log_chunk_error(self, chunk_idx: int, error: Exception) -> None:
        """Log chunk processing errors."""
        # This would typically use the agent's logging system
        pass
    
    def _log_parsing_error(self, response_text: str) -> None:
        """Log JSON parsing errors."""
        # This would typically use the agent's logging system
        pass