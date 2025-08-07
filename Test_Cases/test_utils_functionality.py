#!/usr/bin/env python3

"""
Test Utils Functionality

Validates that the new shared utilities work correctly and can be imported.
"""

import sys
import os

# Add the parent directory to Python path for imports (since we're in Test_Cases subdirectory)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def test_request_utils():
    """Test RequestIdGenerator functionality"""
    print("[TEST] Testing RequestIdGenerator...")
    
    from Utils.request_utils import RequestIdGenerator
    
    # Test basic request ID generation
    req_id = RequestIdGenerator.create_request_id()
    print(f"   Default request ID: {req_id}")
    assert req_id.startswith("req-")
    assert len(req_id.split('-')[1]) == 12
    
    # Test custom prefix and length
    custom_id = RequestIdGenerator.create_request_id("test", 8)
    print(f"   Custom request ID: {custom_id}")
    assert custom_id.startswith("test-")
    assert len(custom_id.split('-')[1]) == 8
    
    # Test PII token generation
    pii_token = RequestIdGenerator.create_pii_token()
    print(f"   PII token: {pii_token}")
    assert pii_token.startswith("PII_TOKEN_")
    
    # Test agent-specific IDs
    triage_id = RequestIdGenerator.create_agent_specific_id("triage")
    extraction_id = RequestIdGenerator.create_agent_specific_id("rule_extraction")
    detok_id = RequestIdGenerator.create_agent_specific_id("pii", "detokenize")
    
    print(f"   Triage ID: {triage_id}")
    print(f"   Extraction ID: {extraction_id}")
    print(f"   Detokenize ID: {detok_id}")
    
    assert triage_id.startswith("triage-")
    assert extraction_id.startswith("rule-ext-")
    assert detok_id.startswith("detok-")
    
    # Test validation
    assert RequestIdGenerator.validate_request_id(req_id) == True
    assert RequestIdGenerator.validate_request_id("invalid") == False
    assert RequestIdGenerator.validate_request_id("") == False
    
    # Test prefix extraction
    assert RequestIdGenerator.extract_prefix(req_id) == "req"
    assert RequestIdGenerator.extract_prefix(custom_id) == "test"
    assert RequestIdGenerator.extract_prefix("invalid") is None
    
    print("   [PASS] RequestIdGenerator tests completed")

def test_time_utils():
    """Test TimeUtils functionality"""
    print("[TEST] Testing TimeUtils...")
    
    from Utils.time_utils import TimeUtils
    import time
    
    # Test timestamp generation
    timestamp = TimeUtils.get_current_utc_timestamp()
    print(f"   Current timestamp: {timestamp}")
    assert timestamp.tzinfo is not None
    
    # Test duration calculation
    start_time = TimeUtils.get_current_utc_timestamp()
    time.sleep(0.01)  # 10ms
    duration_ms = TimeUtils.calculate_duration_ms(start_time)
    print(f"   Duration: {duration_ms:.2f}ms")
    assert duration_ms >= 10  # At least 10ms
    
    # Test timestamp formatting
    iso_format = TimeUtils.format_timestamp()
    log_format = TimeUtils.format_timestamp_for_logs()
    print(f"   ISO format: {iso_format}")
    print(f"   Log format: {log_format}")
    
    # Test timestamp parsing
    parsed = TimeUtils.parse_iso_timestamp(iso_format)
    assert parsed is not None
    
    # Test timer
    timer = TimeUtils.create_operation_timer()
    time.sleep(0.01)
    elapsed = timer()
    print(f"   Timer elapsed: {elapsed:.2f}ms")
    assert elapsed >= 10
    
    print("   [PASS] TimeUtils tests completed")

def test_json_utils():
    """Test JsonUtils functionality"""
    print("[TEST] Testing JsonUtils...")
    
    from Utils.json_utils import JsonUtils
    
    # Test safe loads
    valid_json = '{"test": "value", "number": 42}'
    invalid_json = '{"invalid": json}'
    
    result = JsonUtils.safe_loads(valid_json)
    print(f"   Valid JSON parsed: {result}")
    assert result == {"test": "value", "number": 42}
    
    result = JsonUtils.safe_loads(invalid_json, {"default": True})
    print(f"   Invalid JSON fallback: {result}")
    assert result == {"default": True}
    
    # Test safe dumps
    data = {"test": "value", "list": [1, 2, 3]}
    json_str = JsonUtils.safe_dumps(data)
    print(f"   Serialized JSON: {json_str[:50]}...")
    assert "test" in json_str
    
    # Test dict-specific parsing
    dict_result = JsonUtils.safe_loads_dict(valid_json)
    assert isinstance(dict_result, dict)
    
    list_result = JsonUtils.safe_loads_list('[1, 2, 3]')
    assert isinstance(list_result, list)
    
    # Test JSON extraction from text
    text_with_json = 'Some text\n```json\n{"extracted": "value"}\n```\nMore text'
    extracted = JsonUtils.extract_json_from_text(text_with_json)
    print(f"   Extracted JSON: {extracted}")
    assert extracted == {"extracted": "value"}
    
    # Test validation
    valid, errors = JsonUtils.validate_json_structure(
        {"name": "test", "age": 25},
        required_keys=["name"],
        expected_types={"age": int}
    )
    print(f"   Validation result: {valid}, errors: {errors}")
    assert valid == True
    
    print("   [PASS] JsonUtils tests completed")

def test_text_processing_utils():
    """Test TextProcessingUtils functionality"""
    print("[TEST] Testing TextProcessingUtils...")
    
    from Utils.text_processing import TextProcessingUtils
    
    # Test data preparation
    dict_data = {"test": "value"}
    text_data, is_dict = TextProcessingUtils.prepare_input_data(dict_data)
    print(f"   Prepared data: {text_data[:30]}..., is_dict: {is_dict}")
    assert is_dict == True
    assert "test" in text_data
    
    # Test data restoration
    restored = TextProcessingUtils.restore_data_format(text_data, is_dict)
    print(f"   Restored data: {restored}")
    assert restored == dict_data
    
    # Test text cleaning
    messy_text = "  Line 1  \n\n\n  Line 2  \n  "
    cleaned = TextProcessingUtils.clean_text_for_processing(messy_text)
    print(f"   Cleaned text: '{cleaned}'")
    assert "Line 1" in cleaned and "Line 2" in cleaned
    
    # Test truncation
    long_text = "This is a very long text that needs to be truncated"
    truncated = TextProcessingUtils.truncate_text(long_text, 20)
    print(f"   Truncated: '{truncated}'")
    assert len(truncated) <= 20
    assert truncated.endswith("...")
    
    # Test code block extraction
    markdown_text = "Some text\n```python\nprint('hello')\n```\nMore text"
    code_blocks = TextProcessingUtils.extract_code_blocks(markdown_text)
    print(f"   Code blocks found: {len(code_blocks)}")
    if code_blocks:
        print(f"   First block: {code_blocks[0]}")
    assert len(code_blocks) >= 1
    
    # Test token estimation
    tokens = TextProcessingUtils.count_tokens_estimate("Hello world this is a test")
    print(f"   Estimated tokens: {tokens}")
    assert tokens > 0
    
    # Test keyword extraction
    text = "Machine learning artificial intelligence data science"
    keywords = TextProcessingUtils.extract_keywords(text)
    print(f"   Keywords: {keywords}")
    assert len(keywords) > 0
    
    print("   [PASS] TextProcessingUtils tests completed")

def test_utils_imports():
    """Test that Utils can be imported through __init__.py"""
    print("[TEST] Testing Utils imports...")
    
    from Utils import RequestIdGenerator, TimeUtils, JsonUtils, TextProcessingUtils
    
    # Quick functionality tests
    req_id = RequestIdGenerator.create_request_id("import_test")
    timestamp = TimeUtils.get_current_utc_timestamp()
    json_data = JsonUtils.safe_loads('{"import": "test"}')
    text_data, is_dict = TextProcessingUtils.prepare_input_data("test")
    
    print(f"   Import test - req_id: {req_id}")
    print(f"   Import test - timestamp: {timestamp}")
    print(f"   Import test - json: {json_data}")
    print(f"   Import test - text: {text_data}, is_dict: {is_dict}")
    
    assert req_id.startswith("import_test-")
    assert timestamp is not None
    assert json_data == {"import": "test"}
    assert text_data == "test" and is_dict == False
    
    print("   [PASS] Utils imports working correctly")

def main():
    """Run all Utils tests"""
    print("UTILS FUNCTIONALITY TEST")
    print("========================")
    print("Testing shared utility functions for AI agents\n")
    
    try:
        test_request_utils()
        test_time_utils()
        test_json_utils()
        test_text_processing_utils()
        test_utils_imports()
        
        print("\n" + "=" * 50)
        print("ALL UTILS TESTS PASSED")
        print("=" * 50)
        print("[PASS] RequestIdGenerator - Working")
        print("[PASS] TimeUtils - Working")
        print("[PASS] JsonUtils - Working") 
        print("[PASS] TextProcessingUtils - Working")
        print("[PASS] Utils module imports - Working")
        print("\n[SUCCESS] Shared utilities are ready for agent integration!")
        
    except Exception as e:
        print(f"\n[FAIL] Utils test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()