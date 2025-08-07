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

    def triage_submission(self, submission_data: Dict[str, Any], audit_level: int = AuditLevel.LEVEL_1.value) -> Dict[str, Any]:
        """
        Processes an incoming submission using an LLM and logs the process based on audit_level.

        Args:
            submission_data: A dictionary containing the submission details.
            audit_level: An integer representing the desired audit granularity (1-4).

        Returns:
            A dictionary containing the triage decision and audit log.
        """
        request_id = f"req-{uuid.uuid4().hex}"
        start_time = datetime.datetime.now(datetime.timezone.utc)

        user_id = submission_data.get("user_id", "anonymous")
        session_id = submission_data.get("session_id", request_id)
        ip_address = submission_data.get("ip_address", "N/A")

        # 1. Apply PII scrubbing if enabled
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

        # 2. Prepare LLM prompt using scrubbed data
        system_prompt, user_prompt = self._prepare_llm_prompt(scrubbed_submission_data)

        llm_input_data = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "model_name": self.model_name,
            "llm_provider": self.llm_provider
        }

        llm_response = None
        triage_decision = {"decision": "Error", "reasoning": "LLM call failed"}
        tokens_input = 0
        tokens_output = 0
        # tool_calls = # TODO: Define tool_calls structure when tool calling is implemented
        # retrieved_chunks = # TODO: Define retrieved_chunks structure for RAG integration if applicable
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

            # Simulate tool calls if the LLM decided to use them
            # For example, if the LLM output indicated a need to check a rule engine
            if mock_llm_output.get("decision") == "Escalate to Human" and "rule_engine_checker" in self.tools_available:
                tool_calls.append({
                    "tool_name": "rule_engine_checker",
                    "arguments": {"submission_id": submission_data.get('id'), "risk_score": mock_llm_output.get('risk_score')},
                    "output": {"status": "Rule check initiated", "result": "Potential fraud flag detected by Rule Engine XYZ"}
                })
                # This would be a call to a separate business rule engine, e.g., FICO Blaze [1]
                # or a custom rule set [19], which can provide deterministic checks.
                self.logger.info(f"Tool 'rule_engine_checker' invoked.", request_id=request_id)

            triage_decision = mock_llm_output

        except json.JSONDecodeError as e:
            error_details = f"LLM response was not valid JSON: {e}. Raw response: {llm_response}"
            self.logger.error(error_details, request_id=request_id, exception=e)
            # Log processing state to audit trail
            self._log_exception_to_audit(request_id, e, "JSON_DECODE_ERROR", {
                "raw_response": llm_response[:500] if llm_response else "None",
                "tokens_processed": tokens_input + tokens_output,
                "submission_id": submission_data.get('id', 'N/A')
            })
            triage_decision["reasoning"] = "LLM response format error."
        except KeyboardInterrupt as e:
            error_details = f"Processing interrupted by user"
            self.logger.warning(error_details, request_id=request_id)
            self._log_exception_to_audit(request_id, e, "USER_INTERRUPTION", {
                "submission_id": submission_data.get('id', 'N/A'),
                "processing_stage": "triage"
            })
            triage_decision["reasoning"] = "Processing interrupted by user."
        except TimeoutError as e:
            error_details = f"Operation timed out: {e}"
            self.logger.error(error_details, request_id=request_id, exception=e)
            self._log_exception_to_audit(request_id, e, "TIMEOUT_ERROR", {
                "timeout_duration": self.API_TIMEOUT_SECONDS,
                "tokens_processed": tokens_input + tokens_output,
                "submission_id": submission_data.get('id', 'N/A')
            })
            triage_decision["reasoning"] = f"LLM processing timeout: {str(e)}"
        except Exception as e:
            error_details = f"Unexpected error during triage: {e}"
            self.logger.error(error_details, request_id=request_id, exception=e)
            self._log_exception_to_audit(request_id, e, "UNEXPECTED_ERROR", {
                "exception_type": type(e).__name__,
                "tokens_processed": tokens_input + tokens_output,
                "submission_id": submission_data.get('id', 'N/A'),
                "processing_stage": "triage"
            })
            triage_decision["reasoning"] = f"LLM processing error: {str(e)}"

        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # 2. Call the AgentAuditing class after the LLM call
        # Include logger session data in the audit
        logger_session_summary = self.logger.create_audit_summary(
            operation_name="submission_triage",
            request_id=request_id,
            status="SUCCESS" if triage_decision.get("decision") != "Error" else "FAILED",
            decision=triage_decision.get("decision"),
            risk_score=triage_decision.get("risk_score"),
            submission_id=submission_data.get('id', 'N/A'),
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

        # Prepare final result with PII information if applicable
        result = {
            "triage_decision": triage_decision,
            "audit_log": audit_log_data
        }
        
        # Add PII scrubbing information to result if PII processing was performed
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
