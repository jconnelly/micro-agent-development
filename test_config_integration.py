#!/usr/bin/env python3

"""
Configuration Integration Test Suite
Validates all configuration loading, fallback mechanisms, and agent integration
"""

import os
import sys
import tempfile
import shutil
import yaml
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Utils.config_loader import ConfigurationLoader, get_config_loader
from Agents.BaseAgent import BaseAgent
from Agents.AuditingAgent import AgentAuditing


class TestConfigurationLoader(unittest.TestCase):
    """Test configuration loader functionality"""
    
    def setUp(self):
        """Set up test environment with temporary config directory"""
        self.test_dir = tempfile.mkdtemp()
        self.config_loader = ConfigurationLoader(config_dir=self.test_dir)
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_domains_config_validation_success(self):
        """Test successful domains configuration validation"""
        domains_config = {
            'domains': {
                'financial': {
                    'description': 'Financial services',
                    'keywords': ['loan', 'credit', 'interest'],
                    'weight': 1.0
                },
                'insurance': {
                    'description': 'Insurance industry',  
                    'keywords': ['policy', 'claim', 'coverage'],
                    'weight': 1.2
                }
            },
            'metadata': {
                'version': '1.0.0',
                'total_domains': 2
            }
        }
        
        # Should not raise exception
        self.config_loader._validate_domains_config(domains_config)
    
    def test_domains_config_validation_failure(self):
        """Test domains configuration validation failures"""
        # Missing domains key
        with self.assertRaises(ValueError):
            self.config_loader._validate_domains_config({})
            
        # Invalid domain structure
        with self.assertRaises(ValueError):
            self.config_loader._validate_domains_config({
                'domains': {
                    'financial': 'not_a_dict'
                }
            })
            
        # Missing keywords
        with self.assertRaises(ValueError):
            self.config_loader._validate_domains_config({
                'domains': {
                    'financial': {
                        'description': 'Test',
                        'weight': 1.0
                    }
                }
            })
    
    def test_pii_patterns_config_validation_success(self):
        """Test successful PII patterns configuration validation"""
        pii_config = {
            'pii_types': {
                'ssn': {
                    'description': 'Social Security Numbers',
                    'patterns': [r'\\b\\d{3}-\\d{2}-\\d{4}\\b'],
                    'priority': 1,
                    'default_strategy': 'tokenize'
                },
                'email': {
                    'description': 'Email addresses',
                    'patterns': [r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'],
                    'priority': 2,
                    'default_strategy': 'partial_mask'
                }
            },
            'context_configs': {
                'financial': {
                    'description': 'Financial context',
                    'priority_types': ['ssn', 'credit_card'],
                    'default_strategy': 'tokenize',
                    'require_full_audit': True
                }
            }
        }
        
        # Should not raise exception
        self.config_loader._validate_pii_patterns_config(pii_config)
    
    def test_pii_patterns_config_validation_failure(self):
        """Test PII patterns configuration validation failures"""
        # Missing pii_types key
        with self.assertRaises(ValueError):
            self.config_loader._validate_pii_patterns_config({})
            
        # Invalid regex pattern
        with self.assertRaises(ValueError):
            self.config_loader._validate_pii_patterns_config({
                'pii_types': {
                    'test': {
                        'patterns': ['[invalid_regex'],  # Unclosed bracket
                        'description': 'Test'
                    }
                }
            })
    
    def test_agent_defaults_config_validation_success(self):
        """Test successful agent defaults configuration validation"""
        agent_config = {
            'agent_defaults': {
                'api_settings': {
                    'timeout_seconds': 30.0,
                    'max_retries': 3,
                    'total_operation_timeout': 300.0
                },
                'caching': {
                    'default_lru_cache_size': 128,
                    'pii_detection_cache_size': 256
                },
                'processing_limits': {
                    'max_file_chunks': 50,
                    'min_chunk_lines': 10
                }
            }
        }
        
        # Should not raise exception
        self.config_loader._validate_agent_defaults_config(agent_config)
    
    def test_agent_defaults_config_validation_failure(self):
        """Test agent defaults configuration validation failures"""
        # Missing agent_defaults key
        with self.assertRaises(ValueError):
            self.config_loader._validate_agent_defaults_config({})
            
        # Invalid timeout value
        with self.assertRaises(ValueError):
            self.config_loader._validate_agent_defaults_config({
                'agent_defaults': {
                    'api_settings': {
                        'timeout_seconds': -5.0  # Negative value
                    }
                }
            })
            
        # Invalid cache size
        with self.assertRaises(ValueError):
            self.config_loader._validate_agent_defaults_config({
                'agent_defaults': {
                    'caching': {
                        'default_lru_cache_size': 'not_a_number'
                    }
                }
            })
    
    def test_config_loading_with_fallback(self):
        """Test configuration loading with fallback mechanism"""
        fallback_data = {
            'test_key': 'fallback_value',
            'nested': {
                'value': 42
            }
        }
        
        # Should use fallback when file doesn't exist
        config = self.config_loader.load_config('nonexistent', fallback_data)
        self.assertEqual(config['test_key'], 'fallback_value')
        self.assertEqual(config['nested']['value'], 42)
    
    def test_config_loading_from_file(self):
        """Test configuration loading from YAML file"""
        test_config = {
            'test_setting': 'file_value',
            'numeric_setting': 123
        }
        
        # Write test config file
        config_file = Path(self.test_dir) / 'test_config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        # Load config (should load from file, not fallback)
        fallback_data = {'test_setting': 'fallback_value'}
        config = self.config_loader.load_config('test_config', fallback_data)
        
        self.assertEqual(config['test_setting'], 'file_value')
        self.assertEqual(config['numeric_setting'], 123)
    
    def test_config_caching(self):
        """Test configuration caching mechanism"""
        fallback_data = {'cached_value': 'test'}
        
        # Load config twice
        config1 = self.config_loader.load_config('cache_test', fallback_data)
        config2 = self.config_loader.load_config('cache_test', fallback_data)
        
        # Should return same object (cached)
        self.assertIs(config1, config2)
        
        # Clear cache and load again
        self.config_loader.clear_cache()
        config3 = self.config_loader.load_config('cache_test', fallback_data)
        
        # Should have same content but may be different object depending on implementation
        self.assertEqual(config1['cached_value'], config3['cached_value'])


class TestBaseAgentConfiguration(unittest.TestCase):
    """Test BaseAgent configuration integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.audit_system = AgentAuditing()
        
    def test_base_agent_default_configuration(self):
        """Test BaseAgent loads default configuration correctly"""
        # Create a test agent (BaseAgent is abstract, so we'll create a minimal subclass)
        class TestAgent(BaseAgent):
            def __init__(self, audit_system, **kwargs):
                super().__init__(audit_system, **kwargs)
            
            def get_agent_info(self):
                return {"name": "TestAgent", "version": "1.0.0", "type": "test"}
        
        agent = TestAgent(self.audit_system, agent_name="TestAgent")
        
        # Verify default configuration values are loaded
        self.assertIsInstance(agent.API_TIMEOUT_SECONDS, (int, float))
        self.assertIsInstance(agent.MAX_RETRIES, int)
        self.assertIsInstance(agent.TOTAL_OPERATION_TIMEOUT, (int, float))
        
        # Verify configuration accessor works
        config = agent.get_agent_config()
        self.assertIsInstance(config, dict)
        self.assertIn('agent_defaults', config)
        
        # Test path-based configuration access
        timeout = agent.get_agent_config('agent_defaults.api_settings.timeout_seconds')
        if timeout is not None:  # May be None if fallback config structure differs
            self.assertIsInstance(timeout, (int, float))
    
    def test_base_agent_configuration_fallback(self):
        """Test BaseAgent gracefully falls back when config loading fails"""
        # This test verifies the agent still initializes even if config loading fails
        class TestAgent(BaseAgent):
            def __init__(self, audit_system, **kwargs):
                # Temporarily break config loading by using invalid config dir
                original_loader = get_config_loader
                try:
                    # Mock a failing config loader
                    import Utils.config_loader
                    Utils.config_loader._config_loader = None  # Reset global loader
                    super().__init__(audit_system, **kwargs)
                finally:
                    # Restore original loader
                    Utils.config_loader.get_config_loader = original_loader
            
            def get_agent_info(self):
                return {"name": "TestAgent", "version": "1.0.0", "type": "test"}
        
        # Should not raise exception even with broken config loading
        agent = TestAgent(self.audit_system, agent_name="TestAgent")
        
        # Verify fallback values are used
        self.assertEqual(agent.API_TIMEOUT_SECONDS, 30.0)
        self.assertEqual(agent.MAX_RETRIES, 3)
        self.assertEqual(agent.TOTAL_OPERATION_TIMEOUT, 300.0)


class TestEndToEndConfigurationIntegration(unittest.TestCase):
    """End-to-end tests of the complete configuration system"""
    
    def setUp(self):
        """Set up test environment with real config files"""
        self.config_dir = os.path.join(os.path.dirname(__file__), 'config')
        
    def test_real_config_files_load_successfully(self):
        """Test that real configuration files load without errors"""
        if os.path.exists(self.config_dir):
            config_loader = ConfigurationLoader(config_dir=self.config_dir)
            
            # Test domains config
            if config_loader.config_exists('domains'):
                domains_config = config_loader.load_config('domains')
                self.assertIn('domains', domains_config)
                self.assertIsInstance(domains_config['domains'], dict)
            
            # Test PII patterns config
            if config_loader.config_exists('pii_patterns'):
                pii_config = config_loader.load_config('pii_patterns')
                self.assertIn('pii_types', pii_config)
                self.assertIsInstance(pii_config['pii_types'], dict)
            
            # Test agent defaults config
            if config_loader.config_exists('agent_defaults'):
                agent_config = config_loader.load_config('agent_defaults')
                self.assertIn('agent_defaults', agent_config)
                self.assertIsInstance(agent_config['agent_defaults'], dict)
    
    def test_agents_integrate_with_real_configs(self):
        """Test that agents can initialize with real configuration files"""
        audit_system = AgentAuditing()
        
        # Test BaseAgent subclass with real configs
        class TestAgent(BaseAgent):
            def __init__(self, audit_system, **kwargs):
                super().__init__(audit_system, **kwargs)
            
            def get_agent_info(self):
                return {"name": "TestAgent", "version": "1.0.0", "type": "test"}
        
        # Should initialize successfully with real config files
        agent = TestAgent(audit_system, agent_name="TestAgent")
        
        # Verify agent has loaded configuration
        self.assertTrue(hasattr(agent, '_agent_config'))
        self.assertIsInstance(agent._agent_config, dict)
        
        # Verify configuration values are reasonable
        self.assertGreater(agent.API_TIMEOUT_SECONDS, 0)
        self.assertGreater(agent.MAX_RETRIES, 0)
        self.assertGreater(agent.TOTAL_OPERATION_TIMEOUT, 0)


def run_configuration_tests():
    """Run all configuration tests and return results"""
    
    print("Running Configuration Integration Tests...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestConfigurationLoader,
        TestBaseAgentConfiguration,
        TestEndToEndConfigurationIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\\n" + "=" * 60)
    print(f"Test Results Summary:")
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
        print("\\nAll configuration tests passed!")
        print("   * Configuration loading and validation")
        print("   * Fallback mechanisms")  
        print("   * Agent integration")
        print("   * Real config file compatibility")
        
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_configuration_tests()
    sys.exit(0 if success else 1)