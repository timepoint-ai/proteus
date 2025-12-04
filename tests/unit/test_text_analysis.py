"""
Unit tests for text analysis (Levenshtein distance).
"""

import pytest


@pytest.mark.unit
class TestLevenshteinDistance:
    """Test Levenshtein distance calculations."""

    @pytest.fixture
    def levenshtein(self):
        """Get Levenshtein distance function."""
        try:
            from Levenshtein import distance
            return distance
        except ImportError:
            pytest.skip("python-Levenshtein not installed")

    def test_identical_strings(self, levenshtein):
        """Test distance between identical strings is 0."""
        assert levenshtein("hello", "hello") == 0
        assert levenshtein("", "") == 0
        assert levenshtein("test prediction", "test prediction") == 0

    def test_empty_string(self, levenshtein):
        """Test distance with empty string."""
        assert levenshtein("hello", "") == 5
        assert levenshtein("", "world") == 5

    def test_single_character_difference(self, levenshtein):
        """Test single character operations."""
        # Substitution
        assert levenshtein("hello", "hallo") == 1
        # Insertion
        assert levenshtein("hello", "helllo") == 1
        # Deletion
        assert levenshtein("hello", "helo") == 1

    def test_completely_different(self, levenshtein):
        """Test completely different strings."""
        assert levenshtein("abc", "xyz") == 3
        assert levenshtein("cat", "dog") == 3

    def test_case_sensitivity(self, levenshtein):
        """Test that comparison is case-sensitive."""
        assert levenshtein("Hello", "hello") == 1
        assert levenshtein("HELLO", "hello") == 5

    def test_prediction_comparison(self, levenshtein):
        """Test typical prediction text comparison."""
        actual = "Mars is the future of humanity"
        prediction1 = "Mars is the future"
        prediction2 = "The moon is closer"
        prediction3 = "Mars is the future of humanity"

        # Exact match
        assert levenshtein(actual, prediction3) == 0
        # Partial match
        distance1 = levenshtein(actual, prediction1)
        # Completely different
        distance2 = levenshtein(actual, prediction2)

        # Closer prediction should have smaller distance
        assert distance1 < distance2


@pytest.mark.unit
class TestTextNormalization:
    """Test text normalization for comparison."""

    def test_strip_punctuation(self):
        """Test stripping punctuation from text."""
        import re

        def strip_punctuation(text):
            return re.sub(r'[^\w\s]', '', text)

        assert strip_punctuation("Hello, world!") == "Hello world"
        assert strip_punctuation("What's up?") == "Whats up"
        assert strip_punctuation("Test... test!!!") == "Test test"

    def test_normalize_whitespace(self):
        """Test normalizing whitespace."""
        def normalize_whitespace(text):
            return " ".join(text.split())

        assert normalize_whitespace("hello   world") == "hello world"
        assert normalize_whitespace("  test  ") == "test"
        assert normalize_whitespace("a\t\nb") == "a b"

    def test_lowercase_comparison(self):
        """Test lowercase comparison."""
        text1 = "HELLO WORLD"
        text2 = "hello world"

        assert text1.lower() == text2.lower()

    def test_full_normalization_pipeline(self):
        """Test complete text normalization."""
        import re

        def normalize_text(text):
            # Lowercase
            text = text.lower()
            # Remove punctuation
            text = re.sub(r'[^\w\s]', '', text)
            # Normalize whitespace
            text = " ".join(text.split())
            return text

        assert normalize_text("Hello, World!") == "hello world"
        assert normalize_text("  Test...  Test!!!  ") == "test test"
        assert normalize_text("What's UP?!") == "whats up"
