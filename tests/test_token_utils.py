"""
Tests for token compression/decompression utilities
"""

import pytest

from app.utils.token_utils import (
    compress_token,
    decompress_token,
    parse_credentials,
    validate_token_format,
)


def test_compress_decompress_roundtrip():
    """Test that compression and decompression are reversible"""
    original = "test_token_12345|test_cookie_67890"
    compressed = compress_token(original)
    decompressed = decompress_token(compressed)
    
    assert decompressed == original
    assert isinstance(compressed, str)
    assert len(compressed) > 0


def test_compress_reduces_size():
    """Test that compression actually reduces size for longer strings"""
    # Create a long repetitive string
    original = "qwen_token_" * 100 + "|" + "ssxmod_itna_" * 100
    compressed = compress_token(original)
    
    # Compressed should be significantly smaller
    assert len(compressed) < len(original)


def test_decompress_invalid_format():
    """Test that decompressing invalid data raises error"""
    with pytest.raises((ValueError, Exception)):  # noqa: B017
        decompress_token("invalid_base64_!@#$")


def test_parse_credentials_valid():
    """Test parsing valid credentials string"""
    credentials = "abc123token|xyz789cookie"
    parsed = parse_credentials(credentials)
    
    assert parsed is not None
    assert parsed['qwen_token'] == "abc123token"
    assert parsed['ssxmod_itna'] == "xyz789cookie"


def test_parse_credentials_invalid():
    """Test parsing invalid credentials (no separator)"""
    credentials = "no_separator_here"
    parsed = parse_credentials(credentials)
    
    assert parsed is None


def test_parse_credentials_with_whitespace():
    """Test that parsing handles whitespace correctly"""
    credentials = " abc123 | xyz789 "
    parsed = parse_credentials(credentials)
    
    assert parsed is not None
    assert parsed['qwen_token'] == "abc123"
    assert parsed['ssxmod_itna'] == "xyz789"


def test_validate_token_format_valid():
    """Test validation of valid compressed token"""
    original = "test_token|test_cookie"
    compressed = compress_token(original)
    
    assert validate_token_format(compressed) is True


def test_validate_token_format_invalid():
    """Test validation of invalid token formats"""
    assert validate_token_format("not_base64_!@#$") is False
    assert validate_token_format("") is False
    assert validate_token_format("validbase64butnotgzip") is False


def test_empty_credentials():
    """Test handling of empty credentials"""
    with pytest.raises(ValueError):
        compress_token("")


def test_unicode_credentials():
    """Test handling of unicode characters in credentials"""
    original = "token_with_émojis_🎉|cookie_数据_测试"
    compressed = compress_token(original)
    decompressed = decompress_token(compressed)
    
    assert decompressed == original
