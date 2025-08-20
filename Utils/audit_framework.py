"""
Standardized Audit Trail Framework for Agent Platform

This module provides comprehensive audit trail management and consistent logging
across all agents, implementing Phase 14 Medium Priority Task #7: Enhance audit
trail consistency.

Key features:
- Standardized audit entry generation and formatting
- Consistent audit levels with business-friendly descriptions
- Integration with error handling and input validation frameworks
- Compliance-ready audit trails for regulatory requirements
- Performance metrics and operation tracking
- Secure audit data handling with PII protection
"""

import json
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict

from Agents.ComplianceMonitoringAgent import AuditLevel


class AuditOperationType(Enum):
    """Standardized operation types for consistent audit classification."""
    # Core business operations
    BUSINESS_RULE_EXTRACTION = "business_rule_extraction"
    APPLICATION_TRIAGE = "application_triage"
    PII_DETECTION = "pii_detection"
    PII_MASKING = "pii_masking"
    DOCUMENT_GENERATION = "document_generation"
    COMPLIANCE_CHECK = "compliance_check"
    
    # System operations
    INPUT_VALIDATION = "input_validation"
    ERROR_HANDLING = "error_handling"
    RESOURCE_MANAGEMENT = "resource_management"
    CONFIGURATION_LOAD = "configuration_load"
    
    # Security operations
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SECURITY_SCAN = "security_scan"
    ACCESS_CONTROL = "access_control"
    
    # Data operations
    DATA_PROCESSING = "data_processing"
    FILE_OPERATION = "file_operation"
    DATABASE_ACCESS = "database_access"
    NETWORK_REQUEST = "network_request"


class AuditSeverity(Enum):
    """Audit severity levels for prioritizing audit entries."""
    ROUTINE = 1        # Normal operations
    NOTABLE = 2        # Significant operations worth tracking
    IMPORTANT = 3      # Important operations requiring attention
    CRITICAL = 4       # Critical operations requiring immediate review


class AuditOutcome(Enum):
    """Standardized outcomes for audit entries."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class AuditMetrics:
    """Performance and operational metrics for audit entries."""
    duration_ms: float = 0.0
    cpu_time_ms: float = 0.0
    memory_used_mb: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    records_processed: int = 0
    files_processed: int = 0
    errors_encountered: int = 0
    retries_attempted: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class StandardAuditEntry:
    """
    Standardized audit entry structure for consistent audit logging.
    
    Provides comprehensive audit information with consistent formatting
    across all agent operations.
    """
    # Core identification
    entry_id: str = field(default_factory=lambda: f"audit_{uuid.uuid4().hex[:12]}")
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Operation details
    operation_type: AuditOperationType = AuditOperationType.DATA_PROCESSING
    operation_name: str = "unknown_operation"
    agent_name: str = "UnknownAgent"
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    severity: AuditSeverity = AuditSeverity.ROUTINE
    
    # Context information
    user_context: Dict[str, Any] = field(default_factory=dict)
    system_context: Dict[str, Any] = field(default_factory=dict)
    business_context: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    metrics: AuditMetrics = field(default_factory=AuditMetrics)
    
    # Results and outcomes
    success: bool = True
    result_summary: str = ""
    error_details: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    
    # Compliance and security
    compliance_flags: List[str] = field(default_factory=list)
    security_flags: List[str] = field(default_factory=list)
    data_classification: str = "internal"
    
    # Additional metadata
    environment: str = "development"
    version: str = "1.0.0"
    correlation_id: Optional[str] = None
    parent_request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit entry to dictionary for logging/serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert audit entry to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def get_legacy_format(self) -> Dict[str, Any]:
        """
        Convert to legacy format for compatibility with existing audit system.
        
        Returns:
            Dictionary in format expected by ComplianceMonitoringAgent
        """
        return {
            'activity_type': self.operation_type.value,
            'activity_data': {
                'operation_name': self.operation_name,
                'agent_name': self.agent_name,
                'outcome': self.outcome.value,
                'severity': self.severity.value,
                'success': self.success,
                'result_summary': self.result_summary,
                'error_details': self.error_details,
                'duration_ms': self.metrics.duration_ms,
                'records_processed': self.metrics.records_processed,
                'user_context': self.user_context,
                'system_context': self.system_context,
                'business_context': self.business_context,
                'compliance_flags': self.compliance_flags,
                'security_flags': self.security_flags
            },
            'request_id': self.request_id,
            'timestamp': self.timestamp,
            'user_id': self.user_context.get('user_id', 'system'),
            'session_id': self.user_context.get('session_id', self.request_id),
            'ip_address': self.user_context.get('ip_address', '127.0.0.1')
        }


class StandardAuditTrail:
    """
    Comprehensive audit trail manager for consistent logging across all agents.
    
    Provides standardized audit entry creation, formatting, and logging with
    integration to existing audit systems.
    """
    
    def __init__(self, 
                 audit_system: Any = None,
                 default_audit_level: int = AuditLevel.LEVEL_2.value,
                 environment: str = "development",
                 version: str = "1.0.0"):
        """
        Initialize audit trail manager.
        
        Args:
            audit_system: Existing audit system (ComplianceMonitoringAgent)
            default_audit_level: Default audit verbosity level
            environment: Current environment (development, staging, production)
            version: Application version for audit entries
        """
        self.audit_system = audit_system
        self.default_audit_level = default_audit_level
        self.environment = environment
        self.version = version
        self.active_operations = {}  # Track ongoing operations
        
        # Operation type to severity mapping
        self.operation_severity_map = {
            AuditOperationType.AUTHENTICATION: AuditSeverity.CRITICAL,
            AuditOperationType.AUTHORIZATION: AuditSeverity.CRITICAL,
            AuditOperationType.SECURITY_SCAN: AuditSeverity.IMPORTANT,
            AuditOperationType.PII_DETECTION: AuditSeverity.IMPORTANT,
            AuditOperationType.PII_MASKING: AuditSeverity.IMPORTANT,
            AuditOperationType.COMPLIANCE_CHECK: AuditSeverity.IMPORTANT,
            AuditOperationType.BUSINESS_RULE_EXTRACTION: AuditSeverity.NOTABLE,
            AuditOperationType.APPLICATION_TRIAGE: AuditSeverity.NOTABLE,
            AuditOperationType.DOCUMENT_GENERATION: AuditSeverity.NOTABLE,
            AuditOperationType.ERROR_HANDLING: AuditSeverity.NOTABLE,
        }
    
    def create_audit_entry(self,
                          operation_type: Union[AuditOperationType, str],
                          operation_name: str,
                          agent_name: str,
                          request_id: str = None,
                          outcome: AuditOutcome = AuditOutcome.SUCCESS,
                          user_context: Dict[str, Any] = None,
                          system_context: Dict[str, Any] = None,
                          business_context: Dict[str, Any] = None,
                          metrics: AuditMetrics = None,
                          **kwargs) -> StandardAuditEntry:
        """
        Create a standardized audit entry with comprehensive information.
        
        Args:
            operation_type: Type of operation being audited
            operation_name: Specific name of the operation
            agent_name: Name of the agent performing the operation
            request_id: Optional request identifier
            outcome: Operation outcome
            user_context: User-related context information
            system_context: System-related context information  
            business_context: Business-related context information
            metrics: Performance and operational metrics
            **kwargs: Additional audit entry fields
            
        Returns:
            Fully populated StandardAuditEntry
        """
        # Convert string operation type to enum
        if isinstance(operation_type, str):
            try:
                operation_type = AuditOperationType(operation_type)
            except ValueError:
                operation_type = AuditOperationType.DATA_PROCESSING
        
        # Determine severity based on operation type
        severity = self.operation_severity_map.get(operation_type, AuditSeverity.ROUTINE)
        
        # Create audit entry with defaults
        audit_entry = StandardAuditEntry(
            request_id=request_id or f"req_{uuid.uuid4().hex[:8]}",
            operation_type=operation_type,
            operation_name=operation_name,
            agent_name=agent_name,
            outcome=outcome,
            severity=severity,
            user_context=user_context or {},
            system_context=system_context or {},
            business_context=business_context or {},
            metrics=metrics or AuditMetrics(),
            environment=self.environment,
            version=self.version,
            **kwargs
        )
        
        # Set success flag based on outcome
        audit_entry.success = outcome in [
            AuditOutcome.SUCCESS, 
            AuditOutcome.PARTIAL_SUCCESS
        ]
        
        return audit_entry
    
    def log_operation_start(self,
                           operation_type: Union[AuditOperationType, str],
                           operation_name: str,
                           agent_name: str,
                           request_id: str = None,
                           user_context: Dict[str, Any] = None,
                           audit_level: int = None) -> str:
        """
        Log the start of an operation and begin tracking.
        
        Args:
            operation_type: Type of operation starting
            operation_name: Specific name of the operation
            agent_name: Name of the agent performing the operation
            request_id: Optional request identifier
            user_context: User-related context information
            audit_level: Audit verbosity level
            
        Returns:
            Request ID for the operation
        """
        request_id = request_id or f"req_{uuid.uuid4().hex[:8]}"
        audit_level = audit_level or self.default_audit_level
        
        # Track operation start
        self.active_operations[request_id] = {
            'operation_type': operation_type,
            'operation_name': operation_name,
            'agent_name': agent_name,
            'start_time': time.time(),
            'user_context': user_context or {},
            'audit_level': audit_level
        }
        
        # Create and log start audit entry (if audit level allows)
        if audit_level >= AuditLevel.LEVEL_3.value:  # Log starts at detailed level
            start_entry = self.create_audit_entry(
                operation_type=operation_type,
                operation_name=f"{operation_name}_start",
                agent_name=agent_name,
                request_id=request_id,
                user_context=user_context,
                system_context={'phase': 'start', 'audit_level': audit_level}
            )
            
            self._log_to_audit_system(start_entry, audit_level)
        
        return request_id
    
    def log_operation_complete(self,
                              request_id: str,
                              outcome: AuditOutcome = AuditOutcome.SUCCESS,
                              result_summary: str = "",
                              error_details: str = None,
                              metrics: AuditMetrics = None,
                              business_context: Dict[str, Any] = None,
                              compliance_flags: List[str] = None,
                              security_flags: List[str] = None) -> StandardAuditEntry:
        """
        Log the completion of a tracked operation.
        
        Args:
            request_id: Request identifier for the operation
            outcome: Final outcome of the operation
            result_summary: Summary of operation results
            error_details: Error details if operation failed
            metrics: Performance and operational metrics
            business_context: Business-related context information
            compliance_flags: Compliance-related flags or violations
            security_flags: Security-related flags or issues
            
        Returns:
            Complete StandardAuditEntry for the operation
        """
        operation_info = self.active_operations.get(request_id, {})
        
        if not operation_info:
            # Create minimal audit entry for unknown operation
            return self.create_audit_entry(
                operation_type=AuditOperationType.DATA_PROCESSING,
                operation_name="unknown_operation_complete",
                agent_name="UnknownAgent",
                request_id=request_id,
                outcome=outcome,
                error_details="Operation not found in active tracking"
            )
        
        # Calculate duration and enhance metrics
        end_time = time.time()
        duration_ms = (end_time - operation_info['start_time']) * 1000
        
        if metrics is None:
            metrics = AuditMetrics()
        metrics.duration_ms = duration_ms
        
        # Create comprehensive completion audit entry
        completion_entry = self.create_audit_entry(
            operation_type=operation_info['operation_type'],
            operation_name=operation_info['operation_name'],
            agent_name=operation_info['agent_name'],
            request_id=request_id,
            outcome=outcome,
            user_context=operation_info['user_context'],
            system_context={'phase': 'complete', 'duration_ms': duration_ms},
            business_context=business_context or {},
            metrics=metrics,
            result_summary=result_summary,
            error_details=error_details,
            compliance_flags=compliance_flags or [],
            security_flags=security_flags or []
        )
        
        # Log to audit system
        audit_level = operation_info.get('audit_level', self.default_audit_level)
        self._log_to_audit_system(completion_entry, audit_level)
        
        # Remove from active tracking
        del self.active_operations[request_id]
        
        return completion_entry
    
    def log_immediate_event(self,
                           operation_type: Union[AuditOperationType, str],
                           operation_name: str,
                           agent_name: str,
                           outcome: AuditOutcome = AuditOutcome.SUCCESS,
                           result_summary: str = "",
                           user_context: Dict[str, Any] = None,
                           system_context: Dict[str, Any] = None,
                           audit_level: int = None,
                           **kwargs) -> StandardAuditEntry:
        """
        Log an immediate event that doesn't require start/complete tracking.
        
        Args:
            operation_type: Type of operation/event
            operation_name: Specific name of the operation/event
            agent_name: Name of the agent performing the operation
            outcome: Outcome of the event
            result_summary: Summary of event results
            user_context: User-related context information
            system_context: System-related context information
            audit_level: Audit verbosity level
            **kwargs: Additional audit entry fields
            
        Returns:
            StandardAuditEntry for the event
        """
        audit_level = audit_level or self.default_audit_level
        
        # Create immediate audit entry
        event_entry = self.create_audit_entry(
            operation_type=operation_type,
            operation_name=operation_name,
            agent_name=agent_name,
            outcome=outcome,
            result_summary=result_summary,
            user_context=user_context or {},
            system_context=system_context or {},
            **kwargs
        )
        
        # Log to audit system
        self._log_to_audit_system(event_entry, audit_level)
        
        return event_entry
    
    def _log_to_audit_system(self, audit_entry: StandardAuditEntry, audit_level: int) -> None:
        """
        Log audit entry to the underlying audit system.
        
        Args:
            audit_entry: Standardized audit entry to log
            audit_level: Audit verbosity level
        """
        if not self.audit_system or not hasattr(self.audit_system, 'log_agent_activity'):
            return
        
        try:
            # Convert to legacy format and log
            legacy_format = audit_entry.get_legacy_format()
            legacy_format['audit_level'] = audit_level
            
            self.audit_system.log_agent_activity(**legacy_format)
            
        except Exception as e:
            # Don't let audit failures break the application
            print(f"Warning: Failed to log audit entry {audit_entry.entry_id}: {e}")
    
    def get_active_operations(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active operations being tracked."""
        return self.active_operations.copy()
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """Get summary of audit trail activity."""
        return {
            'active_operations_count': len(self.active_operations),
            'active_operations': list(self.active_operations.keys()),
            'environment': self.environment,
            'version': self.version,
            'default_audit_level': self.default_audit_level
        }


@contextmanager
def audited_operation(audit_trail: StandardAuditTrail,
                     operation_type: Union[AuditOperationType, str],
                     operation_name: str,
                     agent_name: str,
                     user_context: Dict[str, Any] = None,
                     audit_level: int = None):
    """
    Context manager for automatic audit trail logging of operations.
    
    Usage:
        with audited_operation(audit_trail, AuditOperationType.PII_DETECTION, 
                              "detect_ssn", "PersonalDataProtectionAgent") as request_id:
            # Perform operation
            result = detect_pii_in_text(text)
            return result
    """
    request_id = audit_trail.log_operation_start(
        operation_type=operation_type,
        operation_name=operation_name,
        agent_name=agent_name,
        user_context=user_context,
        audit_level=audit_level
    )
    
    start_time = time.time()
    outcome = AuditOutcome.SUCCESS
    error_details = None
    result_summary = "Operation completed successfully"
    
    try:
        yield request_id
    except Exception as e:
        outcome = AuditOutcome.ERROR
        error_details = str(e)
        result_summary = f"Operation failed: {type(e).__name__}"
        raise
    finally:
        # Calculate basic metrics
        duration_ms = (time.time() - start_time) * 1000
        metrics = AuditMetrics(duration_ms=duration_ms)
        
        audit_trail.log_operation_complete(
            request_id=request_id,
            outcome=outcome,
            result_summary=result_summary,
            error_details=error_details,
            metrics=metrics
        )


# Export commonly used components
__all__ = [
    'AuditOperationType',
    'AuditSeverity', 
    'AuditOutcome',
    'AuditMetrics',
    'StandardAuditEntry',
    'StandardAuditTrail',
    'audited_operation'
]