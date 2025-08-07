# Rule Documentation Agent Test Runner

This enhanced test runner provides multiple modes for testing the RuleDocumentationAgent with different output formats.

## Usage Options

### 1. Full Extraction + Documentation (Original Mode)
```bash
python ./Test_Cases/test_runner_for_document_agent.py
# OR explicitly:
python ./Test_Cases/test_runner_for_document_agent.py --mode full
```
- Runs complete LegacyRuleExtractionAgent + RuleDocumentationAgent workflow
- Uses LLM to extract rules from CLIPS code file
- Generates markdown documentation

### 2. Test All Documentation Formats
```bash
python ./Test_Cases/test_runner_for_document_agent.py --mode formats
```
- Uses pre-extracted rules from `./Rule_Agent_Output_Files/extracted_rules_output.json`
- Generates documentation in ALL formats (markdown, JSON, HTML)
- Creates separate output files for each format
- Fast - no LLM calls needed

### 3. Test Single Documentation Format
```bash
# Test HTML format
python ./Test_Cases/test_runner_for_document_agent.py --mode single-format --format html

# Test JSON format  
python ./Test_Cases/test_runner_for_document_agent.py --mode single-format --format json

# Test Markdown format
python ./Test_Cases/test_runner_for_document_agent.py --mode single-format --format markdown
```
- Uses pre-extracted rules from existing JSON file
- Tests only the specified format
- Fast and targeted testing

### 4. Custom Rules File
```bash
python ./Test_Cases/test_runner_for_document_agent.py --mode formats --rules-file /path/to/your/rules.json
```
- Use any custom rules JSON file as input
- Test documentation generation with different rule sets

## Output Files

### Full Mode
- `extracted_rules_output.json` - Extracted rules from LLM
- `business_rules_documentation.md` - Markdown documentation
- `audit_logs.jsonl` - Full audit trail

### Format Testing Modes
- `business_rules_documentation_markdown.md` - Markdown format
- `business_rules_documentation_json.json` - JSON format  
- `business_rules_documentation_html.html` - HTML format
- `doc_test_{format}_audit.jsonl` - Format-specific audit logs

## Benefits

### ✅ **Faster Development**
- Test documentation formats without waiting for LLM extraction
- Iterate quickly on format improvements

### ✅ **Format Comparison** 
- Generate all formats with identical data
- Compare output quality across formats

### ✅ **Clean Rule IDs**
- All formats now use clean rule IDs (no chunk prefixes)
- Professional-looking documentation

### ✅ **Performance Optimized**
- Benefits from Phase 3 performance improvements
- LRU caching, set operations, pre-compiled regex patterns

## Example Output Samples

### Markdown Format
```markdown
### Rule ID: high_income_fast_track
- **Business Description:** This rule identifies high-income, low-risk applicants...
- **Conditions:** `The applicant's annual income is over $150,000...`
- **Actions:** `Mark the application as eligible for fast-track processing.`
```

### HTML Format  
```html
<li><h3>Rule ID: high_income_fast_track</h3>
<p><b>Business Description:</b> This rule identifies high-income, low-risk applicants...</p>
<p><b>Conditions:</b> <code>The applicant's annual income is over $150,000...</code></p>
```

### JSON Format
```json
{
  "rule_id": "high_income_fast_track",
  "conditions": "The applicant's annual income is over $150,000...",
  "actions": "Mark the application as eligible for fast-track processing.",
  "business_description": "This rule identifies high-income, low-risk applicants..."
}
```

## Technical Features

- **Clean Rule IDs**: No chunk prefixes (fixed from `chunk2_rule_name` to `rule_name`)
- **Intelligent Deduplication**: Duplicate rules get clean versioning (`rule_v2`, `rule_v3`)
- **Domain Classification**: Automatically detects business domain (lending, banking, etc.)
- **Performance Optimized**: Uses all Phase 3 performance improvements
- **Full Audit Trail**: Complete compliance logging for all operations

Perfect for testing different output formats quickly and efficiently! 🚀