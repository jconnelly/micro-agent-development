"""
Pytest configuration and fixtures for comprehensive agent testing.

Provides shared fixtures, test configuration, and utilities for
all test suites in the project.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
from typing import Dict, Any, Generator

# Import core components for testing
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel
from Agents.Logger import AgentLogger


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_audit_system():
    """Provide a mock audit system for testing."""
    audit_system = Mock(spec=ComplianceMonitoringAgent)
    audit_system.log_agent_activity.return_value = {
        'success': True,
        'audit_id': 'test_audit_123',
        'timestamp': '2023-12-01T10:00:00Z'
    }
    return audit_system


@pytest.fixture
def mock_llm_client():
    """Provide a mock LLM client for testing."""
    client = Mock()
    client.generate_content.return_value = Mock(
        text="Mock LLM response for testing",
        usage_metadata=Mock(
            prompt_token_count=10,
            candidates_token_count=20,
            total_token_count=30
        )
    )
    return client


@pytest.fixture
def test_logger():
    """Provide a test logger instance."""
    return AgentLogger(log_level=1, agent_name="TestAgent")


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for test file operations."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_pii_text():
    """Provide sample text containing various PII types for testing."""
    return """
    John Doe's contact information:
    Email: john.doe@example.com
    Phone: (555) 123-4567
    SSN: 123-45-6789
    Credit Card: 4532-1234-5678-9012
    Address: 123 Main St, Anytown, CA 90210
    IP Address: 192.168.1.100
    """


@pytest.fixture
def sample_legacy_code():
    """Provide sample legacy code for rule extraction testing."""
    return """
    IF CUSTOMER-CREDIT-SCORE > 700 THEN
        SET LOAN-APPROVAL = 'APPROVED'
        SET INTEREST-RATE = 3.5
    ELSE
        IF CUSTOMER-INCOME > 50000 THEN
            SET LOAN-APPROVAL = 'CONDITIONAL'
            SET INTEREST-RATE = 4.2
        ELSE
            SET LOAN-APPROVAL = 'DENIED'
        END-IF
    END-IF
    """


@pytest.fixture
def sample_business_rules():
    """Provide sample business rules for documentation testing."""
    return [
        {
            "rule_id": "LOAN_001",
            "condition": "credit_score > 700",
            "action": "approve_loan",
            "priority": "high",
            "business_domain": "lending"
        },
        {
            "rule_id": "LOAN_002", 
            "condition": "income < 30000",
            "action": "deny_loan",
            "priority": "high",
            "business_domain": "lending"
        }
    ]


@pytest.fixture
def sample_document_content():
    """Provide sample document content for triage testing."""
    return {
        "filename": "loan_application.pdf",
        "content": "Loan Application Form\nApplicant: Jane Smith\nRequested Amount: $50,000\nPurpose: Home improvement",
        "metadata": {
            "size": 1024,
            "type": "application/pdf",
            "created": "2023-12-01T10:00:00Z"
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables and configurations."""
    # Set test environment variables
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    # Mock external service calls during testing
    monkeypatch.setenv("MOCK_LLM_CALLS", "1")


@pytest.fixture
def performance_threshold():
    """Define performance thresholds for testing."""
    return {
        "pii_detection_ms": 100,        # PII detection should complete in <100ms
        "rule_extraction_s": 30,        # Rule extraction should complete in <30s
        "document_processing_s": 10,    # Document processing should complete in <10s
        "audit_logging_ms": 50,         # Audit logging should complete in <50ms
    }


# Test markers for categorizing tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "security: marks tests as security-focused"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance-focused"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "critical: marks tests as critical for production"
    )


# Utility functions for tests
def create_test_agent_config() -> Dict[str, Any]:
    """Create a test configuration for agents."""
    return {
        "timeout_seconds": 30,
        "max_retries": 3,
        "api_delay_seconds": 0.1,
        "cache_size": 128,
        "batch_size": 10,
        "chunk_size": 1024,
        "enable_audit": True,
        "enable_caching": True
    }


def assert_audit_called_with_operation(mock_audit, operation_type: str):
    """Assert that audit system was called with specific operation type."""
    assert mock_audit.log_agent_activity.called
    call_args = mock_audit.log_agent_activity.call_args
    assert operation_type in str(call_args)


def assert_no_pii_in_output(output: str, known_pii: list):
    """Assert that output doesn't contain any known PII values."""
    for pii_value in known_pii:
        assert pii_value not in output, f"PII value {pii_value} found in output"


def assert_performance_threshold(duration_ms: float, threshold_ms: float, operation: str):
    """Assert that operation completed within performance threshold."""
    assert duration_ms <= threshold_ms, \
        f"{operation} took {duration_ms}ms, exceeding threshold of {threshold_ms}ms"