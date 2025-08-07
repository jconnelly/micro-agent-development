# legacy_rule_extraction_agent.py (Relevant section within the class)

import json
import uuid
import datetime
import socket
import time
import asyncio
from typing import Dict, Any, List, Optional

# Import other Agents from current location, change package location if moved
from .AuditingAgent import AgentAuditing, AuditLevel
from .LoggerAgent import AgentLogger

# Import the Google Generative AI library
import google.generativeai as genai
from google.generativeai import types # For GenerateContentConfig and other types

class LegacyRuleExtractionAgent:
    # Rate limiting constants
    API_DELAY_SECONDS = 1.0
    MAX_RETRIES = 3
    
    # Timeout constants
    API_TIMEOUT_SECONDS = 30
    TOTAL_OPERATION_TIMEOUT = 600  # 10 minutes
    
    def __init__(self, llm_client: Any, audit_system: AgentAuditing, agent_id: str = None, 
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
        self.llm_client = llm_client
        self.audit_system = audit_system
        self.agent_id = agent_id if agent_id else f"RuleExtractorAgent-{uuid.uuid4().hex[:8]}"
        self.logger = AgentLogger(log_level=log_level, agent_name="LegacyRuleExtractor")
        self.model_name = model_name
        self.llm_provider = llm_provider
        self.agent_name = "Legacy Rule Extraction and Translator Agent"
        self.version = "1.0.0"

    # Get IP Address to use for audit trail
    def get_ip_address(self) -> str:
        ip_address = ""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except socket.gaierror:
            self.logger.warning("Could not resolve hostname to IP address.")
        return ip_address

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
            f"""

            """
        )
        if context:
            user_prompt = f"Consider the following context: {context}\n\n" + user_prompt

        return system_prompt, user_prompt
    
    def _extract_file_context(self, lines: List[str], max_lines: int = 50) -> List[str]:
        """
        Extract file context (headers, imports, templates, comments) from the beginning of the file.
        This context will be included with each chunk to provide necessary background.
        """
        context_lines = []
        context_keywords = [
            'import', 'include', '#include', 'using', 'package', 'deftemplate', 
            'entity-engine-xml', '<?xml', 'definitions', 'namespace', 'typedef',
            'class ', 'struct ', 'interface ', 'namespace ', 'module ', 'program ',
            ';; ', '# ', '// ', '/* ', '<!--'
        ]
        
        for i, line in enumerate(lines[:max_lines]):
            line_lower = line.lower().strip()
            
            # Include header comments and metadata
            if (line.strip().startswith((';;', '#', '//', '/*', '<!--')) or
                any(keyword in line_lower for keyword in context_keywords) or
                line_lower.startswith('<?') or
                'deftemplate' in line_lower or
                'entity-engine-xml' in line_lower):
                context_lines.append(line)
        
        return context_lines
    
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
    
    def _log_exception_to_audit(self, request_id: str, exception: Exception, error_type: str, context: dict):
        """
        Log exception details to the audit system with processing context.
        
        Args:
            request_id: The request ID for tracking
            exception: The exception that occurred
            error_type: Type of error for categorization
            context: Additional context about the processing state
        """
        try:
            # Create audit summary with logger session data
            audit_summary = self.logger.create_audit_summary(
                operation_name="rule_extraction_exception",
                request_id=request_id,
                status="FAILED",
                error_type=error_type,
                exception_message=str(exception),
                exception_type=type(exception).__name__,
                processing_context=context
            )
            
            # Log to audit system if available
            if self.audit_system:
                self.audit_system.log_agent_activity(
                    request_id=request_id,
                    user_id="system",
                    session_id=request_id,
                    ip_address=self.get_ip_address(),
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    agent_version=self.version,
                    step_type="EXCEPTION_HANDLING",
                    llm_model_name=self.model_name,
                    llm_provider=self.llm_provider,
                    llm_input={"error_type": error_type},
                    llm_output=audit_summary,
                    tokens_input=0,
                    tokens_output=0,
                    duration_ms=0,
                    success=False,
                    error_message=str(exception),
                    audit_level=1  # Always log exceptions
                )
        except Exception as audit_error:
            # Don't let audit logging failures break the main process
            self.logger.error(f"Failed to log exception to audit trail: {audit_error}", request_id=request_id)
    
    def _api_call_with_retry(self, prompt: str):
        """
        Make API call with retry logic, exponential backoff, and timeout handling using asyncio.
        """
        return asyncio.run(self._api_call_with_retry_async(prompt))
    
    async def _api_call_with_retry_async(self, prompt: str):
        """
        Async API call with retry logic and timeout handling.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                # Use asyncio.wait_for for timeout handling
                response = await asyncio.wait_for(
                    self._make_api_call_async(prompt),
                    timeout=self.API_TIMEOUT_SECONDS
                )
                return response
                
            except asyncio.TimeoutError:
                self.logger.warning(f"API call timed out after {self.API_TIMEOUT_SECONDS} seconds")
                if attempt == self.MAX_RETRIES - 1:
                    raise TimeoutError(f"API call failed after {self.MAX_RETRIES} attempts due to timeouts")
                    
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise e
                
            # Exponential backoff: wait 2^attempt seconds
            wait_time = 2 ** attempt
            self.logger.warning(f"API call failed (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying in {wait_time}s")
            await asyncio.sleep(wait_time)
    
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
            raise ValueError(f"chunk_size ({chunk_size}) must be at least MIN_CHUNK_SIZE + overlap_size ({MIN_CHUNK_SIZE + overlap_size})")
        
        # For small files, return as single chunk
        if total_lines <= chunk_size:
            return [content]
        
        # Estimate chunk count and validate
        estimated_chunks = max(1, (total_lines - overlap_size) // (chunk_size - overlap_size))
        if estimated_chunks > MAX_CHUNKS:
            raise ValueError(f"File too large: would create ~{estimated_chunks} chunks (max {MAX_CHUNKS}). Consider increasing chunk_size or processing manually.")
        
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
            
            # Determine if chunking is needed based on file size
            line_count = len(legacy_code_snippet.split('\n'))
            if line_count > 175:  # Threshold for chunking
                self.logger.info(f"Large file detected ({line_count} lines). Using chunked processing...", request_id=request_id)
                chunks = self._chunk_large_file(legacy_code_snippet)
                
                # Process each chunk with progress tracking
                all_rules = []
                total_tokens_input = 0
                total_tokens_output = 0
                chunk_start_time = time.time()
                
                self.logger.progress(f"Processing {len(chunks)} chunks...", request_id=request_id)
                self.logger.progress("Press Ctrl+C at any time to cancel processing")
                
                for chunk_idx, chunk_content in enumerate(chunks):
                    # Progress indicator
                    progress_percent = (chunk_idx / len(chunks)) * 100
                    elapsed_time = time.time() - chunk_start_time
                    
                    if chunk_idx > 0:
                        avg_time_per_chunk = elapsed_time / chunk_idx
                        estimated_remaining = avg_time_per_chunk * (len(chunks) - chunk_idx)
                        self.logger.progress(f"Processing chunk {chunk_idx + 1}/{len(chunks)} ({progress_percent:.1f}% complete)", request_id=request_id)
                        self.logger.progress(f"Estimated time remaining: {estimated_remaining:.1f} seconds", request_id=request_id)
                    else:
                        self.logger.progress(f"Processing chunk {chunk_idx + 1}/{len(chunks)} (starting...)", request_id=request_id)
                    
                    # Check for timeout
                    if elapsed_time > self.TOTAL_OPERATION_TIMEOUT:
                        self.logger.warning(f"Total operation timeout ({self.TOTAL_OPERATION_TIMEOUT}s) exceeded. Stopping with partial results.", request_id=request_id)
                        break
                    
                    # Prepare prompt for this chunk
                    chunk_system_prompt, chunk_user_prompt = self._prepare_llm_prompt(chunk_content, context)
                    chunk_full_prompt = f"{chunk_system_prompt}\n\n{chunk_user_prompt}"
                    
                    try:
                        # Rate limiting: sleep before API call (except for first chunk)
                        if chunk_idx > 0:
                            time.sleep(self.API_DELAY_SECONDS)
                        
                        # API call with retry logic
                        chunk_response = self._api_call_with_retry(chunk_full_prompt)
                        
                        # Parse chunk response
                        chunk_response_raw = chunk_response.text
                        chunk_response_data = json.loads(chunk_response_raw)
                        
                        # Handle different response formats
                        if isinstance(chunk_response_data, dict) and 'business_rules' in chunk_response_data:
                            chunk_rules = chunk_response_data['business_rules']
                        elif isinstance(chunk_response_data, list):
                            chunk_rules = chunk_response_data
                        else:
                            chunk_rules = chunk_response_data
                        
                        # Add chunk info to rule IDs to prevent duplicates
                        for rule in chunk_rules:
                            if 'rule_id' in rule:
                                rule['rule_id'] = f"chunk{chunk_idx + 1}_{rule['rule_id']}"
                        
                        all_rules.extend(chunk_rules)
                        
                        # Track tokens
                        if chunk_response.usage_metadata:
                            total_tokens_input += chunk_response.usage_metadata.prompt_token_count
                            total_tokens_output += chunk_response.usage_metadata.candidates_token_count
                        
                        self.logger.debug(f"Chunk {chunk_idx + 1} extracted {len(chunk_rules)} rules", request_id=request_id)
                        
                    except KeyboardInterrupt:
                        self.logger.warning(f"Processing interrupted by user. Returning partial results from {chunk_idx} chunks.", request_id=request_id)
                        break
                        
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Chunk {chunk_idx + 1} JSON parse error", request_id=request_id, exception=e)
                        continue
                    except Exception as e:
                        self.logger.error(f"Chunk {chunk_idx + 1} processing error", request_id=request_id, exception=e)
                        continue
                
                # Final progress summary
                total_time = time.time() - chunk_start_time
                self.logger.progress(f"Processing complete!", request_id=request_id)
                self.logger.info(f"Total chunks processed: {len([r for r in all_rules if r])}", request_id=request_id)
                self.logger.info(f"Total rules extracted: {len(all_rules)}", request_id=request_id)
                self.logger.info(f"Total processing time: {total_time:.1f} seconds", request_id=request_id)
                self.logger.info(f"Average time per chunk: {total_time / len(chunks):.1f} seconds", request_id=request_id)
                
                # Combine results
                extracted_rules = all_rules
                self.logger.debug(f"After assignment - all_rules length: {len(all_rules)}, extracted_rules length: {len(extracted_rules)}", request_id=request_id)
                tokens_input = total_tokens_input
                tokens_output = total_tokens_output
                llm_response_raw = f"Processed {len(chunks)} chunks, extracted {len(extracted_rules)} rules"
                
            else:
                self.logger.info(f"Small file ({line_count} lines). Using single-pass processing...", request_id=request_id)
                
                # --- SINGLE-PASS PROCESSING FOR SMALL FILES ---
                system_prompt, user_prompt = self._prepare_llm_prompt(legacy_code_snippet, context)
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = self._api_call_with_retry(full_prompt)

                llm_response_raw = response.text
                
                # Access token usage from usage_metadata
                if response.usage_metadata:
                    tokens_input = response.usage_metadata.prompt_token_count
                    tokens_output = response.usage_metadata.candidates_token_count
                else:
                    self.logger.warning(f"No usage_metadata found in Gemini response.", request_id=request_id)

                # Attempt to parse the JSON response
                response_data = json.loads(llm_response_raw)
                
                # Handle different response formats from Gemini
                if isinstance(response_data, dict) and 'business_rules' in response_data:
                    extracted_rules = response_data['business_rules']
                elif isinstance(response_data, list):
                    extracted_rules = response_data
                else:
                    extracted_rules = response_data

        except json.JSONDecodeError as e:
            error_details = f"LLM response was not valid JSON: {e}. Raw response: {llm_response_raw}"
            self.logger.error(error_details, request_id=request_id, exception=e)
            # Log processing state to audit trail
            self._log_exception_to_audit(request_id, e, "JSON_DECODE_ERROR", {
                "raw_response": llm_response_raw[:500] if llm_response_raw else "None",
                "tokens_processed": tokens_input + tokens_output,
                "rules_extracted_before_error": len(extracted_rules)
            })
        except KeyboardInterrupt as e:
            error_details = f"Processing interrupted by user"
            self.logger.warning(error_details, request_id=request_id)
            # Don't treat user interruption as an error in audit trail
            self._log_exception_to_audit(request_id, e, "USER_INTERRUPTION", {
                "rules_extracted_before_interruption": len(extracted_rules),
                "processing_stage": "rule_extraction"
            })
        except TimeoutError as e:
            error_details = f"Operation timed out: {e}"
            self.logger.error(error_details, request_id=request_id, exception=e)
            self._log_exception_to_audit(request_id, e, "TIMEOUT_ERROR", {
                "timeout_duration": self.TOTAL_OPERATION_TIMEOUT,
                "tokens_processed": tokens_input + tokens_output,
                "rules_extracted_before_timeout": len(extracted_rules)
            })
        except Exception as e:
            error_details = f"Unexpected error during rule extraction: {e}"
            self.logger.error(error_details, request_id=request_id, exception=e)
            self._log_exception_to_audit(request_id, e, "UNEXPECTED_ERROR", {
                "exception_type": type(e).__name__,
                "tokens_processed": tokens_input + tokens_output,
                "rules_extracted_before_error": len(extracted_rules),
                "processing_stage": "rule_extraction"
            })

        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # 2. Call the AgentAuditing class after the LLM call
        # Include logger session data in the audit
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