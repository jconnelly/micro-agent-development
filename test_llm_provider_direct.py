#!/usr/bin/env python3
"""
Direct LLM Provider Test

Test the LLM provider directly to verify it's working correctly.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_llm_provider():
    """Test the LLM provider directly."""
    
    print("=== Direct LLM Provider Test ===")
    
    # Check API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("[!] GOOGLE_API_KEY not found")
        return False
    
    print(f"[+] API key configured (length: {len(api_key)})")
    
    try:
        from Utils.llm_providers import GeminiLLMProvider
        
        # Initialize provider
        provider = GeminiLLMProvider(model_name="gemini-1.5-flash")
        print("[+] GeminiLLMProvider initialized")
        
        # Test simple prompt
        simple_prompt = "What is 2+2? Respond with just the number."
        print(f"[*] Testing simple prompt: '{simple_prompt}'")
        
        response = provider.generate_content(simple_prompt)
        
        print(f"[*] Response received:")
        print(f"  - Content: '{response.content}'")
        print(f"  - Model: {response.model_name}")
        print(f"  - Provider: {response.provider_type}")
        print(f"  - Response time: {response.response_time_ms}ms")
        print(f"  - Error: {response.error}")
        
        if response.error:
            print(f"[!] LLM call failed: {response.error}")
            return False
        
        if not response.content or response.content.strip() == "":
            print(f"[!] Empty response content")
            return False
            
        print(f"[+] LLM provider working correctly!")
        
        # Test JSON response
        json_prompt = """
Please respond with valid JSON containing a simple greeting message.
Format: {"message": "your greeting here"}
"""
        print(f"[*] Testing JSON response...")
        
        json_response = provider.generate_content(json_prompt, temperature=0.1)
        
        print(f"[*] JSON Response:")
        print(f"  - Content: '{json_response.content}'")
        print(f"  - Error: {json_response.error}")
        
        if json_response.error:
            print(f"[!] JSON LLM call failed: {json_response.error}")
            return False
            
        if not json_response.content or json_response.content.strip() == "":
            print(f"[!] Empty JSON response content")
            return False
            
        # Try to parse as JSON (with cleaning)
        import json
        
        def clean_json_response(response_text):
            """Clean JSON response from markdown."""
            if not response_text:
                return "{}"
            cleaned = response_text.strip()
            if cleaned.startswith("```json") and cleaned.endswith("```"):
                lines = cleaned.split('\n')
                if len(lines) >= 3:
                    json_lines = lines[1:-1]
                    cleaned = '\n'.join(json_lines).strip()
            elif cleaned.startswith("```") and cleaned.endswith("```"):
                lines = cleaned.split('\n')
                if len(lines) >= 3:
                    json_lines = lines[1:-1]
                    cleaned = '\n'.join(json_lines).strip()
            return cleaned if cleaned else "{}"
        
        try:
            cleaned_content = clean_json_response(json_response.content)
            print(f"[*] Cleaned content: '{cleaned_content}'")
            parsed = json.loads(cleaned_content)
            print(f"[+] JSON parsing successful: {parsed}")
        except Exception as e:
            print(f"[!] JSON parsing failed: {e}")
            print(f"Raw content: '{json_response.content}'")
            return False
            
        print(f"[+] JSON response test successful!")
        return True
        
    except Exception as e:
        print(f"[!] Error during LLM provider test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_provider()
    print(f"\n=== Test Result: {'SUCCESS' if success else 'FAILED'} ===")
    sys.exit(0 if success else 1)