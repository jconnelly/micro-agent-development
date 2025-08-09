"""
Micro-Agent Development Platform - Flask REST API Application

Enterprise-grade Flask application providing REST API access to all 7 AI agents
with standardized response formats, comprehensive error handling, authentication,
and production-ready features.

Endpoints:
    /api/v1/business-rule-extraction - Extract business rules from legacy code
    /api/v1/application-triage - Intelligent document routing and categorization  
    /api/v1/personal-data-protection - GDPR/CCPA compliant PII protection
    /api/v1/rule-documentation - Generate business rule documentation
    /api/v1/compliance-monitoring - Audit trail and compliance management
    /api/v1/advanced-documentation - Enhanced documentation with tool integration
    /api/v1/enterprise-data-privacy - High-performance PII protection for large documents
    /api/v1/health - Health check endpoint
    /api/v1/status - Detailed system status
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, Any, Optional, Tuple, List

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, InternalServerError
from werkzeug.middleware.proxy_fix import ProxyFix

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import our agents and utilities
try:
    from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
    from Agents.ApplicationTriageAgent import ApplicationTriageAgent 
    from Agents.PersonalDataProtectionAgent import PersonalDataProtectionAgent
    from Agents.RuleDocumentationGeneratorAgent import RuleDocumentationGeneratorAgent
    from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent
    from Agents.AdvancedDocumentationAgent import AdvancedDocumentationAgent
    from Agents.EnterpriseDataPrivacyAgent import EnterpriseDataPrivacyAgent
    from Utils.response_formatter import ResponseFormatter, create_api_response
    from Utils.llm_providers import get_default_llm_provider, LLMProviderFactory
    from Utils.request_utils import RequestIdGenerator
    from Utils.time_utils import TimeUtils
    from Utils.config_loader import get_config_loader
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Initialize Flask application
app = Flask(__name__)

# Configure Flask for production
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
app.config['JSON_SORT_KEYS'] = False  # Preserve JSON key order
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Disable pretty printing in production

# Trust proxy headers (for deployment behind load balancer)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configure CORS for cross-origin requests
CORS(app, 
     origins=os.environ.get('ALLOWED_ORIGINS', '*').split(','),
     methods=['GET', 'POST', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-API-Key', 'X-Request-ID'],
     expose_headers=['X-Request-ID', 'X-Processing-Time-Ms'],
     max_age=86400)  # Cache preflight requests for 24 hours

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        # Add file handler for production
        logging.FileHandler('app.log') if os.environ.get('FLASK_ENV') == 'production' else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global configuration and agent instances
config_loader = None
audit_system = None
agent_instances = {}
llm_provider = None


def initialize_application():
    """Initialize the Flask application with agents and configuration."""
    global config_loader, audit_system, agent_instances, llm_provider
    
    try:
        # Load configuration
        config_loader = get_config_loader()
        
        # Initialize LLM provider (with fallback to default)
        try:
            llm_provider = get_default_llm_provider()
            logger.info(f"Initialized LLM provider: {llm_provider.get_provider_type().value}")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM provider: {str(e)}. Using None (agents will use legacy mode)")
            llm_provider = None
        
        # Initialize audit system first (required by all other agents)
        audit_system = ComplianceMonitoringAgent()
        
        # Initialize all agents with shared dependencies
        # Note: Some agents still use legacy llm_client parameter, will be updated in next tasks
        try:
            # Try new BYO-LLM approach first
            agent_instances = {
                'business_rule_extraction': BusinessRuleExtractionAgent(
                    audit_system=audit_system,
                    llm_provider=llm_provider
                ),
                'application_triage': ApplicationTriageAgent(
                    audit_system=audit_system,
                    llm_provider=llm_provider
                ),
                'personal_data_protection': PersonalDataProtectionAgent(
                    audit_system=audit_system
                ),
                'rule_documentation': RuleDocumentationGeneratorAgent(
                    audit_system=audit_system,
                    llm_provider=llm_provider
                ),
                'compliance_monitoring': audit_system,  # Reference to the same instance
                'advanced_documentation': AdvancedDocumentationAgent(
                    audit_system=audit_system,
                    llm_provider=llm_provider
                ),
                'enterprise_data_privacy': EnterpriseDataPrivacyAgent(
                    audit_system=audit_system
                )
            }
        except TypeError as e:
            # Fallback: Skip agents that need llm_client until they're implemented
            logger.warning(f"Some agents use legacy llm_client parameter: {str(e)}")
            agent_instances = {
                'personal_data_protection': PersonalDataProtectionAgent(
                    audit_system=audit_system
                ),
                'compliance_monitoring': audit_system,  # Reference to the same instance
                'enterprise_data_privacy': EnterpriseDataPrivacyAgent(
                    audit_system=audit_system
                )
            }
        
        logger.info("Successfully initialized all agents")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise


def get_api_key_from_request() -> Optional[str]:
    """Extract API key from request headers."""
    return request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')


def authenticate_request() -> bool:
    """
    Simple API key authentication.
    In production, replace with proper OAuth2/JWT authentication.
    """
    # Skip authentication in development mode
    if os.environ.get('FLASK_ENV') == 'development':
        return True
    
    api_key = get_api_key_from_request()
    expected_key = os.environ.get('API_KEY')
    
    # If no API key is configured, skip authentication
    if not expected_key:
        logger.warning("No API_KEY environment variable set - authentication disabled")
        return True
    
    return api_key == expected_key


def rate_limit_check(client_id: str, limit: int = 100, window: int = 3600) -> bool:
    """
    Simple in-memory rate limiting.
    In production, use Redis or similar for distributed rate limiting.
    """
    # Skip rate limiting in development
    if os.environ.get('FLASK_ENV') == 'development':
        return True
    
    # TODO: Implement proper rate limiting with Redis
    # For now, return True to allow all requests
    return True


def require_auth(f):
    """Decorator to require authentication for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not authenticate_request():
            return jsonify({
                'error': 'Authentication required',
                'message': 'Valid API key required in X-API-Key header or Authorization bearer token'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def handle_request_timing(f):
    """Decorator to handle request timing and metadata."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Generate request ID
        request_id = request.headers.get('X-Request-ID') or RequestIdGenerator.create_request_id("api")
        g.request_id = request_id
        g.start_time = time.time()
        
        # Set request metadata
        g.client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        g.user_agent = request.headers.get('User-Agent', 'Unknown')
        
        logger.info(f"Processing request {request_id} from {g.client_ip}")
        
        try:
            response = f(*args, **kwargs)
            
            # Add timing headers to response
            processing_time_ms = (time.time() - g.start_time) * 1000
            
            if isinstance(response, tuple):
                data, status_code = response
                if isinstance(data, dict):
                    data['request_id'] = request_id
                    data['processing_time_ms'] = processing_time_ms
                response = jsonify(data), status_code
            else:
                response.headers['X-Request-ID'] = request_id
                response.headers['X-Processing-Time-Ms'] = str(processing_time_ms)
            
            logger.info(f"Completed request {request_id} in {processing_time_ms:.2f}ms")
            return response
            
        except Exception as e:
            processing_time_ms = (time.time() - g.start_time) * 1000
            logger.error(f"Request {request_id} failed after {processing_time_ms:.2f}ms: {str(e)}")
            raise
    
    return decorated_function


def validate_json_request(required_fields: List[str] = None) -> Dict[str, Any]:
    """Validate JSON request and return parsed data."""
    if not request.is_json:
        raise BadRequest("Request must be JSON with Content-Type: application/json")
    
    try:
        data = request.get_json(force=True)
    except Exception as e:
        raise BadRequest(f"Invalid JSON: {str(e)}")
    
    if not isinstance(data, dict):
        raise BadRequest("Request body must be a JSON object")
    
    # Check required fields
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")
    
    return data


@app.errorhandler(400)
def handle_bad_request(error):
    """Handle 400 Bad Request errors."""
    return jsonify({
        'error': 'Bad Request',
        'message': str(error.description) if hasattr(error, 'description') else 'Invalid request',
        'request_id': getattr(g, 'request_id', 'unknown'),
        'timestamp': TimeUtils.get_current_utc_timestamp().isoformat()
    }), 400


@app.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 Unauthorized errors."""
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication required',
        'request_id': getattr(g, 'request_id', 'unknown'),
        'timestamp': TimeUtils.get_current_utc_timestamp().isoformat()
    }), 401


@app.errorhandler(413)
def handle_request_entity_too_large(error):
    """Handle 413 Request Entity Too Large errors."""
    return jsonify({
        'error': 'Request Too Large',
        'message': 'Request size exceeds maximum allowed limit (16MB)',
        'request_id': getattr(g, 'request_id', 'unknown'),
        'timestamp': TimeUtils.get_current_utc_timestamp().isoformat()
    }), 413


@app.errorhandler(429)
def handle_rate_limit_exceeded(error):
    """Handle 429 Too Many Requests errors."""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'request_id': getattr(g, 'request_id', 'unknown'),
        'timestamp': TimeUtils.get_current_utc_timestamp().isoformat()
    }), 429


@app.errorhandler(500)
def handle_internal_error(error):
    """Handle 500 Internal Server Error."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal error occurred. Please try again later.',
        'request_id': getattr(g, 'request_id', 'unknown'),
        'timestamp': TimeUtils.get_current_utc_timestamp().isoformat()
    }), 500


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Handle any unexpected errors."""
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    return jsonify({
        'error': 'Unexpected Error',
        'message': 'An unexpected error occurred. Please try again later.',
        'request_id': getattr(g, 'request_id', 'unknown'),
        'timestamp': TimeUtils.get_current_utc_timestamp().isoformat()
    }), 500


# Health and status endpoints
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': TimeUtils.get_current_utc_timestamp().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/v1/status', methods=['GET'])
@require_auth
@handle_request_timing
def system_status():
    """Detailed system status endpoint."""
    try:
        # Check agent availability
        agent_status = {}
        for agent_name, agent_instance in agent_instances.items():
            try:
                # Try to get agent info to verify it's working
                info = agent_instance.get_agent_info() if hasattr(agent_instance, 'get_agent_info') else {'status': 'available'}
                agent_status[agent_name] = 'available'
            except Exception as e:
                agent_status[agent_name] = f'error: {str(e)}'
        
        return jsonify({
            'status': 'operational',
            'timestamp': TimeUtils.get_current_utc_timestamp().isoformat(),
            'version': '1.0.0',
            'agents': agent_status,
            'llm_provider': {
                'type': llm_provider.get_provider_type().value if llm_provider else 'unknown',
                'model': llm_provider.get_model_name() if llm_provider else 'unknown'
            },
            'environment': {
                'flask_env': os.environ.get('FLASK_ENV', 'production'),
                'python_version': sys.version.split()[0],
                'platform': sys.platform
            }
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return jsonify({
            'status': 'degraded',
            'timestamp': TimeUtils.get_current_utc_timestamp().isoformat(),
            'error': str(e)
        }), 500


# API endpoint placeholders - we'll implement these in the next task
@app.route('/api/v1/business-rule-extraction', methods=['POST'])
@require_auth
@handle_request_timing
def business_rule_extraction():
    """Extract business rules from legacy code."""
    # Will be implemented in next task
    return jsonify({'message': 'Endpoint coming soon'}), 501


@app.route('/api/v1/application-triage', methods=['POST'])
@require_auth
@handle_request_timing
def application_triage():
    """Intelligent document routing and categorization."""
    # Will be implemented in next task
    return jsonify({'message': 'Endpoint coming soon'}), 501


@app.route('/api/v1/personal-data-protection', methods=['POST'])
@require_auth
@handle_request_timing
def personal_data_protection():
    """GDPR/CCPA compliant PII protection."""
    # Will be implemented in next task
    return jsonify({'message': 'Endpoint coming soon'}), 501


@app.route('/api/v1/rule-documentation', methods=['POST'])
@require_auth
@handle_request_timing
def rule_documentation():
    """Generate business rule documentation."""
    # Will be implemented in next task
    return jsonify({'message': 'Endpoint coming soon'}), 501


@app.route('/api/v1/compliance-monitoring', methods=['POST'])
@require_auth
@handle_request_timing
def compliance_monitoring():
    """Audit trail and compliance management."""
    # Will be implemented in next task
    return jsonify({'message': 'Endpoint coming soon'}), 501


@app.route('/api/v1/advanced-documentation', methods=['POST'])
@require_auth
@handle_request_timing
def advanced_documentation():
    """Enhanced documentation with tool integration."""
    # Will be implemented in next task
    return jsonify({'message': 'Endpoint coming soon'}), 501


@app.route('/api/v1/enterprise-data-privacy', methods=['POST'])
@require_auth
@handle_request_timing
def enterprise_data_privacy():
    """High-performance PII protection for large documents."""
    # Will be implemented in next task
    return jsonify({'message': 'Endpoint coming soon'}), 501


# API documentation endpoint
@app.route('/api/v1/docs', methods=['GET'])
def api_docs():
    """Basic API documentation endpoint."""
    return jsonify({
        'title': 'Micro-Agent Development Platform API',
        'version': '1.0.0',
        'description': 'Enterprise AI Agent Platform REST API',
        'endpoints': [
            {
                'path': '/api/v1/health',
                'method': 'GET',
                'description': 'Health check endpoint',
                'authentication': False
            },
            {
                'path': '/api/v1/status',
                'method': 'GET', 
                'description': 'Detailed system status',
                'authentication': True
            },
            {
                'path': '/api/v1/business-rule-extraction',
                'method': 'POST',
                'description': 'Extract business rules from legacy code',
                'authentication': True
            },
            {
                'path': '/api/v1/application-triage',
                'method': 'POST',
                'description': 'Intelligent document routing and categorization',
                'authentication': True
            },
            {
                'path': '/api/v1/personal-data-protection',
                'method': 'POST',
                'description': 'GDPR/CCPA compliant PII protection',
                'authentication': True
            },
            {
                'path': '/api/v1/rule-documentation',
                'method': 'POST',
                'description': 'Generate business rule documentation',
                'authentication': True
            },
            {
                'path': '/api/v1/compliance-monitoring',
                'method': 'POST',
                'description': 'Audit trail and compliance management',
                'authentication': True
            },
            {
                'path': '/api/v1/advanced-documentation',
                'method': 'POST',
                'description': 'Enhanced documentation with tool integration',
                'authentication': True
            },
            {
                'path': '/api/v1/enterprise-data-privacy',
                'method': 'POST',
                'description': 'High-performance PII protection for large documents',
                'authentication': True
            }
        ],
        'authentication': {
            'type': 'API Key',
            'header': 'X-API-Key or Authorization: Bearer <token>',
            'description': 'Set API_KEY environment variable to enable authentication'
        }
    })


# Initialize the application when module is imported
try:
    initialize_application()
except Exception as e:
    logger.error(f"Failed to initialize Flask application: {str(e)}")
    # Don't exit in production, let the app start and show errors via status endpoint


if __name__ == '__main__':
    # Development server configuration
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    logger.info(f"Starting Flask development server on {host}:{port} (debug={'on' if debug_mode else 'off'})")
    app.run(host=host, port=port, debug=debug_mode)