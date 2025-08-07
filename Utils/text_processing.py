"""
Text Processing Utilities - Common text handling and transformation functions.

Provides standardized text processing operations used across agents.
"""

import json
from typing import Any, Dict, List, Tuple, Union, Optional


class TextProcessingUtils:
    """Utility class for text processing operations across agents."""
    
    @staticmethod
    def prepare_input_data(data: Union[str, Dict[str, Any]]) -> Tuple[str, bool]:
        """
        Prepare input data for text processing by converting to string format.
        
        Args:
            data: Input data (string or dictionary)
            
        Returns:
            Tuple of (text_data, is_dict_input) where:
            - text_data: String representation of the data
            - is_dict_input: Boolean indicating if input was originally a dict
        """
        if isinstance(data, dict):
            text_data = json.dumps(data, indent=2)
            is_dict_input = True
        else:
            text_data = str(data)
            is_dict_input = False
        
        return text_data, is_dict_input
    
    @staticmethod
    def restore_data_format(
        text_data: str, 
        was_dict: bool, 
        fallback_to_string: bool = True
    ) -> Union[str, Dict[str, Any]]:
        """
        Restore data to its original format after text processing.
        
        Args:
            text_data: Processed text data
            was_dict: Whether original input was a dictionary
            fallback_to_string: Whether to fallback to string if parsing fails
            
        Returns:
            Data in original format (dict or string)
        """
        if was_dict:
            try:
                return json.loads(text_data)
            except json.JSONDecodeError:
                if fallback_to_string:
                    return text_data
                else:
                    raise ValueError("Failed to parse processed text back to JSON format")
        
        return text_data
    
    @staticmethod
    def clean_text_for_processing(text: str) -> str:
        """
        Clean text for processing by removing extra whitespace and normalizing.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace but preserve single spaces
        lines = [line.strip() for line in text.split('\n')]
        # Remove empty lines but preserve paragraph structure
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append("")
                prev_empty = True
        
        return '\n'.join(cleaned_lines).strip()
    
    @staticmethod
    def truncate_text(
        text: str, 
        max_length: int, 
        ellipsis: str = "...",
        preserve_words: bool = True
    ) -> str:
        """
        Truncate text to specified maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length allowed
            ellipsis: String to append when truncating
            preserve_words: Whether to avoid cutting in middle of words
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        # Account for ellipsis length
        target_length = max_length - len(ellipsis)
        
        if not preserve_words or target_length <= 0:
            return text[:target_length] + ellipsis
        
        # Find last space before target length
        truncated = text[:target_length]
        last_space = truncated.rfind(' ')
        
        if last_space > target_length * 0.8:  # Don't truncate too aggressively
            return text[:last_space] + ellipsis
        else:
            return text[:target_length] + ellipsis
    
    @staticmethod
    def extract_code_blocks(text: str, language: str = None) -> List[Dict[str, str]]:
        """
        Extract code blocks from markdown-style text.
        
        Args:
            text: Text containing code blocks
            language: Specific language to filter for (optional)
            
        Returns:
            List of dicts with 'language' and 'code' keys
        """
        import re
        
        # Pattern to match ```language\ncode\n```
        pattern = r'```(\w+)?\s*\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        code_blocks = []
        for lang, code in matches:
            if language is None or lang.lower() == language.lower():
                code_blocks.append({
                    'language': lang or 'text',
                    'code': code.strip()
                })
        
        return code_blocks
    
    @staticmethod
    def count_tokens_estimate(text: str) -> int:
        """
        Provide rough estimate of token count for text.
        
        This is a simple approximation - actual tokenizers may vary.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Simple approximation: ~4 characters per token on average
        # This varies significantly by tokenizer and language
        return len(text) // 4
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split text into sentences using simple heuristics.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        import re
        
        # Simple sentence splitting - handles most cases
        sentences = re.split(r'[.!?]+\s+', text)
        
        # Clean up and filter empty sentences
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def find_common_prefixes(texts: List[str], min_length: int = 3) -> List[str]:
        """
        Find common prefixes among a list of texts.
        
        Args:
            texts: List of text strings
            min_length: Minimum prefix length to consider
            
        Returns:
            List of common prefixes found
        """
        if len(texts) < 2:
            return []
        
        prefixes = set()
        
        for i, text1 in enumerate(texts):
            for text2 in texts[i+1:]:
                # Find longest common prefix
                common_len = 0
                for j in range(min(len(text1), len(text2))):
                    if text1[j] == text2[j]:
                        common_len += 1
                    else:
                        break
                
                if common_len >= min_length:
                    prefixes.add(text1[:common_len])
        
        return sorted(list(prefixes), key=len, reverse=True)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace in text - convert all whitespace to single spaces.
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized whitespace
        """
        import re
        return re.sub(r'\s+', ' ', text).strip()
    
    @staticmethod
    def extract_keywords(
        text: str, 
        min_word_length: int = 3,
        exclude_common: bool = True
    ) -> List[str]:
        """
        Extract potential keywords from text using simple heuristics.
        
        Args:
            text: Text to extract keywords from
            min_word_length: Minimum word length to consider
            exclude_common: Whether to exclude common English words
            
        Returns:
            List of potential keywords
        """
        import re
        from collections import Counter
        
        # Common words to exclude (basic stop words)
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
            'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'
        } if exclude_common else set()
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b[a-zA-Z]\w+\b', text.lower())
        
        # Filter words
        filtered_words = [
            word for word in words 
            if len(word) >= min_word_length and word not in common_words
        ]
        
        # Count frequency and return most common
        word_counts = Counter(filtered_words)
        return [word for word, count in word_counts.most_common()]