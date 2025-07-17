import logging
import re
from typing import Dict, Any, List
import Levenshtein
from config import Config

logger = logging.getLogger(__name__)

class TextAnalysisService:
    def __init__(self):
        self.levenshtein_threshold = Config.LEVENSHTEIN_THRESHOLD
        
    def clean_text(self, text: str) -> str:
        """Clean text by removing punctuation and normalizing whitespace"""
        try:
            # Remove punctuation (keep only letters, numbers, and spaces)
            cleaned = re.sub(r'[^\w\s]', '', text)
            
            # Normalize whitespace
            cleaned = ' '.join(cleaned.split())
            
            # Convert to lowercase for comparison
            cleaned = cleaned.lower()
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text.lower()
            
    def calculate_levenshtein_distance(self, text1: str, text2: str) -> int:
        """Calculate Levenshtein distance between two texts"""
        try:
            # Clean both texts
            clean_text1 = self.clean_text(text1)
            clean_text2 = self.clean_text(text2)
            
            # Calculate distance
            distance = Levenshtein.distance(clean_text1, clean_text2)
            
            logger.debug(f"Levenshtein distance between '{clean_text1}' and '{clean_text2}': {distance}")
            return distance
            
        except Exception as e:
            logger.error(f"Error calculating Levenshtein distance: {e}")
            return max(len(text1), len(text2))  # Return max possible distance on error
            
    def calculate_similarity_percentage(self, text1: str, text2: str) -> float:
        """Calculate similarity percentage between two texts"""
        try:
            # Clean both texts
            clean_text1 = self.clean_text(text1)
            clean_text2 = self.clean_text(text2)
            
            # Calculate distance
            distance = Levenshtein.distance(clean_text1, clean_text2)
            
            # Calculate similarity percentage
            max_len = max(len(clean_text1), len(clean_text2))
            if max_len == 0:
                return 1.0  # Both texts are empty
                
            similarity = 1 - (distance / max_len)
            
            logger.debug(f"Similarity between '{clean_text1}' and '{clean_text2}': {similarity:.2%}")
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating similarity percentage: {e}")
            return 0.0
            
    def is_match(self, predicted_text: str, actual_text: str) -> bool:
        """Determine if predicted text matches actual text based on threshold"""
        try:
            similarity = self.calculate_similarity_percentage(predicted_text, actual_text)
            return similarity >= self.levenshtein_threshold
            
        except Exception as e:
            logger.error(f"Error determining text match: {e}")
            return False
            
    def analyze_text_differences(self, text1: str, text2: str) -> Dict[str, Any]:
        """Analyze differences between two texts"""
        try:
            # Clean both texts
            clean_text1 = self.clean_text(text1)
            clean_text2 = self.clean_text(text2)
            
            # Calculate metrics
            distance = Levenshtein.distance(clean_text1, clean_text2)
            similarity = self.calculate_similarity_percentage(text1, text2)
            
            # Split into words for word-level analysis
            words1 = clean_text1.split()
            words2 = clean_text2.split()
            
            # Calculate word-level metrics
            word_distance = Levenshtein.distance(' '.join(words1), ' '.join(words2))
            
            # Find common words
            common_words = set(words1) & set(words2)
            unique_words1 = set(words1) - set(words2)
            unique_words2 = set(words2) - set(words1)
            
            # Calculate word overlap
            total_unique_words = len(set(words1) | set(words2))
            word_overlap = len(common_words) / max(total_unique_words, 1)
            
            return {
                'original_text1': text1,
                'original_text2': text2,
                'cleaned_text1': clean_text1,
                'cleaned_text2': clean_text2,
                'character_distance': distance,
                'word_distance': word_distance,
                'similarity_percentage': similarity,
                'is_match': similarity >= self.levenshtein_threshold,
                'threshold_used': self.levenshtein_threshold,
                'word_count1': len(words1),
                'word_count2': len(words2),
                'common_words': list(common_words),
                'unique_words1': list(unique_words1),
                'unique_words2': list(unique_words2),
                'word_overlap': word_overlap,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text differences: {e}")
            return {
                'error': str(e),
                'original_text1': text1,
                'original_text2': text2,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
    def validate_text_content(self, text: str) -> Dict[str, Any]:
        """Validate text content for betting purposes"""
        try:
            if not text or not text.strip():
                return {
                    'valid': False,
                    'error': 'Text cannot be empty'
                }
                
            # Clean text
            cleaned = self.clean_text(text)
            
            # Check minimum length
            if len(cleaned) < 3:
                return {
                    'valid': False,
                    'error': 'Text must be at least 3 characters after cleaning'
                }
                
            # Check maximum length
            if len(cleaned) > 1000:
                return {
                    'valid': False,
                    'error': 'Text cannot exceed 1000 characters after cleaning'
                }
                
            # Check for reasonable word count
            words = cleaned.split()
            if len(words) < 1:
                return {
                    'valid': False,
                    'error': 'Text must contain at least one word'
                }
                
            if len(words) > 200:
                return {
                    'valid': False,
                    'error': 'Text cannot exceed 200 words'
                }
                
            return {
                'valid': True,
                'cleaned_text': cleaned,
                'word_count': len(words),
                'character_count': len(cleaned),
                'original_length': len(text)
            }
            
        except Exception as e:
            logger.error(f"Error validating text content: {e}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
            
    def batch_analyze_texts(self, text_pairs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Batch analyze multiple text pairs"""
        try:
            results = []
            
            for i, pair in enumerate(text_pairs):
                try:
                    text1 = pair.get('text1', '')
                    text2 = pair.get('text2', '')
                    
                    analysis = self.analyze_text_differences(text1, text2)
                    analysis['pair_index'] = i
                    results.append(analysis)
                    
                except Exception as e:
                    logger.error(f"Error analyzing text pair {i}: {e}")
                    results.append({
                        'pair_index': i,
                        'error': str(e),
                        'original_text1': pair.get('text1', ''),
                        'original_text2': pair.get('text2', '')
                    })
                    
            return results
            
        except Exception as e:
            logger.error(f"Error in batch text analysis: {e}")
            return []
            
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """Get detailed statistics about a text"""
        try:
            original_length = len(text)
            cleaned = self.clean_text(text)
            words = cleaned.split()
            
            # Character frequency
            char_freq = {}
            for char in cleaned:
                char_freq[char] = char_freq.get(char, 0) + 1
                
            # Word frequency
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
                
            # Average word length
            avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
            
            return {
                'original_length': original_length,
                'cleaned_length': len(cleaned),
                'word_count': len(words),
                'unique_words': len(set(words)),
                'average_word_length': avg_word_length,
                'character_frequency': char_freq,
                'word_frequency': word_freq,
                'most_common_words': sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10],
                'longest_word': max(words, key=len) if words else '',
                'shortest_word': min(words, key=len) if words else ''
            }
            
        except Exception as e:
            logger.error(f"Error getting text statistics: {e}")
            return {
                'error': str(e),
                'original_length': len(text) if text else 0
            }

from datetime import datetime
