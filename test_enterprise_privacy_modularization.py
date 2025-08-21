#!/usr/bin/env python3

"""
Test Suite for Enterprise Privacy Agent Modularization

Validates the modularized components of EnterpriseDataPrivacyAgent:
- PiiDetectionEngine: Core PII detection with grep tool integration
- FileProcessor: Standard file processing and encoding handling
- StreamingProcessor: Large file streaming and memory optimization
- BatchProcessor: Batch and concurrent processing operations

This test suite ensures all components work correctly after modularization.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Import the modularized components
from Agents.enterprise_privacy_components import (
    PiiDetectionEngine,
    FileProcessor,
    StreamingProcessor,
    BatchProcessor
)

# Import base types
from Utils.pii_components import PIIType, MaskingStrategy


class TestEnterprisePrivacyModularization(unittest.TestCase):
    """Test suite for enterprise privacy agent modularization."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock logger
        self.mock_logger = Mock()
        
        # Sample PII patterns for testing
        self.test_patterns = {
            PIIType.SSN: [r'\b\d{3}-\d{2}-\d{4}\b'],
            PIIType.EMAIL: [r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'],
            PIIType.PHONE_NUMBER: [r'\b\d{3}[- ]?\d{3}[- ]?\d{4}\b']
        }
        
        # Test configuration
        self.test_config = {
            'performance_thresholds': {
                'large_text_threshold': 10000,
                'large_file_mb': 10
            },
            'streaming': {
                'default_chunk_size': 1024,
                'max_chunk_size': 4096,
                'min_chunk_size': 512,
                'overlap_size': 100
            }
        }
        
        # Sample test content with PII
        self.test_content = """
        John Doe's information:
        SSN: 123-45-6789
        Email: john.doe@example.com
        Phone: 555-123-4567
        
        Additional data follows...
        """
    
    def test_pii_detection_engine_initialization(self):
        """Test PII detection engine initialization."""
        engine = PiiDetectionEngine(
            patterns=self.test_patterns,
            grep_tool=None,
            agent_config=self.test_config,
            logger=self.mock_logger
        )
        
        self.assertIsNotNone(engine)
        self.assertEqual(len(engine.patterns), 3)
        self.assertIn(PIIType.SSN, engine.patterns)
        self.assertIn(PIIType.EMAIL, engine.patterns)
        self.assertIn(PIIType.PHONE_NUMBER, engine.patterns)
        
        # Check compiled patterns were created
        self.assertEqual(len(engine._compiled_patterns), 3)
        
        # Validate performance stats initialization
        self.assertEqual(engine.detection_stats['total_detections'], 0)
        
        return True
    
    def test_pii_detection_engine_context_config(self):
        """Test context-specific configuration retrieval."""
        engine = PiiDetectionEngine(
            patterns=self.test_patterns,
            agent_config=self.test_config,
            logger=self.mock_logger
        )
        
        # Test different contexts
        financial_config = engine.get_context_config('financial')
        self.assertIn(PIIType.SSN, financial_config['priority_types'])
        self.assertIn(PIIType.CREDIT_CARD, financial_config['priority_types'])
        self.assertTrue(financial_config['strict_mode'])
        
        general_config = engine.get_context_config('general')
        self.assertIn(PIIType.EMAIL, general_config['priority_types'])
        self.assertFalse(general_config['strict_mode'])
        
        return True
    
    def test_pii_detection_with_standard_patterns(self):
        """Test PII detection using standard patterns."""
        engine = PiiDetectionEngine(
            patterns=self.test_patterns,
            agent_config=self.test_config,
            logger=self.mock_logger
        )
        
        result = engine.detect_pii_with_grep_tool(
            text=self.test_content,
            context="general",
            request_id="test-123"
        )
        
        self.assertTrue('detected_types' in result)
        self.assertTrue('matches' in result)
        self.assertTrue('detection_metadata' in result)
        
        # Should detect at least SSN, email, and phone
        detected_types = result['detected_types']
        self.assertGreater(len(detected_types), 0)
        
        # Check detection metadata
        metadata = result['detection_metadata']
        self.assertEqual(metadata['context'], 'general')
        self.assertEqual(metadata['request_id'], 'test-123')
        self.assertGreater(metadata['text_length'], 0)
        
        return True
    
    def test_file_processor_initialization(self):
        """Test file processor initialization."""
        processor = FileProcessor(
            read_tool=None,
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        self.assertIsNotNone(processor)
        self.assertEqual(processor.processing_stats['files_processed'], 0)
        
        return True
    
    def test_file_processor_with_temp_file(self):
        """Test file processor with temporary file."""
        processor = FileProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write(self.test_content)
            temp_file_path = temp_file.name
        
        try:
            result = processor.read_file_content(temp_file_path, "test-file-read")
            
            self.assertTrue(result['success'])
            self.assertIn('content', result)
            self.assertIn('metadata', result)
            self.assertIn('processing_info', result)
            
            # Check content was read correctly
            self.assertIn('john.doe@example.com', result['content'])
            
            # Check metadata
            metadata = result['metadata']
            self.assertTrue(metadata['file_exists'])
            self.assertGreater(metadata['file_size_bytes'], 0)
            
            # Check processing info
            processing_info = result['processing_info']
            self.assertGreater(processing_info['processing_duration_ms'], 0)
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
        
        return True
    
    def test_streaming_processor_initialization(self):
        """Test streaming processor initialization."""
        processor = StreamingProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        self.assertIsNotNone(processor)
        self.assertEqual(processor.streaming_stats['files_streamed'], 0)
        self.assertEqual(processor.default_chunk_size, 1024)
        self.assertEqual(processor.max_chunk_size, 4096)
        
        return True
    
    def test_streaming_processor_chunk_size_calculation(self):
        """Test optimal chunk size calculation."""
        processor = StreamingProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        # Test different file sizes
        small_file_chunk = processor._calculate_optimal_chunk_size(1024 * 1024)  # 1MB
        medium_file_chunk = processor._calculate_optimal_chunk_size(100 * 1024 * 1024)  # 100MB
        large_file_chunk = processor._calculate_optimal_chunk_size(5 * 1024 * 1024 * 1024)  # 5GB
        
        self.assertGreaterEqual(small_file_chunk, processor.min_chunk_size)
        self.assertLessEqual(small_file_chunk, processor.max_chunk_size)
        
        self.assertGreaterEqual(medium_file_chunk, small_file_chunk)
        self.assertLessEqual(large_file_chunk, processor.max_chunk_size)
        
        return True
    
    def test_batch_processor_initialization(self):
        """Test batch processor initialization."""
        processor = BatchProcessor(
            max_workers=4,
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        self.assertIsNotNone(processor)
        self.assertEqual(processor.max_workers, 4)
        self.assertEqual(processor.batch_stats['batches_processed'], 0)
        
        return True
    
    def test_batch_processor_file_analysis(self):
        """Test batch processor file analysis functionality."""
        processor = BatchProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        # Create multiple temporary files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f'_test_{i}.txt') as temp_file:
                temp_file.write(f"Test content {i}\n" * (100 * (i + 1)))  # Different sizes
                temp_files.append(temp_file.name)
        
        try:
            # Analyze the file batch
            analysis = processor._analyze_file_batch(temp_files)
            
            self.assertEqual(analysis['total_files'], 3)
            self.assertEqual(analysis['analyzable_files'], 3)
            self.assertGreater(analysis['total_size_bytes'], 0)
            self.assertGreater(analysis['average_file_size_bytes'], 0)
            
            # Test strategy determination
            strategy = processor._determine_processing_strategy(analysis)
            
            self.assertIn('use_concurrent_processor', strategy)
            self.assertIn('recommended_workers', strategy)
            self.assertIn('processing_mode', strategy)
            self.assertGreater(strategy['recommended_workers'], 0)
            
        finally:
            # Clean up
            for temp_file in temp_files:
                os.unlink(temp_file)
        
        return True
    
    def test_component_integration(self):
        """Test integration between modularized components."""
        # Initialize all components
        pii_engine = PiiDetectionEngine(
            patterns=self.test_patterns,
            agent_config=self.test_config,
            logger=self.mock_logger
        )
        
        file_processor = FileProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        streaming_processor = StreamingProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        batch_processor = BatchProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        # Verify all components initialized successfully
        self.assertIsNotNone(pii_engine)
        self.assertIsNotNone(file_processor)
        self.assertIsNotNone(streaming_processor)
        self.assertIsNotNone(batch_processor)
        
        # Test basic functionality integration
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write(self.test_content)
            temp_file_path = temp_file.name
        
        try:
            # File processing
            file_result = file_processor.read_file_content(temp_file_path)
            self.assertTrue(file_result['success'])
            
            # PII detection on the content
            pii_result = pii_engine.detect_pii_with_grep_tool(
                text=file_result['content'],
                context="general",
                request_id="integration-test"
            )
            self.assertIn('detected_types', pii_result)
            
        finally:
            os.unlink(temp_file_path)
        
        return True
    
    def test_performance_summaries(self):
        """Test performance summary generation for all components."""
        # Initialize components
        pii_engine = PiiDetectionEngine(
            patterns=self.test_patterns,
            agent_config=self.test_config,
            logger=self.mock_logger
        )
        
        file_processor = FileProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        streaming_processor = StreamingProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        batch_processor = BatchProcessor(
            logger=self.mock_logger,
            agent_config=self.test_config
        )
        
        # Get performance summaries
        pii_summary = pii_engine.get_performance_summary()
        file_summary = file_processor.get_performance_summary()
        streaming_summary = streaming_processor.get_performance_summary()
        batch_summary = batch_processor.get_performance_summary()
        
        # Validate summary structure
        self.assertIn('total_detections', pii_summary)
        self.assertIn('files_processed', file_summary)
        self.assertIn('files_streamed', streaming_summary)
        self.assertIn('batches_processed', batch_summary)
        
        # All should start with zero activity
        self.assertEqual(pii_summary['total_detections'], 0)
        self.assertEqual(file_summary['files_processed'], 0)
        self.assertEqual(streaming_summary['files_streamed'], 0)
        self.assertEqual(batch_summary['batches_processed'], 0)
        
        return True


def run_modularization_tests():
    """Run all modularization tests and return results."""
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestEnterprisePrivacyModularization)
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
        'all_passed': len(result.failures) == 0 and len(result.errors) == 0
    }


if __name__ == '__main__':
    print("Running Enterprise Privacy Agent Modularization Tests...")
    
    results = run_modularization_tests()
    
    print(f"\nTest Results Summary:")
    print(f"   Tests Run: {results['tests_run']}")
    print(f"   Failures: {results['failures']}")
    print(f"   Errors: {results['errors']}")
    print(f"   Success Rate: {results['success_rate']:.1f}%")
    
    if results['all_passed']:
        print("All modularization tests passed successfully!")
    else:
        print("Some tests failed. Review the output above for details.")
    
    exit(0 if results['all_passed'] else 1)