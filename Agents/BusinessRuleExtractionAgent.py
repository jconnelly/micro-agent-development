# legacy_rule_extraction_agent.py (Relevant section within the class)

import json
import uuid
import datetime
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from functools import lru_cache

# Import other Agents from current location, change package location if moved
from .BaseAgent import BaseAgent
from .ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel
from .Exceptions import RuleExtractionError, ValidationError

# Import Language Detection System (Phase 15A)
from Utils.language_detection import LanguageDetector, DetectionResult, LanguageDetectionError

# Import Intelligent Chunking System (Phase 15B)  
from Utils.intelligent_chunker import IntelligentChunker, ChunkingResult

# Import Rule Completeness Analyzer (Phase 15C)
from Utils.rule_completeness_analyzer import RuleCompletenessAnalyzer, CompletenessStatus

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
    The process works by taking a legacy code base (one file at a time) and walks through the file
    line by line to pull out business logic from the functional(non-business) logic and formats the business rules
    into a .json output file.  This output file can then be feed to the RuleDocumentationGeneratorAgent which will
    output the rules into a business and user friendly Markdown or HTML file.
    
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

    **Additional Legacy Technologies:**
    - Most structured legacy file types should work.  Feel free to contact me at contact@jeremiahconnelly.dev for any questions 
    or to verify if your specific file type will work with this Micro-Agent
    
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
    
    def __init__(self, audit_system: ComplianceMonitoringAgent, llm_client: Any = None, 
                 agent_id: str = None, log_level: int = 0, model_name: str = None, 
                 llm_provider = None):
        """
        Initialize the BusinessRuleExtractionAgent with BYO-LLM support.

        Args:
            audit_system: An instance of the ComplianceMonitoringAgent for auditing.
            llm_client: (Legacy) An initialized LLM client - deprecated, use llm_provider instead.
            agent_id: Unique identifier for this agent instance.
            log_level: 0 = production (silent), 1 = development (verbose)
            model_name: Name of the LLM model being used (optional, inferred from provider)
            llm_provider: LLM provider instance or provider type string (defaults to Gemini)
        """
        # Initialize base agent with BYO-LLM support
        super().__init__(
            audit_system=audit_system,
            agent_id=agent_id,
            log_level=log_level,
            model_name=model_name,
            llm_provider=llm_provider,
            agent_name="BusinessRuleExtractionAgent"
        )
        
        # Rule extraction specific configuration
        self.llm_client = llm_client
        
        # Initialize Language Detection System (Phase 15A)
        try:
            self.language_detector = LanguageDetector()
            self.logger.debug("Language detection system initialized successfully")
        except LanguageDetectionError as e:
            self.logger.warning(f"Language detection initialization failed: {e}")
            self.language_detector = None
        
        # Initialize Intelligent Chunking System (Phase 15B)
        try:
            self.intelligent_chunker = IntelligentChunker(self.language_detector)
            self.logger.debug("Intelligent chunking system initialized successfully")
        except Exception as e:
            self.logger.warning(f"Intelligent chunker initialization failed: {e}")
            self.intelligent_chunker = None
        
        # Initialize Rule Completeness Analyzer (Phase 15C)
        try:
            self.completeness_analyzer = RuleCompletenessAnalyzer()
            self.logger.debug("Rule completeness analyzer initialized successfully")
        except Exception as e:
            self.logger.warning(f"Completeness analyzer initialization failed: {e}")
            self.completeness_analyzer = None

    # get_ip_address() method now inherited from BaseAgent
    
    def _detect_language_and_get_chunking_params(self, filename: str, content: str) -> Tuple[DetectionResult, Dict[str, Any]]:
        """
        Detect programming language and return appropriate chunking parameters.
        
        Phase 15A: Language Detection & Profile System
        Provides language-aware chunking with ±50% size flexibility.
        
        Args:
            filename: Name of the file being processed
            content: Content of the file
            
        Returns:
            Tuple of (DetectionResult, chunking_parameters)
        """
        # Default chunking parameters (fallback)
        default_params = {
            "preferred_size": 175,
            "min_size": 87,   # -50% flexibility
            "max_size": 262,  # +50% flexibility
            "overlap_size": 25
        }
        
        if not self.language_detector:
            self.logger.debug("Language detector not available, using default chunking parameters")
            return None, default_params
        
        try:
            # Detect programming language
            detection_result = self.language_detector.detect_language(filename, content)
            
            self.logger.info(f"Language detection: {detection_result.language} "
                           f"(confidence: {detection_result.confidence:.1%})")
            
            # Log detection evidence for debugging
            if detection_result.evidence:
                strong_patterns = len(detection_result.evidence.get('pattern_matches', {}).get('strong', []))
                rule_patterns = sum(match['matches'] for match in 
                                  detection_result.evidence.get('pattern_matches', {}).get('rules', []))
                self.logger.debug(f"Detection evidence: {strong_patterns} strong patterns, "
                                f"{rule_patterns} rule patterns")
            
            # Get language-specific chunking parameters
            if detection_result.profile and detection_result.is_confident:
                chunking_config = detection_result.profile.chunking
                language_params = {
                    "preferred_size": chunking_config.get('preferred_size', 175),
                    "min_size": chunking_config.get('min_size', 87),
                    "max_size": chunking_config.get('max_size', 262),
                    "overlap_size": chunking_config.get('overlap_size', 25),
                    "section_priority": chunking_config.get('section_priority', {}),
                    "language": detection_result.language
                }
                
                self.logger.info(f"Using {detection_result.language}-specific chunking: "
                               f"size={language_params['preferred_size']} "
                               f"(range: {language_params['min_size']}-{language_params['max_size']})")
                
                return detection_result, language_params
            else:
                self.logger.warning(f"Low confidence language detection ({detection_result.confidence:.1%}), "
                                  f"using default chunking parameters")
                for recommendation in detection_result.recommendations:
                    self.logger.info(f"Recommendation: {recommendation}")
                
                return detection_result, default_params
                
        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return None, default_params

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
    
    async def _make_api_call_async(self, prompt: str) -> Dict[str, Any]:
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
        
    def _chunk_large_file(self, content: str, chunk_size: int = None, overlap_size: int = None, chunking_params: Dict[str, Any] = None, filename: str = "unknown.txt") -> List[str]:
        """
        Enterprise-grade chunking strategy for large files with language-aware processing.
        
        Phase 15A Enhancement: Uses language detection for optimal chunking parameters.
        
        Args:
            content: The full file content as a string
            chunk_size: Number of lines per chunk (uses language-specific config if None)
            overlap_size: Number of overlapping lines between chunks (uses language-specific config if None)
            chunking_params: Language-specific chunking parameters from detection system
            filename: Name of file being processed for language detection
            
        Returns:
            List of chunks, each containing context + chunk content optimized for detected language
        """
        # Phase 15A: Language-aware chunking parameter selection
        if not chunking_params:
            # Perform language detection if parameters not provided
            detection_result, chunking_params = self._detect_language_and_get_chunking_params(filename, content)
        
        # Use language-specific parameters or fallback to configuration
        processing_config = self.agent_config.get('processing_limits', {})
        chunk_size = chunk_size or chunking_params.get('preferred_size', processing_config.get('chunking_line_threshold', 175))
        overlap_size = overlap_size or chunking_params.get('overlap_size', processing_config.get('chunk_overlap_size', 25))
        
        # Get language-specific constraints
        MIN_CHUNK_SIZE = chunking_params.get('min_size', processing_config.get('min_chunk_lines', 10))
        MAX_CHUNK_SIZE = chunking_params.get('max_size', chunk_size * 2)
        MAX_CHUNKS = processing_config.get('max_file_chunks', 50)
        
        # Log language-aware chunking decision
        language = chunking_params.get('language', 'unknown')
        if language != 'unknown':
            self.logger.info(f"Using {language}-optimized chunking: size={chunk_size} "
                           f"(range: {MIN_CHUNK_SIZE}-{MAX_CHUNK_SIZE}), overlap={overlap_size}")
        
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
    
    def _process_file_chunks(self, legacy_code_snippet: str, context: Optional[str], request_id: str, filename: str = "unknown.txt") -> tuple[List[Dict], int, int, str]:
        """
        Process large files using chunked approach with progress tracking.
        
        Phase 15A Enhancement: Uses language-aware chunking for optimal rule extraction.
        
        Returns:
            Tuple of (extracted_rules, tokens_input, tokens_output, llm_response_raw)
        """
        # Phase 15B: Intelligent chunking replaces fixed-size chunking
        if self.intelligent_chunker:
            self.logger.info("Using intelligent section-aware chunking for optimal rule extraction")
            chunking_result = self.intelligent_chunker.chunk_content(legacy_code_snippet, filename)
            chunks = chunking_result.chunks
            # Store chunking result for completeness analysis
            self._last_chunking_result = chunking_result
            
            # Log intelligent chunking results
            self.logger.info(f"Intelligent chunking: {chunking_result.language} language detected")
            self.logger.info(f"Strategy used: {chunking_result.strategy_used.value}")
            self.logger.info(f"Created {chunking_result.chunk_count} optimized chunks")
            self.logger.info(f"Average chunk size: {chunking_result.average_chunk_size:.1f} lines")
            self.logger.info(f"Estimated rule coverage: {chunking_result.estimated_rule_coverage:.1%}")
        else:
            # Fallback to legacy chunking if intelligent chunker unavailable
            self.logger.warning("Intelligent chunker unavailable, falling back to legacy chunking")
            detection_result, chunking_params = self._detect_language_and_get_chunking_params(filename, legacy_code_snippet)
            chunks = self._chunk_large_file(legacy_code_snippet, chunking_params=chunking_params, filename=filename)
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
                
                # Phase 15C: Real-time completeness monitoring
                if self.completeness_analyzer and hasattr(self, '_enable_realtime_monitoring'):
                    self._monitor_extraction_progress(all_rules, chunk_idx + 1, len(chunks), request_id)
                
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
    
    def _process_single_file(self, legacy_code_snippet: str, context: Optional[str], request_id: str, filename: str = "unknown.txt") -> tuple[List[Dict], int, int, str]:
        """
        Process small files using single-pass approach with language detection.
        
        Phase 15A Enhancement: Includes language detection for consistency.
        
        Returns:
            Tuple of (extracted_rules, tokens_input, tokens_output, llm_response_raw)
        """
        # Phase 15A: Language detection for single files (informational)
        if self.language_detector:
            try:
                detection_result = self.language_detector.detect_language(filename, legacy_code_snippet)
                self.logger.info(f"Single file language detection: {detection_result.language} "
                               f"(confidence: {detection_result.confidence:.1%})")
            except Exception as e:
                self.logger.debug(f"Language detection failed for single file: {e}")
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
    
    def _monitor_extraction_progress(self, current_rules: List[Dict], chunks_processed: int, total_chunks: int, request_id: str) -> None:
        """
        Monitor extraction progress in real-time with completeness analysis.
        
        Phase 15C: Provides real-time feedback on extraction completeness.
        """
        if not self.completeness_analyzer:
            return
        
        # Estimate expected total rules (simplified for real-time monitoring)
        expected_total = 24  # Known from COBOL analysis - could be made dynamic
        
        # Create progress data for monitoring
        chunk_results = [current_rules]  # Simplified - in real implementation, would track per-chunk
        
        try:
            progress = self.completeness_analyzer.monitor_extraction_progress(
                chunk_results=chunk_results,
                expected_total=expected_total
            )
            
            current_count = len(current_rules)
            progress_pct = progress['progress_percentage']
            
            # Log progress with completeness context
            self.logger.progress(f"Extracted {current_count} rules so far ({progress_pct:.1f}% of expected)", request_id=request_id)
            
            # Issue warnings if below thresholds
            for warning in progress['warnings']:
                if warning['level'] == 'critical':
                    self.logger.warning(f"COMPLETENESS CRITICAL: {warning['message']}", request_id=request_id)
                    self.logger.warning(f"Recommendation: {warning['recommendation']}", request_id=request_id)
                elif warning['level'] == 'warning':
                    self.logger.warning(f"COMPLETENESS WARNING: {warning['message']}", request_id=request_id)
                    self.logger.info(f"Recommendation: {warning['recommendation']}", request_id=request_id)
            
            # Positive feedback when approaching/achieving target
            if progress_pct >= 90 and progress_pct < 95:
                self.logger.progress(f"EXCELLENT: Approaching completeness target ({progress_pct:.1f}%)", request_id=request_id)
            elif progress_pct >= 95:
                self.logger.progress(f"OUTSTANDING: Exceeding completeness target ({progress_pct:.1f}%)", request_id=request_id)
            
        except Exception as e:
            self.logger.debug(f"Progress monitoring failed: {e}", request_id=request_id)
    
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

    def extract_and_translate_rules(self, legacy_code_snippet: str, context: Optional[str] = None, audit_level: int = AuditLevel.LEVEL_1.value, filename: str = "unknown.txt") -> Dict[str, Any]:
        """
        Extracts and translates business rules from a legacy code snippet using an LLM,
        with intelligent language-aware chunking and audit logging.

        Phase 15A Enhancement: Automatically detects programming language and uses 
        optimized chunking parameters for better rule extraction accuracy.

        Args:
            legacy_code_snippet: A string containing the legacy code to analyze.
            context: Optional, additional context for the LLM (e.g., system purpose).
            audit_level: An integer representing the desired audit granularity (1-4).
            filename: Name of the file being processed (for language detection).

        Returns:
            A dictionary containing the extracted rules and the audit log.
        """
        request_id = f"rule-ext-{uuid.uuid4().hex}"
        start_time = datetime.datetime.now(datetime.timezone.utc)

        # Validate input parameters using standardized validation
        try:
            parameters = {
                'legacy_code_snippet': legacy_code_snippet,
                'context': context,
                'audit_level': audit_level
            }
            
            validation_rules = {
                'legacy_code_snippet': {
                    'expected_type': str,
                    'required': True,
                    'min_length': 10,
                    'max_length': 1000000,  # 1MB max
                    # No pattern validation for legacy code - it can contain any characters
                },
                'context': {
                    'expected_type': str,
                    'required': False,
                    'max_length': 1000,
                    'pattern': 'safe_string'
                },
                'audit_level': {
                    'expected_type': int,
                    'required': True,
                    'min_value': 0,
                    'max_value': 4,
                    'allowed_values': [0, 1, 2, 3, 4]
                }
            }
            
            validated_params = self.validate_input(
                parameters, 
                validation_rules,
                "business_rule_extraction"
            )
            
            # Use validated parameters
            legacy_code_snippet = validated_params['legacy_code_snippet']
            context = validated_params['context']
            audit_level = validated_params['audit_level']
            
        except Exception as validation_error:
            # Handle validation error with standardized error handling
            error_record = self.handle_error_standardized(
                validation_error,
                "input_parameter_validation",
                request_id=request_id,
                user_context={
                    'code_length': len(legacy_code_snippet) if legacy_code_snippet else 0,
                    'context_provided': context is not None,
                    'audit_level_requested': audit_level
                }
            )
            # Re-raise to prevent processing invalid input
            raise validation_error

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
                    legacy_code_snippet, context, request_id, filename
                )
            else:
                self.logger.info(f"Small file ({line_count} lines). Using single-pass processing...", request_id=request_id)
                extracted_rules, tokens_input, tokens_output, llm_response_raw = self._process_single_file(
                    legacy_code_snippet, context, request_id, filename
                )

        except json.JSONDecodeError as e:
            # Use standardized error handling
            from Utils.error_handling import StandardErrorHandler, StandardErrorContext
            context = StandardErrorContext(
                operation="rule_extraction_json_parsing",
                agent_name=self.__class__.__name__,
                request_id=request_id,
                user_context={
                    "tokens_processed": tokens_input + tokens_output,
                    "rules_extracted": len(extracted_rules)
                },
                system_context={
                    "raw_response_length": len(llm_response_raw) if llm_response_raw else 0,
                    "response_preview": llm_response_raw[:200] if llm_response_raw else "None"
                }
            )
            error_handler = StandardErrorHandler(self.logger, self.audit_system)
            error_record = error_handler.handle_error(e, context)
        except KeyboardInterrupt as e:
            # Use standardized error handling for user interruption
            from Utils.error_handling import StandardErrorHandler, StandardErrorContext
            context = StandardErrorContext(
                operation="rule_extraction_user_interruption", 
                agent_name=self.__class__.__name__,
                request_id=request_id,
                user_context={"rules_extracted_before_interruption": len(extracted_rules)}
            )
            error_handler = StandardErrorHandler(self.logger, self.audit_system)
            error_record = error_handler.handle_error(e, context)
        except TimeoutError as e:
            # Use standardized error handling for timeouts
            from Utils.error_handling import StandardErrorHandler, StandardErrorContext
            context = StandardErrorContext(
                operation="rule_extraction_timeout",
                agent_name=self.__class__.__name__, 
                request_id=request_id,
                system_context={
                    "timeout_duration": self.TOTAL_OPERATION_TIMEOUT,
                    "tokens_processed": tokens_input + tokens_output,
                    "rules_extracted": len(extracted_rules)
                }
            )
            error_handler = StandardErrorHandler(self.logger, self.audit_system)
            error_record = error_handler.handle_error(e, context)
        except Exception as e:
            # Use standardized error handling for unexpected errors
            from Utils.error_handling import StandardErrorHandler, StandardErrorContext
            context = StandardErrorContext(
                operation="rule_extraction_unexpected_error",
                agent_name=self.__class__.__name__,
                request_id=request_id,
                user_context={
                    "tokens_processed": tokens_input + tokens_output,
                    "rules_extracted": len(extracted_rules)
                }
            )
            error_handler = StandardErrorHandler(self.logger, self.audit_system)
            error_record = error_handler.handle_error(e, context)

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

        # Phase 15C: Final completeness analysis
        if self.completeness_analyzer and extracted_rules:
            self._perform_final_completeness_analysis(legacy_code_snippet, extracted_rules, filename, request_id)
        
        # Debug logging to trace the issue
        self.logger.debug(f"Final return - extracted_rules type: {type(extracted_rules)}, length: {len(extracted_rules)}", request_id=request_id)
        
        return {
            "extracted_rules": extracted_rules,
            "audit_log": audit_log_data
        }
    
    def _perform_final_completeness_analysis(self, source_content: str, extracted_rules: List[Dict], 
                                           filename: str, request_id: str) -> None:
        """
        Perform final completeness analysis of extracted business rules.
        
        Phase 15C: Analyzes the completeness of rule extraction and provides
        actionable recommendations for improvement.
        
        Args:
            source_content: Original source code content
            extracted_rules: List of extracted rule dictionaries  
            filename: Name of the file being analyzed
            request_id: Unique request identifier for logging
        """
        try:
            # Get chunking result if available for enhanced analysis
            chunking_result = getattr(self, '_last_chunking_result', None)
            
            # Perform comprehensive completeness analysis
            completeness_report = self.completeness_analyzer.analyze_extraction_completeness(
                source_content=source_content,
                extracted_rules=extracted_rules,
                chunking_result=chunking_result,
                filename=filename
            )
            
            # Log comprehensive completeness results
            self.logger.info(
                f"Completeness Analysis Complete: {completeness_report.total_extracted_rules}/"
                f"{completeness_report.total_expected_rules} rules extracted "
                f"({completeness_report.completeness_percentage:.1f}%) - "
                f"Status: {completeness_report.status.value.upper()}",
                request_id=request_id
            )
            
            # Log target achievement status
            if completeness_report.is_target_achieved:
                self.logger.success(
                    f"SUCCESS: 90% completeness target achieved! "
                    f"({completeness_report.completeness_percentage:.1f}%)",
                    request_id=request_id
                )
            else:
                gap_count = completeness_report.gap_count
                self.logger.warning(
                    f"Target not achieved: {gap_count} rules missing for 90% threshold. "
                    f"Current: {completeness_report.completeness_percentage:.1f}%",
                    request_id=request_id
                )
            
            # Log section-level analysis
            poor_sections = []
            for section_name, analysis in completeness_report.section_analysis.items():
                if analysis['completeness'] < 90:
                    poor_sections.append(f"{section_name} ({analysis['completeness']:.1f}%)")
            
            if poor_sections:
                self.logger.warning(
                    f"Sections below 90% completeness: {', '.join(poor_sections)}",
                    request_id=request_id
                )
            
            # Log key recommendations
            if completeness_report.recommendations:
                self.logger.info(f"Key recommendations:", request_id=request_id)
                for i, recommendation in enumerate(completeness_report.recommendations[:3], 1):
                    self.logger.info(f"  {i}. {recommendation}", request_id=request_id)
            
            # Log rule gaps by category
            if completeness_report.rule_gaps:
                gap_summary = {}
                for gap in completeness_report.rule_gaps:
                    category = gap.category.value
                    gap_summary[category] = gap_summary.get(category, 0) + gap.gap_count
                
                if gap_summary:
                    gap_details = ", ".join([f"{cat}: {count}" for cat, count in gap_summary.items()])
                    self.logger.warning(f"Missing rules by category: {gap_details}", request_id=request_id)
            
            # Store analysis results for external access
            self._last_completeness_report = completeness_report
            
            # Create audit entry for completeness analysis
            self.audit_system.log_activity(
                agent_name="BusinessRuleExtractionAgent",
                activity_type="completeness_analysis",
                details={
                    "filename": filename,
                    "total_expected": completeness_report.total_expected_rules,
                    "total_extracted": completeness_report.total_extracted_rules,
                    "completeness_percentage": completeness_report.completeness_percentage,
                    "status": completeness_report.status.value,
                    "target_achieved": completeness_report.is_target_achieved,
                    "gap_count": completeness_report.gap_count,
                    "processing_time_ms": completeness_report.processing_time_ms,
                    "recommendations_count": len(completeness_report.recommendations)
                },
                request_id=request_id,
                user_id="system",
                session_id="analysis_session",
                ip_address="internal",
                user_agent="BusinessRuleExtractionAgent",
                audit_level=AuditLevel.INFO
            )
            
        except Exception as e:
            self.logger.error(f"Completeness analysis failed: {e}", request_id=request_id)
            # Don't let completeness analysis failure break the main extraction
            import traceback
            self.logger.debug(f"Completeness analysis error details: {traceback.format_exc()}", request_id=request_id)
    
    def get_last_completeness_report(self):
        """
        Get the most recent completeness analysis report.
        
        Returns:
            CompletenessReport object or None if no analysis has been performed
        """
        return getattr(self, '_last_completeness_report', None)
    
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
                "chunked_processing",
                "intelligent_chunking",
                "language_detection",
                "completeness_analysis",
                "real_time_progress_monitoring"
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