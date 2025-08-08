"""
Production Logger for Agent Operations

A lightweight logging class that can be toggled between production (silent) and development modes.
Provides structured logging with different levels and can be easily integrated with existing audit systems.
"""

import datetime
from typing import Optional, Any, Dict


class AgentLogger:
    """
    Simple production logger with on/off switch.
    
    Logging levels:
    0 = OFF (production mode - no console output)
    1 = ON (development mode - all messages to console)
    """
    
    def __init__(self, log_level: int = 0, agent_name: str = "Agent"):
        """
        Initialize the logger.
        
        Args:
            log_level: 0 = OFF (production), 1 = ON (development)
            agent_name: Name of the agent for log prefixes
        """
        self.log_level = log_level
        self.agent_name = agent_name
        self.session_logs = []  # Store logs in memory for audit trail
    
    def _format_message(self, level: str, message: str, request_id: Optional[str] = None) -> str:
        """Format a log message with timestamp and metadata."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        prefix = f"[{timestamp}]"
        
        if request_id:
            prefix += f"[{request_id}]"
        
        prefix += f"[{self.agent_name}]"
        
        if level:
            prefix += f"[{level}]"
            
        return f"{prefix} {message}"
    
    def info(self, message: str, request_id: Optional[str] = None, **kwargs) -> None:
        """Log an info message."""
        formatted_msg = self._format_message("INFO", message, request_id)
        
        # Store in session logs for audit trail
        log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": "INFO", 
            "message": message,
            "request_id": request_id,
            "metadata": kwargs
        }
        self.session_logs.append(log_entry)
        
        # Print if logging is enabled
        if self.log_level >= 1:
            print(formatted_msg)
    
    def warning(self, message: str, request_id: Optional[str] = None, **kwargs) -> None:
        """Log a warning message."""
        formatted_msg = self._format_message("WARN", message, request_id)
        
        log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": "WARNING",
            "message": message,
            "request_id": request_id,
            "metadata": kwargs
        }
        self.session_logs.append(log_entry)
        
        if self.log_level >= 1:
            print(formatted_msg)
    
    def error(self, message: str, request_id: Optional[str] = None, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log an error message."""
        formatted_msg = self._format_message("ERROR", message, request_id)
        
        log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": "ERROR",
            "message": message,
            "request_id": request_id,
            "exception": str(exception) if exception else None,
            "exception_type": type(exception).__name__ if exception else None,
            "metadata": kwargs
        }
        self.session_logs.append(log_entry)
        
        if self.log_level >= 1:
            print(formatted_msg)
            if exception:
                print(f"  Exception: {exception}")
    
    def progress(self, message: str, request_id: Optional[str] = None, **kwargs) -> None:
        """Log a progress message (always shown even in production for user feedback)."""
        formatted_msg = self._format_message("", message, request_id)
        
        log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": "PROGRESS",
            "message": message,
            "request_id": request_id,
            "metadata": kwargs
        }
        self.session_logs.append(log_entry)
        
        # Progress messages shown regardless of log level for user experience
        print(formatted_msg)
    
    def debug(self, message: str, request_id: Optional[str] = None, **kwargs) -> None:
        """Log a debug message (only in development mode)."""
        formatted_msg = self._format_message("DEBUG", message, request_id)
        
        log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": "DEBUG",
            "message": message,
            "request_id": request_id,
            "metadata": kwargs
        }
        self.session_logs.append(log_entry)
        
        if self.log_level >= 1:
            print(formatted_msg)
    
    def get_session_logs(self) -> list:
        """Get all logs from the current session for audit trail."""
        return self.session_logs.copy()
    
    def clear_session_logs(self) -> None:
        """Clear session logs (useful between operations)."""
        self.session_logs.clear()
    
    def set_log_level(self, level: int) -> None:
        """Change the logging level at runtime."""
        self.log_level = level
    
    def create_audit_summary(self, operation_name: str, request_id: str, status: str, **metadata) -> Dict[str, Any]:
        """
        Create a comprehensive audit summary for the audit trail.
        
        Args:
            operation_name: Name of the operation being audited
            request_id: Unique request identifier
            status: SUCCESS, FAILED, PARTIAL, etc.
            **metadata: Additional metadata for the audit
            
        Returns:
            Structured audit summary including all session logs
        """
        return {
            "operation_name": operation_name,
            "request_id": request_id,
            "status": status,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "agent_name": self.agent_name,
            "session_logs": self.get_session_logs(),
            "log_count": len(self.session_logs),
            "error_count": len([log for log in self.session_logs if log["level"] == "ERROR"]),
            "warning_count": len([log for log in self.session_logs if log["level"] == "WARNING"]),
            "metadata": metadata
        }