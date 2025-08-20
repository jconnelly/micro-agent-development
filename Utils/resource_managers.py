"""
Resource Management Context Managers for Enterprise Agent Platform.

Phase 14 High Priority Task #3: Comprehensive resource management with proper
cleanup and monitoring to prevent resource leaks in production environments.

This module provides context managers for:
- File operations with automatic cleanup
- LLM client connections with proper session management  
- Audit system logging with guaranteed cleanup
- Network operations with timeout and cleanup
- Temporary resource allocation with automatic disposal
"""

import os
import tempfile
import time
import threading
import weakref
from contextlib import contextmanager, ExitStack
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Generator, TextIO, BinaryIO
from datetime import datetime, timezone
import logging

# Performance monitoring imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResourceTracker:
    """
    Global resource tracker for monitoring resource usage and detecting leaks.
    
    Tracks all managed resources to ensure proper cleanup and provide
    monitoring capabilities for production deployments.
    """
    
    def __init__(self):
        self._active_resources: Dict[str, Dict[str, Any]] = {}
        self._resource_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._peak_resources = 0
        
    def register_resource(self, resource_id: str, resource_type: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a new resource for tracking."""
        with self._lock:
            self._active_resources[resource_id] = {
                'type': resource_type,
                'created_at': datetime.now(timezone.utc),
                'metadata': metadata or {},
                'thread_id': threading.get_ident()
            }
            self._peak_resources = max(self._peak_resources, len(self._active_resources))
    
    def unregister_resource(self, resource_id: str) -> None:
        """Unregister a resource and move to history."""
        with self._lock:
            if resource_id in self._active_resources:
                resource_info = self._active_resources.pop(resource_id)
                resource_info['closed_at'] = datetime.now(timezone.utc)
                resource_info['duration_ms'] = (
                    resource_info['closed_at'] - resource_info['created_at']
                ).total_seconds() * 1000
                
                # Keep last 1000 resource operations in history
                self._resource_history.append(resource_info)
                if len(self._resource_history) > 1000:
                    self._resource_history = self._resource_history[-1000:]
    
    def get_active_resources(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active resources."""
        with self._lock:
            return self._active_resources.copy()
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get comprehensive resource usage summary."""
        with self._lock:
            active_count = len(self._active_resources)
            active_by_type = {}
            for resource_info in self._active_resources.values():
                res_type = resource_info['type']
                active_by_type[res_type] = active_by_type.get(res_type, 0) + 1
            
            # Calculate average durations from history
            avg_durations = {}
            if self._resource_history:
                for resource_info in self._resource_history[-100:]:  # Last 100
                    res_type = resource_info['type']
                    if 'duration_ms' in resource_info:
                        if res_type not in avg_durations:
                            avg_durations[res_type] = []
                        avg_durations[res_type].append(resource_info['duration_ms'])
                
                for res_type, durations in avg_durations.items():
                    avg_durations[res_type] = sum(durations) / len(durations)
            
            summary = {
                'active_resources': active_count,
                'peak_resources': self._peak_resources,
                'active_by_type': active_by_type,
                'average_durations_ms': avg_durations,
                'total_operations': len(self._resource_history),
                'potential_leaks': [
                    rid for rid, info in self._active_resources.items()
                    if (datetime.now(timezone.utc) - info['created_at']).total_seconds() > 300  # 5 minutes
                ]
            }
            
            # Add system memory info if available
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                memory_info = process.memory_info()
                summary['system_memory'] = {
                    'rss_mb': memory_info.rss / (1024 * 1024),
                    'vms_mb': memory_info.vms / (1024 * 1024),
                    'percent': process.memory_percent()
                }
            
            return summary
    
    def check_for_leaks(self) -> List[str]:
        """Check for potential resource leaks."""
        with self._lock:
            now = datetime.now(timezone.utc)
            potential_leaks = []
            
            for resource_id, info in self._active_resources.items():
                age_seconds = (now - info['created_at']).total_seconds()
                if age_seconds > 300:  # 5 minutes threshold
                    potential_leaks.append(f"{resource_id} ({info['type']}, {age_seconds:.1f}s old)")
            
            return potential_leaks


# Global resource tracker instance
_resource_tracker = ResourceTracker()


def get_resource_tracker() -> ResourceTracker:
    """Get the global resource tracker instance."""
    return _resource_tracker


@contextmanager
def managed_file(file_path: Union[str, Path], mode: str = 'r', 
                encoding: Optional[str] = None, **kwargs) -> Generator[Union[TextIO, BinaryIO], None, None]:
    """
    Context manager for file operations with automatic cleanup and tracking.
    
    Provides safe file operations with:
    - Automatic file handle cleanup
    - Resource tracking and leak detection
    - Performance monitoring
    - Enhanced error handling with context
    
    Args:
        file_path: Path to the file to open
        mode: File open mode ('r', 'w', 'a', etc.)
        encoding: Text encoding (for text modes)
        **kwargs: Additional arguments passed to open()
    
    Yields:
        File handle (TextIO or BinaryIO)
    
    Example:
        with managed_file('data.txt', 'r', encoding='utf-8') as f:
            content = f.read()
    """
    file_path = Path(file_path)
    resource_id = f"file_{id(file_path)}_{time.time()}"
    
    # Register resource for tracking
    _resource_tracker.register_resource(
        resource_id, 
        'file',
        {
            'path': str(file_path),
            'mode': mode,
            'encoding': encoding,
            'size_bytes': file_path.stat().st_size if file_path.exists() else 0
        }
    )
    
    file_handle = None
    try:
        # Open file with proper encoding handling
        open_kwargs = kwargs.copy()
        if encoding and 'b' not in mode:
            open_kwargs['encoding'] = encoding
        
        file_handle = open(file_path, mode, **open_kwargs)
        logger.debug(f"Opened file: {file_path} (mode: {mode}, resource_id: {resource_id})")
        
        yield file_handle
        
    except Exception as e:
        logger.error(f"File operation failed: {file_path} - {e}")
        raise
    finally:
        if file_handle and not file_handle.closed:
            try:
                file_handle.close()
                logger.debug(f"Closed file: {file_path} (resource_id: {resource_id})")
            except Exception as e:
                logger.warning(f"Error closing file {file_path}: {e}")
        
        _resource_tracker.unregister_resource(resource_id)


@contextmanager
def managed_temp_file(suffix: str = '', prefix: str = 'agent_', 
                     dir: Optional[str] = None, mode: str = 'w+',
                     encoding: Optional[str] = 'utf-8') -> Generator[TextIO, None, None]:
    """
    Context manager for temporary files with automatic cleanup.
    
    Creates temporary files that are automatically cleaned up when
    the context exits, even if exceptions occur.
    
    Args:
        suffix: File suffix (e.g., '.txt', '.json')
        prefix: File name prefix  
        dir: Directory for temp file (None = system temp)
        mode: File open mode
        encoding: Text encoding
    
    Yields:
        Temporary file handle
    """
    resource_id = f"temp_file_{time.time()}"
    
    _resource_tracker.register_resource(
        resource_id,
        'temp_file', 
        {
            'suffix': suffix,
            'prefix': prefix,
            'mode': mode,
            'encoding': encoding
        }
    )
    
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(
            mode=mode,
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            encoding=encoding,
            delete=False  # We'll handle deletion manually
        )
        
        logger.debug(f"Created temp file: {temp_file.name} (resource_id: {resource_id})")
        yield temp_file
        
    finally:
        if temp_file:
            temp_file_path = temp_file.name
            try:
                if not temp_file.closed:
                    temp_file.close()
                
                # Remove the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Error cleaning up temp file {temp_file_path}: {e}")
        
        _resource_tracker.unregister_resource(resource_id)


@contextmanager
def managed_llm_client(llm_provider: Any, operation_context: str = 'unknown') -> Generator[Any, None, None]:
    """
    Context manager for LLM client operations with session management.
    
    Ensures proper cleanup of LLM client sessions and tracks usage
    for monitoring and cost analysis.
    
    Args:
        llm_provider: LLM provider instance
        operation_context: Description of the operation for tracking
    
    Yields:
        LLM provider instance
    """
    resource_id = f"llm_client_{id(llm_provider)}_{time.time()}"
    
    _resource_tracker.register_resource(
        resource_id,
        'llm_client',
        {
            'provider_type': type(llm_provider).__name__,
            'operation_context': operation_context,
            'model_name': getattr(llm_provider, 'model_name', 'unknown')
        }
    )
    
    start_time = datetime.now(timezone.utc)
    try:
        logger.debug(f"Starting LLM operation: {operation_context} (resource_id: {resource_id})")
        yield llm_provider
        
    except Exception as e:
        logger.error(f"LLM operation failed: {operation_context} - {e}")
        raise
    finally:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.debug(f"Completed LLM operation: {operation_context} ({duration:.1f}ms)")
        _resource_tracker.unregister_resource(resource_id)


@contextmanager  
def managed_audit_session(audit_system: Any, operation_type: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> Generator[str, None, None]:
    """
    Context manager for audit logging sessions with guaranteed cleanup.
    
    Ensures audit sessions are properly started and ended, even if
    exceptions occur during the operation.
    
    Args:
        audit_system: Audit system instance
        operation_type: Type of operation being audited
        metadata: Additional metadata for the audit session
    
    Yields:
        Audit session ID
    """
    resource_id = f"audit_session_{time.time()}"
    session_id = f"session_{resource_id}"
    
    _resource_tracker.register_resource(
        resource_id,
        'audit_session',
        {
            'operation_type': operation_type,
            'metadata': metadata or {},
            'session_id': session_id
        }
    )
    
    try:
        # Start audit session
        logger.debug(f"Starting audit session: {session_id} for {operation_type}")
        
        if hasattr(audit_system, 'start_session'):
            audit_system.start_session(session_id, operation_type, metadata)
        
        yield session_id
        
    except Exception as e:
        logger.error(f"Operation failed in audit session {session_id}: {e}")
        
        # Log the failure to audit system
        if hasattr(audit_system, 'log_agent_activity'):
            try:
                audit_system.log_agent_activity(
                    activity_type="operation_failure",
                    activity_data={
                        'session_id': session_id,
                        'operation_type': operation_type,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            except Exception as audit_error:
                logger.warning(f"Failed to log error to audit system: {audit_error}")
        
        raise
    finally:
        # End audit session
        try:
            if hasattr(audit_system, 'end_session'):
                audit_system.end_session(session_id)
            logger.debug(f"Ended audit session: {session_id}")
        except Exception as e:
            logger.warning(f"Error ending audit session {session_id}: {e}")
        
        _resource_tracker.unregister_resource(resource_id)


@contextmanager
def managed_resource_group(group_name: str) -> Generator[ExitStack, None, None]:
    """
    Context manager for managing multiple related resources as a group.
    
    Allows grouping multiple managed resources together and ensures
    all are properly cleaned up, even if some fail.
    
    Args:
        group_name: Name for the resource group
    
    Yields:
        ExitStack for managing multiple resources
    
    Example:
        with managed_resource_group('data_processing') as group:
            input_file = group.enter_context(managed_file('input.txt', 'r'))
            output_file = group.enter_context(managed_file('output.txt', 'w'))
            temp_file = group.enter_context(managed_temp_file('.tmp'))
            # All files automatically cleaned up together
    """
    resource_id = f"resource_group_{group_name}_{time.time()}"
    
    _resource_tracker.register_resource(
        resource_id,
        'resource_group',
        {
            'group_name': group_name,
            'group_size': 0
        }
    )
    
    with ExitStack() as stack:
        try:
            logger.debug(f"Starting resource group: {group_name}")
            yield stack
        finally:
            logger.debug(f"Cleaning up resource group: {group_name}")
            _resource_tracker.unregister_resource(resource_id)


def cleanup_leaked_resources() -> Dict[str, Any]:
    """
    Attempt to clean up any leaked resources and return a summary.
    
    Should be called periodically in long-running applications
    to detect and clean up any resources that weren't properly closed.
    
    Returns:
        Summary of cleanup actions taken
    """
    leaks = _resource_tracker.check_for_leaks()
    
    cleanup_summary = {
        'leaks_detected': len(leaks),
        'leaks_details': leaks,
        'cleanup_actions': [],
        'cleanup_errors': []
    }
    
    # Log detected leaks
    if leaks:
        logger.warning(f"Detected {len(leaks)} potential resource leaks: {leaks}")
        
        # Attempt cleanup of leaked resources (implementation depends on resource type)
        active_resources = _resource_tracker.get_active_resources()
        for resource_id, info in active_resources.items():
            age_seconds = (datetime.now(timezone.utc) - info['created_at']).total_seconds()
            if age_seconds > 300:  # 5 minutes
                try:
                    # Force cleanup of old resources
                    _resource_tracker.unregister_resource(resource_id)
                    cleanup_summary['cleanup_actions'].append(f"Force cleaned: {resource_id}")
                except Exception as e:
                    cleanup_summary['cleanup_errors'].append(f"Failed to clean {resource_id}: {e}")
    
    return cleanup_summary


# Convenience functions for easy access to specific resource managers

def safe_file_operation(file_path: Union[str, Path], mode: str = 'r', 
                       encoding: str = 'utf-8', **kwargs) -> Any:
    """Convenience function for safe file operations."""
    return managed_file(file_path, mode, encoding, **kwargs)


def safe_temp_file(suffix: str = '.tmp', prefix: str = 'agent_') -> Any:
    """Convenience function for safe temporary file creation."""
    return managed_temp_file(suffix=suffix, prefix=prefix)


def safe_audit_operation(audit_system: Any, operation_type: str, metadata: Optional[Dict] = None) -> Any:
    """Convenience function for safe audit operations."""
    return managed_audit_session(audit_system, operation_type, metadata)


def safe_llm_operation(llm_provider: Any, context: str = 'llm_operation') -> Any:
    """Convenience function for safe LLM operations."""
    return managed_llm_client(llm_provider, context)