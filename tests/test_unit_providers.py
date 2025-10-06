#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit Tests for Provider Classes
Tests provider initialization, model listing, and configuration
"""

import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.zai_provider import ZAIProvider
from app.providers.k2think_provider import K2ThinkProvider
from app.providers.qwen_provider import QwenProvider


# ========================================
# Z.AI Provider Tests
# ========================================

class TestZAIProvider:
    """Test Z.AI provider functionality"""
    
    def test_provider_initialization(self):
        """Test Z.AI provider can be initialized"""
        provider = ZAIProvider()
        assert provider is not None
        assert provider.provider_name == "zai"
    
    def test_supported_models(self):
        """Test Z.AI returns correct supported models"""
        provider = ZAIProvider()
        models = provider.get_supported_models()
        
        assert isinstance(models, list)
        assert len(models) == 7
        
        # Check all expected models are present
        expected_models = [
            "GLM-4.5",
            "GLM-4.5-Thinking",
            "GLM-4.5-Search",
            "GLM-4.5-Air",
            "GLM-4.6",
            "GLM-4.6-Thinking",
            "GLM-4.6-Search",
        ]
        
        for model in expected_models:
            assert model in models, f"Model {model} not found in supported models"
    
    def test_model_validation(self):
        """Test Z.AI model validation"""
        provider = ZAIProvider()
        
        # Valid models should return True
        assert provider.supports_model("GLM-4.5") is True
        assert provider.supports_model("GLM-4.5-Thinking") is True
        assert provider.supports_model("GLM-4.6") is True
        
        # Invalid models should return False
        assert provider.supports_model("invalid-model") is False
        assert provider.supports_model("gpt-4") is False
    
    def test_capabilities(self):
        """Test Z.AI provider capabilities"""
        provider = ZAIProvider()
        
        # Should support streaming
        assert hasattr(provider, 'supports_streaming')
        
        # Should have model mapping
        assert hasattr(provider, 'models')
        assert len(provider.models) > 0


# ========================================
# K2Think Provider Tests
# ========================================

class TestK2ThinkProvider:
    """Test K2Think provider functionality"""
    
    def test_provider_initialization(self):
        """Test K2Think provider can be initialized"""
        provider = K2ThinkProvider()
        assert provider is not None
        assert provider.provider_name == "k2think"
    
    def test_supported_models(self):
        """Test K2Think returns correct supported model"""
        provider = K2ThinkProvider()
        models = provider.get_supported_models()
        
        assert isinstance(models, list)
        assert len(models) == 1
        assert "MBZUAI-IFM/K2-Think" in models
    
    def test_model_validation(self):
        """Test K2Think model validation"""
        provider = K2ThinkProvider()
        
        # Valid model
        assert provider.supports_model("MBZUAI-IFM/K2-Think") is True
        
        # Invalid models
        assert provider.supports_model("invalid-model") is False
        assert provider.supports_model("GLM-4.5") is False
    
    def test_reasoning_capability(self):
        """Test K2Think has reasoning capability"""
        provider = K2ThinkProvider()
        
        # K2Think is designed for advanced reasoning
        assert hasattr(provider, 'models')
        assert "K2-Think" in str(provider.models)


# ========================================
# Qwen Provider Tests
# ========================================

class TestQwenProvider:
    """Test Qwen provider functionality"""
    
    def test_provider_initialization(self):
        """Test Qwen provider can be initialized"""
        provider = QwenProvider()
        assert provider is not None
        assert provider.provider_name == "qwen"
    
    def test_supported_models(self):
        """Test Qwen returns supported models"""
        provider = QwenProvider()
        models = provider.get_supported_models()
        
        assert isinstance(models, list)
        assert len(models) >= 35  # At least 35 models
        
        # Check some key models
        key_models = ["qwen-max", "qwen-plus", "qwen-turbo"]
        for model in key_models:
            found = any(model in m for m in models)
            assert found, f"Key model variant {model} not found"
    
    def test_model_variants(self):
        """Test Qwen has various model variants"""
        provider = QwenProvider()
        models = provider.get_supported_models()
        
        # Should have thinking variants
        thinking_models = [m for m in models if "thinking" in m.lower()]
        assert len(thinking_models) > 0, "Should have thinking models"
        
        # Should have search variants
        search_models = [m for m in models if "search" in m.lower()]
        assert len(search_models) > 0, "Should have search models"
    
    def test_model_validation(self):
        """Test Qwen model validation"""
        provider = QwenProvider()
        
        # Should validate against actual model list
        models = provider.get_supported_models()
        
        # First model should be valid
        if models:
            assert provider.supports_model(models[0]) is True
        
        # Invalid model should fail
        assert provider.supports_model("totally-invalid-model-xyz") is False


# ========================================
# Multi-Provider Tests
# ========================================

class TestMultiProvider:
    """Test multiple providers together"""
    
    def test_all_providers_initialized(self):
        """Test all providers can be initialized"""
        providers = [
            ZAIProvider(),
            K2ThinkProvider(),
            QwenProvider()
        ]
        
        assert len(providers) == 3
        for provider in providers:
            assert provider is not None
    
    def test_unique_models_across_providers(self):
        """Test that each provider has unique models"""
        zai = ZAIProvider()
        k2 = K2ThinkProvider()
        qwen = QwenProvider()
        
        zai_models = set(zai.get_supported_models())
        k2_models = set(k2.get_supported_models())
        qwen_models = set(qwen.get_supported_models())
        
        # Z.AI and K2Think should not overlap
        assert len(zai_models & k2_models) == 0
        
        # Z.AI and Qwen should not overlap
        assert len(zai_models & qwen_models) == 0
        
        # K2Think and Qwen should not overlap
        assert len(k2_models & qwen_models) == 0
    
    def test_total_model_count(self):
        """Test total model count across all providers"""
        zai = ZAIProvider()
        k2 = K2ThinkProvider()
        qwen = QwenProvider()
        
        total = (
            len(zai.get_supported_models()) +
            len(k2.get_supported_models()) +
            len(qwen.get_supported_models())
        )
        
        # Should have at least 43 models (7 + 1 + 35)
        assert total >= 43, f"Expected at least 43 models, got {total}"
    
    def test_provider_names_unique(self):
        """Test that each provider has unique name"""
        providers = [
            ZAIProvider(),
            K2ThinkProvider(),
            QwenProvider()
        ]
        
        names = [p.provider_name for p in providers]
        assert len(names) == len(set(names)), "Provider names should be unique"


# ========================================
# Run Tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
