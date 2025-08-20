"""
Unit tests for BusinessRuleExtractionAgent with COBOL sample data.

This test module specifically validates that the BusinessRuleExtractionAgent
can process COBOL legacy code without input validation errors.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel
from Agents.Exceptions import ValidationError


class TestBusinessRuleExtractionCOBOL:
    """Test BusinessRuleExtractionAgent with COBOL legacy code."""
    
    @pytest.fixture
    def cobol_sample_code(self):
        """Load the COBOL sample file for testing."""
        cobol_file_path = project_root / "Sample_Data_Files" / "sample_legacy_insurance.cbl"
        
        if not cobol_file_path.exists():
            pytest.skip(f"COBOL sample file not found: {cobol_file_path}")
        
        with open(cobol_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client for testing."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = """
        {
            "extracted_rules": [
                {
                    "rule_id": "AGE_MINIMUM",
                    "rule_name": "Minimum Age Requirement",
                    "description": "Applicant must be at least 18 years old",
                    "business_logic": "IF APPLICANT-AGE < MIN-AGE THEN REJECT",
                    "domain": "Insurance Eligibility"
                },
                {
                    "rule_id": "CREDIT_SCORE_MIN",
                    "rule_name": "Credit Score Validation",
                    "description": "Credit score must be at least 600",
                    "business_logic": "IF CREDIT-SCORE < MIN-CREDIT-SCORE THEN REJECT",
                    "domain": "Financial Validation"
                }
            ]
        }
        """
        mock_client.generate_content.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def audit_system(self):
        """Create audit system for testing."""
        import os
        os.makedirs("./Rule_Agent_Output_Files", exist_ok=True)
        return ComplianceMonitoringAgent(log_storage_path="./Rule_Agent_Output_Files/cobol_test_audit.jsonl")
    
    @pytest.fixture
    def agent(self, mock_llm_client, audit_system):
        """Create BusinessRuleExtractionAgent with mock dependencies."""
        return BusinessRuleExtractionAgent(
            llm_client=mock_llm_client,
            audit_system=audit_system,
            log_level=1,
            model_name="mock-model",
            llm_provider="mock"
        )
    
    def test_cobol_input_validation_passes(self, agent, cobol_sample_code):
        """Test that COBOL code passes input validation without errors."""
        # This should not raise ValidationError
        try:
            # Test just the validation part without calling LLM
            with patch.object(agent, '_api_call_with_retry') as mock_llm:
                mock_llm.return_value = {
                    "extracted_rules": [],
                    "processing_notes": ["Mock response"]
                }
                
                result = agent.extract_and_translate_rules(
                    legacy_code_snippet=cobol_sample_code,
                    context="COBOL insurance validation system",
                    audit_level=AuditLevel.LEVEL_1.value
                )
                
                # Should return a dict with extracted_rules
                assert isinstance(result, dict)
                assert "extracted_rules" in result
                
        except ValidationError as e:
            pytest.fail(f"COBOL code failed input validation: {e}")
    
    def test_cobol_special_characters_accepted(self, agent):
        """Test that COBOL-specific special characters are accepted."""
        cobol_snippet = """
        77  MIN-AGE                    PIC 99 VALUE 18.
        * Business Rule: Minimum age requirement
        IF APPLICANT-AGE < MIN-AGE
            MOVE 'REJECTED' TO POLICY-STATUS
        END-IF.
        """
        
        with patch.object(agent, '_api_call_with_retry') as mock_llm:
            mock_llm.return_value = {"extracted_rules": []}
            
            # Should not raise ValidationError
            result = agent.extract_and_translate_rules(
                legacy_code_snippet=cobol_snippet,
                context="COBOL business rule test",
                audit_level=AuditLevel.LEVEL_1.value
            )
            
            assert isinstance(result, dict)
    
    def test_cobol_file_size_handling(self, agent, cobol_sample_code):
        """Test that large COBOL files are handled properly."""
        # The sample file is 11,040 characters, should trigger chunking
        assert len(cobol_sample_code) > 5000, "Sample file should be large enough to test chunking"
        
        with patch.object(agent, '_api_call_with_retry') as mock_llm:
            mock_llm.return_value = {"extracted_rules": []}
            
            result = agent.extract_and_translate_rules(
                legacy_code_snippet=cobol_sample_code,
                context="Large COBOL file test",
                audit_level=AuditLevel.LEVEL_1.value
            )
            
            assert isinstance(result, dict)
            assert "extracted_rules" in result
    
    def test_cobol_context_parameter(self, agent, cobol_sample_code):
        """Test that COBOL context is properly handled."""
        contexts = [
            "Legacy COBOL insurance system from 1985",
            "Mainframe COBOL business rules",
            "COBOL policy validation logic"
        ]
        
        for context in contexts:
            with patch.object(agent, '_api_call_with_retry') as mock_llm:
                mock_llm.return_value = {"extracted_rules": []}
                
                result = agent.extract_and_translate_rules(
                    legacy_code_snippet=cobol_sample_code[:1000],  # Use subset for speed
                    context=context,
                    audit_level=AuditLevel.LEVEL_1.value
                )
                
                assert isinstance(result, dict)
    
    def test_input_validation_parameters(self, agent):
        """Test that input validation parameters work correctly."""
        valid_params = {
            'legacy_code_snippet': "77 TEST-VALUE PIC 99 VALUE 10.",
            'context': "Test context",
            'audit_level': 1
        }
        
        # Test each parameter validation
        with patch.object(agent, '_api_call_with_retry') as mock_llm:
            mock_llm.return_value = {"extracted_rules": []}
            
            # Valid parameters should work
            result = agent.extract_and_translate_rules(**valid_params)
            assert isinstance(result, dict)
            
            # Test minimum length requirement
            with pytest.raises(ValidationError):
                agent.extract_and_translate_rules(
                    legacy_code_snippet="short",  # Too short
                    context="Test",
                    audit_level=1
                )
            
            # Test maximum length (should not exceed 1MB)
            large_code = "A" * (1000000 + 1)  # 1MB + 1 byte
            with pytest.raises(ValidationError):
                agent.extract_and_translate_rules(
                    legacy_code_snippet=large_code,
                    context="Test",
                    audit_level=1
                )

    @pytest.mark.integration
    def test_cobol_end_to_end_mock(self, agent, cobol_sample_code, mock_llm_client):
        """Integration test with mocked LLM for COBOL processing."""
        # Configure mock to return structured response
        mock_response = Mock()
        mock_response.text = '{"extracted_rules": [{"rule_id": "TEST", "rule_name": "Test Rule"}]}'
        mock_llm_client.generate_content.return_value = mock_response
        
        result = agent.extract_and_translate_rules(
            legacy_code_snippet=cobol_sample_code,
            context="End-to-end COBOL test",
            audit_level=AuditLevel.LEVEL_1.value
        )
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "extracted_rules" in result
        assert "audit_log" in result
        
        # Verify audit log
        audit_log = result["audit_log"]
        assert audit_log["operation"] == "extract_and_translate_rules"
        assert "cobol" in audit_log["context"].lower() or "insurance" in audit_log["context"].lower()


if __name__ == "__main__":
    # Can be run directly
    pytest.main([__file__, "-v"])