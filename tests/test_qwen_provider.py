"""
Tests for Qwen Provider
"""

import pytest

from app.providers.qwen import QwenProvider


@pytest.fixture
def provider():
    """Create Qwen provider instance"""
    return QwenProvider()


def test_provider_initialization(provider):
    """Test provider initializes correctly"""
    assert provider.name == "qwen"
    assert provider.base_url == "https://chat.qwen.ai"
    assert len(provider.models) > 0
    assert 'qwen-max' in provider.models


def test_parse_model_name_basic(provider):
    """Test parsing basic model names"""
    result = provider.parse_model_name('qwen-max')
    
    assert result['base_model'] == 'qwen-max'
    assert result['chat_type'] == 't2t'
    assert result['thinking'] is False
    assert result['search'] is False
    assert result['image'] is False


def test_parse_model_name_thinking(provider):
    """Test parsing model with thinking suffix"""
    result = provider.parse_model_name('qwen-max-thinking')
    
    assert result['base_model'] == 'qwen-max'
    assert result['chat_type'] == 't2t'
    assert result['thinking'] is True


def test_parse_model_name_search(provider):
    """Test parsing model with search suffix"""
    result = provider.parse_model_name('qwen-max-search')
    
    assert result['base_model'] == 'qwen-max'
    assert result['chat_type'] == 'search'
    assert result['search'] is True


def test_parse_model_name_image(provider):
    """Test parsing model with image suffix"""
    result = provider.parse_model_name('qwen-max-image')
    
    assert result['base_model'] == 'qwen-max'
    assert result['chat_type'] == 't2i'
    assert result['image'] is True


def test_parse_model_name_image_edit(provider):
    """Test parsing model with image_edit suffix"""
    result = provider.parse_model_name('qwen-max-image_edit')
    
    assert result['base_model'] == 'qwen-max'
    assert result['chat_type'] == 'image_edit'
    assert result['image_edit'] is True
    assert result['image'] is False  # Should not be True when image_edit is True


def test_parse_model_name_video(provider):
    """Test parsing model with video suffix"""
    result = provider.parse_model_name('qwen-max-video')
    
    assert result['base_model'] == 'qwen-max'
    assert result['chat_type'] == 't2v'
    assert result['video'] is True


def test_parse_model_name_deep_research(provider):
    """Test parsing deep research model"""
    result = provider.parse_model_name('qwen-deep-research')
    
    assert result['base_model'] == 'qwen-deep-research'
    assert result['chat_type'] == 'deep_research'


def test_calculate_aspect_ratio_square(provider):
    """Test aspect ratio calculation for square images"""
    assert provider.calculate_aspect_ratio('1024x1024') == '1:1'
    assert provider.calculate_aspect_ratio('512x512') == '1:1'


def test_calculate_aspect_ratio_wide(provider):
    """Test aspect ratio calculation for wide images"""
    assert provider.calculate_aspect_ratio('1792x1024') == '7:4'
    assert provider.calculate_aspect_ratio('1920x1080') == '16:9'


def test_calculate_aspect_ratio_tall(provider):
    """Test aspect ratio calculation for tall images"""
    assert provider.calculate_aspect_ratio('1024x1792') == '4:7'
    assert provider.calculate_aspect_ratio('1080x1920') == '9:16'


def test_calculate_aspect_ratio_invalid(provider):
    """Test aspect ratio calculation with invalid input"""
    assert provider.calculate_aspect_ratio('invalid') == '1:1'
    assert provider.calculate_aspect_ratio('') == '1:1'


@pytest.mark.asyncio
async def test_transform_request_text_chat(provider):
    """Test transforming text chat request"""
    request = {
        'model': 'qwen-max',
        'messages': [
            {'role': 'user', 'content': 'Hello'}
        ]
    }
    headers = {'Authorization': 'Bearer test'}
    
    transformed = await provider.transform_request(request, headers)
    
    assert transformed['model'] == 'qwen-max'
    assert transformed['stream'] is True
    assert transformed['incremental_output'] is True
    assert transformed['chat_type'] == 't2t'
    assert 'session_id' in transformed
    assert 'chat_id' in transformed
    assert transformed['feature_config']['thinking_enabled'] is False


@pytest.mark.asyncio
async def test_transform_request_thinking_mode(provider):
    """Test transforming request with thinking mode"""
    request = {
        'model': 'qwen-max-thinking',
        'messages': [
            {'role': 'user', 'content': 'Solve this problem'}
        ]
    }
    headers = {'Authorization': 'Bearer test'}
    
    transformed = await provider.transform_request(request, headers)
    
    assert transformed['chat_type'] == 't2t'
    assert transformed['feature_config']['thinking_enabled'] is True


@pytest.mark.asyncio
async def test_transform_request_search_mode(provider):
    """Test transforming request with search mode"""
    request = {
        'model': 'qwen-max-search',
        'messages': [
            {'role': 'user', 'content': 'What is the latest news?'}
        ]
    }
    headers = {'Authorization': 'Bearer test'}
    
    transformed = await provider.transform_request(request, headers)
    
    assert transformed['chat_type'] == 'search'


@pytest.mark.asyncio
async def test_transform_request_with_thinking_budget(provider):
    """Test transforming request with custom thinking budget"""
    request = {
        'model': 'qwen-max-thinking',
        'messages': [
            {'role': 'user', 'content': 'Complex problem'}
        ],
        'thinking_budget': 10000
    }
    headers = {'Authorization': 'Bearer test'}
    
    transformed = await provider.transform_request(request, headers)
    
    assert transformed['feature_config']['thinking_budget'] == 10000


@pytest.mark.asyncio
async def test_get_auth_headers_with_compressed_token():
    """Test getting auth headers with compressed token"""
    from app.utils.token_utils import compress_token
    
    provider = QwenProvider()
    
    # Create a valid compressed token
    credentials = "test_qwen_token_123|test_ssxmod_itna_cookie_456"
    compressed = compress_token(credentials)
    
    # Get headers
    headers = await provider.get_auth_headers(compressed)
    
    # Verify headers
    assert 'Authorization' in headers
    assert headers['Authorization'] == 'Bearer test_qwen_token_123'
    assert 'Cookie' in headers
    assert 'ssxmod_itna=test_ssxmod_itna_cookie_456' in headers['Cookie']
    assert headers['Content-Type'] == 'application/json'
    assert headers['source'] == 'web'


def test_model_name_parsing_multiple_suffixes(provider):
    """Test that multiple suffix parsing works correctly"""
    # Image edit should take precedence over image
    result = provider.parse_model_name('qwen-max-image_edit')
    assert result['image_edit'] is True
    assert result['image'] is False
    
    # Thinking with search
    result = provider.parse_model_name('qwen-max-thinking-search')
    assert result['thinking'] is True
    assert result['search'] is True
    assert result['chat_type'] == 'search'  # Search takes precedence


def test_session_id_generation_uniqueness(provider):
    """Test that session IDs are unique"""
    import asyncio
    
    async def get_transformed():
        request = {
            'model': 'qwen-max',
            'messages': [{'role': 'user', 'content': 'test'}]
        }
        headers = {'Authorization': 'Bearer test'}
        return await provider.transform_request(request, headers)
    
    # Get two transformed requests
    result1 = asyncio.run(get_transformed())
    result2 = asyncio.run(get_transformed())
    
    # Session IDs should be different
    assert result1['session_id'] != result2['session_id']
    assert result1['chat_id'] != result2['chat_id']
