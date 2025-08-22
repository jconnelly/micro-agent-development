#!/usr/bin/env python3

"""
Test Suite for Standardized Error Handling

Validates that the new standardized error handling patterns work correctly
across all updated agents and provide consistent error messages and context.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from typing import Dict, Any

# Import the standardized error handling system
from Utils.error_handling import (
    StandardizedErrorHandler, 
    handle_config_error, 
    handle_validation_error,
    handle_processing_error
)

# Import agent exceptions
from Agents.Exceptions import (
    AgentException, ConfigurationError, PIIProcessingError, 
    RuleExtractionError, TriageProcessingError
)


class TestStandardizedErrorHandler(unittest.TestCase):
    """Test the core StandardizedErrorHandler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_request_id = "test_req_123"
        self.mock_logger = Mock()
    
    def test_handle_agent_error_basic(self):
        """Test basic agent error handling."""
        original_error = ValueError("Test error")
        
        result = StandardizedErrorHandler.handle_agent_error(
            operation="test operation",
            agent_type="pii",
            original_error=original_error,
            request_id=self.test_request_id,
            logger=self.mock_logger
        )
        
        # Verify correct exception type is returned
        self.assertIsInstance(result, PIIProcessingError)
        self.assertEqual(result.request_id, self.test_request_id)
        self.assertIn("test operation failed", result.message)
        
        # Verify logger was called
        self.mock_logger.error.assert_called_once()
    
    def test_exception_type_mapping(self):
        """Test that agent types map to correct exception classes."""
        test_cases = [
            ("pii", PIIProcessingError),
            ("rule", RuleExtractionError),
            ("triage", TriageProcessingError),
            ("config", ConfigurationError),
            ("unknown", AgentException)
        ]
        
        for agent_type, expected_class in test_cases:
            with self.subTest(agent_type=agent_type):
                result = StandardizedErrorHandler.handle_agent_error(
                    operation="test",
                    agent_type=agent_type,
                    original_error=Exception("test"),
                    request_id=self.test_request_id
                )
                self.assertIsInstance(result, expected_class)
    
    def test_safe_operation_wrapper(self):
        """Test the safe operation wrapper decorator."""
        @StandardizedErrorHandler.safe_operation_wrapper(
            operation_name="test_operation",
            agent_type="pii",
            request_id=self.test_request_id,
            logger=self.mock_logger,
            max_retries=2
        )
        def failing_function():
            raise ValueError("Test failure")
        
        # Should raise PIIProcessingError after retries
        with self.assertRaises(PIIProcessingError):
            failing_function()
        
        # Verify retry logging
        self.assertTrue(self.mock_logger.warning.called)
    
    def test_input_validation(self):
        """Test standardized input validation."""
        # Valid input should not raise exception
        StandardizedErrorHandler.validate_input(
            field_name="test_field",
            value="test_string",
            expected_type=str,
            request_id=self.test_request_id
        )
        
        # Invalid type should raise ValidationError
        from Agents.Exceptions import ValidationError
        with self.assertRaises(ValidationError):
            StandardizedErrorHandler.validate_input(
                field_name="test_field",
                value=123,
                expected_type=str,
                request_id=self.test_request_id
            )


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for common error scenarios."""
    
    def test_handle_config_error(self):
        """Test configuration error handling."""
        error = handle_config_error(
            message="Config file not found",
            config_name="test_config",
            request_id="req_123"
        )
        
        self.assertIsInstance(error, ConfigurationError)
        self.assertEqual(error.request_id, "req_123")
        self.assertIn("Config file not found", error.message)
    
    def test_handle_validation_error(self):
        """Test validation error handling."""
        error = handle_validation_error(
            field="test_field",
            value=123,
            expected="string",
            request_id="req_123"
        )
        
        from Agents.Exceptions import ValidationError
        self.assertIsInstance(error, ValidationError)
        self.assertIn("Invalid test_field", error.message)
    
    def test_handle_processing_error(self):
        """Test processing error handling."""
        error = handle_processing_error(
            operation="file processing",
            agent_type="pii",
            details="File not found",
            request_id="req_123"
        )
        
        self.assertIsInstance(error, PIIProcessingError)
        self.assertIn("file processing failed", error.message)


class TestAgentIntegration(unittest.TestCase):
    """Test integration with actual agent classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_request_id = "integration_test_123"
    
    @patch('Agents.BaseAgent.get_config_loader')
    def test_baseagent_config_error_handling(self, mock_config_loader):
        """Test BaseAgent configuration error handling."""
        # Mock config loader to raise exception
        mock_config_loader.side_effect = Exception("Config load failed")
        
        # Import here to avoid import issues during setup
        try:
            from Agents.BaseAgent import BaseAgent
            
            # Create a concrete subclass for testing
            class TestAgent(BaseAgent):
                def perform_action(self, action_data: Dict[str, Any], 
                                 context: str = "test", audit_level: int = 2) -> Dict[str, Any]:
                    return {"result": "test"}
            
            # Creating agent should handle config error gracefully
            agent = TestAgent(
                agent_id="test_agent",
                agent_version="1.0.0",
                model_name="test_model"
            )
            
            # Verify fallback values are used
            self.assertEqual(agent.API_TIMEOUT_SECONDS, 30.0)
            self.assertEqual(agent.MAX_RETRIES, 3)
            
        except ImportError:
            self.skipTest("BaseAgent import failed - may have dependency issues")
    
    def test_error_context_preservation(self):
        """Test that error context is properly preserved."""
        original_error = ValueError("Original error message")
        
        standardized_error = StandardizedErrorHandler.handle_agent_error(
            operation="test operation",
            agent_type="pii",
            original_error=original_error,
            context={"custom_field": "custom_value"},
            request_id=self.test_request_id
        )
        
        error_dict = standardized_error.to_dict()
        
        # Verify context preservation
        self.assertEqual(error_dict["request_id"], self.test_request_id)
        self.assertIn("custom_field", error_dict["context"])
        self.assertEqual(error_dict["context"]["custom_field"], "custom_value")
        self.assertIn("operation", error_dict["context"])
        self.assertIn("original_error_type", error_dict["context"])


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery mechanisms."""
    
    def test_retry_mechanism(self):
        """Test retry mechanism in safe operation wrapper."""
        call_count = 0
        
        @StandardizedErrorHandler.safe_operation_wrapper(
            operation_name="retry_test",
            agent_type="test",
            max_retries=2,
            retry_delay=0.1  # Short delay for testing
        )
        def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 times, succeed on 3rd
                raise ValueError(f"Attempt {call_count} failed")
            return f"Success on attempt {call_count}"
        
        # Should succeed after retries
        result = sometimes_failing_function()
        self.assertEqual(result, "Success on attempt 3")
        self.assertEqual(call_count, 3)
    
    def test_allowed_exceptions_passthrough(self):
        """Test that allowed exceptions pass through without wrapping."""
        from Agents.Exceptions import ValidationError
        
        @StandardizedErrorHandler.safe_operation_wrapper(
            operation_name="passthrough_test",
            agent_type="test",
            allowed_exceptions=(ValidationError,)
        )
        def validation_failing_function():
            raise ValidationError("This should pass through")
        
        # ValidationError should pass through unchanged
        with self.assertRaises(ValidationError) as cm:
            validation_failing_function()
        
        self.assertEqual(str(cm.exception), "This should pass through")


def run_error_handling_tests():
    """Run all standardized error handling tests."""
    print("Running Standardized Error Handling Tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestStandardizedErrorHandler,
        TestConvenienceFunctions,
        TestAgentIntegration,
        TestErrorRecovery
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Standardized Error Handling Validation Test")
    print("=" * 50)
    
    success = run_error_handling_tests()
    
    if success:
        print("\n✅ All error handling tests passed! Standardization complete.")
    else:
        print("\n❌ Some tests failed. Review error handling implementation.")
    
    print("\nStandardized error handling validation completed!")