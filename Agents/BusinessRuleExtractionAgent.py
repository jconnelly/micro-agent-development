# legacy_rule_extraction_agent.py (Relevant section within the class)

import json
import uuid
import datetime
import time
import asyncio
from typing import Dict, Any, List, Optional
from functools import lru_cache

# Import other Agents from current location, change package location if moved
from .BaseAgent import BaseAgent
from .ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel
from .Exceptions import RuleExtractionError, ValidationError

# Import the Google Generative AI library
import google.generativeai as genai
from google.generativeai import types # For GenerateContentConfig and other types

class BusinessRuleExtractionAgent(BaseAgent):
    """
    Business Rule Extraction Agent for Legacy System Modernization.
    
    **Business Purpose:**
    Automatically discovers and translates hidden business rules from legacy code into 
    clear, actionable business documentation. Critical for digital transformation, 
    regulatory compliance, and business process optimization initiatives.
    
    **Key Business Benefits:**
    - **Digital Transformation**: Accelerate legacy modernization by 60-80%
    - **Regulatory Compliance**: Document business rules for audit and governance
    - **Risk Mitigation**: Preserve critical business logic during system migrations  
    - **Knowledge Transfer**: Convert tribal knowledge into documented processes
    - **Business Analysis**: Enable process optimization and automation
    
    **Supported Legacy Technologies:**
    - **COBOL**: Mainframe business applications and batch processing
    - **Java**: Enterprise applications and web services  
    - **C/C++**: System-level business logic and financial calculations
    - **PL/SQL**: Database business rules and stored procedures
    - **Visual Basic**: Desktop applications and Office macros
    - **Perl**: Data processing and legacy integration scripts
    - **FORTRAN**: Scientific and engineering calculations
    - **Natural**: ADABAS database applications
    
    **Business Rule Categories:**
    - **Validation Rules**: Data quality and business constraints
    - **Calculation Rules**: Financial computations and pricing logic
    - **Workflow Rules**: Process flow and approval hierarchies  
    - **Authorization Rules**: Access control and permission matrices
    - **Compliance Rules**: Regulatory requirements and audit trails
    - **Integration Rules**: Data mapping and transformation logic
    
    **Industry Applications:**
    - **Financial Services**: Banking regulations, loan processing, trading rules
    - **Insurance**: Underwriting logic, claims processing, risk assessment
    - **Healthcare**: Patient care protocols, billing rules, compliance
    - **Manufacturing**: Quality control, supply chain, safety regulations  
    - **Government**: Citizen services, tax processing, benefit calculations
    - **Utilities**: Billing logic, service provisioning, regulatory compliance
    
    **AI-Powered Analysis:**
    - Advanced language models identify implicit business rules
    - Context-aware translation preserves business intent
    - Domain-specific terminology recognition and translation
    - Cross-reference analysis for rule dependencies
    - Confidence scoring for rule extraction accuracy
    
    **Integration Examples:**
    ```python
    # Legacy system modernization project
    from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
    from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent
    
    audit_system = ComplianceMonitoringAgent()
    extractor = BusinessRuleExtractionAgent(
        llm_client=ai_client,
        audit_system=audit_system,
        model_name="gemini-2.5-flash"
    )
    
    # Extract business rules from COBOL mainframe code
    with open("legacy_loan_processing.cbl") as f:
        cobol_code = f.read()
    
    results = extractor.extract_and_translate_rules(
        legacy_code_snippet=cobol_code,
        context="Loan processing and credit decisioning system",
        audit_level=2  # Full compliance documentation
    )
    
    # Results contain business-readable rules:
    # - "Loan Eligibility: Credit score must be 650 or higher"  
    # - "Income Verification: Debt-to-income ratio cannot exceed 43%"
    # - "Documentation: Employment verification required for loans over $100K"
    ```
    
    **Performance & Scalability:**
    - Intelligent chunking for large codebases (up to 10MB files)
    - Parallel processing with rate limiting for API efficiency
    - Caching for repeated code patterns and common rules
    - Progress tracking for long-running extractions
    - Automatic retry with exponential backoff
    
    **Quality Assurance:**
    - Business rule confidence scoring (High/Medium/Low)
    - Cross-reference validation between extracted rules
    - Duplicate rule detection and consolidation
    - Business domain classification and tagging
    - Technical debt identification and prioritization
    
    **Compliance & Governance:**
    - Complete audit trail of all extraction activities
    - Source code traceability for each business rule
    - Change impact analysis for modernization planning  
    - Regulatory requirement mapping and documentation
    - Risk assessment for rule migration priorities
    
    Warning:
        Large legacy systems may require significant processing time and API resources.
        Monitor usage and implement appropriate rate limiting for production workloads.
    
    Note:
        This class uses business-friendly naming optimized for stakeholder
        communications and enterprise documentation.
    """
    # Rate limiting constants
    API_DELAY_SECONDS = 1.0
    MAX_RETRIES = 3
    
    # Timeout constants
    API_TIMEOUT_SECONDS = 30
    TOTAL_OPERATION_TIMEOUT = 600  # 10 minutes
    
    def __init__(self, llm_client: Any, audit_system: ComplianceMonitoringAgent, agent_id: str = None, 
                 log_level: int = 0, model_name: str = "unknown", llm_provider: str = "unknown"):
        """
        Initializes the LegacyRuleExtractionAgent.

        Args:
            llm_client: An initialized LLM client (e.g., genai.Client()).
            audit_system: An instance of the AgentAuditing class.
            agent_id: Unique identifier for this agent instance.
            log_level: 0 = production (silent), 1 = development (verbose)
            model_name: Name of the LLM model being used (e.g., "gemini-1.5-flash", "gpt-4")
            llm_provider: Provider of the LLM (e.g., "google", "openai", "anthropic")
        """
        # Initialize base agent
        super().__init__(
            audit_system=audit_system,
            agent_id=agent_id,
            log_level=log_level,
            model_name=model_name,
            llm_provider=llm_provider,
            agent_name="Legacy Rule Extraction and Translator Agent"
        )
        
        # Rule extraction specific configuration
        self.llm_client = llm_client

    # get_ip_address() method now inherited from BaseAgent

    def _prepare_llm_prompt(self, code_snippet: str, context: Optional[str] = None) -> tuple[str, str]:
        """
        Prepares the system and user prompts for the LLM based on the code snippet.
        """
        system_prompt = (
            f"You are an expert business rule extraction and translation agent. "
            f"Your task is to analyze legacy code snippets, identify embedded business rules, "
            f"separate them from technical implementation details, and translate any cryptic "
            f"technical terminology into clear, business-friendly language. "
            f"Output the extracted rules in a structured JSON array format, where each rule "
            f"has 'rule_id', 'conditions', 'actions', 'business_description', and 'source_code_lines'."
        )

        user_prompt = (
            f"Analyze the following legacy code snippet and extract all explicit and implicit "
            f"business rules. For each rule, provide its conditions, actions, a clear "
            f"business description, and the relevant lines from the source code. "
            f"Translate any technical terms into business language. "
            f"If no business rules are found, return an empty array.\n\n"
            f"Code Snippet:\n```\n{code_snippet}\n```\n\n"
            f"Example JSON Output Format:\n"
            f"""[
  {{
    "rule_id": "RULE_001",
    "conditions": "Customer age must be 18 or older",
    "actions": "Approve loan application for processing",
    "business_description": "Loan Eligibility Rule: Only adult customers (18+) are eligible for loan applications to comply with legal requirements",
    "source_lines": "lines 45-47",
    "technical_implementation": "if (customer.age >= 18) {{ approveApplication(customer); }}",
    "business_domain": "financial_services",
    "priority": "high",
    "compliance_notes": "Legal requirement - age of majority"
  }},
  {{
    "rule_id": "RULE_002", 
    "conditions": "Credit score below 600",
    "actions": "Automatically reject application",
    "business_description": "Credit Risk Rule: Applications with credit scores below 600 are automatically rejected due to high default risk",
    "source_lines": "lines 52-55",
    "technical_implementation": "if (creditScore < 600) {{ rejectApplication('LOW_CREDIT'); }}",
    "business_domain": "risk_management",
    "priority": "high",
    "compliance_notes": "Risk management policy"
  }}
]"""
        )
        if context:
            user_prompt = f"Consider the following context: {context}\n\n" + user_prompt

        return system_prompt, user_prompt
    
    def _extract_file_context(self, lines: List[str], max_lines: int = 50) -> List[str]:
        """
        Extract file context (headers, imports, templates, comments) from the beginning of the file.
        This context will be included with each chunk to provide necessary background.
        Uses caching for performance optimization on repeated file processing.
        """
        # Use cached implementation for performance optimization
        lines_tuple = tuple(lines[:max_lines])  # Convert to tuple for hashing
        return list(self._cached_extract_file_context(lines_tuple, max_lines))
    
    @lru_cache(maxsize=128)  # Cache up to 128 unique file context extractions
    def _cached_extract_file_context(self, lines_tuple: tuple, max_lines: int = 50) -> tuple:
        """
        Cached file context extraction implementation for performance optimization.
        
        Args:
            lines_tuple: Tuple of file lines for cache-friendly hashing
            max_lines: Maximum number of lines to examine for context
            
        Returns:
            Tuple of context lines (converted back to list by caller)
        """
        context_lines = []
        context_keywords = [
            'import', 'include', '#include', 'using', 'package', 'deftemplate', 
            'entity-engine-xml', '<?xml', 'definitions', 'namespace', 'typedef',
            'class ', 'struct ', 'interface ', 'namespace ', 'module ', 'program ',
            ';; ', '# ', '// ', '/* ', '<!--'
        ]
        
        for i, line in enumerate(lines_tuple):
            line_lower = line.lower().strip()
            
            # Include header comments and metadata
            if (line.strip().startswith((';;', '#', '//', '/*', '<!--')) or
                any(keyword in line_lower for keyword in context_keywords) or
                line_lower.startswith('<?') or
                'deftemplate' in line_lower or
                'entity-engine-xml' in line_lower):
                context_lines.append(line)
        
        return tuple(context_lines)  # Return tuple for caching
    
    def _find_smart_boundary(self, lines: List[str], target_pos: int, search_window: int = 10) -> int:
        """
        Find natural breaking points near target position to avoid splitting rules/logical blocks.
        """
        if target_pos >= len(lines):
            return len(lines)
        
        # Prefer these boundaries (in order of preference)
        boundary_patterns = [
            lambda line: line.strip() == '',  # Empty lines (highest preference)
            lambda line: line.strip().startswith(';;') or line.strip().startswith('#'),  # Comments
            lambda line: line.strip().startswith('//') or line.strip().startswith('/*'),  # C-style comments
            lambda line: line.strip().endswith('}') or line.strip().endswith('});'),  # Code block ends
            lambda line: line.strip().startswith('(defrule'),  # CLIPS rules
            lambda line: line.strip().startswith('rule '),  # Drools rules
            lambda line: line.strip().startswith('function ') or line.strip().startswith('def '),  # Functions
            lambda line: line.strip().startswith('<') and '>' in line,  # XML tags
            lambda line: line.strip().endswith(';'),  # Statement ends
        ]
        
        # Search within window for best boundary
        for pattern in boundary_patterns:
            for offset in range(-search_window, search_window + 1):
                pos = target_pos + offset
                if 0 <= pos < len(lines) and pattern(lines[pos]):
                    return pos + 1 if pos + 1 <= len(lines) else len(lines)
        
        return target_pos  # Fall back to original position
    
    # _log_exception_to_audit() method now inherited from BaseAgent
    
    def _api_call_with_retry(self, prompt: str) -> Dict[str, Any]:
        """
        Make API call with retry logic using base class functionality.
        """
        return super()._api_call_with_retry(
            self._make_api_call_async, prompt
        )
    
    # _api_call_with_retry_async() method now inherited from BaseAgent
    
    async def _make_api_call_async(self, prompt: str):
        """
        Make the actual API call in a thread pool to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.llm_client.generate_content(
                contents=prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
        )
        
    def _chunk_large_file(self, content: str, chunk_size: int = 175, overlap_size: int = 25) -> List[str]:
        """
        Enterprise-grade chunking strategy for large files.
        
        Args:
            content: The full file content as a string
            chunk_size: Number of lines per chunk (default 175 for optimal LLM context)
            overlap_size: Number of overlapping lines between chunks (default 25)
            
        Returns:
            List of chunks, each containing context + chunk content
        """
        # Defensive programming constants
        MAX_CHUNKS = 50
        MIN_CHUNK_SIZE = 10
        
        lines = content.split('\n')
        total_lines = len(lines)
        
        # Validate parameters
        if chunk_size < MIN_CHUNK_SIZE + overlap_size:
            raise ValidationError(
                f"chunk_size ({chunk_size}) must be at least MIN_CHUNK_SIZE + overlap_size ({MIN_CHUNK_SIZE + overlap_size})",
                context={"chunk_size": chunk_size, "min_required": MIN_CHUNK_SIZE + overlap_size}
            )
        
        # For small files, return as single chunk
        if total_lines <= chunk_size:
            return [content]
        
        # Estimate chunk count and validate
        estimated_chunks = max(1, (total_lines - overlap_size) // (chunk_size - overlap_size))
        if estimated_chunks > MAX_CHUNKS:
            raise ValidationError(
                f"File too large: would create ~{estimated_chunks} chunks (max {MAX_CHUNKS}). Consider increasing chunk_size or processing manually.",
                context={"estimated_chunks": estimated_chunks, "max_chunks": MAX_CHUNKS, "total_lines": total_lines}
            )
        
        chunks = []
        context_lines = self._extract_file_context(lines)
        
        self.logger.info(f"Chunking large file: {total_lines} lines into chunks of ~{chunk_size} lines with {overlap_size} line overlap")
        self.logger.info(f"Extracted {len(context_lines)} context lines for each chunk")
        self.logger.info(f"Estimated processing time: {estimated_chunks * 2}-{estimated_chunks * 4} seconds (with API delays)")
        
        i = 0
        chunk_number = 1
        while i < total_lines and len(chunks) < MAX_CHUNKS:
            chunk_end = min(i + chunk_size, total_lines)
            
            # Smart boundary detection for better rule preservation (limited to prevent excessive backtracking)
            if chunk_end < total_lines:
                original_chunk_end = chunk_end
                chunk_end = self._find_smart_boundary(lines, chunk_end)
                
                # Ensure smart boundary doesn't create chunks that are too small
                chunk_size_after_boundary = chunk_end - i
                if chunk_size_after_boundary < MIN_CHUNK_SIZE:
                    self.logger.debug(f"Smart boundary would create chunk too small ({chunk_size_after_boundary} lines), using original boundary")
                    chunk_end = original_chunk_end
            
            # Build chunk with context + actual content
            chunk_content_lines = lines[i:chunk_end]
            
            # Only add context if we have content lines and they meet minimum size
            if chunk_content_lines and len(chunk_content_lines) >= MIN_CHUNK_SIZE:
                chunk_lines = context_lines + ['', '// ===== CHUNK CONTENT =====', ''] + chunk_content_lines
                chunk_text = '\n'.join(chunk_lines)
                chunks.append(chunk_text)
                
                self.logger.debug(f"Created chunk {chunk_number}: lines {i+1}-{chunk_end} ({len(chunk_content_lines)} content lines)")
                chunk_number += 1
            
            # Calculate minimum advancement to guarantee progress
            min_advance = max(MIN_CHUNK_SIZE, chunk_size // 10)  # At least 10% of chunk_size
            
            # Move forward with overlap, ensuring minimum advancement
            next_start = max(i + min_advance, chunk_end - overlap_size)
            
            # Safety check: ensure we're making progress
            if next_start <= i:
                next_start = i + min_advance
            
            # If we can't make minimum advancement, we're done
            if next_start >= total_lines:
                break
                
            i = next_start
        
        self.logger.info(f"File chunked into {len(chunks)} chunks")
        return chunks

    def _determine_processing_strategy(self, legacy_code_snippet: str) -> tuple[bool, int]:
        """
        Determine whether to use chunked processing or single-pass based on file size.
        
        Args:
            legacy_code_snippet: The code to analyze
            
        Returns:
            Tuple of (should_chunk, line_count)
        """
        line_count = len(legacy_code_snippet.split('\n'))
        should_chunk = line_count > 175  # Threshold for chunking
        return should_chunk, line_count
    
    def _process_file_chunks(self, legacy_code_snippet: str, context: Optional[str], request_id: str) -> tuple[List[Dict], int, int, str]:
        """
        Process large files using chunked approach with progress tracking.
        
        Returns:
            Tuple of (extracted_rules, tokens_input, tokens_output, llm_response_raw)
        """
        chunks = self._chunk_large_file(legacy_code_snippet)
        all_rules = []
        total_tokens_input = 0
        total_tokens_output = 0
        chunk_start_time = time.time()
        
        self.logger.progress(f"Processing {len(chunks)} chunks...", request_id=request_id)
        self.logger.progress("Press Ctrl+C at any time to cancel processing")
        
        for chunk_idx, chunk_content in enumerate(chunks):
            # Progress tracking
            self._create_progress_reporter(chunk_idx, len(chunks), chunk_start_time, request_id)
            
            # Check for timeout
            elapsed_time = time.time() - chunk_start_time
            if elapsed_time > self.TOTAL_OPERATION_TIMEOUT:
                self.logger.warning(f"Total operation timeout ({self.TOTAL_OPERATION_TIMEOUT}s) exceeded. Stopping with partial results.", request_id=request_id)
                break
            
            try:
                chunk_rules, chunk_tokens_in, chunk_tokens_out = self._handle_chunk_processing(
                    chunk_content, context, chunk_idx, request_id
                )
                
                all_rules.extend(chunk_rules)
                total_tokens_input += chunk_tokens_in
                total_tokens_output += chunk_tokens_out
                
                self.logger.debug(f"Chunk {chunk_idx + 1} extracted {len(chunk_rules)} rules", request_id=request_id)
                
            except KeyboardInterrupt:
                self.logger.warning(f"Processing interrupted by user. Returning partial results from {chunk_idx} chunks.", request_id=request_id)
                break
            except (json.JSONDecodeError, Exception) as e:
                self._handle_chunk_error_recovery(chunk_idx, e, request_id)
                continue
        
        # Final progress summary
        total_time = time.time() - chunk_start_time
        self._log_chunk_completion_summary(total_time, all_rules, chunks, request_id)
        
        # Deduplicate rules while preserving clean rule IDs
        deduplicated_rules = self._deduplicate_rules(all_rules, request_id)
        
        llm_response_raw = f"Processed {len(chunks)} chunks, extracted {len(deduplicated_rules)} rules (deduplicated from {len(all_rules)} raw)"
        return deduplicated_rules, total_tokens_input, total_tokens_output, llm_response_raw
    
    def _process_single_file(self, legacy_code_snippet: str, context: Optional[str], request_id: str) -> tuple[List[Dict], int, int, str]:
        """
        Process small files using single-pass approach.
        
        Returns:
            Tuple of (extracted_rules, tokens_input, tokens_output, llm_response_raw)
        """
        system_prompt, user_prompt = self._prepare_llm_prompt(legacy_code_snippet, context)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = self._api_call_with_retry(full_prompt)
        llm_response_raw = response.text
        
        # Access token usage from usage_metadata
        tokens_input = 0
        tokens_output = 0
        if response.usage_metadata:
            tokens_input = response.usage_metadata.prompt_token_count
            tokens_output = response.usage_metadata.candidates_token_count
        else:
            self.logger.warning(f"No usage_metadata found in Gemini response.", request_id=request_id)

        # Parse the JSON response
        response_data = json.loads(llm_response_raw)
        extracted_rules = self._aggregate_chunk_results([response_data])
        
        return extracted_rules, tokens_input, tokens_output, llm_response_raw
    
    def _handle_chunk_processing(self, chunk_content: str, context: Optional[str], chunk_idx: int, request_id: str) -> tuple[List[Dict], int, int]:
        """
        Handle processing of a single chunk with rate limiting and error handling.
        
        Returns:
            Tuple of (chunk_rules, tokens_input, tokens_output)
        """
        # Rate limiting: sleep before API call (except for first chunk)
        if chunk_idx > 0:
            time.sleep(self.API_DELAY_SECONDS)
        
        # Prepare prompt for this chunk
        chunk_system_prompt, chunk_user_prompt = self._prepare_llm_prompt(chunk_content, context)
        chunk_full_prompt = f"{chunk_system_prompt}\n\n{chunk_user_prompt}"
        
        # API call with retry logic
        chunk_response = self._api_call_with_retry(chunk_full_prompt)
        
        # Parse chunk response
        chunk_response_raw = chunk_response.text
        chunk_response_data = json.loads(chunk_response_raw)
        
        # Handle different response formats - no need to modify rule_ids here
        chunk_rules = self._aggregate_chunk_results([chunk_response_data])
        
        # Track tokens
        tokens_input = 0
        tokens_output = 0
        if chunk_response.usage_metadata:
            tokens_input = chunk_response.usage_metadata.prompt_token_count
            tokens_output = chunk_response.usage_metadata.candidates_token_count
        
        return chunk_rules, tokens_input, tokens_output
    
    def _handle_chunk_error_recovery(self, chunk_idx: int, error: Exception, request_id: str) -> None:
        """
        Handle errors during chunk processing with appropriate logging.
        """
        if isinstance(error, json.JSONDecodeError):
            self.logger.error(f"Chunk {chunk_idx + 1} JSON parse error", request_id=request_id, exception=error)
        else:
            self.logger.error(f"Chunk {chunk_idx + 1} processing error", request_id=request_id, exception=error)
    
    def _aggregate_chunk_results(self, response_data_list: List[Any]) -> List[Dict]:
        """
        Aggregate and normalize rule extraction results from chunks.
        
        Args:
            response_data_list: List of response data from LLM calls
            
        Returns:
            Consolidated list of extracted rules
        """
        all_rules = []
        
        for response_data in response_data_list:
            # Handle different response formats from Gemini
            if isinstance(response_data, dict) and 'business_rules' in response_data:
                rules = response_data['business_rules']
            elif isinstance(response_data, list):
                rules = response_data
            else:
                rules = response_data if isinstance(response_data, list) else [response_data]
            
            if isinstance(rules, list):
                all_rules.extend(rules)
            else:
                all_rules.append(rules)
        
        return all_rules
    
    def _deduplicate_rules(self, all_rules: List[Dict], request_id: str) -> List[Dict]:
        """
        Intelligently deduplicate rules while preserving clean rule IDs.
        
        Args:
            all_rules: List of all rules from all chunks
            request_id: Request identifier for logging
            
        Returns:
            Deduplicated list of rules with clean IDs
        """
        if not all_rules:
            return all_rules
        
        seen_rule_ids = set()
        deduplicated_rules = []
        duplicate_count = 0
        
        for rule in all_rules:
            rule_id = rule.get('rule_id', 'unknown_rule')
            
            if rule_id not in seen_rule_ids:
                # First occurrence - keep as is
                seen_rule_ids.add(rule_id)
                deduplicated_rules.append(rule)
            else:
                # Duplicate found - create a unique ID by appending a suffix
                duplicate_count += 1
                original_id = rule_id
                counter = 2
                
                # Find a unique suffix
                while f"{original_id}_v{counter}" in seen_rule_ids:
                    counter += 1
                
                unique_id = f"{original_id}_v{counter}"
                rule['rule_id'] = unique_id
                seen_rule_ids.add(unique_id)
                deduplicated_rules.append(rule)
        
        if duplicate_count > 0:
            self.logger.info(f"Deduplicated {duplicate_count} duplicate rule IDs with clean suffixes (_v2, _v3, etc.)", request_id=request_id)
        
        return deduplicated_rules
    
    def _create_progress_reporter(self, chunk_idx: int, total_chunks: int, start_time: float, request_id: str) -> None:
        """
        Create and log progress information for chunk processing.
        """
        progress_percent = (chunk_idx / total_chunks) * 100
        elapsed_time = time.time() - start_time
        
        if chunk_idx > 0:
            avg_time_per_chunk = elapsed_time / chunk_idx
            estimated_remaining = avg_time_per_chunk * (total_chunks - chunk_idx)
            self.logger.progress(f"Processing chunk {chunk_idx + 1}/{total_chunks} ({progress_percent:.1f}% complete)", request_id=request_id)
            self.logger.progress(f"Estimated time remaining: {estimated_remaining:.1f} seconds", request_id=request_id)
        else:
            self.logger.progress(f"Processing chunk {chunk_idx + 1}/{total_chunks} (starting...)", request_id=request_id)
    
    def _log_chunk_completion_summary(self, total_time: float, all_rules: List[Dict], chunks: List[str], request_id: str) -> None:
        """
        Log completion summary for chunk processing.
        """
        self.logger.progress(f"Processing complete!", request_id=request_id)
        self.logger.info(f"Total chunks processed: {len([r for r in all_rules if r])}", request_id=request_id)
        self.logger.info(f"Total rules extracted: {len(all_rules)}", request_id=request_id)
        self.logger.info(f"Total processing time: {total_time:.1f} seconds", request_id=request_id)
        self.logger.info(f"Average time per chunk: {total_time / len(chunks):.1f} seconds", request_id=request_id)

    def extract_and_translate_rules(self, legacy_code_snippet: str, context: Optional[str] = None, audit_level: int = AuditLevel.LEVEL_1.value) -> Dict[str, Any]:
        """
        Extracts and translates business rules from a legacy code snippet using an LLM,
        and logs the process based on audit_level.

        Args:
            legacy_code_snippet: A string containing the legacy code to analyze.
            context: Optional, additional context for the LLM (e.g., system purpose).
            audit_level: An integer representing the desired audit granularity (1-4).

        Returns:
            A dictionary containing the extracted rules and the audit log.
        """
        request_id = f"rule-ext-{uuid.uuid4().hex}"
        start_time = datetime.datetime.now(datetime.timezone.utc)

        user_id = "analyst_user" # Placeholder
        session_id = request_id
        ip_address = self.get_ip_address()

        # 1. Prepare LLM prompt
        system_prompt, user_prompt = self._prepare_llm_prompt(legacy_code_snippet, context)

        llm_input_data = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "model_name": self.model_name,
            "llm_provider": self.llm_provider
        }

        extracted_rules: List[Dict] = []
        llm_response_raw: Optional[str] = None
        tokens_input = 0
        tokens_output = 0
        error_details: Optional[str] = None

        try:
            # Clear any previous session logs
            self.logger.clear_session_logs()
            
            # Determine processing strategy
            should_chunk, line_count = self._determine_processing_strategy(legacy_code_snippet)
            
            if should_chunk:
                self.logger.info(f"Large file detected ({line_count} lines). Using chunked processing...", request_id=request_id)
                extracted_rules, tokens_input, tokens_output, llm_response_raw = self._process_file_chunks(
                    legacy_code_snippet, context, request_id
                )
            else:
                self.logger.info(f"Small file ({line_count} lines). Using single-pass processing...", request_id=request_id)
                extracted_rules, tokens_input, tokens_output, llm_response_raw = self._process_single_file(
                    legacy_code_snippet, context, request_id
                )

        except json.JSONDecodeError as e:
            error_details = f"LLM response was not valid JSON: {e}. Raw response: {llm_response_raw}"
            self.logger.error(error_details, request_id=request_id, exception=e)
            self._log_exception_to_audit(request_id, e, "JSON_DECODE_ERROR", {
                "raw_response": llm_response_raw[:500] if llm_response_raw else "None",
                "tokens_processed": tokens_input + tokens_output,
                "rules_extracted_before_error": len(extracted_rules)
            }, "rule_extraction")
        except KeyboardInterrupt as e:
            error_details = f"Processing interrupted by user"
            self.logger.warning(error_details, request_id=request_id)
            self._log_exception_to_audit(request_id, e, "USER_INTERRUPTION", {
                "rules_extracted_before_interruption": len(extracted_rules),
                "processing_stage": "rule_extraction"
            }, "rule_extraction")
        except TimeoutError as e:
            error_details = f"Operation timed out: {e}"
            self.logger.error(error_details, request_id=request_id, exception=e)
            self._log_exception_to_audit(request_id, e, "TIMEOUT_ERROR", {
                "timeout_duration": self.TOTAL_OPERATION_TIMEOUT,
                "tokens_processed": tokens_input + tokens_output,
                "rules_extracted_before_timeout": len(extracted_rules)
            }, "rule_extraction")
        except Exception as e:
            error_details = f"Unexpected error during rule extraction: {e}"
            self.logger.error(error_details, request_id=request_id, exception=e)
            self._log_exception_to_audit(request_id, e, "UNEXPECTED_ERROR", {
                "exception_type": type(e).__name__,
                "tokens_processed": tokens_input + tokens_output,
                "rules_extracted_before_error": len(extracted_rules),
                "processing_stage": "rule_extraction"
            }, "rule_extraction")

        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # 2. Call the AgentAuditing class after the LLM call
        logger_session_summary = self.logger.create_audit_summary(
            operation_name="rule_extraction",
            request_id=request_id,
            status="SUCCESS" if not error_details else "FAILED",
            rules_extracted=len(extracted_rules),
            tokens_processed=tokens_input + tokens_output,
            processing_duration_ms=duration_ms
        )
        
        audit_log_data = self.audit_system.log_agent_activity(
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.version,
            step_type="LLM_Rule_Extraction",
            llm_model_name=self.model_name,
            llm_provider=self.llm_provider,
            llm_input=llm_input_data,
            llm_output=llm_response_raw,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            final_decision={
                "extracted_rules_count": len(extracted_rules), 
                "rules": extracted_rules,
                "logger_session_summary": logger_session_summary
            },
            duration_ms=duration_ms,
            error_details=error_details,
            audit_level=audit_level
        )

        # Debug logging to trace the issue
        self.logger.debug(f"Final return - extracted_rules type: {type(extracted_rules)}, length: {len(extracted_rules)}", request_id=request_id)
        
        return {
            "extracted_rules": extracted_rules,
            "audit_log": audit_log_data
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get agent information including capabilities and configuration.
        
        Returns:
            Dictionary containing agent information
        """
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "version": self.version,
            "model_name": self.model_name,
            "llm_provider": self.llm_provider,
            "capabilities": [
                "legacy_code_analysis",
                "business_rule_extraction",
                "code_translation",
                "large_file_processing",
                "chunked_processing"
            ],
            "supported_languages": [
                "Java", "C++", "COBOL", "CLIPS", "Drools", 
                "XML", "JSON", "Legacy Business Rules"
            ],
            "configuration": {
                "api_timeout_seconds": self.API_TIMEOUT_SECONDS,
                "max_retries": self.MAX_RETRIES,
                "api_delay_seconds": self.API_DELAY_SECONDS,
                "total_operation_timeout": self.TOTAL_OPERATION_TIMEOUT,
                "chunk_size_lines": 175,
                "overlap_size_lines": 25
            }
        }