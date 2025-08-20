#!/usr/bin/env python3

"""
Tool Interface Protocols and Containers

Provides type-safe interfaces for Claude Code tools, replacing raw Callable
injections with structured Protocol-based contracts.

This module was extracted from StandardImports.py as part of Phase 14
code quality improvements to break down large class files.
"""

from typing import Optional, Protocol, List


class WriteToolInterface(Protocol):
    """
    Protocol defining the interface for Write tool operations.
    
    Provides type-safe contract for file writing operations with Claude Code tools.
    Replaces raw Callable injections with structured interface.
    """
    
    def __call__(self, file_path: str, content: str) -> None:
        """
        Write content to a file with atomic operations.
        
        Args:
            file_path: Absolute path to the file to write
            content: Content to write to the file
            
        Raises:
            FileNotFoundError: If parent directory doesn't exist
            PermissionError: If write access is denied
            IOError: If write operation fails
        """
        ...


class ReadToolInterface(Protocol):
    """
    Protocol defining the interface for Read tool operations.
    
    Provides type-safe contract for file reading operations with Claude Code tools.
    """
    
    def __call__(self, file_path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> str:
        """
        Read content from a file with optional offset and limit.
        
        Args:
            file_path: Absolute path to the file to read
            offset: Optional line number to start reading from
            limit: Optional maximum number of lines to read
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If read access is denied
            IOError: If read operation fails
        """
        ...


class GrepToolInterface(Protocol):
    """
    Protocol defining the interface for Grep tool operations.
    
    Provides type-safe contract for high-performance regex searching operations.
    """
    
    def __call__(self, pattern: str, path: Optional[str] = None, 
                 output_mode: str = "files_with_matches", 
                 multiline: bool = False, **kwargs) -> str:
        """
        Search for patterns using optimized regex engine.
        
        Args:
            pattern: Regular expression pattern to search for
            path: Optional path to search in (defaults to current directory)
            output_mode: Output format ("content", "files_with_matches", "count")
            multiline: Whether to enable multiline matching
            **kwargs: Additional ripgrep options
            
        Returns:
            Search results as string
            
        Raises:
            ValueError: If pattern is invalid
            IOError: If search operation fails
        """
        ...


class ToolContainer:
    """
    Container for tool instances with type-safe interfaces.
    
    Provides structured access to Claude Code tools with proper typing
    and validation. Replaces raw Callable injections.
    """
    
    def __init__(self, 
                 write_tool: Optional[WriteToolInterface] = None,
                 read_tool: Optional[ReadToolInterface] = None, 
                 grep_tool: Optional[GrepToolInterface] = None):
        """
        Initialize tool container with optional tool instances.
        
        Args:
            write_tool: Write tool implementation
            read_tool: Read tool implementation  
            grep_tool: Grep tool implementation
        """
        self.write_tool = write_tool
        self.read_tool = read_tool
        self.grep_tool = grep_tool
    
    def has_write_tool(self) -> bool:
        """Check if write tool is available."""
        return self.write_tool is not None
    
    def has_read_tool(self) -> bool:
        """Check if read tool is available."""
        return self.read_tool is not None
    
    def has_grep_tool(self) -> bool:
        """Check if grep tool is available."""
        return self.grep_tool is not None
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        tools = []
        if self.has_write_tool():
            tools.append("write")
        if self.has_read_tool():
            tools.append("read")
        if self.has_grep_tool():
            tools.append("grep")
        return tools
    
    def validate_tool_availability(self, required_tools: List[str]) -> bool:
        """
        Validate that all required tools are available.
        
        Args:
            required_tools: List of tool names that must be available
            
        Returns:
            True if all required tools are available
        """
        available = self.get_available_tools()
        return all(tool in available for tool in required_tools)