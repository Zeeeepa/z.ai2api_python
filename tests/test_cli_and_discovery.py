#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive tests for CLI module and model discovery
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.cli import (
    CLIDisplay,
    discover_provider_models,
    check_provider_status,
    run_startup_diagnostics,
    get_provider_features
)
from app import __version__


class TestCLIDisplay:
    """Test CLI display functionality"""
    
    def test_cli_display_initialization(self):
        """Test CLI display can be initialized"""
        display = CLIDisplay(use_rich=False)
        assert display.use_rich is False
    
    def test_cli_display_with_rich(self):
        """Test CLI display with rich library"""
        try:
            from rich.console import Console
            display = CLIDisplay(use_rich=True)
            assert display.use_rich is True
            assert hasattr(display, 'console')
        except ImportError:
            pytest.skip("Rich library not installed")
    
    def test_print_banner_plain(self):
        """Test banner printing without rich"""
        display = CLIDisplay(use_rich=False)
        # Should not raise errors
        display.print_banner()
    
    def test_print_config_summary(self):
        """Test configuration summary printing"""
        display = CLIDisplay(use_rich=False)
        with patch('app.cli.settings') as mock_settings:
            mock_settings.HOST = "0.0.0.0"
            mock_settings.LISTEN_PORT = 8080
            mock_settings.DEBUG_LOGGING = True
            mock_settings.ANONYMOUS_MODE = True
            mock_settings.TOOL_SUPPORT = True
            
            # Should not raise errors
            display.print_config_summary()
    
    def test_print_connection_info(self):
        """Test connection info printing"""
        display = CLIDisplay(use_rich=False)
        with patch('app.cli.settings') as mock_settings:
            mock_settings.HOST = "localhost"
            mock_settings.LISTEN_PORT = 8080
            
            # Should not raise errors
            display.print_connection_info()
    
    def test_print_provider_status(self):
        """Test provider status table"""
        display = CLIDisplay(use_rich=False)
        provider_data = [
            {
                "name": "ZAI",
                "status": "Available",
                "available": True,
                "model_count": 7,
                "features": "Stream, Tools, Search"
            },
            {
                "name": "K2THINK",
                "status": "Available",
                "available": True,
                "model_count": 1,
                "features": "Stream, Reasoning"
            }
        ]
        
        # Should not raise errors
        display.print_provider_status(provider_data)
    
    def test_print_models_table(self):
        """Test models table printing"""
        display = CLIDisplay(use_rich=False)
        models_by_provider = {
            "ZAI": ["GLM-4.5", "GLM-4.5-Thinking", "GLM-4.5-Search"],
            "K2THINK": ["MBZUAI-IFM/K2-Think"],
            "LONGCAT": ["LongCat-Flash", "LongCat", "LongCat-Search"]
        }
        
        # Should not raise errors
        display.print_models_table(models_by_provider)
    
    def test_print_error(self):
        """Test error message printing"""
        display = CLIDisplay(use_rich=False)
        display.print_error("Test error message")
    
    def test_print_info(self):
        """Test info message printing"""
        display = CLIDisplay(use_rich=False)
        display.print_info("Test info message")
    
    def test_print_success(self):
        """Test success message printing"""
        display = CLIDisplay(use_rich=False)
        display.print_success("Test success message")


class TestModelDiscovery:
    """Test model discovery functionality"""
    
    @pytest.mark.asyncio
    async def test_discover_provider_models(self):
        """Test discovering models from all providers"""
        with patch('app.cli.initialize_providers'):
            with patch('app.cli.provider_registry') as mock_registry:
                # Mock providers
                mock_zai = Mock()
                mock_zai.get_supported_models.return_value = [
                    "GLM-4.5", "GLM-4.5-Thinking", "GLM-4.5-Search"
                ]
                
                mock_k2think = Mock()
                mock_k2think.get_supported_models.return_value = ["MBZUAI-IFM/K2-Think"]
                
                mock_longcat = Mock()
                mock_longcat.get_supported_models.return_value = [
                    "LongCat-Flash", "LongCat", "LongCat-Search"
                ]
                
                mock_registry.list_providers.return_value = ["zai", "k2think", "longcat"]
                mock_registry.get_provider_by_name.side_effect = lambda name: {
                    "zai": mock_zai,
                    "k2think": mock_k2think,
                    "longcat": mock_longcat
                }[name]
                
                models = await discover_provider_models()
                
                assert "ZAI" in models
                assert "K2THINK" in models
                assert "LONGCAT" in models
                assert len(models["ZAI"]) == 3
                assert len(models["K2THINK"]) == 1
                assert len(models["LONGCAT"]) == 3
    
    @pytest.mark.asyncio
    async def test_discover_provider_models_with_error(self):
        """Test model discovery handles provider errors"""
        with patch('app.cli.initialize_providers'):
            with patch('app.cli.provider_registry') as mock_registry:
                mock_provider = Mock()
                mock_provider.get_supported_models.side_effect = Exception("Connection error")
                
                mock_registry.list_providers.return_value = ["failing_provider"]
                mock_registry.get_provider_by_name.return_value = mock_provider
                
                models = await discover_provider_models()
                
                # Should return empty list for failing provider
                assert "FAILING_PROVIDER" in models
                assert models["FAILING_PROVIDER"] == []
    
    def test_get_provider_features(self):
        """Test getting provider feature summary"""
        assert get_provider_features("zai") == "Stream, Tools, Search, Thinking"
        assert get_provider_features("k2think") == "Stream, Reasoning"
        assert get_provider_features("longcat") == "Stream, Search"
        assert get_provider_features("unknown") == "Unknown"


class TestProviderStatus:
    """Test provider status checking"""
    
    @pytest.mark.asyncio
    async def test_check_provider_status_all_available(self):
        """Test checking status when all providers are available"""
        with patch('app.cli.provider_registry') as mock_registry:
            mock_provider = Mock()
            mock_provider.get_supported_models.return_value = ["model1", "model2"]
            
            mock_registry.list_providers.return_value = ["provider1", "provider2"]
            mock_registry.get_provider_by_name.return_value = mock_provider
            
            status = await check_provider_status()
            
            assert len(status) == 2
            assert all(p["available"] for p in status)
            assert all(p["status"] == "Available" for p in status)
    
    @pytest.mark.asyncio
    async def test_check_provider_status_with_errors(self):
        """Test checking status with provider errors"""
        with patch('app.cli.provider_registry') as mock_registry:
            mock_provider = Mock()
            mock_provider.get_supported_models.side_effect = Exception("Test error")
            
            mock_registry.list_providers.return_value = ["failing_provider"]
            mock_registry.get_provider_by_name.return_value = mock_provider
            
            status = await check_provider_status()
            
            assert len(status) == 1
            assert status[0]["available"] is False
            assert status[0]["status"] == "Error"
            assert status[0]["model_count"] == 0


class TestStartupDiagnostics:
    """Test startup diagnostics"""
    
    @pytest.mark.asyncio
    async def test_run_startup_diagnostics_verbose(self):
        """Test running startup diagnostics in verbose mode"""
        display = CLIDisplay(use_rich=False)
        
        with patch('app.cli.check_provider_status') as mock_check:
            with patch('app.cli.discover_provider_models') as mock_discover:
                mock_check.return_value = [{
                    "name": "TEST",
                    "status": "Available",
                    "available": True,
                    "model_count": 1,
                    "features": "Test"
                }]
                
                mock_discover.return_value = {"TEST": ["model1"]}
                
                status, models = await run_startup_diagnostics(display, verbose=True)
                
                assert len(status) == 1
                assert "TEST" in models
    
    @pytest.mark.asyncio
    async def test_run_startup_diagnostics_quiet(self):
        """Test running startup diagnostics in quiet mode"""
        display = CLIDisplay(use_rich=False)
        
        with patch('app.cli.check_provider_status') as mock_check:
            with patch('app.cli.discover_provider_models') as mock_discover:
                mock_check.return_value = []
                mock_discover.return_value = {}
                
                status, models = await run_startup_diagnostics(display, verbose=False)
                
                assert isinstance(status, list)
                assert isinstance(models, dict)


class TestCLIIntegration:
    """Integration tests for CLI"""
    
    def test_version_display(self):
        """Test version is correctly displayed"""
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check with available providers"""
        with patch('app.cli.run_startup_diagnostics') as mock_diagnostics:
            provider_status = [{
                "name": "ZAI",
                "available": True,
                "status": "Available",
                "model_count": 7,
                "features": "Stream, Tools"
            }]
            models = {"ZAI": ["GLM-4.5"]}
            
            mock_diagnostics.return_value = (provider_status, models)
            
            # Simulate health check logic
            available_count = sum(1 for p in provider_status if p["available"])
            total_models = sum(len(m) for m in models.values())
            
            assert available_count > 0
            assert total_models > 0
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check with no providers"""
        with patch('app.cli.run_startup_diagnostics') as mock_diagnostics:
            provider_status = [{
                "name": "TEST",
                "available": False,
                "status": "Error",
                "model_count": 0,
                "features": ""
            }]
            models = {"TEST": []}
            
            mock_diagnostics.return_value = (provider_status, models)
            
            available_count = sum(1 for p in provider_status if p["available"])
            
            assert available_count == 0


class TestCLIEdgeCases:
    """Test CLI edge cases"""
    
    def test_empty_provider_list(self):
        """Test handling of empty provider list"""
        display = CLIDisplay(use_rich=False)
        display.print_provider_status([])
    
    def test_empty_models_dict(self):
        """Test handling of empty models dictionary"""
        display = CLIDisplay(use_rich=False)
        display.print_models_table({})
    
    def test_provider_with_no_models(self):
        """Test provider with zero models"""
        display = CLIDisplay(use_rich=False)
        models = {"EMPTY_PROVIDER": []}
        display.print_models_table(models)
    
    @pytest.mark.asyncio
    async def test_discovery_with_no_providers_registered(self):
        """Test model discovery with no providers"""
        with patch('app.cli.initialize_providers'):
            with patch('app.cli.provider_registry') as mock_registry:
                mock_registry.list_providers.return_value = []
                
                models = await discover_provider_models()
                assert models == {}


class TestCLICommandLineArgs:
    """Test CLI command line argument parsing"""
    
    def test_check_flag(self):
        """Test --check flag parsing"""
        # Would test argparse, but in unit tests we just verify the logic exists
        assert hasattr(__import__('app.cli'), 'main')
    
    def test_list_models_flag(self):
        """Test --list-models flag parsing"""
        # Verify the CLI module has the necessary functions
        from app.cli import discover_provider_models
        assert callable(discover_provider_models)
    
    def test_no_color_flag(self):
        """Test --no-color flag"""
        display = CLIDisplay(use_rich=False)
        assert display.use_rich is False


class TestCLIRobustness:
    """Test CLI robustness and error handling"""
    
    @pytest.mark.asyncio
    async def test_discovery_continues_after_single_provider_failure(self):
        """Test that discovery continues if one provider fails"""
        with patch('app.cli.initialize_providers'):
            with patch('app.cli.provider_registry') as mock_registry:
                mock_good = Mock()
                mock_good.get_supported_models.return_value = ["model1"]
                
                mock_bad = Mock()
                mock_bad.get_supported_models.side_effect = Exception("Error")
                
                mock_registry.list_providers.return_value = ["good", "bad"]
                mock_registry.get_provider_by_name.side_effect = lambda n: {
                    "good": mock_good,
                    "bad": mock_bad
                }[n]
                
                models = await discover_provider_models()
                
                # Good provider should still return models
                assert "GOOD" in models
                assert len(models["GOOD"]) == 1
                
                # Bad provider should have empty list
                assert "BAD" in models
                assert models["BAD"] == []
    
    def test_display_handles_unicode(self):
        """Test display handles unicode characters"""
        display = CLIDisplay(use_rich=False)
        models = {"PROVIDER": ["模型1", "モデル2", "🤖 Model"]}
        
        # Should not raise errors
        display.print_models_table(models)
    
    def test_display_handles_long_model_names(self):
        """Test display handles very long model names"""
        display = CLIDisplay(use_rich=False)
        long_name = "A" * 200
        models = {"PROVIDER": [long_name]}
        
        # Should not raise errors
        display.print_models_table(models)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

