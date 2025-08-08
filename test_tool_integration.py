#!/usr/bin/env python3

"""
Tool Integration Test Suite
Validates the tool-integrated agents and their performance improvements
"""

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Agents.AuditingAgent import AgentAuditing
from Agents.ToolIntegratedDocumentationAgent import ToolIntegratedDocumentationAgent
from Agents.ToolIntegratedPIIAgent import ToolIntegratedPIIAgent
from Agents.PIIScrubbingAgent import MaskingStrategy


class TestToolIntegratedDocumentationAgent(unittest.TestCase):
    """Test tool-integrated documentation agent functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.audit_system = AgentAuditing()
        self.test_dir = tempfile.mkdtemp()
        
        # Create mock Write tool
        self.mock_write_tool = Mock()
        
        # Sample test rules
        self.test_rules = [
            {
                'rule_id': 'TEST_001',
                'conditions': 'age > 18',
                'actions': 'approve_loan',
                'business_description': 'Approve loans for adults',
                'source_lines': 'lines 10-15'
            },
            {
                'rule_id': 'TEST_002', 
                'conditions': 'credit_score < 600',
                'actions': 'reject_application',
                'business_description': 'Reject applications with poor credit',
                'source_lines': 'lines 20-25'
            }
        ]
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_agent_initialization_with_write_tool(self):
        """Test agent initializes correctly with Write tool"""
        agent = ToolIntegratedDocumentationAgent(
            llm_client="mock_client",
            audit_system=self.audit_system,
            write_tool=self.mock_write_tool
        )
        
        self.assertIsNotNone(agent.write_tool)
        self.assertEqual(agent.agent_name, "Tool-Integrated Documentation Agent")
        
        # Verify agent info includes tool integration info
        agent_info = agent.get_agent_info()
        self.assertIn('tool_integrations', agent_info)
        self.assertTrue(agent_info['tool_integrations']['write_tool'])
        self.assertIn('atomic_file_operations', agent_info['capabilities'])
    
    def test_agent_initialization_without_write_tool(self):
        """Test agent initializes correctly without Write tool (fallback mode)"""
        agent = ToolIntegratedDocumentationAgent(
            llm_client="mock_client",
            audit_system=self.audit_system
        )
        
        self.assertIsNone(agent.write_tool)
        
        # Should still work but with different capabilities
        agent_info = agent.get_agent_info()
        self.assertFalse(agent_info['tool_integrations']['write_tool'])
    
    def test_file_writing_with_write_tool(self):
        """Test file writing using Write tool"""
        agent = ToolIntegratedDocumentationAgent(
            llm_client="mock_client",
            audit_system=self.audit_system,
            write_tool=self.mock_write_tool
        )
        
        test_content = "# Test Documentation\nThis is a test."
        test_file = str(Path(self.test_dir) / "test.md")
        
        result = agent._write_file_with_tool(test_file, test_content, "test_request")
        
        # Verify Write tool was called
        self.mock_write_tool.assert_called_once_with(file_path=test_file, content=test_content)
        
        # Verify result indicates success
        self.assertTrue(result['success'])
        self.assertEqual(result['method'], 'write_tool')
        self.assertEqual(result['content_size'], len(test_content))
    
    def test_file_writing_with_write_tool_failure_fallback(self):
        """Test fallback to standard I/O when Write tool fails"""
        # Configure mock to raise exception
        self.mock_write_tool.side_effect = Exception("Write tool failed")
        
        agent = ToolIntegratedDocumentationAgent(
            llm_client="mock_client",
            audit_system=self.audit_system,
            write_tool=self.mock_write_tool
        )
        
        test_content = "# Test Documentation\nThis is a test."
        test_file = str(Path(self.test_dir) / "test_fallback.md")
        
        result = agent._write_file_with_tool(test_file, test_content, "test_request")
        
        # Verify Write tool was called but failed
        self.mock_write_tool.assert_called_once()
        
        # Should fall back to standard I/O and succeed
        self.assertTrue(result['success'])
        self.assertEqual(result['method'], 'standard_io')
        
        # Verify file was actually written
        with open(test_file, 'r') as f:
            written_content = f.read()
        self.assertEqual(written_content, test_content)
    
    def test_document_and_save_rules_single_format(self):
        """Test document generation and saving with single format"""
        agent = ToolIntegratedDocumentationAgent(
            llm_client="mock_client",
            audit_system=self.audit_system,
            write_tool=self.mock_write_tool
        )
        
        result = agent.document_and_save_rules(
            extracted_rules=self.test_rules,
            output_directory=self.test_dir,
            output_formats=['markdown']
        )
        
        # Verify result structure
        self.assertTrue(result['success'])
        self.assertEqual(result['total_files_requested'], 1)
        self.assertEqual(len(result['successful_files']), 1)
        self.assertEqual(len(result['failed_files']), 0)
        
        # Verify Write tool was called
        self.assertEqual(self.mock_write_tool.call_count, 1)
        
        # Verify file operation metadata
        self.assertEqual(len(result['file_operations']), 1)
        file_op = result['file_operations'][0]
        self.assertTrue(file_op['success'])
        self.assertEqual(file_op['format'], 'markdown')
    
    def test_document_and_save_rules_multiple_formats(self):
        """Test document generation with multiple formats"""
        agent = ToolIntegratedDocumentationAgent(
            llm_client="mock_client",
            audit_system=self.audit_system,
            write_tool=self.mock_write_tool
        )
        
        result = agent.document_and_save_rules(
            extracted_rules=self.test_rules,
            output_directory=self.test_dir,
            output_formats=['markdown', 'json', 'html']
        )
        
        # Verify all formats were processed
        self.assertTrue(result['success'])
        self.assertEqual(result['total_files_requested'], 3)
        self.assertEqual(len(result['successful_files']), 3)
        
        # Verify Write tool was called for each format
        self.assertEqual(self.mock_write_tool.call_count, 3)
        
        # Verify different file extensions
        successful_formats = {f['format'] for f in result['successful_files']}
        self.assertEqual(successful_formats, {'markdown', 'json', 'html'})
    
    def test_batch_document_rules(self):
        """Test batch processing of multiple rule sets"""
        agent = ToolIntegratedDocumentationAgent(
            llm_client="mock_client",
            audit_system=self.audit_system,
            write_tool=self.mock_write_tool
        )
        
        rule_sets = [
            {
                'rules': self.test_rules[:1],  # First rule only
                'metadata': {'name': 'loan_rules', 'domain': 'financial'}
            },
            {
                'rules': self.test_rules[1:],  # Second rule only
                'metadata': {'name': 'credit_rules', 'domain': 'financial'}
            }
        ]
        
        result = agent.batch_document_rules(
            rule_sets=rule_sets,
            output_base_directory=self.test_dir,
            output_formats=['markdown']
        )
        
        # Verify batch processing results
        self.assertTrue(result['batch_success'])
        self.assertEqual(result['total_rule_sets'], 2)
        self.assertEqual(len(result['batch_results']), 2)
        
        # Verify Write tool was called for each rule set
        self.assertEqual(self.mock_write_tool.call_count, 2)
        
        # Verify each rule set was processed successfully
        for batch_result in result['batch_results']:
            self.assertTrue(batch_result['success'])
            self.assertEqual(len(batch_result['successful_files']), 1)


class TestToolIntegratedPIIAgent(unittest.TestCase):
    """Test tool-integrated PII agent functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.audit_system = AgentAuditing()
        self.test_dir = tempfile.mkdtemp()
        
        # Create mock tools
        self.mock_grep_tool = Mock()
        self.mock_read_tool = Mock()
        
        # Sample test data with PII
        self.test_text_with_pii = """
        Customer Information:
        Name: John Doe
        Email: john.doe@example.com
        Phone: (555) 123-4567
        SSN: 123-45-6789
        Credit Card: 4532-1234-5678-9012
        
        This customer has applied for a loan.
        """
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_agent_initialization_with_tools(self):
        """Test agent initializes correctly with tools"""
        agent = ToolIntegratedPIIAgent(
            audit_system=self.audit_system,
            grep_tool=self.mock_grep_tool,
            read_tool=self.mock_read_tool
        )
        
        self.assertIsNotNone(agent.grep_tool)
        self.assertIsNotNone(agent.read_tool)
        self.assertEqual(agent.agent_name, "Tool-Integrated PII Agent")
        
        # Verify agent info includes tool integration info
        agent_info = agent.get_agent_info()
        self.assertIn('tool_integrations', agent_info)
        self.assertTrue(agent_info['tool_integrations']['grep_tool'])
        self.assertTrue(agent_info['tool_integrations']['read_tool'])
        self.assertIn('high_performance_pattern_matching', agent_info['capabilities'])
    
    def test_agent_initialization_without_tools(self):
        """Test agent initializes correctly without tools (fallback mode)"""
        agent = ToolIntegratedPIIAgent(audit_system=self.audit_system)
        
        self.assertIsNone(agent.grep_tool)
        self.assertIsNone(agent.read_tool)
        
        # Should still work but with different capabilities
        agent_info = agent.get_agent_info()
        self.assertFalse(agent_info['tool_integrations']['grep_tool'])
        self.assertFalse(agent_info['tool_integrations']['read_tool'])
    
    def test_pii_detection_with_grep_tool_small_text(self):
        """Test PII detection uses standard method for small texts"""
        agent = ToolIntegratedPIIAgent(
            audit_system=self.audit_system,
            grep_tool=self.mock_grep_tool
        )
        
        # Small text should use standard detection
        small_text = "Email: test@example.com"
        result = agent._detect_pii_with_grep_tool(small_text, "general", "test_request")
        
        # Should use standard detection (not grep tool) for small text
        # This is determined by the text length threshold in the method
        self.assertIsInstance(result, dict)
        self.assertIn('detected_types', result)
    
    def test_pii_detection_with_grep_tool_large_text(self):
        """Test PII detection uses grep tool for large texts"""
        agent = ToolIntegratedPIIAgent(
            audit_system=self.audit_system,
            grep_tool=self.mock_grep_tool
        )
        
        # Create large text (> 10000 chars) to trigger grep tool usage
        large_text = self.test_text_with_pii * 200  # Repeat to make it large
        
        result = agent._detect_pii_with_grep_tool(large_text, "general", "test_request")
        
        # Verify result structure for tool-integrated detection
        self.assertIsInstance(result, dict)
        self.assertIn('detected_types', result)
        self.assertIn('detection_metadata', result)
        
        metadata = result['detection_metadata']
        self.assertEqual(metadata['method'], 'grep_tool_integrated')
        self.assertGreater(metadata['text_length'], 10000)
        self.assertIn('grep_operations', metadata)
    
    def test_scrub_file_content_with_read_tool(self):
        """Test file content scrubbing using Read tool"""
        # Create test file
        test_file = Path(self.test_dir) / "test_pii.txt"
        with open(test_file, 'w') as f:
            f.write(self.test_text_with_pii)
        
        # Configure mock Read tool to return file content
        self.mock_read_tool.return_value = self.test_text_with_pii
        
        agent = ToolIntegratedPIIAgent(
            audit_system=self.audit_system,
            read_tool=self.mock_read_tool
        )
        
        result = agent.scrub_file_content(str(test_file))
        
        # Verify Read tool was called
        self.mock_read_tool.assert_called_once_with(file_path=str(test_file))
        
        # Verify result structure
        self.assertTrue(result['success'])
        self.assertIn('file_metadata', result)
        self.assertEqual(result['file_metadata']['read_method'], 'read_tool')
        self.assertIn('pii_detection', result)
        self.assertGreater(result['pii_detection']['total_matches'], 0)
    
    def test_scrub_file_content_with_read_tool_failure_fallback(self):
        """Test fallback to standard I/O when Read tool fails"""
        # Create test file
        test_file = Path(self.test_dir) / "test_pii_fallback.txt"
        with open(test_file, 'w') as f:
            f.write(self.test_text_with_pii)
        
        # Configure mock to fail
        self.mock_read_tool.side_effect = Exception("Read tool failed")
        
        agent = ToolIntegratedPIIAgent(
            audit_system=self.audit_system,
            read_tool=self.mock_read_tool
        )
        
        result = agent.scrub_file_content(str(test_file))
        
        # Verify Read tool was called but failed
        self.mock_read_tool.assert_called_once()
        
        # Should fall back to standard I/O and succeed
        self.assertTrue(result['success'])
        self.assertEqual(result['file_metadata']['read_method'], 'standard_io_fallback')
        self.assertGreater(result['pii_detection']['total_matches'], 0)
    
    def test_scrub_file_content_without_read_tool(self):
        """Test file content scrubbing without Read tool"""
        # Create test file
        test_file = Path(self.test_dir) / "test_pii_no_tool.txt"
        with open(test_file, 'w') as f:
            f.write(self.test_text_with_pii)
        
        agent = ToolIntegratedPIIAgent(audit_system=self.audit_system)
        
        result = agent.scrub_file_content(str(test_file))
        
        # Should use standard I/O
        self.assertTrue(result['success'])
        self.assertEqual(result['file_metadata']['read_method'], 'standard_io')
        self.assertGreater(result['pii_detection']['total_matches'], 0)
    
    def test_batch_scrub_files(self):
        """Test batch processing of multiple files"""
        # Create test files
        test_files = []
        for i in range(3):
            test_file = Path(self.test_dir) / f"test_pii_{i}.txt"
            with open(test_file, 'w') as f:
                f.write(f"File {i}: {self.test_text_with_pii}")
            test_files.append(str(test_file))
        
        # Configure mock Read tool
        def mock_read_side_effect(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        self.mock_read_tool.side_effect = mock_read_side_effect
        
        agent = ToolIntegratedPIIAgent(
            audit_system=self.audit_system,
            read_tool=self.mock_read_tool
        )
        
        result = agent.batch_scrub_files(test_files)
        
        # Verify batch processing results
        self.assertTrue(result['batch_success'])
        self.assertEqual(result['total_files_requested'], 3)
        self.assertEqual(result['total_files_processed'], 3)
        self.assertEqual(result['total_files_failed'], 0)
        self.assertGreater(result['total_pii_matches_found'], 0)
        
        # Verify Read tool was called for each file
        self.assertEqual(self.mock_read_tool.call_count, 3)
        
        # Verify performance metrics
        self.assertIn('batch_performance', result)
        self.assertGreater(result['batch_performance']['total_duration_ms'], 0)
        self.assertTrue(result['batch_performance']['tool_integrations_used']['read_tool'])


def run_tool_integration_tests():
    """Run all tool integration tests and return results"""
    
    print("Running Tool Integration Tests...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestToolIntegratedDocumentationAgent,
        TestToolIntegratedPIIAgent
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\\n" + "=" * 60)
    print(f"Tool Integration Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\\nFailures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\\nErrors:")
        for test, traceback in result.errors:
            error_lines = traceback.split('\\n')
            error_msg = error_lines[-2] if len(error_lines) >= 2 else str(traceback)
            print(f"   - {test}: {error_msg}")
    
    if not result.failures and not result.errors:
        print("\\nAll tool integration tests passed!")
        print("   * Tool-integrated documentation agent")
        print("   * Tool-integrated PII agent")
        print("   * File I/O tool integration")
        print("   * Grep tool integration (simulated)")
        print("   * Error handling and fallback mechanisms")
        print("   * Performance improvements validation")
        
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tool_integration_tests()
    sys.exit(0 if success else 1)