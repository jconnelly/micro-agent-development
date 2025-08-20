"""
Production Logger for Agent Operations

A lightweight logging class that can be toggled between production (silent) and development modes.
Provides structured logging with different levels and can be easily integrated with existing audit systems.
"""

import datetime
import re
from typing import Optional, Any, Dict


class AgentLogger:
    """
    Simple production logger with on/off switch.
    
    Logging levels:
    0 = OFF (production mode - no console output)
    1 = ON (development mode - all messages to console)
    """
    
    def __init__(self, log_level: int = 0, agent_name: str = "Agent", config: Dict[str, Any] = None) -> None:
        """
        Initialize the logger.
        
        Args:
            log_level: 0 = OFF (production), 1 = ON (development)
            agent_name: Name of the agent for log prefixes
            config: Configuration dictionary containing processing_limits settings
        """
        self.log_level = log_level
        self.agent_name = agent_name
        self.session_logs = []  # Store logs in memory for audit trail
        self.config = config or {}
    
    def _sanitize_message(self, message: str) -> str:
        """
        Enhanced sanitization to prevent comprehensive log injection attacks.
        Removes control characters, escape sequences, injection patterns, and other dangerous content.
        """
        if not isinstance(message, str):
            message = str(message)
        
        # Remove all control characters (including null bytes, backspace, etc.)
        message = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', message)
        
        # Remove ANSI escape sequences (color codes, cursor movement, etc.)
        message = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', message)
        
        # Remove log injection patterns that could confuse log parsers
        injection_patterns = [
            r'%[0-9a-fA-F]{2}',              # URL encoded characters
            r'\\[nrtfbav\\]',                # Escape sequences
            r'\$\{[^}]*\}',                  # Variable substitution patterns
            r'<%[^>]*%>',                    # Template injection patterns
            r'\{\{[^}]*\}\}',                # Template engine patterns
            r'javascript:',                   # JavaScript protocol
            r'data:',                        # Data URI scheme
            r'vbscript:',                    # VBScript protocol
            r'<script[^>]*>.*?</script>',    # Script tags
            r'<iframe[^>]*>.*?</iframe>',    # Iframe tags
            r'on\w+\s*=',                    # Event handlers (onclick, onload, etc.)
            r'expression\s*\(',             # CSS expression
            r'eval\s*\(',                   # Eval function
            r'alert\s*\(',                  # Alert function
            r'document\.',                   # Document object access
            r'window\.',                     # Window object access
            r'location\.',                   # Location object access
            r'\.innerHTML',                  # InnerHTML property
            r'\.outerHTML',                  # OuterHTML property
        ]
        
        # Apply each injection pattern filter
        for pattern in injection_patterns:
            message = re.sub(pattern, '[FILTERED]', message, flags=re.IGNORECASE)
        
        # Remove potential SQL injection patterns
        sql_patterns = [
            r"'[^']*';?\s*(union|select|insert|update|delete|drop|create|alter|exec|execute)",
            r'"[^"]*";?\s*(union|select|insert|update|delete|drop|create|alter|exec|execute)',
            r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b.*(\bfrom\b|\binto\b|\bset\b|\bwhere\b)',
            r'--\s',                         # SQL comments
            r'/\*.*?\*/',                    # Multi-line SQL comments
            r'\bor\b\s+\d+\s*=\s*\d+',     # OR 1=1 type injections
            r'\band\b\s+\d+\s*=\s*\d+',    # AND 1=1 type injections
        ]
        
        for pattern in sql_patterns:
            message = re.sub(pattern, '[SQL_FILTERED]', message, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove path traversal attempts
        message = re.sub(r'\.\.[\\/]', '[PATH_FILTERED]', message)
        message = re.sub(r'[\\/]etc[\\/]', '[PATH_FILTERED]', message)
        message = re.sub(r'[\\/]proc[\\/]', '[PATH_FILTERED]', message)
        message = re.sub(r'[\\/]var[\\/]log', '[PATH_FILTERED]', message)
        
        # Remove potential command injection patterns
        command_patterns = [
            r'[;&|`]',                       # Command separators and backticks
            r'\$\([^)]*\)',                  # Command substitution
            r'`[^`]*`',                      # Backtick command execution
            r'\|\s*(cat|ls|ps|id|whoami|uname|pwd|echo|grep|find|which)',  # Piped commands
        ]
        
        for pattern in command_patterns:
            message = re.sub(pattern, '[CMD_FILTERED]', message, flags=re.IGNORECASE)
        
        # Limit message length to prevent log flooding attacks (from config)
        processing_limits = self.config.get('processing_limits', {})
        max_length = processing_limits.get('max_log_message_length', 2000)
        if len(message) > max_length:
            message = message[:max_length] + "... [TRUNCATED_FOR_SECURITY]"
        
        # Replace newlines and carriage returns to prevent log format confusion
        message = message.replace('\n', ' ').replace('\r', ' ')
        
        # Remove excessive whitespace that could be used for obfuscation
        message = re.sub(r'\s+', ' ', message).strip()
        
        return message
    
    def _format_message(self, level: str, message: str, request_id: Optional[str] = None) -> str:
        """Format a log message with timestamp and metadata."""
        # Sanitize the message to prevent injection attacks
        clean_message = self._sanitize_message(message)
        
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        prefix = f"[{timestamp}]"
        
        if request_id:
            # Also sanitize request_id to be safe
            clean_request_id = self._sanitize_message(str(request_id)) if request_id else None
            prefix += f"[{clean_request_id}]"
        
        prefix += f"[{self.agent_name}]"
        
        if level:
            prefix += f"[{level}]"
            
        return f"{prefix} {clean_message}"
    
    def info(self, message: str, request_id: Optional[str] = None, **kwargs) -> None:
        """Log an info message."""
        formatted_msg = self._format_message("INFO", message, request_id)
        
        # Store in session logs for audit trail (with sanitized message)
        log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": "INFO", 
            "message": self._sanitize_message(message),
            "request_id": self._sanitize_message(str(request_id)) if request_id else None,
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
            "message": self._sanitize_message(message),
            "request_id": self._sanitize_message(str(request_id)) if request_id else None,
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
            "message": self._sanitize_message(message),
            "request_id": self._sanitize_message(str(request_id)) if request_id else None,
            "exception": self._sanitize_message(str(exception)) if exception else None,
            "exception_type": type(exception).__name__ if exception else None,
            "metadata": kwargs
        }
        self.session_logs.append(log_entry)
        
        if self.log_level >= 1:
            print(formatted_msg)
            if exception:
                sanitized_exception = self._sanitize_message(str(exception))
                print(f"  Exception: {sanitized_exception}")
    
    def progress(self, message: str, request_id: Optional[str] = None, **kwargs) -> None:
        """Log a progress message (always shown even in production for user feedback)."""
        formatted_msg = self._format_message("", message, request_id)
        
        log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": "PROGRESS",
            "message": self._sanitize_message(message),
            "request_id": self._sanitize_message(str(request_id)) if request_id else None,
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
            "message": self._sanitize_message(message),
            "request_id": self._sanitize_message(str(request_id)) if request_id else None,
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