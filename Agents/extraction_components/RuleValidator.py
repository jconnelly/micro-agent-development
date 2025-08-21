"""
Rule Validation Component for Business Rule Extraction

This module handles rule validation, deduplication, completeness analysis, and quality
assurance for the BusinessRuleExtractionAgent.

Extracted from BusinessRuleExtractionAgent.py as part of Phase 16 Task 2 modularization.
"""

import time
from typing import Dict, Any, List, Optional, Tuple

# Import Rule Completeness Analyzer (Phase 15C)
from Utils.rule_completeness_analyzer import RuleCompletenessAnalyzer, CompletenessStatus


class RuleValidator:
    """
    Handles rule validation, deduplication, and completeness analysis.
    
    Responsibilities:
    - Rule deduplication across chunks
    - Rule quality validation
    - Completeness analysis and reporting
    - Progress monitoring and feedback
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """Initialize the rule validator with configuration."""
        self.agent_config = agent_config
        self.completeness_analyzer = RuleCompletenessAnalyzer()
        self._last_completeness_report = None
        
    def deduplicate_rules(self, all_rules: List[Dict], request_id: str = None) -> List[Dict]:
        """
        Remove duplicate rules from the aggregated results.
        
        Args:
            all_rules: List of all extracted rules
            request_id: Request ID for logging
            
        Returns:
            List of deduplicated rules
        """
        if not all_rules:
            return []
        
        seen_rules = set()
        unique_rules = []
        similarity_threshold = 0.8  # Configurable threshold
        
        for rule in all_rules:
            # Create a normalized key for deduplication
            rule_key = self._create_rule_key(rule)
            
            # Check for exact duplicates first
            if rule_key in seen_rules:
                continue
            
            # Check for similar rules (fuzzy matching)
            is_duplicate = False
            for existing_rule in unique_rules:
                if self._calculate_rule_similarity(rule, existing_rule) > similarity_threshold:
                    is_duplicate = True
                    # Keep the rule with more information
                    if len(str(rule)) > len(str(existing_rule)):
                        # Replace the existing rule with the more detailed one
                        existing_idx = unique_rules.index(existing_rule)
                        unique_rules[existing_idx] = rule
                    break
            
            if not is_duplicate:
                seen_rules.add(rule_key)
                unique_rules.append(rule)
        
        # Log deduplication results
        if request_id:
            self._log_deduplication_result(len(all_rules), len(unique_rules), request_id)
        
        return unique_rules
    
    def aggregate_chunk_results(self, response_data_list: List[Any]) -> List[Dict]:
        """
        Aggregate rule extraction results from multiple chunks.
        
        Args:
            response_data_list: List of responses from chunk processing
            
        Returns:
            Aggregated list of rules
        """
        all_rules = []
        
        for response_data in response_data_list:
            if response_data and isinstance(response_data, dict):
                rules = response_data.get('rules', [])
                if isinstance(rules, list):
                    all_rules.extend(rules)
                elif isinstance(rules, dict):
                    # Single rule case
                    all_rules.append(rules)
        
        return all_rules
    
    def perform_completeness_analysis(self, source_content: str, extracted_rules: List[Dict], 
                                    processing_results: Dict[str, Any] = None, 
                                    request_id: str = None) -> Dict[str, Any]:
        """
        Perform comprehensive rule completeness analysis.
        
        Args:
            source_content: Original source code content
            extracted_rules: List of extracted rules
            processing_results: Processing metadata
            request_id: Request ID for logging
            
        Returns:
            Completeness analysis results
        """
        try:
            start_time = time.time()
            
            # Perform completeness analysis
            completeness_result = self.completeness_analyzer.analyze_completeness(
                source_content=source_content,
                extracted_rules=extracted_rules,
                processing_context=processing_results
            )
            
            analysis_time = time.time() - start_time
            
            # Store the latest report
            self._last_completeness_report = {
                'analysis_result': completeness_result,
                'analysis_time_ms': analysis_time * 1000,
                'timestamp': time.time(),
                'request_id': request_id
            }
            
            # Log analysis results
            if request_id:
                self._log_completeness_analysis(completeness_result, analysis_time, request_id)
            
            return {
                'completeness_status': completeness_result.status.value,
                'completeness_percentage': completeness_result.completeness_percentage,
                'expected_rules': completeness_result.expected_rule_count,
                'found_rules': completeness_result.found_rule_count,
                'analysis_time_ms': analysis_time * 1000,
                'recommendations': completeness_result.recommendations,
                'missing_categories': completeness_result.gap_analysis.get('missing_categories', [])
            }
            
        except Exception as e:
            # Log analysis failure but don't break the main workflow
            analysis_error = {
                'completeness_status': 'analysis_failed',
                'error': str(e),
                'found_rules': len(extracted_rules)
            }
            
            if request_id:
                self._log_analysis_error(e, request_id)
                
            return analysis_error
    
    def monitor_extraction_progress(self, current_rules: List[Dict], chunks_processed: int, 
                                  total_chunks: int, request_id: str = None) -> None:
        """
        Monitor and report extraction progress.
        
        Args:
            current_rules: Currently extracted rules
            chunks_processed: Number of chunks processed so far
            total_chunks: Total number of chunks
            request_id: Request ID for logging
        """
        progress_percentage = (chunks_processed / total_chunks) * 100 if total_chunks > 0 else 0
        rules_count = len(current_rules)
        
        # Create progress report
        progress_info = {
            'chunks_processed': chunks_processed,
            'total_chunks': total_chunks,
            'progress_percentage': progress_percentage,
            'rules_extracted': rules_count,
            'average_rules_per_chunk': rules_count / max(chunks_processed, 1)
        }
        
        # Log progress
        if request_id:
            self._log_progress_update(progress_info, request_id)
    
    def validate_rule_quality(self, rule: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate the quality of an extracted rule.
        
        Args:
            rule: Rule dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check required fields
        required_fields = ['rule_id', 'conditions', 'actions', 'business_description']
        for field in required_fields:
            if field not in rule or not rule[field]:
                issues.append(f"Missing or empty required field: {field}")
        
        # Check field quality
        if 'business_description' in rule:
            desc = rule['business_description']
            if len(desc) < 10:
                issues.append("Business description too short")
            elif len(desc) > 500:
                issues.append("Business description too long")
        
        if 'conditions' in rule:
            conditions = rule['conditions']
            if len(conditions) < 5:
                issues.append("Conditions too vague")
        
        if 'actions' in rule:
            actions = rule['actions']
            if len(actions) < 3:
                issues.append("Actions too vague")
        
        return len(issues) == 0, issues
    
    def get_last_completeness_report(self) -> Optional[Dict[str, Any]]:
        """Get the last completeness analysis report."""
        return self._last_completeness_report
    
    def _create_rule_key(self, rule: Dict[str, Any]) -> str:
        """Create a normalized key for rule deduplication."""
        # Use conditions and actions to create a unique key
        conditions = str(rule.get('conditions', '')).lower().strip()
        actions = str(rule.get('actions', '')).lower().strip()
        
        # Normalize whitespace and common variations
        conditions = ' '.join(conditions.split())
        actions = ' '.join(actions.split())
        
        return f"{conditions}|{actions}"
    
    def _calculate_rule_similarity(self, rule1: Dict[str, Any], rule2: Dict[str, Any]) -> float:
        """Calculate similarity between two rules."""
        # Simple similarity based on conditions and actions
        conditions1 = str(rule1.get('conditions', '')).lower()
        conditions2 = str(rule2.get('conditions', '')).lower()
        actions1 = str(rule1.get('actions', '')).lower()
        actions2 = str(rule2.get('actions', '')).lower()
        
        # Calculate Jaccard similarity for conditions and actions
        conditions_similarity = self._jaccard_similarity(conditions1, conditions2)
        actions_similarity = self._jaccard_similarity(actions1, actions2)
        
        # Weight conditions and actions equally
        return (conditions_similarity + actions_similarity) / 2
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two text strings."""
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _log_deduplication_result(self, original_count: int, unique_count: int, request_id: str) -> None:
        """Log deduplication results."""
        duplicates_removed = original_count - unique_count
        # This would typically use the agent's logging system
        pass
    
    def _log_completeness_analysis(self, result: Any, analysis_time: float, request_id: str) -> None:
        """Log completeness analysis results."""
        # This would typically use the agent's logging system
        pass
    
    def _log_analysis_error(self, error: Exception, request_id: str) -> None:
        """Log analysis errors."""
        # This would typically use the agent's logging system
        pass
    
    def _log_progress_update(self, progress_info: Dict[str, Any], request_id: str) -> None:
        """Log progress updates."""
        # This would typically use the agent's logging system
        pass