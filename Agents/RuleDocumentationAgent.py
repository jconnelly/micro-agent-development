import json
import uuid
import datetime
from typing import Dict, Any, List, Optional

# Import other Agents from current location, change package location if moved
from .BaseAgent import BaseAgent
from .AuditingAgent import AgentAuditing, AuditLevel
from .Exceptions import DocumentationError, ValidationError

# Import Utils - handle both relative and absolute imports
try:
    from ..Utils import config_loader
except ImportError:
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from Utils import config_loader

class RuleDocumentationAgent(BaseAgent):
    def __init__(self, llm_client: Any, audit_system: AgentAuditing, agent_id: str = None, 
                 log_level: int = 0, model_name: str = "gemini-1.5-flash", llm_provider: str = "google"):
        """
        Initializes the RuleDocumentationAgent.

        Args:
            llm_client: An initialized LLM client (e.g., OpenAI, LangChain).
            audit_system: An instance of the AgentAuditing class.
            agent_id: Unique identifier for this agent instance.
            log_level: 0 for production (silent), 1 for development (verbose)
            model_name: Name of the LLM model being used
            llm_provider: Name of the LLM provider
        """
        # Initialize base agent
        super().__init__(
            audit_system=audit_system,
            agent_id=agent_id,
            log_level=log_level,
            model_name=model_name,
            llm_provider=llm_provider,
            agent_name="Rule Documentation and Visualization Agent"
        )
        
        # Documentation-specific configuration
        self.llm_client = llm_client

    def _prepare_llm_prompt_for_documentation(self, rules: List[Dict]) -> tuple[str, str]:
        """
        Prepares the system and user prompts for the LLM to generate documentation.
        """
        rules_json_str = json.dumps(rules, indent=2)
        system_prompt = (
            f"You are an expert business rule documentation and translation agent. "
            f"Your task is to take a list of structured business rules, refine their "
            f"business descriptions for clarity, and generate a concise, human-readable "
            f"summary of the rule set. Ensure all technical jargon is replaced with "
            f"business-friendly terminology. Output should be a JSON object containing "
            f"'summary' (string) and 'detailed_rules' (array of refined rules)."
        )

        user_prompt = (
            f"Refine the business descriptions and summarize the following set of business rules. "
            f"Ensure the language is clear for non-technical stakeholders.\n\n"
            f"Rules:\n```json\n{rules_json_str}\n```\n\n"
            f"Provide output in JSON: {{'summary': '...', 'detailed_rules': [...]}}"
        )
        return system_prompt, user_prompt

    def _classify_business_domain(self, extracted_rules: List[Dict]) -> Dict[str, Any]:
        """
        Classifies the business domain based on extracted rules content.
        Returns domain information with primary domain, keywords, and confidence scores.
        Uses external configuration with fallback to hardcoded values.
        """
        # Fallback configuration (preserved from original hardcoded values)
        fallback_domain_keywords = {
            'domains': {
                'insurance': {
                    'keywords': ['policy', 'premium', 'coverage', 'beneficiary', 'accident', 'smoker', 'dui', 
                               'vehicle', 'life insurance', 'auto insurance', 'claim', 'deductible', 'underwriting'],
                    'weight': 1.0
                },
                'trading': {
                    'keywords': ['trade', 'position', 'margin', 'leverage', 'portfolio', 'volatility', 'order',
                               'risk', 'trader', 'execution', 'market', 'liquidity', 'hedge', 'derivative'],
                    'weight': 1.0
                },
                'lending': {
                    'keywords': ['loan', 'credit score', 'dti', 'debt', 'income', 'collateral', 'interest rate',
                               'mortgage', 'approval', 'borrower', 'refinance', 'amortization'],
                    'weight': 1.0
                },
                'banking': {
                    'keywords': ['account', 'deposit', 'balance', 'transaction', 'withdrawal', 'overdraft',
                               'fee', 'branch', 'atm', 'wire transfer', 'routing'],
                    'weight': 1.0
                },
                'healthcare': {
                    'keywords': ['patient', 'diagnosis', 'treatment', 'medication', 'doctor', 'hospital',
                               'medical', 'prescription', 'therapy', 'clinic', 'procedure'],
                    'weight': 1.0
                },
                'ecommerce': {
                    'keywords': ['order', 'customer', 'product', 'payment', 'shipping', 'inventory',
                               'cart', 'checkout', 'refund', 'discount', 'catalog'],
                    'weight': 1.0
                }
            }
        }
        
        # Load configuration with graceful fallback
        try:
            domains_config = config_loader.load_config("domains", fallback_domain_keywords)
            domain_keywords = domains_config.get('domains', fallback_domain_keywords['domains'])
            self.logger.debug("Loaded domain classification configuration from external file")
        except Exception as e:
            self.logger.warning(f"Failed to load domains configuration: {e}. Using fallback.")
            domain_keywords = fallback_domain_keywords['domains']
        
        domain_scores = {domain: 0 for domain in domain_keywords.keys()}
        total_text = ""
        
        # Aggregate all text from rules for analysis
        for rule in extracted_rules:
            rule_text = ""
            rule_text += str(rule.get('business_description', '')).lower() + " "
            rule_text += str(rule.get('conditions', '')).lower() + " "
            rule_text += str(rule.get('actions', '')).lower() + " "
            
            # Handle source_code_lines which might be a string or list
            source_lines = rule.get('source_code_lines', '')
            if isinstance(source_lines, list):
                rule_text += " ".join(str(line) for line in source_lines).lower() + " "
            else:
                rule_text += str(source_lines).lower() + " "
            
            total_text += rule_text
        
        # Pre-convert text to lowercase once for performance (instead of multiple .lower() calls)
        total_text_lower = total_text.lower()
        
        # Score each domain based on keyword frequency
        for domain, config in domain_keywords.items():
            for keyword in config['keywords']:
                count = total_text_lower.count(keyword.lower())
                domain_scores[domain] += count * config['weight']
        
        # Determine primary domain(s)
        total_score = sum(domain_scores.values())
        if total_score == 0:
            return {
                'primary_domain': 'general',
                'confidence': 0.0,
                'domain_percentages': {},
                'detected_keywords': [],
                'is_multi_domain': False
            }
        
        # Calculate percentages
        domain_percentages = {domain: (score / total_score) * 100 
                            for domain, score in domain_scores.items() 
                            if score > 0}
        
        # Find primary domain
        primary_domain = max(domain_scores, key=domain_scores.get)
        primary_confidence = domain_percentages.get(primary_domain, 0.0)
        
        # Check if multi-domain (more than one domain with >20% score) - O(1) lookup with set
        significant_domains = [domain for domain, pct in domain_percentages.items() if pct >= 20.0]
        is_multi_domain = len(significant_domains) > 1
        
        # Extract detected keywords for context - use set to avoid duplicates and improve performance
        detected_keywords_set = set()
        domains_with_scores = {domain for domain, score in domain_scores.items() if score > 0}
        
        for domain in domains_with_scores:
            config = domain_keywords[domain]
            for keyword in config['keywords']:
                if keyword.lower() in total_text_lower:
                    detected_keywords_set.add(keyword)
        
        detected_keywords = list(detected_keywords_set)
        
        return {
            'primary_domain': primary_domain,
            'confidence': primary_confidence,
            'domain_percentages': domain_percentages,
            'detected_keywords': detected_keywords[:10],  # Limit to top 10
            'is_multi_domain': is_multi_domain,
            'significant_domains': significant_domains
        }

    def _generate_domain_summary(self, domain_info: Dict[str, Any], rule_count: int) -> str:
        """
        Generates a contextually appropriate summary based on domain classification.
        """
        primary_domain = domain_info['primary_domain']
        confidence = domain_info['confidence']
        is_multi_domain = domain_info['is_multi_domain']
        significant_domains = domain_info['significant_domains']
        detected_keywords = domain_info['detected_keywords']
        
        # Domain-specific summary templates
        domain_templates = {
            'insurance': {
                'system_type': 'insurance policy validation system',
                'governs': 'policy application approval and premium calculation',
                'common_features': 'age restrictions, coverage limits, risk assessments, and premium adjustments'
            },
            'trading': {
                'system_type': 'financial trading and risk management system',
                'governs': 'trade validation, position limits, and risk controls',
                'common_features': 'position sizing, leverage limits, volatility thresholds, and margin requirements'
            },
            'lending': {
                'system_type': 'loan processing and approval system',
                'governs': 'loan application evaluation and interest rate determination',
                'common_features': 'credit score validation, income verification, debt-to-income ratios, and collateral requirements'
            },
            'banking': {
                'system_type': 'banking operations system',
                'governs': 'account management and transaction processing',
                'common_features': 'balance checks, transaction limits, fee calculations, and compliance rules'
            },
            'healthcare': {
                'system_type': 'healthcare management system',
                'governs': 'patient care protocols and medical decision support',
                'common_features': 'treatment guidelines, medication rules, and patient eligibility criteria'
            },
            'ecommerce': {
                'system_type': 'e-commerce platform',
                'governs': 'order processing and customer management',
                'common_features': 'pricing rules, inventory controls, shipping logic, and payment validation'
            },
            'general': {
                'system_type': 'business rules system',
                'governs': 'various business processes and decisions',
                'common_features': 'validation rules, approval workflows, and business logic'
            }
        }
        
        if is_multi_domain and len(significant_domains) > 1:
            # Multi-domain summary
            domain_list = ", ".join(significant_domains[:-1]) + f" and {significant_domains[-1]}"
            summary = f"This multi-domain system contains {rule_count} business rules spanning {domain_list} operations. "
            summary += "The rules integrate cross-functional business logic with domain-specific validation and processing requirements."
        else:
            # Single domain summary
            template = domain_templates.get(primary_domain, domain_templates['general'])
            summary = f"This {template['system_type']} contains {rule_count} business rules that govern {template['governs']}. "
            summary += f"The rules implement {template['common_features']}."
        
        # Add keyword context if available
        if detected_keywords:
            key_terms = ", ".join(detected_keywords[:5])  # Show top 5 keywords
            summary += f" Key business concepts include: {key_terms}."
        
        return summary

    def _prepare_documentation_data(self, extracted_rules: List[Dict], request_id: str) -> tuple[str, List[Dict], int, int, str]:
        """
        Prepare documentation data and generate summary.
        
        Returns:
            Tuple of (documentation_summary, refined_rules, tokens_input, tokens_output, llm_response_raw)
        """
        try:
            print(f"[{request_id}] Processing rule documentation (using actual extracted rules).")
            
            # Generate a dynamic summary based on domain classification
            rule_count = len(extracted_rules)
            domain_info = self._classify_business_domain(extracted_rules)
            documentation_summary = self._generate_domain_summary(domain_info, rule_count)
            
            # Use the actual extracted rules passed in
            refined_rules = extracted_rules
            
            # Mock token counts for audit
            tokens_input = len(str(extracted_rules))
            tokens_output = len(documentation_summary) + sum(len(str(rule)) for rule in refined_rules)
            llm_response_raw = f"Generated documentation for {len(refined_rules)} business rules"
            
            return documentation_summary, refined_rules, tokens_input, tokens_output, llm_response_raw
            
        except Exception as e:
            error_details = f"Documentation preparation failed: {e}"
            print(f"[{request_id}] {error_details}")
            # Return defaults for failed processing
            return "Failed to generate summary.", [], 0, 0, None
    
    def _generate_markdown_output(self, documentation_summary: str, refined_rules: List[Dict]) -> str:
        """
        Generate documentation in Markdown format.
        
        Returns:
            Markdown formatted documentation string
        """
        generated_documentation = f"# Business Rules Documentation\n\n"
        generated_documentation += f"## Summary\n{documentation_summary}\n\n"
        generated_documentation += f"## Detailed Rules\n\n"
        
        for rule in refined_rules:
            generated_documentation += f"### Rule ID: {rule.get('rule_id', 'N/A')}\n"
            generated_documentation += f"- **Business Description:** {rule.get('business_description', 'N/A')}\n"
            generated_documentation += f"- **Conditions:** `{rule.get('conditions', 'N/A')}`\n"
            generated_documentation += f"- **Actions:** `{rule.get('actions', 'N/A')}`\n"
            generated_documentation += f"- **Source Code Lines:** {rule.get('source_code_lines', 'N/A')}\n\n"
        
        # Conceptual placeholder for visualization link
        generated_documentation += f"## Rule Flow Visualization\n"
        generated_documentation += f"A conceptual visualization of rule execution flow can be generated here (e.g., link to a diagram).\n"
        
        return generated_documentation
    
    def _generate_json_output(self, documentation_summary: str, refined_rules: List[Dict]) -> str:
        """
        Generate documentation in JSON format.
        
        Returns:
            JSON formatted documentation string
        """
        return json.dumps({
            "summary": documentation_summary,
            "detailed_rules": refined_rules,
            "visualization_note": "Conceptual visualization link/data would be here."
        }, indent=2)
    
    def _generate_html_output(self, documentation_summary: str, refined_rules: List[Dict]) -> str:
        """
        Generate documentation in HTML format.
        
        Returns:
            HTML formatted documentation string
        """
        generated_documentation = f"<h1>Business Rules Documentation</h1>"
        generated_documentation += f"<h2>Summary</h2><p>{documentation_summary}</p>"
        generated_documentation += f"<h2>Detailed Rules</h2><ul>"
        
        for rule in refined_rules:
            generated_documentation += f"<li><h3>Rule ID: {rule.get('rule_id', 'N/A')}</h3>"
            generated_documentation += f"<p><b>Business Description:</b> {rule.get('business_description', 'N/A')}</p>"
            generated_documentation += f"<p><b>Conditions:</b> <code>{rule.get('conditions', 'N/A')}</code></p>"
            generated_documentation += f"<p><b>Actions:</b> <code>{rule.get('actions', 'N/A')}</code></p>"
            generated_documentation += f"<p><b>Source Code Lines:</b> {rule.get('source_code_lines', 'N/A')}</p></li>"
        
        generated_documentation += f"</ul><h2>Rule Flow Visualization</h2><p>A conceptual visualization of rule execution flow can be embedded here (e.g., an SVG or image).</p>"
        
        return generated_documentation
    
    def _generate_formatted_output(self, output_format: str, documentation_summary: str, refined_rules: List[Dict]) -> tuple[str, Optional[str]]:
        """
        Generate documentation in the specified format.
        
        Returns:
            Tuple of (generated_documentation, error_details)
        """
        error_details = None
        
        if output_format == "markdown":
            generated_documentation = self._generate_markdown_output(documentation_summary, refined_rules)
        elif output_format == "json":
            generated_documentation = self._generate_json_output(documentation_summary, refined_rules)
        elif output_format == "html":
            generated_documentation = self._generate_html_output(documentation_summary, refined_rules)
        else:
            generated_documentation = "Unsupported output format."
            error_details = "Unsupported output format specified."
        
        return generated_documentation, error_details

    def document_and_visualize_rules(self, extracted_rules: List[Dict], output_format: str = "markdown", audit_level: int = AuditLevel.LEVEL_1.value) -> Dict[str, Any]:
        """
        Generates documentation and conceptual visualization for a set of extracted business rules.

        Args:
            extracted_rules: A list of dictionaries, where each dictionary represents an extracted rule.
                             (e.g., output from LegacyRuleExtractionAgent).
            output_format: Desired output format ('markdown', 'json', 'html').
            audit_level: An integer representing the desired audit granularity (1-4).

        Returns:
            A dictionary containing the generated documentation and the audit log.
        """
        request_id = f"rule-doc-{uuid.uuid4().hex}"
        print(f"\nExtracted {request_id} document.")
        start_time = datetime.datetime.now(datetime.timezone.utc)

        user_id = "doc_generator_user" # Placeholder
        session_id = request_id
        ip_address = "127.0.0.1"

        # 1. Prepare LLM prompt for documentation
        system_prompt, user_prompt = self._prepare_llm_prompt_for_documentation(extracted_rules)

        llm_input_data = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "model_name": "gemini-1.5-flash" # Using Gemini 1.5 Flash for code analysis
        }

        # 2. Prepare documentation data
        documentation_summary, refined_rules, tokens_input, tokens_output, llm_response_raw = self._prepare_documentation_data(
            extracted_rules, request_id
        )

        # 3. Generate documentation in specified format
        generated_documentation, error_details = self._generate_formatted_output(
            output_format, documentation_summary, refined_rules
        )

        # 4. Calculate processing duration and create audit entry
        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        audit_log_data = self.audit_system.log_agent_activity(
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.version,
            step_type="Rule_Documentation_Generation",
            llm_input=llm_input_data,
            llm_output=llm_response_raw,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            final_decision={"documentation_length": len(generated_documentation), "output_format": output_format},
            duration_ms=duration_ms,
            error_details=error_details,
            audit_level=audit_level
        )

        return {
            "generated_documentation": generated_documentation,
            "audit_log": audit_log_data
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get agent information including capabilities and configuration.
        
        Returns:
            Dictionary containing agent information
        """
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "version": self.version,
            "model_name": self.model_name,
            "llm_provider": self.llm_provider,
            "capabilities": [
                "rule_documentation",
                "business_domain_classification", 
                "multi_format_output",
                "visualization_generation",
                "contextual_summarization"
            ],
            "supported_formats": ["markdown", "json", "html"],
            "supported_domains": [
                "insurance", "trading", "lending", "banking", 
                "healthcare", "ecommerce", "general"
            ],
            "configuration": {
                "api_timeout_seconds": self.API_TIMEOUT_SECONDS,
                "max_retries": self.MAX_RETRIES,
                "default_format": "markdown"
            }
        }