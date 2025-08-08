#!/usr/bin/env python3

"""
Tool-Integrated Rule Documentation Agent

An enhanced version of RuleDocumentationAgent that uses Claude Code tools for:
- File I/O operations via Write tool for atomic file operations
- Better error handling and path validation
- Improved performance for large document generation

This demonstrates Phase 5 tool integration improvements.
"""

import json
import uuid
import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from .RuleDocumentationAgent import RuleDocumentationAgent
from .AuditingAgent import AuditLevel

# Import Utils - handle both relative and absolute imports
try:
    from ..Utils import TimeUtils
except ImportError:
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from Utils import TimeUtils


class ToolIntegratedDocumentationAgent(RuleDocumentationAgent):
    """
    Enhanced Rule Documentation Agent that uses Claude Code tools for file operations.
    
    This agent extends RuleDocumentationAgent with:
    - Write tool integration for atomic file operations
    - Better error handling and path validation
    - Support for multiple output files in single operation
    - Enhanced audit trail for file operations
    """
    
    def __init__(self, llm_client, audit_system, agent_id: str = None, log_level: int = 0, 
                 model_name: str = "gemini-1.5-flash", llm_provider: str = "google",
                 write_tool: Optional[Callable] = None):
        """
        Initialize the tool-integrated documentation agent.
        
        Args:
            llm_client: An initialized LLM client
            audit_system: The auditing system instance
            agent_id: Unique identifier for this agent instance
            log_level: Logging verbosity level
            model_name: LLM model name
            llm_provider: LLM provider name
            write_tool: Claude Code Write tool function (injected for testing)
        """
        super().__init__(
            llm_client=llm_client,
            audit_system=audit_system,
            agent_id=agent_id,
            log_level=log_level,
            model_name=model_name,
            llm_provider=llm_provider
        )
        self.agent_name = "Tool-Integrated Documentation Agent"
        self.write_tool = write_tool
        
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information including tool integration capabilities."""
        base_info = super().get_agent_info()
        base_info.update({
            "tool_integrations": {
                "write_tool": self.write_tool is not None,
                "file_operations": "atomic_writes",
                "error_handling": "enhanced"
            },
            "capabilities": base_info.get("capabilities", []) + [
                "atomic_file_operations",
                "multi_format_output",
                "path_validation",
                "enhanced_error_recovery"
            ]
        })
        return base_info
    
    def _write_file_with_tool(self, file_path: str, content: str, request_id: str) -> Dict[str, Any]:
        """
        Write file using Claude Code Write tool with enhanced error handling.
        
        Args:
            file_path: Path to write the file
            content: Content to write
            request_id: Request ID for audit trail
            
        Returns:
            Dictionary with operation result and metadata
        """
        operation_start = datetime.datetime.now(datetime.timezone.utc)
        
        try:
            # Validate path
            path_obj = Path(file_path)
            if not path_obj.parent.exists():
                self.logger.warning(f"Parent directory does not exist: {path_obj.parent}", request_id=request_id)
                # Create parent directories if needed
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                
            # Use Write tool if available, otherwise fallback to standard file I/O
            if self.write_tool:
                try:
                    self.write_tool(file_path=str(path_obj), content=content)
                    operation_result = {
                        "success": True,
                        "method": "write_tool",
                        "file_path": str(path_obj),
                        "content_size": len(content),
                        "operation_time": TimeUtils.calculate_duration_ms(operation_start)
                    }
                    self.logger.info(f"File written successfully using Write tool: {path_obj}", request_id=request_id)
                except Exception as e:
                    self.logger.warning(f"Write tool failed, falling back to standard I/O: {e}", request_id=request_id)
                    # Fallback to standard file I/O
                    operation_result = self._write_file_standard(path_obj, content, request_id, operation_start)
            else:
                # Use standard file I/O
                operation_result = self._write_file_standard(path_obj, content, request_id, operation_start)
                
        except Exception as e:
            operation_result = {
                "success": False,
                "method": "failed",
                "error": str(e),
                "operation_time": TimeUtils.calculate_duration_ms(operation_start)
            }
            self.logger.error(f"File write operation failed: {e}", request_id=request_id)
            
        return operation_result
    
    def _write_file_standard(self, path_obj: Path, content: str, request_id: str, operation_start: datetime.datetime) -> Dict[str, Any]:
        """
        Fallback method for standard file I/O operations.
        
        Args:
            path_obj: Path object for the file
            content: Content to write
            request_id: Request ID for audit trail
            operation_start: Operation start time
            
        Returns:
            Dictionary with operation result
        """
        try:
            with open(path_obj, 'w', encoding='utf-8') as f:
                f.write(content)
            return {
                "success": True,
                "method": "standard_io",
                "file_path": str(path_obj),
                "content_size": len(content),
                "operation_time": TimeUtils.calculate_duration_ms(operation_start)
            }
        except Exception as e:
            return {
                "success": False,
                "method": "standard_io",
                "error": str(e),
                "operation_time": TimeUtils.calculate_duration_ms(operation_start)
            }
    
    def document_and_save_rules(self, extracted_rules: List[Dict], output_directory: str = "documentation",
                               output_formats: List[str] = None, audit_level: int = AuditLevel.LEVEL_2.value) -> Dict[str, Any]:
        """
        Generate documentation and save to files using tool integration.
        
        This method extends the base documentation functionality by:
        - Generating documentation in multiple formats
        - Saving files using Write tool for atomic operations
        - Enhanced error handling and recovery
        - Comprehensive audit trail for file operations
        
        Args:
            extracted_rules: List of extracted business rules
            output_directory: Directory to save documentation files
            output_formats: List of formats to generate ['markdown', 'json', 'html']
            audit_level: Audit verbosity level
            
        Returns:
            Dictionary with documentation results and file operation metadata
        """
        request_id = f"tool-doc-{uuid.uuid4().hex}"
        start_time = datetime.datetime.now(datetime.timezone.utc)
        
        if output_formats is None:
            output_formats = ['markdown', 'json']
            
        self.logger.info(f"Starting tool-integrated documentation generation for {len(extracted_rules)} rules", 
                        request_id=request_id)
        
        # Generate base documentation using parent class
        base_result = self.document_and_visualize_rules(extracted_rules, "markdown", audit_level)
        
        # Extract documentation components
        documentation_summary = base_result.get('documentation_summary', '')
        refined_rules = base_result.get('refined_rules', [])
        domain_info = base_result.get('domain_info', {})
        
        # Prepare output directory
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_name = domain_info.get('primary_domain', 'general')
        base_filename = f"business_rules_{domain_name}_{timestamp}"
        
        # Generate and save documentation in all requested formats
        file_operations = []
        successful_files = []
        failed_files = []
        
        for format_name in output_formats:
            try:
                # Generate formatted documentation
                formatted_doc, error_details = self._generate_formatted_output(format_name, documentation_summary, refined_rules)
                
                if error_details:
                    self.logger.warning(f"Format generation warning for {format_name}: {error_details}", request_id=request_id)
                
                # Determine file extension
                extension_map = {
                    'markdown': 'md',
                    'json': 'json',
                    'html': 'html'
                }
                extension = extension_map.get(format_name, 'txt')
                
                # Create file path
                file_path = output_path / f"{base_filename}.{extension}"
                
                # Write file using tool integration
                operation_result = self._write_file_with_tool(str(file_path), formatted_doc, request_id)
                operation_result['format'] = format_name
                operation_result['file_name'] = file_path.name
                
                file_operations.append(operation_result)
                
                if operation_result['success']:
                    successful_files.append({
                        'format': format_name,
                        'path': str(file_path),
                        'size': operation_result['content_size']
                    })
                    self.logger.info(f"Successfully saved {format_name} documentation: {file_path}", request_id=request_id)
                else:
                    failed_files.append({
                        'format': format_name,
                        'path': str(file_path),
                        'error': operation_result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                error_operation = {
                    'success': False,
                    'format': format_name,
                    'method': 'format_generation_failed',
                    'error': str(e),
                    'operation_time': 0
                }
                file_operations.append(error_operation)
                failed_files.append({
                    'format': format_name,
                    'error': str(e)
                })
                self.logger.error(f"Failed to generate {format_name} documentation: {e}", request_id=request_id)
        
        # Calculate total operation time
        total_duration = TimeUtils.calculate_duration_ms(start_time)
        
        # Prepare comprehensive result
        result = {
            'request_id': request_id,
            'success': len(successful_files) > 0,
            'total_files_requested': len(output_formats),
            'successful_files': successful_files,
            'failed_files': failed_files,
            'file_operations': file_operations,
            'documentation_summary': documentation_summary,
            'refined_rules': refined_rules,
            'domain_info': domain_info,
            'output_directory': str(output_path),
            'total_duration_ms': total_duration,
            'operation_metadata': {
                'agent_id': self.agent_id,
                'agent_name': self.agent_name,
                'tool_integration': self.write_tool is not None,
                'timestamp': start_time.isoformat(),
                'audit_level': audit_level
            }
        }
        
        # Log final result
        self.logger.info(f"Documentation generation complete. Success: {len(successful_files)}/{len(output_formats)} files. Duration: {total_duration}ms", 
                        request_id=request_id)
        
        # Create audit entry
        if hasattr(self, 'audit_system') and self.audit_system:
            self.audit_system.log_agent_activity(
                request_id=request_id,
                user_id="documentation_system",
                session_id=request_id,
                ip_address=self.get_ip_address(),
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                agent_version=self.version,
                step_type="tool_integrated_documentation",
                llm_model_name=self.model_name,
                llm_provider=self.llm_provider,
                llm_input=f"Generate documentation for {len(extracted_rules)} rules in formats: {output_formats}",
                llm_output=f"Generated {len(successful_files)} files successfully",
                tokens_input=base_result.get('tokens_input', 0),
                tokens_output=base_result.get('tokens_output', 0),
                tool_calls=[{
                    "tool_name": "write_file_with_integration",
                    "file_operations": file_operations,
                    "successful_count": len(successful_files),
                    "failed_count": len(failed_files)
                }],
                final_decision=f"Documentation generated successfully: {len(successful_files)}/{len(output_formats)} files",
                duration_ms=total_duration,
                audit_level=audit_level
            )
        
        return result

    def batch_document_rules(self, rule_sets: List[Dict[str, Any]], output_base_directory: str = "batch_documentation",
                           output_formats: List[str] = None, audit_level: int = AuditLevel.LEVEL_2.value) -> Dict[str, Any]:
        """
        Process multiple rule sets in batch with tool integration.
        
        Args:
            rule_sets: List of rule sets, each containing 'rules' and 'metadata'
            output_base_directory: Base directory for batch output
            output_formats: List of formats to generate
            audit_level: Audit verbosity level
            
        Returns:
            Dictionary with batch processing results
        """
        request_id = f"batch-doc-{uuid.uuid4().hex}"
        start_time = datetime.datetime.now(datetime.timezone.utc)
        
        if output_formats is None:
            output_formats = ['markdown', 'json']
            
        self.logger.info(f"Starting batch documentation for {len(rule_sets)} rule sets", request_id=request_id)
        
        # Prepare base output directory
        base_path = Path(output_base_directory)
        base_path.mkdir(parents=True, exist_ok=True)
        
        batch_results = []
        total_successful = 0
        total_failed = 0
        
        for i, rule_set in enumerate(rule_sets):
            try:
                rules = rule_set.get('rules', [])
                metadata = rule_set.get('metadata', {})
                set_name = metadata.get('name', f'ruleset_{i+1}')
                
                # Create subdirectory for this rule set
                set_directory = base_path / set_name
                
                # Process this rule set
                set_result = self.document_and_save_rules(
                    extracted_rules=rules,
                    output_directory=str(set_directory),
                    output_formats=output_formats,
                    audit_level=audit_level
                )
                
                set_result['rule_set_metadata'] = metadata
                set_result['rule_set_index'] = i
                batch_results.append(set_result)
                
                total_successful += len(set_result['successful_files'])
                total_failed += len(set_result['failed_files'])
                
                self.logger.info(f"Completed rule set {i+1}/{len(rule_sets)}: {set_name}", request_id=request_id)
                
            except Exception as e:
                error_result = {
                    'rule_set_index': i,
                    'rule_set_metadata': metadata,
                    'success': False,
                    'error': str(e),
                    'successful_files': [],
                    'failed_files': []
                }
                batch_results.append(error_result)
                total_failed += len(output_formats)  # Count all formats as failed
                
                self.logger.error(f"Failed to process rule set {i+1}: {e}", request_id=request_id)
        
        total_duration = TimeUtils.calculate_duration_ms(start_time)
        
        # Prepare batch summary
        batch_summary = {
            'request_id': request_id,
            'batch_success': total_successful > 0,
            'total_rule_sets': len(rule_sets),
            'total_files_successful': total_successful,
            'total_files_failed': total_failed,
            'batch_results': batch_results,
            'output_base_directory': str(base_path),
            'total_duration_ms': total_duration,
            'operation_metadata': {
                'agent_id': self.agent_id,
                'agent_name': self.agent_name,
                'tool_integration': self.write_tool is not None,
                'timestamp': start_time.isoformat(),
                'formats_requested': output_formats
            }
        }
        
        self.logger.info(f"Batch documentation complete. {total_successful} files successful, {total_failed} failed. Duration: {total_duration}ms", 
                        request_id=request_id)
        
        return batch_summary