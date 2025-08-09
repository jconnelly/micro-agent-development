"""
Response Formatter - Standardized agent response classes and utilities.

This module provides standardized response formatting for Flask API endpoints,
enabling consistent multi-format output handling across all agents.

Classes:
    AgentOutput: Represents a single output file/format from an agent
    AgentResponse: Complete agent response with primary/secondary outputs and metadata
    ResponseFormatter: Utility class for converting agent results to standardized format
"""

import json
import sys
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
from enum import Enum

# Handle both relative and absolute imports for cross-compatibility
try:
    from .time_utils import TimeUtils
    from .request_utils import RequestIdGenerator
except ImportError:
    # Add parent directory to path for Utils
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from Utils.time_utils import TimeUtils
    from Utils.request_utils import RequestIdGenerator


class OutputFormat(Enum):
    """Supported output formats for agent responses."""
    JSON = "json"
    MARKDOWN = "markdown" 
    HTML = "html"
    JSONL = "jsonl"
    TEXT = "text"
    CSV = "csv"


class ResponseStatus(Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL_SUCCESS = "partial_success"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"


@dataclass
class AgentOutput:
    """
    Represents a single output file/format from an agent.
    
    This class standardizes how agent outputs are represented in API responses,
    supporting multiple formats with embedded content for efficient transmission.
    
    Attributes:
        format: Output format type (json, markdown, html, etc.)
        filename: Suggested filename for saving the content
        content: The actual output content (string or structured data)
        content_type: MIME type for proper HTTP response headers
        size_bytes: Size of the content in bytes
        description: Human-readable description of this output
        metadata: Additional format-specific metadata
    """
    format: str
    filename: str
    content: Union[str, Dict[str, Any], List[Any]]
    content_type: str
    size_bytes: int
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate size_bytes if not provided and validate format."""
        if self.size_bytes == 0:
            if isinstance(self.content, str):
                self.size_bytes = len(self.content.encode('utf-8'))
            else:
                # For structured data, calculate JSON representation size
                self.size_bytes = len(json.dumps(self.content).encode('utf-8'))
        
        # Ensure format is from supported enum
        if isinstance(self.format, str):
            try:
                self.format = OutputFormat(self.format.lower()).value
            except ValueError:
                # Keep original format if not in enum (for extensibility)
                pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def create_json_output(
        cls, 
        content: Union[Dict, List], 
        filename: str = "output.json",
        description: str = "JSON structured data"
    ) -> 'AgentOutput':
        """Create a JSON format output."""
        return cls(
            format=OutputFormat.JSON.value,
            filename=filename,
            content=content,
            content_type="application/json",
            size_bytes=0,  # Will be calculated in __post_init__
            description=description
        )
    
    @classmethod
    def create_markdown_output(
        cls,
        content: str,
        filename: str = "output.md", 
        description: str = "Markdown formatted document"
    ) -> 'AgentOutput':
        """Create a Markdown format output."""
        return cls(
            format=OutputFormat.MARKDOWN.value,
            filename=filename,
            content=content,
            content_type="text/markdown",
            size_bytes=0,  # Will be calculated in __post_init__
            description=description
        )
    
    @classmethod
    def create_html_output(
        cls,
        content: str,
        filename: str = "output.html",
        description: str = "HTML formatted document"
    ) -> 'AgentOutput':
        """Create an HTML format output."""
        return cls(
            format=OutputFormat.HTML.value,
            filename=filename,
            content=content,
            content_type="text/html",
            size_bytes=0,  # Will be calculated in __post_init__
            description=description
        )
    
    @classmethod
    def create_jsonl_output(
        cls,
        content: str,
        filename: str = "output.jsonl",
        description: str = "JSONL audit trail"
    ) -> 'AgentOutput':
        """Create a JSONL format output (typically for audit logs)."""
        return cls(
            format=OutputFormat.JSONL.value,
            filename=filename,
            content=content,
            content_type="application/x-jsonlines",
            size_bytes=0,  # Will be calculated in __post_init__
            description=description
        )


@dataclass
class AgentResponse:
    """
    Complete standardized response from an agent operation.
    
    This class provides a consistent structure for all agent responses,
    supporting multiple output formats and comprehensive metadata for
    enterprise API integration.
    
    Attributes:
        request_id: Unique identifier for tracking this request
        status: Response status (success, error, etc.)
        agent_name: Name of the agent that processed this request
        agent_version: Version of the agent used
        timestamp: When the response was generated (UTC)
        processing_time_ms: Time taken to process the request
        primary_output: Main result from the agent
        secondary_outputs: Additional outputs (documentation, logs, etc.)
        metadata: Additional response metadata
        error: Error information if status indicates failure
        warnings: Non-fatal warnings or notices
    """
    request_id: str
    status: str
    agent_name: str
    agent_version: str
    timestamp: str
    processing_time_ms: float
    primary_output: Optional[AgentOutput]
    secondary_outputs: List[AgentOutput] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate status and set defaults."""
        # Ensure status is from supported enum
        if isinstance(self.status, str):
            try:
                self.status = ResponseStatus(self.status.lower()).value
            except ValueError:
                # Keep original status if not in enum (for extensibility)
                pass
        
        # Ensure timestamp is properly formatted
        if not self.timestamp:
            self.timestamp = TimeUtils.get_current_utc_timestamp().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        
        # Convert AgentOutput objects to dictionaries
        if result['primary_output']:
            result['primary_output'] = result['primary_output']
        
        if result['secondary_outputs']:
            result['secondary_outputs'] = result['secondary_outputs']
        
        return result
    
    def add_secondary_output(self, output: AgentOutput) -> None:
        """Add a secondary output to the response."""
        self.secondary_outputs.append(output)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message to the response."""
        self.warnings.append(warning)
    
    def get_total_output_size(self) -> int:
        """Calculate total size of all outputs in bytes."""
        total_size = 0
        if self.primary_output:
            total_size += self.primary_output.size_bytes
        
        for output in self.secondary_outputs:
            total_size += output.size_bytes
        
        return total_size
    
    def get_output_count(self) -> int:
        """Get total number of outputs (primary + secondary)."""
        count = 1 if self.primary_output else 0
        count += len(self.secondary_outputs)
        return count


class ResponseFormatter:
    """
    Utility class for converting agent results to standardized response format.
    
    This class provides methods to transform various agent output patterns
    into consistent AgentResponse objects for Flask API endpoints.
    """
    
    @staticmethod
    def create_success_response(
        agent_name: str,
        agent_version: str = "1.0.0",
        request_id: str = None,
        processing_time_ms: float = 0,
        primary_output: AgentOutput = None,
        secondary_outputs: List[AgentOutput] = None,
        metadata: Dict[str, Any] = None
    ) -> AgentResponse:
        """Create a successful agent response."""
        if not request_id:
            request_id = RequestIdGenerator.create_request_id("api")
        
        return AgentResponse(
            request_id=request_id,
            status=ResponseStatus.SUCCESS.value,
            agent_name=agent_name,
            agent_version=agent_version,
            timestamp=TimeUtils.get_current_utc_timestamp().isoformat(),
            processing_time_ms=processing_time_ms,
            primary_output=primary_output,
            secondary_outputs=secondary_outputs or [],
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_error_response(
        agent_name: str,
        error_message: str,
        agent_version: str = "1.0.0",
        request_id: str = None,
        processing_time_ms: float = 0,
        status: str = ResponseStatus.ERROR.value,
        metadata: Dict[str, Any] = None
    ) -> AgentResponse:
        """Create an error response."""
        if not request_id:
            request_id = RequestIdGenerator.create_request_id("api")
        
        return AgentResponse(
            request_id=request_id,
            status=status,
            agent_name=agent_name,
            agent_version=agent_version,
            timestamp=TimeUtils.get_current_utc_timestamp().isoformat(),
            processing_time_ms=processing_time_ms,
            primary_output=None,
            secondary_outputs=[],
            metadata=metadata or {},
            error=error_message
        )
    
    @staticmethod
    def format_business_rule_extraction_response(
        agent_result: Dict[str, Any],
        agent_name: str = "BusinessRuleExtractionAgent",
        request_id: str = None,
        processing_time_ms: float = 0
    ) -> AgentResponse:
        """Format BusinessRuleExtractionAgent results into standardized response."""
        try:
            # Extract primary output - the extracted rules
            rules = agent_result.get('extracted_rules', [])
            primary_output = AgentOutput.create_json_output(
                content={"extracted_rules": rules},
                filename="extracted_business_rules.json",
                description="Extracted business rules from legacy code"
            )
            
            secondary_outputs = []
            
            # Add summary if available
            if 'summary' in agent_result:
                summary_output = AgentOutput.create_markdown_output(
                    content=agent_result['summary'],
                    filename="extraction_summary.md",
                    description="Human-readable summary of extraction results"
                )
                secondary_outputs.append(summary_output)
            
            # Add processing metrics as metadata
            metadata = {
                "rules_count": len(rules),
                "source_context": agent_result.get('context', ''),
                "model_used": agent_result.get('model_name', 'unknown')
            }
            
            return ResponseFormatter.create_success_response(
                agent_name=agent_name,
                request_id=request_id,
                processing_time_ms=processing_time_ms,
                primary_output=primary_output,
                secondary_outputs=secondary_outputs,
                metadata=metadata
            )
            
        except Exception as e:
            return ResponseFormatter.create_error_response(
                agent_name=agent_name,
                error_message=f"Failed to format agent response: {str(e)}",
                request_id=request_id,
                processing_time_ms=processing_time_ms
            )
    
    @staticmethod
    def format_documentation_response(
        agent_result: Dict[str, Any],
        agent_name: str = "RuleDocumentationGeneratorAgent",
        request_id: str = None,
        processing_time_ms: float = 0
    ) -> AgentResponse:
        """Format documentation agent results into standardized response."""
        try:
            # Primary output - structured documentation
            doc_data = agent_result.get('documentation', {})
            primary_output = AgentOutput.create_json_output(
                content=doc_data,
                filename="rule_documentation.json",
                description="Structured business rule documentation"
            )
            
            secondary_outputs = []
            
            # Add markdown version if available
            if 'markdown_content' in agent_result:
                md_output = AgentOutput.create_markdown_output(
                    content=agent_result['markdown_content'],
                    filename="business_rules_documentation.md",
                    description="Business-friendly documentation in Markdown format"
                )
                secondary_outputs.append(md_output)
            
            # Add HTML version if available
            if 'html_content' in agent_result:
                html_output = AgentOutput.create_html_output(
                    content=agent_result['html_content'],
                    filename="business_rules_documentation.html",
                    description="Web-ready HTML documentation"
                )
                secondary_outputs.append(html_output)
            
            # Add audit trail if available
            if 'audit_trail' in agent_result:
                audit_output = AgentOutput.create_jsonl_output(
                    content=agent_result['audit_trail'],
                    filename="documentation_audit.jsonl",
                    description="Processing audit trail and compliance log"
                )
                secondary_outputs.append(audit_output)
            
            metadata = {
                "rules_documented": agent_result.get('rule_count', 0),
                "output_formats": len(secondary_outputs) + 1,
                "business_domains": agent_result.get('domains', []),
                "model_used": agent_result.get('model_name', 'unknown')
            }
            
            return ResponseFormatter.create_success_response(
                agent_name=agent_name,
                request_id=request_id,
                processing_time_ms=processing_time_ms,
                primary_output=primary_output,
                secondary_outputs=secondary_outputs,
                metadata=metadata
            )
            
        except Exception as e:
            return ResponseFormatter.create_error_response(
                agent_name=agent_name,
                error_message=f"Failed to format documentation response: {str(e)}",
                request_id=request_id,
                processing_time_ms=processing_time_ms
            )
    
    @staticmethod
    def format_pii_protection_response(
        agent_result: Dict[str, Any],
        agent_name: str = "PersonalDataProtectionAgent",
        request_id: str = None,
        processing_time_ms: float = 0
    ) -> AgentResponse:
        """Format PII protection agent results into standardized response."""
        try:
            # Primary output - scrubbed data with PII information
            pii_result = {
                "scrubbed_text": agent_result.get('scrubbed_text', ''),
                "pii_found": agent_result.get('pii_found', []),
                "masking_strategy": agent_result.get('masking_strategy', 'unknown'),
                "scrubbing_summary": agent_result.get('scrubbing_summary', {})
            }
            
            primary_output = AgentOutput.create_json_output(
                content=pii_result,
                filename="pii_protection_results.json",
                description="PII-protected data with detection summary"
            )
            
            secondary_outputs = []
            
            # Add audit trail for PII processing
            if 'audit_trail' in agent_result:
                audit_output = AgentOutput.create_jsonl_output(
                    content=agent_result['audit_trail'],
                    filename="pii_processing_audit.jsonl",
                    description="PII processing audit trail for compliance"
                )
                secondary_outputs.append(audit_output)
            
            metadata = {
                "pii_types_detected": len(agent_result.get('pii_found', [])),
                "protection_level": agent_result.get('masking_strategy', 'unknown'),
                "compliance_flags": agent_result.get('compliance_flags', []),
                "processing_statistics": agent_result.get('stats', {})
            }
            
            return ResponseFormatter.create_success_response(
                agent_name=agent_name,
                request_id=request_id,
                processing_time_ms=processing_time_ms,
                primary_output=primary_output,
                secondary_outputs=secondary_outputs,
                metadata=metadata
            )
            
        except Exception as e:
            return ResponseFormatter.create_error_response(
                agent_name=agent_name,
                error_message=f"Failed to format PII protection response: {str(e)}",
                request_id=request_id,
                processing_time_ms=processing_time_ms
            )
    
    @staticmethod
    def format_generic_agent_response(
        agent_result: Dict[str, Any],
        agent_name: str,
        primary_output_key: str = "result",
        primary_filename: str = "output.json",
        request_id: str = None,
        processing_time_ms: float = 0
    ) -> AgentResponse:
        """Generic formatter for any agent response following standard patterns."""
        try:
            # Extract primary output
            primary_content = agent_result.get(primary_output_key, agent_result)
            primary_output = AgentOutput.create_json_output(
                content=primary_content,
                filename=primary_filename,
                description=f"Results from {agent_name}"
            )
            
            secondary_outputs = []
            
            # Common secondary outputs
            for key, format_info in [
                ('summary', ('markdown', 'summary.md', 'Processing summary')),
                ('report', ('markdown', 'report.md', 'Detailed report')),
                ('audit_trail', ('jsonl', 'audit.jsonl', 'Processing audit trail')),
                ('logs', ('jsonl', 'logs.jsonl', 'Processing logs'))
            ]:
                if key in agent_result:
                    format_type, filename, description = format_info
                    if format_type == 'markdown':
                        output = AgentOutput.create_markdown_output(
                            content=agent_result[key],
                            filename=filename,
                            description=description
                        )
                    elif format_type == 'jsonl':
                        output = AgentOutput.create_jsonl_output(
                            content=agent_result[key],
                            filename=filename,
                            description=description
                        )
                    secondary_outputs.append(output)
            
            metadata = {
                "model_used": agent_result.get('model_name', 'unknown'),
                "processing_context": agent_result.get('context', ''),
                "additional_info": {k: v for k, v in agent_result.items() 
                                 if k not in [primary_output_key, 'summary', 'report', 'audit_trail', 'logs']}
            }
            
            return ResponseFormatter.create_success_response(
                agent_name=agent_name,
                request_id=request_id,
                processing_time_ms=processing_time_ms,
                primary_output=primary_output,
                secondary_outputs=secondary_outputs,
                metadata=metadata
            )
            
        except Exception as e:
            return ResponseFormatter.create_error_response(
                agent_name=agent_name,
                error_message=f"Failed to format generic agent response: {str(e)}",
                request_id=request_id,
                processing_time_ms=processing_time_ms
            )


# Convenience function for quick response creation
def create_api_response(
    agent_result: Dict[str, Any],
    agent_name: str,
    request_id: str = None,
    processing_time_ms: float = 0,
    formatter_method: str = "generic"
) -> Dict[str, Any]:
    """
    Convenience function to create standardized API responses.
    
    Args:
        agent_result: Result dictionary from agent processing
        agent_name: Name of the agent that processed the request
        request_id: Optional request ID for tracking
        processing_time_ms: Time taken to process the request
        formatter_method: Specific formatter to use (business_rule_extraction, 
                         documentation, pii_protection, or generic)
    
    Returns:
        Dictionary ready for JSON serialization in Flask response
    """
    if formatter_method == "business_rule_extraction":
        response = ResponseFormatter.format_business_rule_extraction_response(
            agent_result, agent_name, request_id, processing_time_ms
        )
    elif formatter_method == "documentation":
        response = ResponseFormatter.format_documentation_response(
            agent_result, agent_name, request_id, processing_time_ms
        )
    elif formatter_method == "pii_protection":
        response = ResponseFormatter.format_pii_protection_response(
            agent_result, agent_name, request_id, processing_time_ms
        )
    else:
        response = ResponseFormatter.format_generic_agent_response(
            agent_result, agent_name, request_id=request_id, 
            processing_time_ms=processing_time_ms
        )
    
    return response.to_dict()