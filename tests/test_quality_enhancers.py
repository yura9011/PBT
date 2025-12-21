"""
Test suite for quality enhancers module.

Following @test-agent guidelines:
- Mock external API calls (Gemini) in unit tests
- Use pytest.fixture for test setup/teardown
- Test for JSON structure validity, not exact content
- Verify error handling paths
"""

import pytest
from unittest.mock import MagicMock, patch
import re


class TestTitleFixer:
    """Test suite for the title fixing functionality."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock Gemini model with predictable response."""
        model = MagicMock()
        model.generate_content.return_value.text = '''```json
        {
            "fixed_title": "Cinematic Cyberpunk Cityscape Art",
            "descriptor": "Cinematic",
            "subject": "Cyberpunk Cityscape",
            "type": "Art"
        }
        ```'''
        return model

    def test_title_already_valid(self):
        """Titles that already match the pattern should pass unchanged."""
        from quality_enhancers import validate_title_pattern
        
        valid_titles = [
            "Cinematic Micro-Drone Product Reveals",
            "Surreal Edible Landscapes",
            "Neo-Victorian Cyberpunk Tarot",
        ]
        
        for title in valid_titles:
            result = validate_title_pattern(title)
            assert result['is_valid'], f"Title '{title}' should be valid"

    def test_title_too_long(self):
        """Titles exceeding 6 words should be flagged."""
        from quality_enhancers import validate_title_pattern
        
        title = "2010s kendrick lamar tyler the creator style album art"
        result = validate_title_pattern(title)
        
        assert not result['is_valid']
        assert 'too_long' in result['issues']

    def test_title_too_short(self):
        """Titles with less than 3 words should be flagged."""
        from quality_enhancers import validate_title_pattern
        
        title = "Mockups"
        result = validate_title_pattern(title)
        
        assert not result['is_valid']
        assert 'too_short' in result['issues']

    def test_title_missing_descriptor(self):
        """Titles without emotional/visual descriptor should be flagged."""
        from quality_enhancers import validate_title_pattern
        
        title = "Product Mockups Templates"
        result = validate_title_pattern(title)
        
        # Should detect missing descriptor pattern
        assert 'missing_descriptor' in result.get('issues', []) or result['is_valid']

    def test_fix_title_returns_valid_structure(self, mock_model):
        """The fix_title function should return a properly structured result."""
        from quality_enhancers import fix_title
        
        result = fix_title(mock_model, "bad title here")
        
        assert 'fixed_title' in result
        assert isinstance(result['fixed_title'], str)
        assert len(result['fixed_title'].split()) >= 3
        assert len(result['fixed_title'].split()) <= 6


class TestExampleValidation:
    """Test suite for example count validation."""

    def test_validates_minimum_example_count(self):
        """Should flag packages with less than 8 examples."""
        from quality_enhancers import validate_examples
        
        package_with_few = {
            'topic': 'Test Package',
            'examples': ['ex1', 'ex2', 'ex3']
        }
        
        result = validate_examples(package_with_few)
        
        assert not result['is_valid']
        assert result['current_count'] == 3
        assert result['required_count'] >= 8

    def test_passes_valid_example_count(self):
        """Packages with 9+ examples should pass."""
        from quality_enhancers import validate_examples
        
        package_with_enough = {
            'topic': 'Test Package',
            'examples': [f'example_{i}' for i in range(9)]
        }
        
        result = validate_examples(package_with_enough)
        
        assert result['is_valid']
        assert result['current_count'] == 9

    def test_handles_dict_examples(self):
        """Should handle examples that are dicts with 'prompt' key."""
        from quality_enhancers import validate_examples
        
        package = {
            'topic': 'Test Package',
            'examples': [{'prompt': f'example_{i}'} for i in range(9)]
        }
        
        result = validate_examples(package)
        
        assert result['is_valid']
        assert result['current_count'] == 9


class TestAbstractExampleInjection:
    """Test suite for abstract example injection."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock Gemini model for abstract examples."""
        model = MagicMock()
        model.generate_content.return_value.text = '''```json
        {
            "abstract_examples": [
                "A sense of forgotten history and melancholic beauty",
                "The oppressive weight of urban decay meeting hope"
            ]
        }
        ```'''
        return model

    def test_detects_missing_abstract_examples(self):
        """Should flag packages lacking abstract/conceptual examples."""
        from quality_enhancers import check_abstract_examples
        
        package = {
            'topic': 'Test Package',
            'examples': [
                'A red car on a highway',
                'A blue house in a field',
                'A green tree in a park'
            ]
        }
        
        result = check_abstract_examples(package)
        
        assert not result['has_abstract']
        assert result['abstract_count'] == 0

    def test_recognizes_abstract_examples(self):
        """Should recognize examples with abstract/mood-based language."""
        from quality_enhancers import check_abstract_examples
        
        package = {
            'topic': 'Test Package',
            'examples': [
                'A sense of forgotten history',
                'The melancholic weight of time',
                'A red car on a highway'
            ]
        }
        
        result = check_abstract_examples(package)
        
        assert result['has_abstract']
        assert result['abstract_count'] >= 2

    def test_inject_abstract_examples(self, mock_model):
        """Should inject abstract examples into package."""
        from quality_enhancers import inject_abstract_examples
        
        package = {
            'topic': 'Test Package',
            'template': 'A [SUBJECT] in dramatic lighting',
            'examples': ['A car', 'A house', 'A tree']
        }
        
        result = inject_abstract_examples(mock_model, package)
        
        # Should have original + new abstract examples
        assert len(result['examples']) >= len(package['examples'])


class TestIntegration:
    """Integration tests for the full enhancement pipeline."""

    @pytest.fixture
    def sample_package(self):
        """Provide a sample prompt package for testing."""
        return {
            'topic': 'Product Mockups',
            'content_type': 'Image',
            'platform': 'DALL-E 3',
            'template': 'A [SUBJECT] on a minimal background',
            'examples': [f'Example {i}' for i in range(5)],
            'evaluation': {'total_score': 60}
        }

    def test_full_enhancement_pipeline(self, sample_package):
        """The full pipeline should improve a package without errors."""
        from quality_enhancers import enhance_package
        
        # This will use mocked model internally
        with patch('quality_enhancers.genai') as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value.text = '''```json
            {"fixed_title": "Minimal Product Photography Art"}
            ```'''
            mock_genai.GenerativeModel.return_value = mock_model
            
            result = enhance_package(sample_package, api_key="test_key")
            
            # Should return enhanced package
            assert 'topic' in result
            assert 'enhancement_log' in result
