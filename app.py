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
    from Utils.response_formatter import ResponseFormatter
    from Utils.llm_providers import get_default_llm_provider, LLMProviderFactory
    from Utils.request_utils import RequestIdGenerator
    from Utils.time_utils import TimeUtils
    from Utils.config_loader import get_config_loader
    from api_docs import api_blueprint  # Import API documentation blueprint
    from app_monitoring import apm_metrics, monitor_request, start_system_metrics_updater
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

# Register API documentation blueprint
app.register_blueprint(api_blueprint, url_prefix='/api/v1')

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
                    data['processing_time_ms'] = processing_time_ms
                response = jsonify(data), status_code
            elif isinstance(response, dict):
                # Handle direct dictionary returns
                response['processing_time_ms'] = processing_time_ms
                response = jsonify(response)
            else:
                # Handle Flask Response objects
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


def create_simple_response(success: bool, message: str, data: Dict[str, Any] = None, 
                          error_code: str = None, error_details: str = None) -> Dict[str, Any]:
    """Create a simple standardized API response."""
    response = {
        'success': success,
        'message': message,
        'timestamp': TimeUtils.get_current_utc_timestamp().isoformat(),
        'request_id': getattr(g, 'request_id', 'unknown')
    }
    
    if success and data:
        response['data'] = data
    elif not success:
        response['error'] = error_code or 'UNKNOWN_ERROR'
        if error_details:
            response['error_details'] = error_details
    
    return response


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


@app.route('/api/v1/metrics', methods=['GET'])
def prometheus_metrics():
    """Prometheus metrics endpoint for monitoring."""
    try:
        metrics_output = apm_metrics.get_metrics()
        from flask import Response
        return Response(metrics_output, mimetype='text/plain')
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {str(e)}")
        return jsonify({'error': 'Metrics unavailable'}), 500


@app.route('/api/v1/performance/summary', methods=['GET'])
@require_auth
def performance_summary():
    """Get application performance summary."""
    try:
        time_window = request.args.get('time_window_minutes', 60, type=int)
        summary = apm_metrics.get_performance_summary(time_window)
        
        return jsonify({
            'status': 'success',
            'timestamp': TimeUtils.get_current_utc_timestamp().isoformat(),
            'performance_summary': summary
        })
        
    except Exception as e:
        logger.error(f"Performance summary failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': TimeUtils.get_current_utc_timestamp().isoformat(),
            'error': str(e)
        }), 500


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


# API endpoints - Full implementation
@app.route('/api/v1/business-rule-extraction', methods=['POST'])
@require_auth
@handle_request_timing
@monitor_request
def business_rule_extraction():
    """Extract business rules from legacy code."""
    try:
        # Validate request data
        data = validate_json_request(['legacy_code'])
        
        # Get the agent
        agent = agent_instances.get('business_rule_extraction')
        if not agent:
            return create_simple_response(
                success=False,
                message="Business Rule Extraction Agent not available", 
                error_code="AGENT_UNAVAILABLE"
            ), 503
        
        # Extract parameters
        legacy_code = data['legacy_code']
        context = data.get('context', None)
        audit_level = data.get('audit_level', 1)
        
        # Validate inputs
        if not legacy_code or not legacy_code.strip():
            return create_simple_response(
                success=False,
                message="Legacy code cannot be empty",
                error_code="VALIDATION_ERROR"
            ), 400
        
        if len(legacy_code) > 1000000:  # 1MB limit for legacy code
            return create_simple_response(
                success=False,
                message="Legacy code exceeds maximum size (1MB)",
                error_code="CONTENT_TOO_LARGE"
            ), 413
        
        # Call the agent
        result = agent.extract_and_translate_rules(
            legacy_code_snippet=legacy_code,
            context=context,
            audit_level=audit_level
        )
        
        # Format response using standardized response formatter
        return create_simple_response(
            success=True,
            message=f"Successfully extracted {len(result['extracted_rules'])} business rules",
            data={
                'extracted_rules': result['extracted_rules'],
                'total_rules': len(result['extracted_rules']),
                'audit_request_id': result['audit_log']['request_id']
            }
        )
        
    except BadRequest:
        # Re-raise BadRequest to be handled by error handler
        raise
    except Exception as e:
        logger.error(f"Business rule extraction failed: {str(e)}", exc_info=True)
        return create_simple_response(
            success=False,
            message="Failed to extract business rules",
            error_code="PROCESSING_ERROR",
            error_details=str(e)
        ), 500


@app.route('/api/v1/application-triage', methods=['POST'])
@require_auth
@handle_request_timing
@monitor_request
def application_triage():
    """Intelligent document routing and categorization."""
    try:
        # Validate request data
        data = validate_json_request(['submission_data'])
        
        # Get the agent
        agent = agent_instances.get('application_triage')
        if not agent:
            return create_simple_response(
                success=False,
                message="Application Triage Agent not available",
                error_code="AGENT_UNAVAILABLE"
            ), 503
        
        # Extract parameters
        submission_data = data['submission_data']
        audit_level = data.get('audit_level', 1)
        
        # Validate inputs
        if not isinstance(submission_data, dict):
            return create_simple_response(
                success=False,
                message="submission_data must be a JSON object",
                error_code="VALIDATION_ERROR"
            ), 400
        
        required_fields = ['id', 'content']
        missing_fields = [field for field in required_fields if field not in submission_data]
        if missing_fields:
            return create_simple_response(
                success=False,
                message=f"submission_data missing required fields: {', '.join(missing_fields)}",
                error_code="VALIDATION_ERROR"
            ), 400
        
        # Call the agent
        result = agent.triage_submission(
            submission_data=submission_data,
            audit_level=audit_level
        )
        
        # Format response
        return create_simple_response(
            success=True,
            message="Successfully processed application triage",
            data={
                'triage_decision': result['triage_decision'],
                'pii_processing': result.get('pii_processing', {}),
                'audit_request_id': result['audit_log']['request_id']
            }
        )
        
    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Application triage failed: {str(e)}", exc_info=True)
        return create_simple_response(
            success=False,
            message="Failed to process application triage",
            error_code="PROCESSING_ERROR",
            error_details=str(e)
        ), 500


@app.route('/api/v1/personal-data-protection', methods=['POST'])
@require_auth
@handle_request_timing
@monitor_request
def personal_data_protection():
    """GDPR/CCPA compliant PII protection."""
    try:
        # Validate request data
        data = validate_json_request(['data'])
        
        # Get the agent
        agent = agent_instances.get('personal_data_protection')
        if not agent:
            return create_simple_response(
                success=False,
                message="Personal Data Protection Agent not available",
                error_code="AGENT_UNAVAILABLE"
            ), 503
        
        # Extract parameters
        input_data = data['data']
        masking_strategy_str = data.get('masking_strategy', 'PARTIAL_MASK')
        audit_level = data.get('audit_level', 1)
        
        # Import and convert masking strategy
        from Agents.PersonalDataProtectionAgent import MaskingStrategy
        try:
            masking_strategy = MaskingStrategy[masking_strategy_str.upper()] if masking_strategy_str else None
        except (KeyError, AttributeError):
            masking_strategy = MaskingStrategy.PARTIAL_MASK  # Default fallback
        
        # Validate inputs
        if not input_data:
            return create_simple_response(
                success=False,
                message="Data for PII protection cannot be empty",
                error_code="VALIDATION_ERROR"
            ), 400
        
        # Call the agent
        result = agent.scrub_data(
            data=input_data,
            request_id=g.request_id,
            custom_strategy=masking_strategy,
            audit_level=audit_level
        )
        
        # Format response
        return create_simple_response(
            success=True,
            message=f"Successfully protected data with {len(result['pii_detected'])} PII types detected",
            data={
                'scrubbed_data': result['scrubbed_data'],
                'pii_types_detected': [pii.value for pii in result['pii_detected']],
                'scrubbing_summary': result['scrubbing_summary'],
                'audit_request_id': result['audit_log']['request_id']
            }
        )
        
    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Personal data protection failed: {str(e)}", exc_info=True)
        return create_simple_response(
            success=False,
            message="Failed to protect personal data",
            error_code="PROCESSING_ERROR",
            error_details=str(e)
        ), 500


@app.route('/api/v1/rule-documentation', methods=['POST'])
@require_auth
@handle_request_timing
@monitor_request
def rule_documentation():
    """Generate business rule documentation."""
    try:
        # Validate request data
        data = validate_json_request(['extracted_rules'])
        
        # Get the agent
        agent = agent_instances.get('rule_documentation')
        if not agent:
            return create_simple_response(
                success=False,
                message="Rule Documentation Agent not available",
                error_code="AGENT_UNAVAILABLE"
            ), 503
        
        # Extract parameters
        extracted_rules = data['extracted_rules']
        output_format = data.get('output_format', 'markdown')
        audit_level = data.get('audit_level', 1)
        
        # Validate inputs
        if not isinstance(extracted_rules, list):
            return create_simple_response(
                success=False,
                message="extracted_rules must be an array",
                error_code="VALIDATION_ERROR"
            ), 400
        
        if not extracted_rules:
            return create_simple_response(
                success=False,
                message="extracted_rules cannot be empty",
                error_code="VALIDATION_ERROR"
            ), 400
        
        if output_format not in ['markdown', 'json', 'html']:
            return create_simple_response(
                success=False,
                message="output_format must be 'markdown', 'json', or 'html'",
                error_code="VALIDATION_ERROR"
            ), 400
        
        # Call the agent
        result = agent.document_and_visualize_rules(
            extracted_rules=extracted_rules,
            output_format=output_format,
            audit_level=audit_level
        )
        
        # Format response
        return create_simple_response(
            success=True,
            message=f"Successfully generated {output_format} documentation for {len(extracted_rules)} rules",
            data={
                'generated_documentation': result['generated_documentation'],
                'output_format': output_format,
                'rule_count': len(extracted_rules),
                'audit_request_id': result['audit_log']['request_id']
            }
        )
        
    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Rule documentation failed: {str(e)}", exc_info=True)
        return create_simple_response(
            success=False,
            message="Failed to generate rule documentation",
            error_code="PROCESSING_ERROR",
            error_details=str(e)
        ), 500


@app.route('/api/v1/compliance-monitoring', methods=['POST'])
@require_auth
@handle_request_timing
@monitor_request
def compliance_monitoring():
    """Audit trail and compliance management."""
    try:
        # Validate request data
        data = validate_json_request(['operation'])
        
        # Get the agent
        agent = agent_instances.get('compliance_monitoring')
        if not agent:
            return create_simple_response(
                success=False,
                message="Compliance Monitoring Agent not available",
                error_code="AGENT_UNAVAILABLE"
            ), 503
        
        # Extract parameters
        operation = data['operation']
        
        # Handle different compliance operations
        if operation == 'query_logs':
            # Query audit logs
            filters = data.get('filters', {})
            result = agent.query_audit_logs(filters)
            
            return create_simple_response(
                success=True,
                message=f"Retrieved {len(result.get('logs', []))} audit log entries",
                data={
                    'audit_logs': result.get('logs', []),
                    'total_count': result.get('total_count', 0),
                    'filters_applied': filters
                }
            )
            
        elif operation == 'generate_report':
            # Generate compliance report
            report_type = data.get('report_type', 'summary')
            date_range = data.get('date_range', {})
            
            result = agent.generate_compliance_report(
                report_type=report_type,
                date_range=date_range
            )
            
            return create_simple_response(
                success=True,
                message=f"Generated {report_type} compliance report",
                data={
                    'report': result,
                    'report_type': report_type,
                    'date_range': date_range
                }
            )
            
        elif operation == 'get_metrics':
            # Get compliance metrics
            metric_type = data.get('metric_type', 'overview')
            
            # Use agent info as basic metrics (since full metrics not implemented)
            agent_info = agent.get_agent_info() if hasattr(agent, 'get_agent_info') else {}
            
            return create_simple_response(
                success=True,
                message="Retrieved compliance metrics",
                data={
                    'metrics': {
                        'agent_status': 'operational',
                        'metric_type': metric_type,
                        'agent_info': agent_info
                    }
                }
            )
            
        else:
            return create_simple_response(
                success=False,
                message=f"Unknown operation: {operation}. Supported: 'query_logs', 'generate_report', 'get_metrics'",
                error_code="VALIDATION_ERROR"
            ), 400
        
    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Compliance monitoring failed: {str(e)}", exc_info=True)
        return create_simple_response(
            success=False,
            message="Failed to process compliance monitoring request",
            error_code="PROCESSING_ERROR",
            error_details=str(e)
        ), 500


@app.route('/api/v1/advanced-documentation', methods=['POST'])
@require_auth
@handle_request_timing
@monitor_request
def advanced_documentation():
    """Enhanced documentation with tool integration."""
    try:
        # Validate request data
        data = validate_json_request(['extracted_rules'])
        
        # Get the agent
        agent = agent_instances.get('advanced_documentation')
        if not agent:
            return create_simple_response(
                success=False,
                message="Advanced Documentation Agent not available",
                error_code="AGENT_UNAVAILABLE"
            ), 503
        
        # Extract parameters
        extracted_rules = data['extracted_rules']
        output_directory = data.get('output_directory', 'documentation')
        output_formats = data.get('output_formats', ['markdown', 'json'])
        audit_level = data.get('audit_level', 2)
        
        # Validate inputs
        if not isinstance(extracted_rules, list):
            return create_simple_response(
                success=False,
                message="extracted_rules must be an array",
                error_code="VALIDATION_ERROR"
            ), 400
        
        if not extracted_rules:
            return create_simple_response(
                success=False,
                message="extracted_rules cannot be empty",
                error_code="VALIDATION_ERROR"
            ), 400
        
        if not isinstance(output_formats, list):
            return create_simple_response(
                success=False,
                message="output_formats must be an array",
                error_code="VALIDATION_ERROR"
            ), 400
        
        valid_formats = ['markdown', 'json', 'html']
        invalid_formats = [fmt for fmt in output_formats if fmt not in valid_formats]
        if invalid_formats:
            return create_simple_response(
                success=False,
                message=f"Invalid output formats: {', '.join(invalid_formats)}. Valid formats: {', '.join(valid_formats)}",
                error_code="VALIDATION_ERROR"
            ), 400
        
        # Call the agent
        result = agent.document_and_save_rules(
            extracted_rules=extracted_rules,
            output_directory=output_directory,
            output_formats=output_formats,
            audit_level=audit_level
        )
        
        # Format response
        return create_simple_response(
            success=True,
            message=f"Successfully generated documentation in {len(result['successful_files'])} files",
            data={
                'successful_files': result['successful_files'],
                'failed_files': result['failed_files'],
                'total_files_requested': result['total_files_requested'],
                'output_directory': result['output_directory'],
                'file_operations': result['file_operations'],
                'tool_integration': result['operation_metadata']['tool_integration']
            }
        )
        
    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Advanced documentation failed: {str(e)}", exc_info=True)
        return create_simple_response(
            success=False,
            message="Failed to generate advanced documentation",
            error_code="PROCESSING_ERROR",
            error_details=str(e)
        ), 500


@app.route('/api/v1/enterprise-data-privacy', methods=['POST'])
@require_auth
@handle_request_timing
@monitor_request
def enterprise_data_privacy():
    """High-performance PII protection for large documents."""
    try:
        # Validate request data
        data = validate_json_request(['data'])
        
        # Get the agent
        agent = agent_instances.get('enterprise_data_privacy')
        if not agent:
            return create_simple_response(
                success=False,
                message="Enterprise Data Privacy Agent not available",
                error_code="AGENT_UNAVAILABLE"
            ), 503
        
        # Extract parameters
        input_data = data['data']
        masking_strategy_str = data.get('masking_strategy', 'PARTIAL_MASK')
        batch_size = data.get('batch_size', 1000)
        audit_level = data.get('audit_level', 1)
        
        # Import and convert masking strategy
        from Agents.PersonalDataProtectionAgent import MaskingStrategy
        try:
            masking_strategy = MaskingStrategy[masking_strategy_str.upper()] if masking_strategy_str else None
        except (KeyError, AttributeError):
            masking_strategy = MaskingStrategy.PARTIAL_MASK  # Default fallback
        
        # Validate inputs
        if not input_data:
            return create_simple_response(
                success=False,
                message="Data for privacy protection cannot be empty",
                error_code="VALIDATION_ERROR"
            ), 400
        
        # Validate batch size
        if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 10000:
            return create_simple_response(
                success=False,
                message="batch_size must be an integer between 1 and 10000",
                error_code="VALIDATION_ERROR"
            ), 400
        
        # Call the agent (assuming it has similar interface to PersonalDataProtectionAgent)
        result = agent.scrub_data(
            data=input_data,
            request_id=g.request_id,
            custom_strategy=masking_strategy,
            audit_level=audit_level
        )
        
        # Format response
        return create_simple_response(
            success=True,
            message=f"Successfully processed enterprise data privacy with {len(result['pii_detected'])} PII types detected",
            data={
                'scrubbed_data': result['scrubbed_data'],
                'pii_types_detected': [pii.value for pii in result['pii_detected']],
                'scrubbing_summary': result['scrubbing_summary'],
                'performance_metrics': {
                    'batch_size': batch_size,
                    'masking_strategy': masking_strategy
                },
                'audit_request_id': result['audit_log']['request_id']
            }
        )
        
    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Enterprise data privacy failed: {str(e)}", exc_info=True)
        return create_simple_response(
            success=False,
            message="Failed to process enterprise data privacy",
            error_code="PROCESSING_ERROR",
            error_details=str(e)
        ), 500


# API documentation redirect endpoint
@app.route('/api/v1/docs', methods=['GET'])
def api_docs_redirect():
    """Redirect to comprehensive Swagger UI documentation."""
    from flask import redirect
    return redirect('/api/v1/docs/', code=302)

# API documentation information endpoint (JSON)
@app.route('/api/v1/docs/info', methods=['GET'])
def api_docs_info():
    """API documentation information endpoint."""
    return jsonify({
        'title': 'Micro-Agent Development Platform API',
        'version': '1.0.0',
        'description': 'Enterprise AI Agent Platform REST API with comprehensive Swagger documentation',
        'documentation_url': '/api/v1/docs/',
        'interactive_docs': 'Available at /api/v1/docs/ for testing and exploration',
        'endpoints_count': 9,
        'authentication': {
            'type': 'API Key',
            'header': 'X-API-Key or Authorization: Bearer <token>',
            'description': 'Set API_KEY environment variable to enable authentication'
        },
        'features': [
            'Interactive API testing with Swagger UI',
            'Comprehensive request/response examples',
            'Authentication flow documentation',
            'Error handling and status code documentation',
            'Multi-format response examples (JSON, Markdown, HTML)',
            'Business context and use case descriptions'
        ],
        'agent_endpoints': {
            'business_rule_extraction': {
                'path': '/api/v1/business-rule-extraction',
                'description': 'Extract business rules from legacy code systems',
                'use_cases': ['Legacy system modernization', 'Code documentation', 'Business rule preservation']
            },
            'personal_data_protection': {
                'path': '/api/v1/personal-data-protection', 
                'description': 'GDPR/CCPA compliant PII detection and masking',
                'use_cases': ['Data privacy compliance', 'PII anonymization', 'Regulatory reporting']
            },
            'application_triage': {
                'path': '/api/v1/application-triage',
                'description': 'Intelligent document routing and categorization',
                'use_cases': ['Document processing automation', 'Content classification', 'Workflow routing']
            },
            'rule_documentation': {
                'path': '/api/v1/rule-documentation',
                'description': 'Generate comprehensive business rule documentation',
                'use_cases': ['Business process documentation', 'Compliance documentation', 'Knowledge management']
            },
            'compliance_monitoring': {
                'path': '/api/v1/compliance-monitoring',
                'description': 'Audit trail and regulatory compliance management',
                'use_cases': ['Audit trail generation', 'Compliance reporting', 'Risk management']
            },
            'advanced_documentation': {
                'path': '/api/v1/advanced-documentation',
                'description': 'Enhanced documentation with tool integration',
                'use_cases': ['Technical documentation', 'API documentation', 'System integration docs']
            },
            'enterprise_data_privacy': {
                'path': '/api/v1/enterprise-data-privacy',
                'description': 'High-performance PII protection for large datasets',
                'use_cases': ['Bulk data processing', 'Data migration privacy', 'Large-scale anonymization']
            }
        }
    })


# Initialize the application when module is imported
try:
    initialize_application()
    # Start APM system metrics collection
    start_system_metrics_updater(update_interval=30)
    logger.info("APM monitoring initialized successfully")
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