"""
Time Utilities - Common timestamp and duration calculation functions.

Provides standardized time handling used across all agents for consistency.
"""

from datetime import datetime, timezone
from typing import Optional


class TimeUtils:
    """Utility class for time-related operations across agents."""
    
    @staticmethod
    def get_current_utc_timestamp() -> datetime:
        """
        Get current UTC timestamp.
        
        Returns:
            Current datetime in UTC timezone
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def calculate_duration_ms(
        start_time: datetime, 
        end_time: Optional[datetime] = None
    ) -> float:
        """
        Calculate duration between two timestamps in milliseconds.
        
        Args:
            start_time: Starting timestamp
            end_time: Ending timestamp (defaults to current time)
            
        Returns:
            Duration in milliseconds as float
        """
        if end_time is None:
            end_time = TimeUtils.get_current_utc_timestamp()
        
        return (end_time - start_time).total_seconds() * 1000
    
    @staticmethod
    def format_timestamp(dt: Optional[datetime] = None) -> str:
        """
        Format timestamp as ISO string.
        
        Args:
            dt: Datetime to format (defaults to current time)
            
        Returns:
            ISO formatted timestamp string
        """
        if dt is None:
            dt = TimeUtils.get_current_utc_timestamp()
        return dt.isoformat()
    
    @staticmethod
    def format_timestamp_for_logs(dt: Optional[datetime] = None) -> str:
        """
        Format timestamp for log messages (HH:MM:SS format).
        
        Args:
            dt: Datetime to format (defaults to current time)
            
        Returns:
            Formatted timestamp string for logs
        """
        if dt is None:
            dt = TimeUtils.get_current_utc_timestamp()
        return dt.strftime("%H:%M:%S")
    
    @staticmethod
    def parse_iso_timestamp(timestamp_str: str) -> Optional[datetime]:
        """
        Parse ISO timestamp string back to datetime object.
        
        Args:
            timestamp_str: ISO formatted timestamp string
            
        Returns:
            Parsed datetime object or None if invalid
        """
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def ensure_utc(dt: datetime) -> datetime:
        """
        Ensure datetime object is in UTC timezone.
        
        Args:
            dt: Datetime object to convert
            
        Returns:
            Datetime object in UTC timezone
        """
        if dt.tzinfo is None:
            # Assume naive datetime is UTC
            return dt.replace(tzinfo=timezone.utc)
        elif dt.tzinfo != timezone.utc:
            # Convert to UTC
            return dt.astimezone(timezone.utc)
        else:
            # Already UTC
            return dt
    
    @staticmethod
    def create_operation_timer():
        """
        Create a simple timer context for measuring operation duration.
        
        Returns:
            Callable that returns elapsed milliseconds when called
        """
        start_time = TimeUtils.get_current_utc_timestamp()
        
        def get_elapsed_ms() -> float:
            return TimeUtils.calculate_duration_ms(start_time)
        
        return get_elapsed_ms