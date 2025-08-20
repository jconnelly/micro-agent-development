"""
Test Output File Management Utilities

This module provides utilities to manage test output files and prevent
file collision issues between different test runs.
"""

import os
import json
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class TestOutputManager:
    """
    Manages test output files to prevent collisions and ensure clean test runs.
    
    Features:
    - Unique filenames per test run using timestamps
    - Clean up old test files
    - Archive previous test results
    - Provide consistent naming patterns
    """
    
    def __init__(self, base_output_dir: str = "./Rule_Agent_Output_Files"):
        """Initialize the test output manager."""
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def get_unique_filename(self, base_name: str, test_name: str = "test") -> Path:
        """
        Generate a unique filename for a test output.
        
        Args:
            base_name: Base name like 'extracted_rules_output.json'
            test_name: Name of the test for identification
            
        Returns:
            Path object with unique filename
            
        Example:
            extracted_rules_output.json -> extracted_rules_output_cobol_test_20241220_143022.json
        """
        name_parts = base_name.split('.')
        if len(name_parts) > 1:
            extension = name_parts[-1]
            base = '.'.join(name_parts[:-1])
            unique_name = f"{base}_{test_name}_{self.timestamp}.{extension}"
        else:
            unique_name = f"{base_name}_{test_name}_{self.timestamp}"
        
        return self.base_output_dir / unique_name
    
    def get_audit_filename(self, test_name: str = "test") -> Path:
        """
        Get a unique audit log filename for a test.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Path to unique audit log file
        """
        return self.get_unique_filename("audit_logs.jsonl", test_name)
    
    def get_rules_output_filename(self, test_name: str = "test") -> Path:
        """
        Get a unique extracted rules output filename.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Path to unique rules output file
        """
        return self.get_unique_filename("extracted_rules_output.json", test_name)
    
    def cleanup_old_test_files(self, days_old: int = 7) -> List[Path]:
        """
        Clean up test output files older than specified days.
        
        Args:
            days_old: Remove files older than this many days
            
        Returns:
            List of files that were removed
        """
        if not self.base_output_dir.exists():
            return []
        
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days_old)
        removed_files = []
        
        # Look for files with timestamp patterns
        test_file_patterns = [
            "*_test_*.json",
            "*_test_*.jsonl",
            "*_cobol_*.json",
            "*_cobol_*.jsonl"
        ]
        
        for pattern in test_file_patterns:
            for file_path in self.base_output_dir.glob(pattern):
                try:
                    if file_path.stat().st_mtime < cutoff_time.timestamp():
                        file_path.unlink()
                        removed_files.append(file_path)
                except (OSError, ValueError):
                    continue
        
        return removed_files
    
    def archive_current_outputs(self, archive_name: Optional[str] = None) -> Path:
        """
        Archive current standard output files before running new tests.
        
        Args:
            archive_name: Name for the archive directory
            
        Returns:
            Path to the created archive directory
        """
        if archive_name is None:
            archive_name = f"archive_{self.timestamp}"
        
        archive_dir = self.base_output_dir / "archives" / archive_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Files to archive
        standard_files = [
            "extracted_rules_output.json",
            "audit_logs.jsonl", 
            "business_rules_documentation.md",
            "business_rules_documentation.html",
            "business_rules_documentation.json"
        ]
        
        archived_files = []
        for filename in standard_files:
            source_file = self.base_output_dir / filename
            if source_file.exists():
                dest_file = archive_dir / filename
                dest_file.write_bytes(source_file.read_bytes())
                archived_files.append(filename)
        
        # Create archive manifest
        manifest = {
            "archive_created": datetime.datetime.now().isoformat(),
            "archived_files": archived_files,
            "original_location": str(self.base_output_dir)
        }
        
        (archive_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding='utf-8'
        )
        
        return archive_dir
    
    def clear_standard_outputs(self) -> List[str]:
        """
        Clear standard output files that are commonly overwritten.
        
        Returns:
            List of files that were cleared
        """
        standard_files = [
            "extracted_rules_output.json",
            "business_rules_documentation.md", 
            "business_rules_documentation.html",
            "business_rules_documentation.json"
        ]
        
        cleared_files = []
        for filename in standard_files:
            file_path = self.base_output_dir / filename
            if file_path.exists():
                file_path.unlink()
                cleared_files.append(filename)
        
        return cleared_files
    
    def get_test_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current test output files.
        
        Returns:
            Dictionary with file counts and sizes
        """
        if not self.base_output_dir.exists():
            return {"error": "Output directory does not exist"}
        
        all_files = list(self.base_output_dir.glob("*"))
        
        summary = {
            "output_directory": str(self.base_output_dir),
            "total_files": len(all_files),
            "json_files": len(list(self.base_output_dir.glob("*.json"))),
            "jsonl_files": len(list(self.base_output_dir.glob("*.jsonl"))),
            "markdown_files": len(list(self.base_output_dir.glob("*.md"))),
            "html_files": len(list(self.base_output_dir.glob("*.html"))),
            "test_files": len(list(self.base_output_dir.glob("*test*"))),
            "recent_files": []
        }
        
        # Get 5 most recent files
        try:
            recent_files = sorted(all_files, key=lambda f: f.stat().st_mtime, reverse=True)[:5]
            summary["recent_files"] = [
                {
                    "name": f.name,
                    "size_bytes": f.stat().st_size,
                    "modified": datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in recent_files
            ]
        except (OSError, ValueError):
            summary["recent_files"] = []
        
        return summary


def create_test_runner_with_unique_outputs(test_name: str):
    """
    Factory function to create a test output manager for a specific test.
    
    Args:
        test_name: Name of the test for file naming
        
    Returns:
        TestOutputManager instance configured for the test
        
    Example:
        >>> manager = create_test_runner_with_unique_outputs("cobol_extraction")
        >>> rules_file = manager.get_rules_output_filename()
        >>> audit_file = manager.get_audit_filename()
    """
    return TestOutputManager()


if __name__ == "__main__":
    # Demo/test the functionality
    print("Test Output Manager Demo")
    print("=" * 40)
    
    manager = TestOutputManager()
    
    # Show current summary
    summary = manager.get_test_summary()
    print(f"Output directory: {summary['output_directory']}")
    print(f"Total files: {summary['total_files']}")
    print(f"JSON files: {summary['json_files']}")
    print(f"JSONL audit files: {summary['jsonl_files']}")
    print(f"Test-specific files: {summary['test_files']}")
    
    print("\nRecent files:")
    for file_info in summary['recent_files']:
        print(f"  - {file_info['name']} ({file_info['size_bytes']} bytes)")
    
    # Example unique filenames
    print(f"\nExample unique filenames:")
    print(f"Rules output: {manager.get_rules_output_filename('cobol_test')}")
    print(f"Audit logs: {manager.get_audit_filename('cobol_test')}")
    
    # Cleanup old files (dry run)
    old_files = manager.cleanup_old_test_files(30)  # 30 days
    if old_files:
        print(f"\nWould clean up {len(old_files)} old test files")
    else:
        print(f"\nNo old test files to clean up")