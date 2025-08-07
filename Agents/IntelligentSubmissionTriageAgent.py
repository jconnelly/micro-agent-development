import json
import uuid
import datetime
import time
import asyncio
import socket
from typing import Dict, Any, Optional, List

# Import other Agents from current location, change package location if moved
from .AuditingAgent import AgentAuditing, AuditLevel
from .LoggerAgent import AgentLogger
from .PIIScrubbingAgent import PIIScrubbingAgent, PIIContext, MaskingStrategy

class IntelligentSubmissionTriageAgent:
    # Rate limiting and timeout constants
    API_DELAY_SECONDS = 1.0
    MAX_RETRIES = 3
    API_TIMEOUT_SECONDS = 30
    TOTAL_OPERATION_TIMEOUT = 300  # 5 minutes
    
    def __init__(self, llm_client: Any, audit_system: AgentAuditing, agent_id: str = None,
                 log_level: int = 0, model_name: str = "unknown", llm_provider: str = "unknown",
                 enable_pii_scrubbing: bool = True, pii_masking_strategy: MaskingStrategy = MaskingStrategy.TOKENIZE):
        """
        Initializes the IntelligentSubmissionTriageAgent.

        Args:
            llm_client: An initialized LLM client (e.g., OpenAI, LangChain).
            audit_system: An instance of the AgentAuditing class.
            agent_id: Unique identifier for this agent instance.
            log_level: 0 = production (silent), 1 = development (verbose)
            model_name: Name of the LLM model being used (e.g., "gpt-4", "claude-3-sonnet")
            llm_provider: Provider of the LLM (e.g., "openai", "anthropic", "google")
            enable_pii_scrubbing: Whether to enable PII scrubbing before sending to LLM
            pii_masking_strategy: Strategy for masking detected PII
        """
        self.llm_client = llm_client
        self.audit_system = audit_system
        self.agent_id = agent_id if agent_id else f"TriageAgent-{uuid.uuid4().hex[:8]}"
        self.logger = AgentLogger(log_level=log_level, agent_name="SubmissionTriage")
        self.model_name = model_name
        self.llm_provider = llm_provider
        self.agent_name = "Intelligent Submission Triage Agent"
        self.version = "1.0.0"
        self.tools_available = ["document_parser", "rule_engine_checker"] # Example tools the agent might use
        
        # Initialize PII scrubbing agent if enabled
        self.enable_pii_scrubbing = enable_pii_scrubbing
        if self.enable_pii_scrubbing:
            self.pii_scrubber = PIIScrubbingAgent(
                audit_system=audit_system,
                context=PIIContext.FINANCIAL,  # Financial context for loan/credit applications
                log_level=log_level,
                enable_tokenization=(pii_masking_strategy == MaskingStrategy.TOKENIZE)
            )
            self.pii_masking_strategy = pii_masking_strategy
        else:
            self.pii_scrubber = None
            self.pii_masking_strategy = None

    def get_ip_address(self):
        """Get the current machine's IP address."""
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            self.logger.warning("Could not resolve hostname to IP address.")
            return "127.0.0.1"
    
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
                operation_name="triage_exception",
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

    def _api_call_with_retry(self, submission_data: Dict[str, Any], request_id: str):
        """
        Make API call with retry logic, exponential backoff, and timeout handling using asyncio.
        """
        return asyncio.run(self._api_call_with_retry_async(submission_data, request_id))
    
    async def _api_call_with_retry_async(self, submission_data: Dict[str, Any], request_id: str):
        """
        Async API call with retry logic and timeout handling.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                # Use asyncio.wait_for for timeout handling
                response = await asyncio.wait_for(
                    self._make_api_call_async(submission_data, request_id),
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
    
    async def _make_api_call_async(self, submission_data: Dict[str, Any], request_id: str):
        """
        Make the actual API call in a thread pool to avoid blocking.
        This is a placeholder for the real LLM API call.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._mock_llm_call(submission_data, request_id)
        )
    
    def _mock_llm_call(self, submission_data: Dict[str, Any], request_id: str):
        """
        Mock LLM call for demonstration. Replace with actual LLM client call.
        """
        # Mock LLM response for demonstration purposes
        mock_llm_output = {
            "decision": "Escalate to Human",
            "reasoning": "High risk identified due to incomplete financial documentation and unusual transaction patterns, requiring human review.",
            "category": "High Risk Loan Application",
            "risk_score": 0.85
        }
        return {
            "response": json.dumps(mock_llm_output),
            "tokens_input": 150,  # Mock token count
            "tokens_output": 50   # Mock token count
        }

    def _prepare_llm_prompt(self, submission_data: Dict[str, Any]) -> tuple[str, str]:
        """
        Prepares the system and user prompts for the LLM based on the submission data.
        """
        # Example: Extracting relevant fields for the LLM prompt
        submission_summary = submission_data.get("summary", "No summary provided.")
        submission_type = submission_data.get("type", "General")
        user_context = submission_data.get("user_context", {})

        system_prompt = (
            f"You are an intelligent submission triage agent. Your task is to analyze "
            f"incoming {submission_type} submissions and categorize them, identify key risks, "
            f"and suggest a preliminary action (e.g., 'Approve', 'Reject', 'Escalate to Human'). "
            f"Be concise and output your decision in a structured JSON format."
        )
        user_prompt = (
            f"Analyze the following submission:\n\n"
            f"Submission ID: {submission_data.get('id', 'N/A')}\n"
            f"Submission Content: {submission_data.get('content', 'N/A')}\n"
            f"Summary: {submission_summary}\n"
            f"User Context: {json.dumps(user_context)}\n\n"
            f"Based on this, what is the triage decision and reasoning? "
            f"Provide output in JSON: {{'decision': '...', 'reasoning': '...', 'category': '...', 'risk_score': '...'}}"
        )
        return system_prompt, user_prompt

    def _setup_request_context(self, submission_data: Dict[str, Any]) -> tuple[str, datetime.datetime, str, str, str]:
        """
        Set up request context including ID, timestamps, and user information.
        
        Returns:
            Tuple of (request_id, start_time, user_id, session_id, ip_address)
        """
        request_id = f"req-{uuid.uuid4().hex}"
        start_time = datetime.datetime.now(datetime.timezone.utc)
        user_id = submission_data.get("user_id", "anonymous")
        session_id = submission_data.get("session_id", request_id)
        ip_address = submission_data.get("ip_address", "N/A")
        
        return request_id, start_time, user_id, session_id, ip_address
    
    def _apply_pii_scrubbing(self, submission_data: Dict[str, Any], request_id: str, audit_level: int) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Apply PII scrubbing if enabled and configured.
        
        Returns:
            Tuple of (scrubbed_data, pii_scrubbing_result)
        """
        scrubbed_submission_data = submission_data
        pii_scrubbing_result = None
        
        if self.enable_pii_scrubbing and self.pii_scrubber:
            self.logger.info(f"Applying PII scrubbing to submission data", request_id=request_id)
            try:
                pii_scrubbing_result = self.pii_scrubber.scrub_data(
                    data=submission_data,
                    request_id=f"{request_id}_pii",
                    custom_strategy=self.pii_masking_strategy,
                    audit_level=min(audit_level, 2)  # Limit PII audit verbosity
                )
                scrubbed_submission_data = pii_scrubbing_result['scrubbed_data']
                self.logger.info(f"PII scrubbing completed. Detected {len(pii_scrubbing_result['pii_detected'])} PII types", request_id=request_id)
            except Exception as e:
                self.logger.error(f"PII scrubbing failed: {str(e)}", request_id=request_id, exception=e)
                # Continue with original data but log the failure
                scrubbed_submission_data = submission_data
        
        return scrubbed_submission_data, pii_scrubbing_result
    
    def _call_llm_with_error_handling(self, submission_data: Dict[str, Any], scrubbed_data: Dict[str, Any], request_id: str) -> tuple[Dict[str, Any], str, int, int, List[Dict], List[Dict]]:
        """
        Call LLM with comprehensive error handling and tool integration.
        
        Returns:
            Tuple of (triage_decision, llm_response, tokens_input, tokens_output, tool_calls, retrieved_chunks)
        """
        # Prepare LLM prompt using scrubbed data
        system_prompt, user_prompt = self._prepare_llm_prompt(scrubbed_data)
        
        # Initialize defaults
        triage_decision = {"decision": "Error", "reasoning": "LLM call failed"}
        llm_response = None
        tokens_input = 0
        tokens_output = 0
        tool_calls = []  # Temporary placeholder list
        retrieved_chunks = []  # Temporary placeholder list
        
        try:
            # Clear any previous session logs
            self.logger.clear_session_logs()
            
            # Use defensive API call with retry and timeout handling
            self.logger.info(f"Calling LLM for submission ID: {submission_data.get('id', 'N/A')}", request_id=request_id)
            
            # Call LLM with defensive programming
            llm_result = self._api_call_with_retry(submission_data, request_id)
            llm_response = llm_result["response"]
            tokens_input = llm_result["tokens_input"]
            tokens_output = llm_result["tokens_output"]

            # Parse the response
            mock_llm_output = json.loads(llm_response)

            # Handle tool calls
            tool_calls = self._process_tool_calls(mock_llm_output, submission_data, request_id)
            triage_decision = mock_llm_output

        except json.JSONDecodeError as e:
            self._handle_json_decode_error(e, llm_response, tokens_input, tokens_output, submission_data, request_id)
            triage_decision["reasoning"] = "LLM response format error."
        except KeyboardInterrupt as e:
            self._handle_user_interruption(e, submission_data, request_id)
            triage_decision["reasoning"] = "Processing interrupted by user."
        except TimeoutError as e:
            self._handle_timeout_error(e, tokens_input, tokens_output, submission_data, request_id)
            triage_decision["reasoning"] = f"LLM processing timeout: {str(e)}"
        except Exception as e:
            self._handle_unexpected_error(e, tokens_input, tokens_output, submission_data, request_id)
            triage_decision["reasoning"] = f"LLM processing error: {str(e)}"
        
        return triage_decision, llm_response, tokens_input, tokens_output, tool_calls, retrieved_chunks
    
    def _process_tool_calls(self, llm_output: Dict[str, Any], submission_data: Dict[str, Any], request_id: str) -> List[Dict]:
        """
        Process and execute tool calls based on LLM output.
        
        Returns:
            List of tool call results
        """
        tool_calls = []
        
        # Simulate tool calls if the LLM decided to use them
        if llm_output.get("decision") == "Escalate to Human" and "rule_engine_checker" in self.tools_available:
            tool_calls.append({
                "tool_name": "rule_engine_checker",
                "arguments": {"submission_id": submission_data.get('id'), "risk_score": llm_output.get('risk_score')},
                "output": {"status": "Rule check initiated", "result": "Potential fraud flag detected by Rule Engine XYZ"}
            })
            self.logger.info(f"Tool 'rule_engine_checker' invoked.", request_id=request_id)
        
        return tool_calls
    
    def _handle_json_decode_error(self, error: json.JSONDecodeError, llm_response: str, tokens_input: int, tokens_output: int, submission_data: Dict[str, Any], request_id: str) -> None:
        """
        Handle JSON decode errors with proper logging and audit trail.
        """
        error_details = f"LLM response was not valid JSON: {error}. Raw response: {llm_response}"
        self.logger.error(error_details, request_id=request_id, exception=error)
        self._log_exception_to_audit(request_id, error, "JSON_DECODE_ERROR", {
            "raw_response": llm_response[:500] if llm_response else "None",
            "tokens_processed": tokens_input + tokens_output,
            "submission_id": submission_data.get('id', 'N/A')
        })
    
    def _handle_user_interruption(self, error: KeyboardInterrupt, submission_data: Dict[str, Any], request_id: str) -> None:
        """
        Handle user interruption with appropriate logging.
        """
        error_details = f"Processing interrupted by user"
        self.logger.warning(error_details, request_id=request_id)
        self._log_exception_to_audit(request_id, error, "USER_INTERRUPTION", {
            "submission_id": submission_data.get('id', 'N/A'),
            "processing_stage": "triage"
        })
    
    def _handle_timeout_error(self, error: TimeoutError, tokens_input: int, tokens_output: int, submission_data: Dict[str, Any], request_id: str) -> None:
        """
        Handle timeout errors with proper logging and audit trail.
        """
        error_details = f"Operation timed out: {error}"
        self.logger.error(error_details, request_id=request_id, exception=error)
        self._log_exception_to_audit(request_id, error, "TIMEOUT_ERROR", {
            "timeout_duration": self.API_TIMEOUT_SECONDS,
            "tokens_processed": tokens_input + tokens_output,
            "submission_id": submission_data.get('id', 'N/A')
        })
    
    def _handle_unexpected_error(self, error: Exception, tokens_input: int, tokens_output: int, submission_data: Dict[str, Any], request_id: str) -> None:
        """
        Handle unexpected errors with comprehensive logging.
        """
        error_details = f"Unexpected error during triage: {error}"
        self.logger.error(error_details, request_id=request_id, exception=error)
        self._log_exception_to_audit(request_id, error, "UNEXPECTED_ERROR", {
            "exception_type": type(error).__name__,
            "tokens_processed": tokens_input + tokens_output,
            "submission_id": submission_data.get('id', 'N/A'),
            "processing_stage": "triage"
        })
    
    def _create_final_audit_entry(self, request_id: str, user_id: str, session_id: str, scrubbed_data: Dict[str, Any], 
                                  triage_decision: Dict[str, Any], llm_response: str, tokens_input: int, tokens_output: int, 
                                  tool_calls: List[Dict], retrieved_chunks: List[Dict], duration_ms: float, audit_level: int) -> Dict[str, Any]:
        """
        Create the final audit entry with all processing information.
        
        Returns:
            Audit log data dictionary
        """
        llm_input_data = {
            "system_prompt": self._prepare_llm_prompt(scrubbed_data)[0],
            "user_prompt": self._prepare_llm_prompt(scrubbed_data)[1],
            "model_name": self.model_name,
            "llm_provider": self.llm_provider
        }
        
        logger_session_summary = self.logger.create_audit_summary(
            operation_name="submission_triage",
            request_id=request_id,
            status="SUCCESS" if triage_decision.get("decision") != "Error" else "FAILED",
            decision=triage_decision.get("decision"),
            risk_score=triage_decision.get("risk_score"),
            submission_id=scrubbed_data.get('id', 'N/A'),
            tokens_processed=tokens_input + tokens_output,
            processing_duration_ms=duration_ms
        )
        
        audit_log_data = self.audit_system.log_agent_activity(
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            ip_address=self.get_ip_address(),
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.version,
            step_type="LLM_Triage",
            llm_model_name=self.model_name,
            llm_provider=self.llm_provider,
            llm_input=llm_input_data,
            llm_output=llm_response,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tool_calls=tool_calls,
            retrieved_chunks=retrieved_chunks,
            final_decision={
                "triage_decision": triage_decision,
                "logger_session_summary": logger_session_summary
            },
            duration_ms=duration_ms,
            error_details=triage_decision.get("reasoning") if triage_decision.get("decision") == "Error" else None,
            audit_level=audit_level
        )
        
        return audit_log_data
    
    def _prepare_final_result(self, triage_decision: Dict[str, Any], audit_log_data: Dict[str, Any], pii_scrubbing_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare the final result including PII processing information.
        
        Returns:
            Complete result dictionary
        """
        result = {
            "triage_decision": triage_decision,
            "audit_log": audit_log_data
        }
        
        # Add PII scrubbing information to result
        if pii_scrubbing_result:
            result["pii_processing"] = {
                "enabled": True,
                "pii_types_detected": [t.value for t in pii_scrubbing_result['pii_detected']],
                "masking_strategy": self.pii_masking_strategy.value,
                "scrubbing_summary": pii_scrubbing_result['scrubbing_summary']
            }
        else:
            result["pii_processing"] = {
                "enabled": self.enable_pii_scrubbing,
                "pii_types_detected": [],
                "masking_strategy": self.pii_masking_strategy.value if self.pii_masking_strategy else None,
                "scrubbing_summary": None
            }
        
        return result

    def triage_submission(self, submission_data: Dict[str, Any], audit_level: int = AuditLevel.LEVEL_1.value) -> Dict[str, Any]:
        """
        Processes an incoming submission using an LLM and logs the process based on audit_level.

        Args:
            submission_data: A dictionary containing the submission details.
            audit_level: An integer representing the desired audit granularity (1-4).

        Returns:
            A dictionary containing the triage decision and audit log.
        """
        # 1. Setup request context
        request_id, start_time, user_id, session_id, ip_address = self._setup_request_context(submission_data)
        
        # 2. Apply PII scrubbing if enabled
        scrubbed_submission_data, pii_scrubbing_result = self._apply_pii_scrubbing(submission_data, request_id, audit_level)
        
        # 3. Call LLM with comprehensive error handling
        triage_decision, llm_response, tokens_input, tokens_output, tool_calls, retrieved_chunks = self._call_llm_with_error_handling(
            submission_data, scrubbed_submission_data, request_id
        )
        
        # 4. Calculate processing duration
        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # 5. Create final audit entry
        audit_log_data = self._create_final_audit_entry(
            request_id, user_id, session_id, scrubbed_submission_data, triage_decision, 
            llm_response, tokens_input, tokens_output, tool_calls, retrieved_chunks, duration_ms, audit_level
        )
        
        # 6. Prepare and return final result
        return self._prepare_final_result(triage_decision, audit_log_data, pii_scrubbing_result)
