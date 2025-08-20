# LLM Validation Setup Guide

## Quick Start - API Key Configuration

### Option 1: Environment Variable (Recommended)
```bash
# Windows (Command Prompt)
set GOOGLE_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:GOOGLE_API_KEY="your_api_key_here"

# Linux/Mac
export GOOGLE_API_KEY="your_api_key_here"
```

### Option 2: Create .env file
```bash
# Create .env file in project root
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

### Option 3: Direct Test (Temporary)
```python
# For testing only - replace 'your_api_key_here' in test script
api_key = "your_api_key_here"
```

## Getting a Google API Key

1. **Visit**: https://aistudio.google.com/app/apikey
2. **Create new API key** for Gemini
3. **Copy the key** (starts with "AIza...")
4. **Set environment variable** using Option 1 above

## Validation Test Commands

### 1. Complete Pipeline Test
```bash
python test_complete_pipeline.py
```
**Expected Output**: Full LLM validation with 90%+ target verification

### 2. Integration Test (Backup)
```bash
python test_completeness_integration.py
```
**Expected Output**: Component validation with simulated results

### 3. Direct COBOL Extraction Test
```bash
python test_cobol_extraction.py
```
**Expected Output**: Real rule extraction from COBOL sample

## Success Criteria

### ✅ Target Achievement
- **Rule Extraction**: 90%+ completeness (32+ out of 36 expected rules)
- **Processing Time**: <60 seconds for COBOL sample
- **Accuracy**: Real business rules extracted, not generic patterns

### ✅ Quality Validation
- **Completeness Report**: Generated automatically after extraction
- **Recommendations**: Actionable feedback if below 90%
- **Audit Trail**: Complete logging of analysis process

### ✅ Performance Validation
- **Analysis Speed**: <5ms for completeness analysis
- **Memory Usage**: Minimal overhead on extraction process
- **Error Handling**: Graceful fallback if analysis fails

## Troubleshooting

### API Key Issues
```bash
# Test API key validity
python -c "import os; from Utils.llm_providers import GeminiLLMProvider; print('API Key:', 'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET')"
```

### Common Issues
- **"GOOGLE_API_KEY environment variable required"**: Set API key using Option 1
- **"API key invalid"**: Verify key at https://aistudio.google.com/app/apikey
- **Rate limiting**: Wait 60 seconds between tests
- **Network issues**: Check internet connection

## Next Steps After Validation

### If 90%+ Target Achieved ✅
1. Document success metrics
2. Prepare for production deployment
3. Create user training materials

### If Below 90% Target ❌
1. Analyze which rules were missed
2. Refine chunking strategy
3. Adjust LLM prompts
4. Re-test until target achieved

## Ready to Test?

Once API key is configured, run:
```bash
python test_complete_pipeline.py
```

This will validate the complete Phase 15 implementation and confirm 90%+ rule extraction target achievement.