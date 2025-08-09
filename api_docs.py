"""
OpenAPI/Swagger Documentation Configuration for Micro-Agent Development Platform

Provides comprehensive interactive API documentation for all 7 agent endpoints
with request/response examples, authentication details, and error handling.
"""

from flask_restx import Api, Resource, fields, Namespace
from flask import Blueprint

# Create API documentation blueprint
api_blueprint = Blueprint('api_docs', __name__)

# Configure Flask-RESTX API with comprehensive metadata
api = Api(
    api_blueprint,
    version='1.0.0',
    title='Micro-Agent Development Platform API',
    description='''
    **Enterprise AI Agent Platform for Business Rule Extraction, PII Protection, and Document Processing**
    
    This API provides access to 7 specialized AI agents designed for enterprise-scale business process automation:
    
    ## 🚀 Key Features
    - **Business Rule Extraction**: Extract and translate business rules from legacy systems
    - **PII Protection**: GDPR/CCPA compliant personally identifiable information detection and masking
    - **Document Processing**: Intelligent document routing and categorization
    - **Compliance Monitoring**: Complete audit trail and regulatory compliance management
    - **Multi-format Documentation**: Generate business documentation in Markdown, JSON, and HTML
    - **BYO-LLM Support**: Bring Your Own LLM with support for OpenAI, Claude, Gemini, and Azure OpenAI
    
    ## 🔐 Authentication
    API requests require authentication via the `X-API-Key` header or `api_key` query parameter.
    
    ## 📊 Rate Limits  
    - **Development**: No limits
    - **Production**: 60 requests/minute, 1000 requests/hour per API key
    
    ## 🎯 Response Format
    All endpoints return standardized JSON responses with consistent error handling and audit metadata.
    ''',
    doc='/docs/',  # Swagger UI endpoint
    contact='Micro-Agent Development Team',
    license='MIT',
    license_url='https://opensource.org/licenses/MIT',
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'API key for authentication. Required for all endpoints except health checks.'
        }
    },
    security='apikey'
)

# =============================================================================
# Shared Models for Request/Response Documentation
# =============================================================================

# Standard response model
standard_response = api.model('StandardResponse', {
    'success': fields.Boolean(description='Whether the operation succeeded', example=True),
    'data': fields.Raw(description='Response data (varies by endpoint)'),
    'metadata': fields.Nested(api.model('ResponseMetadata', {
        'request_id': fields.String(description='Unique request identifier', example='req_a1b2c3d4e5f6'),
        'agent_name': fields.String(description='Name of the processing agent', example='BusinessRuleExtractionAgent'),
        'processing_time_ms': fields.Float(description='Processing time in milliseconds', example=1250.5),
        'timestamp': fields.DateTime(description='Response timestamp', example='2025-01-09T15:30:45Z'),
        'audit_level': fields.Integer(description='Audit detail level used', example=2)
    })),
    'format_info': fields.Nested(api.model('FormatInfo', {
        'primary_format': fields.String(description='Primary response format', example='embedded'),
        'available_formats': fields.List(fields.String(), description='Available output formats', example=['markdown', 'json', 'html']),
        'embedded_content': fields.Raw(description='Embedded formatted content')
    }))
})

# Error response model
error_response = api.model('ErrorResponse', {
    'success': fields.Boolean(description='Always false for errors', example=False),
    'error': fields.Nested(api.model('ErrorDetails', {
        'type': fields.String(description='Error type classification', example='ValidationError'),
        'message': fields.String(description='Human-readable error message', example='Invalid input parameters'),
        'code': fields.String(description='Machine-readable error code', example='INVALID_INPUT'),
        'details': fields.Raw(description='Additional error context'),
        'troubleshooting': fields.Nested(api.model('Troubleshooting', {
            'common_causes': fields.List(fields.String(), description='Common causes of this error'),
            'suggested_solutions': fields.List(fields.String(), description='Suggested solutions'),
            'documentation_links': fields.List(fields.String(), description='Relevant documentation links')
        }))
    })),
    'metadata': fields.Nested(api.model('ErrorMetadata', {
        'request_id': fields.String(description='Request ID for error tracking', example='req_error_123'),
        'timestamp': fields.DateTime(description='Error timestamp', example='2025-01-09T15:30:45Z'),
        'endpoint': fields.String(description='API endpoint that generated the error', example='/api/v1/business-rule-extraction')
    }))
})

# =============================================================================
# Business Rule Extraction Namespace
# =============================================================================
business_rule_ns = Namespace(
    'business-rule-extraction',
    description='Extract and translate business rules from legacy code systems'
)

business_rule_request = api.model('BusinessRuleRequest', {
    'legacy_code_snippet': fields.String(
        required=True,
        description='Legacy code to analyze (COBOL, Java, C++, Python, etc.)',
        example='''
        IF CUSTOMER-AGE > 65 AND ACCOUNT-BALANCE > 10000 
            MOVE "SENIOR-PREMIUM" TO CUSTOMER-TIER
        ELSE
            MOVE "STANDARD" TO CUSTOMER-TIER
        END-IF
        '''
    ),
    'context': fields.String(
        description='Business context for rule extraction (optional)',
        example='Customer tier classification system for banking application'
    ),
    'audit_level': fields.Integer(
        description='Audit detail level (1=basic, 2=detailed, 3=comprehensive, 4=full)',
        example=2,
        enum=[1, 2, 3, 4]
    ),
    'output_format': fields.String(
        description='Preferred output format',
        example='embedded',
        enum=['embedded', 'markdown', 'json']
    )
})

business_rule_response = api.inherit('BusinessRuleResponse', standard_response, {
    'data': fields.Nested(api.model('BusinessRuleData', {
        'extracted_rules': fields.List(
            fields.Nested(api.model('ExtractedRule', {
                'rule_id': fields.String(description='Unique rule identifier', example='RULE_001'),
                'business_logic': fields.String(description='Natural language business rule', example='Senior customers with balance over $10,000 receive premium tier status'),
                'conditions': fields.List(fields.String(), description='Rule conditions', example=['Customer age > 65', 'Account balance > $10,000']),
                'actions': fields.List(fields.String(), description='Rule actions', example=['Set customer tier to SENIOR-PREMIUM']),
                'complexity_score': fields.Float(description='Rule complexity score (0-10)', example=3.5),
                'confidence_level': fields.Float(description='Extraction confidence (0-1)', example=0.95)
            }))
        ),
        'total_rules_found': fields.Integer(description='Total number of rules extracted', example=5),
        'processing_summary': fields.Nested(api.model('ProcessingSummary', {
            'lines_analyzed': fields.Integer(description='Lines of code analyzed', example=150),
            'language_detected': fields.String(description='Programming language detected', example='COBOL'),
            'complexity_assessment': fields.String(description='Overall complexity assessment', example='Medium')
        }))
    }))
})

# =============================================================================
# Personal Data Protection Namespace
# =============================================================================
pii_protection_ns = Namespace(
    'personal-data-protection',
    description='GDPR/CCPA compliant PII detection and masking for data privacy'
)

pii_request = api.model('PIIProtectionRequest', {
    'data': fields.String(
        required=True,
        description='Text data to scan for PII',
        example='Customer John Smith (SSN: 123-45-6789) called from phone 555-123-4567 about his account.'
    ),
    'context': fields.String(
        description='Data context for PII handling',
        example='financial',
        enum=['financial', 'healthcare', 'general', 'legal', 'government']
    ),
    'masking_strategy': fields.String(
        description='PII masking strategy',
        example='partial_mask',
        enum=['full_mask', 'partial_mask', 'tokenize', 'hash', 'remove']
    ),
    'audit_level': fields.Integer(
        description='Audit detail level',
        example=2,
        enum=[1, 2, 3, 4]
    ),
    'enable_tokenization': fields.Boolean(
        description='Enable reversible tokenization for authorized access',
        example=True
    )
})

pii_response = api.inherit('PIIProtectionResponse', standard_response, {
    'data': fields.Nested(api.model('PIIProtectionData', {
        'scrubbed_data': fields.String(description='Data with PII masked/removed', example='Customer [NAME] (SSN: ***-**-****) called from phone ***-***-*567 about his account.'),
        'pii_found': fields.List(
            fields.Nested(api.model('PIIDetection', {
                'type': fields.String(description='Type of PII detected', example='ssn'),
                'original_value': fields.String(description='Original PII value (logged securely)', example='[REDACTED]'),
                'masked_value': fields.String(description='Masked replacement value', example='***-**-****'),
                'position': fields.Nested(api.model('PIIPosition', {
                    'start': fields.Integer(description='Start character position', example=25),
                    'end': fields.Integer(description='End character position', example=36)
                })),
                'confidence': fields.Float(description='Detection confidence score', example=0.98)
            }))
        ),
        'protection_summary': fields.Nested(api.model('PIIProtectionSummary', {
            'total_pii_found': fields.Integer(description='Total PII instances detected', example=3),
            'pii_types_detected': fields.List(fields.String(), description='Types of PII found', example=['ssn', 'phone_number', 'name']),
            'masking_strategy_applied': fields.String(description='Masking strategy used', example='partial_mask'),
            'data_safety_score': fields.Float(description='Data safety score after masking', example=9.8)
        }))
    }))
})

# =============================================================================
# Add namespaces to API
# =============================================================================
api.add_namespace(business_rule_ns, path='/business-rule-extraction')
api.add_namespace(pii_protection_ns, path='/personal-data-protection')

# =============================================================================
# Health and System Status Documentation
# =============================================================================
system_ns = Namespace('system', description='Health checks and system monitoring')

health_response = api.model('HealthResponse', {
    'status': fields.String(description='System health status', example='healthy'),
    'timestamp': fields.DateTime(description='Health check timestamp', example='2025-01-09T15:30:45Z'),
    'uptime_seconds': fields.Float(description='System uptime in seconds', example=3600.5)
})

status_response = api.model('SystemStatusResponse', {
    'system_info': fields.Nested(api.model('SystemInfo', {
        'version': fields.String(description='API version', example='1.0.0'),
        'environment': fields.String(description='Deployment environment', example='production'),
        'uptime_seconds': fields.Float(description='System uptime', example=86400.0)
    })),
    'agents_status': fields.Nested(api.model('AgentsStatus', {
        'total_agents': fields.Integer(description='Total number of agents', example=7),
        'available_agents': fields.List(fields.String(), description='List of available agent endpoints')
    })),
    'performance_metrics': fields.Nested(api.model('PerformanceMetrics', {
        'avg_response_time_ms': fields.Float(description='Average response time', example=125.5),
        'total_requests': fields.Integer(description='Total requests processed', example=10000),
        'error_rate': fields.Float(description='Error rate percentage', example=0.1)
    }))
})

api.add_namespace(system_ns, path='/system')

# =============================================================================
# Example API Responses for Documentation
# =============================================================================
EXAMPLE_RESPONSES = {
    'business_rule_success': {
        "success": True,
        "data": {
            "extracted_rules": [
                {
                    "rule_id": "RULE_001",
                    "business_logic": "Senior customers with balance over $10,000 receive premium tier status",
                    "conditions": ["Customer age > 65", "Account balance > $10,000"],
                    "actions": ["Set customer tier to SENIOR-PREMIUM"],
                    "complexity_score": 3.5,
                    "confidence_level": 0.95
                }
            ],
            "total_rules_found": 1,
            "processing_summary": {
                "lines_analyzed": 6,
                "language_detected": "COBOL",
                "complexity_assessment": "Medium"
            }
        },
        "metadata": {
            "request_id": "req_a1b2c3d4e5f6",
            "agent_name": "BusinessRuleExtractionAgent",
            "processing_time_ms": 1250.5,
            "timestamp": "2025-01-09T15:30:45Z",
            "audit_level": 2
        },
        "format_info": {
            "primary_format": "embedded",
            "available_formats": ["markdown", "json", "html"],
            "embedded_content": {
                "markdown": "# Extracted Business Rules\n\n## Rule 001: Senior Premium Tier Assignment\n...",
                "json": "{ \"rules\": [...] }",
                "html": "<h1>Extracted Business Rules</h1>..."
            }
        }
    },
    'pii_protection_success': {
        "success": True,
        "data": {
            "scrubbed_data": "Customer [NAME] (SSN: ***-**-****) called from phone ***-***-*567 about his account.",
            "pii_found": [
                {
                    "type": "name",
                    "original_value": "[REDACTED]",
                    "masked_value": "[NAME]",
                    "position": {"start": 9, "end": 19},
                    "confidence": 0.92
                },
                {
                    "type": "ssn",
                    "original_value": "[REDACTED]",
                    "masked_value": "***-**-****",
                    "position": {"start": 26, "end": 37},
                    "confidence": 0.99
                }
            ],
            "protection_summary": {
                "total_pii_found": 3,
                "pii_types_detected": ["name", "ssn", "phone_number"],
                "masking_strategy_applied": "partial_mask",
                "data_safety_score": 9.8
            }
        }
    }
}

# =============================================================================
# API Route Documentation (Placeholder - Routes defined in main app.py)
# =============================================================================

@business_rule_ns.route('')
class BusinessRuleExtraction(Resource):
    @business_rule_ns.doc('extract_business_rules')
    @business_rule_ns.expect(business_rule_request)
    @business_rule_ns.marshal_with(business_rule_response)
    @business_rule_ns.response(200, 'Success', business_rule_response)
    @business_rule_ns.response(400, 'Bad Request', error_response)
    @business_rule_ns.response(401, 'Unauthorized', error_response)
    @business_rule_ns.response(413, 'Payload Too Large', error_response)
    @business_rule_ns.response(429, 'Too Many Requests', error_response)
    @business_rule_ns.response(500, 'Internal Server Error', error_response)
    def post(self):
        """
        Extract Business Rules from Legacy Code
        
        Analyzes legacy code (COBOL, Java, C++, Python, etc.) to extract business rules
        and translate them into natural language documentation. Perfect for modernizing
        legacy systems and preserving institutional knowledge.
        
        **Use Cases:**
        - Legacy system modernization projects
        - Business rule documentation for compliance
        - Code-to-documentation transformation
        - System migration preparation
        
        **Supported Languages:**
        - COBOL, Java, C++, Python, JavaScript, C#, VB.NET
        - Database stored procedures (SQL, PL/SQL)
        - Configuration files and business rules engines
        
        **Processing Features:**
        - Automatic language detection
        - Context-aware rule extraction
        - Complexity scoring and confidence levels
        - Multi-format output (Markdown, JSON, HTML)
        """
        # This is a placeholder - actual implementation is in app.py
        pass

@pii_protection_ns.route('')
class PersonalDataProtection(Resource):
    @pii_protection_ns.doc('protect_personal_data')
    @pii_protection_ns.expect(pii_request)
    @pii_protection_ns.marshal_with(pii_response)
    @pii_protection_ns.response(200, 'Success', pii_response)
    @pii_protection_ns.response(400, 'Bad Request', error_response)
    @pii_protection_ns.response(401, 'Unauthorized', error_response)
    def post(self):
        """
        Detect and Mask Personally Identifiable Information
        
        GDPR/CCPA compliant PII detection and masking for data privacy protection.
        Automatically identifies and masks sensitive data while maintaining data utility.
        
        **Regulatory Compliance:**
        - GDPR (General Data Protection Regulation)
        - CCPA (California Consumer Privacy Act)
        - HIPAA (Healthcare data protection)
        - SOX (Financial data compliance)
        
        **Supported PII Types:**
        - Social Security Numbers (SSN)
        - Credit Card Numbers
        - Phone Numbers
        - Email Addresses
        - Names and Addresses
        - Account Numbers
        - Dates of Birth
        - Driver License Numbers
        
        **Masking Strategies:**
        - **full_mask**: Replace with *** (maximum privacy)
        - **partial_mask**: Show first/last chars, mask middle
        - **tokenize**: Replace with reversible tokens
        - **hash**: One-way hash (irreversible)
        - **remove**: Remove entirely from text
        """
        # This is a placeholder - actual implementation is in app.py  
        pass

@system_ns.route('/health')
class HealthCheck(Resource):
    @system_ns.doc('health_check')
    @system_ns.marshal_with(health_response)
    def get(self):
        """Simple health check endpoint for load balancers and monitoring"""
        pass

@system_ns.route('/status') 
class SystemStatus(Resource):
    @system_ns.doc('system_status')
    @system_ns.marshal_with(status_response)
    def get(self):
        """Detailed system status including agent availability and performance metrics"""
        pass