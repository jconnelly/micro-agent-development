"""
Language Detection System for Intelligent Chunking
Phase 15A - Language Detection & Profile System

This module provides automatic language detection capabilities for legacy code files,
enabling language-specific intelligent chunking strategies for optimal business rule extraction.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class DetectionConfidence(Enum):
    """Confidence levels for language detection results."""
    VERY_LOW = 0.0
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


@dataclass
class LanguageProfile:
    """
    Language profile containing detection patterns and chunking configuration.
    """
    name: str
    description: str
    confidence_required: float
    file_extensions: List[str]
    mime_types: List[str]
    strong_patterns: List[str]
    supporting_patterns: List[str]
    rule_patterns: List[str]
    section_markers: List[str]
    chunking: Dict[str, Any]
    rule_density: Dict[str, int]
    
    def __post_init__(self):
        """Compile regex patterns for performance."""
        self._strong_regex = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                             for pattern in self.strong_patterns]
        self._supporting_regex = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                                 for pattern in self.supporting_patterns]  
        self._rule_regex = [re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                           for pattern in self.rule_patterns]
        self._section_regex = [re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                              for pattern in self.section_markers]


@dataclass 
class DetectionResult:
    """
    Result of language detection analysis.
    """
    language: str
    confidence: float
    profile: Optional[LanguageProfile]
    evidence: Dict[str, Any]
    recommendations: List[str]
    
    @property
    def is_confident(self) -> bool:
        """Check if detection confidence meets the profile's threshold."""
        return self.profile and self.confidence >= self.profile.confidence_required
    
    @property 
    def confidence_level(self) -> DetectionConfidence:
        """Get human-readable confidence level."""
        if self.confidence >= 0.95:
            return DetectionConfidence.VERY_HIGH
        elif self.confidence >= 0.8:
            return DetectionConfidence.HIGH
        elif self.confidence >= 0.6:
            return DetectionConfidence.MEDIUM
        elif self.confidence >= 0.3:
            return DetectionConfidence.LOW
        else:
            return DetectionConfidence.VERY_LOW


class LanguageDetectionError(Exception):
    """Raised when language detection encounters an error."""
    pass


class LanguageDetector:
    """
    Intelligent language detection system for legacy code files.
    
    Uses pattern matching, file extensions, and content analysis to identify
    programming languages with high accuracy for optimal chunking strategies.
    """
    
    def __init__(self, profiles_path: Optional[str] = None):
        """
        Initialize the language detector.
        
        Args:
            profiles_path: Path to language profiles YAML file
        """
        self.profiles_path = profiles_path or self._get_default_profiles_path()
        self.profiles: Dict[str, LanguageProfile] = {}
        self.detection_config: Dict[str, Any] = {}
        self._load_profiles()
    
    def _get_default_profiles_path(self) -> str:
        """Get default path to language profiles configuration."""
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "config", 
            "language_profiles.yaml"
        )
    
    def _load_profiles(self) -> None:
        """Load language profiles from YAML configuration."""
        try:
            with open(self.profiles_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.detection_config = config.get('detection', {})
            
            # Load individual language profiles
            for lang_key, lang_data in config.get('languages', {}).items():
                profile = LanguageProfile(
                    name=lang_data['name'],
                    description=lang_data['description'],
                    confidence_required=lang_data['confidence_required'],
                    file_extensions=lang_data['file_extensions'],
                    mime_types=lang_data.get('mime_types', []),
                    strong_patterns=lang_data['strong_patterns'],
                    supporting_patterns=lang_data['supporting_patterns'],
                    rule_patterns=lang_data['rule_patterns'],
                    section_markers=lang_data['section_markers'],
                    chunking=lang_data['chunking'],
                    rule_density=lang_data['rule_density']
                )
                self.profiles[lang_key] = profile
            
            # Load fallback profile
            fallback_data = config.get('fallback', {})
            if fallback_data:
                self.fallback_profile = LanguageProfile(
                    name=fallback_data['name'],
                    description=fallback_data['description'],
                    confidence_required=0.0,  # Always accept fallback
                    file_extensions=[],
                    mime_types=[],
                    strong_patterns=[],
                    supporting_patterns=[],
                    rule_patterns=fallback_data.get('rule_patterns', []),
                    section_markers=[],
                    chunking=fallback_data['chunking'],
                    rule_density=fallback_data['rule_density']
                )
            
        except FileNotFoundError:
            raise LanguageDetectionError(f"Language profiles file not found: {self.profiles_path}")
        except yaml.YAMLError as e:
            raise LanguageDetectionError(f"Error parsing language profiles YAML: {e}")
        except Exception as e:
            raise LanguageDetectionError(f"Error loading language profiles: {e}")
    
    def detect_language(self, filename: str, content: str) -> DetectionResult:
        """
        Detect the programming language of a code file.
        
        Args:
            filename: Name of the file (used for extension analysis)
            content: Content of the file to analyze
            
        Returns:
            DetectionResult with language, confidence, and evidence
        """
        # Analyze file extension
        file_ext = Path(filename).suffix.lower()
        
        # Calculate confidence scores for each language
        language_scores = {}
        
        for lang_key, profile in self.profiles.items():
            score = self._calculate_language_score(
                profile, file_ext, content, filename
            )
            language_scores[lang_key] = score
        
        # Find best match
        if language_scores:
            best_language = max(language_scores.items(), key=lambda x: x[1]['total_score'])
            lang_key, score_data = best_language
            
            profile = self.profiles[lang_key]
            confidence = min(score_data['total_score'], 1.0)  # Cap at 100%
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                confidence, score_data, profile
            )
            
            return DetectionResult(
                language=lang_key,
                confidence=confidence,
                profile=profile,
                evidence=score_data,
                recommendations=recommendations
            )
        else:
            # Use fallback profile
            return DetectionResult(
                language="unknown",
                confidence=0.0,
                profile=self.fallback_profile if hasattr(self, 'fallback_profile') else None,
                evidence={"reason": "no_profiles_loaded"},
                recommendations=["Load language profiles configuration"]
            )
    
    def _calculate_language_score(self, profile: LanguageProfile, file_ext: str, 
                                content: str, filename: str) -> Dict[str, Any]:
        """
        Calculate confidence score for a specific language profile.
        
        Args:
            profile: Language profile to test against
            file_ext: File extension
            content: File content
            filename: Original filename
            
        Returns:
            Dictionary with scoring details
        """
        scoring_config = self.detection_config.get('scoring', {})
        analysis_config = self.detection_config.get('analysis', {})
        
        # Analyze first N lines for efficiency
        sample_lines = analysis_config.get('sample_lines', 100)
        content_sample = '\n'.join(content.split('\n')[:sample_lines])
        
        score_data = {
            'extension_score': 0.0,
            'strong_pattern_score': 0.0,
            'supporting_pattern_score': 0.0,
            'rule_pattern_score': 0.0,
            'pattern_matches': {
                'strong': [],
                'supporting': [],
                'rules': []
            },
            'total_score': 0.0
        }
        
        # File extension scoring
        if file_ext in profile.file_extensions:
            score_data['extension_score'] = scoring_config.get('file_extension_weight', 15.0)
        
        # Strong pattern matching
        strong_matches = 0
        for i, regex in enumerate(profile._strong_regex):
            matches = regex.findall(content_sample)
            if matches:
                strong_matches += len(matches)
                score_data['pattern_matches']['strong'].append({
                    'pattern': profile.strong_patterns[i],
                    'matches': len(matches)
                })
        
        if strong_matches > 0:
            # Apply confidence boost for many strong patterns
            boost_threshold = analysis_config.get('confidence_boost_threshold', 5)
            boost = 1.2 if strong_matches >= boost_threshold else 1.0
            
            score_data['strong_pattern_score'] = (
                min(strong_matches * scoring_config.get('strong_pattern_weight', 10.0), 50.0) * boost
            )
        
        # Supporting pattern matching  
        supporting_matches = 0
        for i, regex in enumerate(profile._supporting_regex):
            matches = regex.findall(content_sample)
            if matches:
                supporting_matches += len(matches)
                score_data['pattern_matches']['supporting'].append({
                    'pattern': profile.supporting_patterns[i],
                    'matches': len(matches)
                })
        
        if supporting_matches > 0:
            score_data['supporting_pattern_score'] = min(
                supporting_matches * scoring_config.get('supporting_pattern_weight', 3.0), 30.0
            )
        
        # Rule pattern matching (business logic indicators)
        rule_matches = 0
        for i, regex in enumerate(profile._rule_regex):
            matches = regex.findall(content_sample)
            if matches:
                rule_matches += len(matches)
                score_data['pattern_matches']['rules'].append({
                    'pattern': profile.rule_patterns[i], 
                    'matches': len(matches)
                })
        
        if rule_matches > 0:
            score_data['rule_pattern_score'] = min(
                rule_matches * scoring_config.get('rule_pattern_weight', 5.0), 25.0
            )
        
        # Calculate total score (normalized to 0-1 scale)
        total_raw_score = (
            score_data['extension_score'] + 
            score_data['strong_pattern_score'] +
            score_data['supporting_pattern_score'] + 
            score_data['rule_pattern_score']
        )
        
        score_data['total_score'] = min(total_raw_score / 100.0, 1.0)  # Normalize to 0-1
        
        return score_data
    
    def _generate_recommendations(self, confidence: float, score_data: Dict[str, Any], 
                                profile: LanguageProfile) -> List[str]:
        """
        Generate recommendations based on detection results.
        
        Args:
            confidence: Detection confidence score
            score_data: Detailed scoring information  
            profile: Detected language profile
            
        Returns:
            List of recommendations for the user
        """
        recommendations = []
        
        if confidence < profile.confidence_required:
            recommendations.append(
                f"Low confidence ({confidence:.1%}) - consider manual verification"
            )
            
            if score_data['extension_score'] == 0:
                recommendations.append(
                    f"File extension not recognized for {profile.name} - verify file type"
                )
            
            if score_data['strong_pattern_score'] < 10:
                recommendations.append(
                    f"Few {profile.name} language patterns found - file may be atypical"
                )
        
        elif confidence >= DetectionConfidence.HIGH.value:
            recommendations.append(f"High confidence {profile.name} detection")
            
            rule_count = sum(
                match['matches'] for match in score_data['pattern_matches']['rules']
            )
            expected_min = profile.rule_density.get('expected_min', 5)
            
            if rule_count >= expected_min:
                recommendations.append(
                    f"Good rule density detected ({rule_count} business logic patterns)"
                )
            else:
                recommendations.append(
                    f"Low rule density ({rule_count} patterns) - file may be data-focused"
                )
        
        if not recommendations:
            recommendations.append(f"Medium confidence {profile.name} detection")
        
        return recommendations
    
    def get_profile(self, language: str) -> Optional[LanguageProfile]:
        """
        Get language profile by language key.
        
        Args:
            language: Language identifier (e.g., 'cobol', 'java')
            
        Returns:
            LanguageProfile if found, None otherwise
        """
        return self.profiles.get(language)
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available language identifiers.
        
        Returns:
            List of language keys that can be detected
        """
        return list(self.profiles.keys())
    
    def validate_detection(self, result: DetectionResult, content: str) -> Dict[str, Any]:
        """
        Validate detection result and provide additional analysis.
        
        Args:
            result: Detection result to validate
            content: Original file content
            
        Returns:
            Dictionary with validation results and suggestions
        """
        if not result.profile:
            return {
                "valid": False,
                "reason": "no_profile_available",
                "suggestions": ["Use fallback chunking strategy"]
            }
        
        # Check if confidence meets requirements
        if not result.is_confident:
            return {
                "valid": False,
                "reason": "confidence_too_low",
                "confidence": result.confidence,
                "required": result.profile.confidence_required,
                "suggestions": [
                    "Consider manual language specification",
                    "Use fallback chunking strategy",
                    "Verify file type and content"
                ]
            }
        
        # Estimate rule density for chunking optimization
        total_lines = len(content.split('\n'))
        rule_matches = sum(
            match['matches'] for match in result.evidence['pattern_matches']['rules']
        )
        estimated_density = (rule_matches / total_lines) * 100 if total_lines > 0 else 0
        
        expected_min = result.profile.rule_density.get('expected_min', 5)
        expected_max = result.profile.rule_density.get('expected_max', 20)
        
        validation_result = {
            "valid": True,
            "confidence": result.confidence,
            "estimated_rule_density": estimated_density,
            "expected_range": f"{expected_min}-{expected_max}",
            "suggestions": []
        }
        
        if estimated_density < expected_min:
            validation_result["suggestions"].append(
                "Low rule density - consider larger chunk sizes"
            )
        elif estimated_density > expected_max:
            validation_result["suggestions"].append(
                "High rule density - consider smaller chunk sizes for better context"
            )
        else:
            validation_result["suggestions"].append(
                "Rule density within expected range - use standard chunking"
            )
        
        return validation_result


def create_language_detector(profiles_path: Optional[str] = None) -> LanguageDetector:
    """
    Factory function to create a LanguageDetector instance.
    
    Args:
        profiles_path: Optional path to language profiles file
        
    Returns:
        Configured LanguageDetector instance
    """
    return LanguageDetector(profiles_path)


# Export main classes and functions
__all__ = [
    'LanguageDetector',
    'LanguageProfile', 
    'DetectionResult',
    'DetectionConfidence',
    'LanguageDetectionError',
    'create_language_detector'
]