#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Direct All-Models Test (No Server Required)
Tests model discovery and listing without requiring API server
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.zai_provider import ZAIProvider
from app.providers.k2think_provider import K2ThinkProvider
from app.providers.qwen_provider import QwenProvider


# ========================================
# Color Output
# ========================================

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# ========================================
# Test All Models Discovery
# ========================================

def test_all_models_discovery():
    """Test all models can be discovered from providers"""
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'ALL MODELS DISCOVERY TEST'.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")
    
    # Initialize providers
    providers = {
        "Z.AI": ZAIProvider(),
        "K2Think": K2ThinkProvider(),
        "Qwen": QwenProvider()
    }
    
    all_models = {}
    total_count = 0
    
    print(f"{Colors.BOLD}Discovering models from all providers...{Colors.END}\n")
    
    # Get models from each provider
    for name, provider in providers.items():
        models = provider.get_supported_models()
        all_models[name] = models
        total_count += len(models)
        
        print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{name} Provider{Colors.END} - {Colors.GREEN}{len(models)} models{Colors.END}")
        print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*80}{Colors.END}\n")
        
        # Display models in a nice format
        for i, model in enumerate(models, 1):
            # Determine model type/features
            features = []
            model_lower = model.lower()
            
            if "thinking" in model_lower:
                features.append(f"{Colors.BLUE}🧠 Reasoning{Colors.END}")
            if "search" in model_lower:
                features.append(f"{Colors.GREEN}🔍 Search{Colors.END}")
            if "vision" in model_lower or "image" in model_lower:
                features.append(f"{Colors.YELLOW}👁️  Vision{Colors.END}")
            if "video" in model_lower:
                features.append(f"{Colors.RED}🎬 Video{Colors.END}")
            if "air" in model_lower or "lite" in model_lower or "light" in model_lower:
                features.append(f"{Colors.CYAN}⚡ Lightweight{Colors.END}")
            if "max" in model_lower or "turbo" in model_lower or "plus" in model_lower:
                features.append(f"{Colors.GREEN}🚀 Fast{Colors.END}")
            if "long" in model_lower:
                features.append(f"{Colors.YELLOW}📜 Long Context{Colors.END}")
            
            features_str = " ".join(features) if features else f"{Colors.CYAN}💬 Standard{Colors.END}"
            
            print(f"  {Colors.GREEN}{i:2d}.{Colors.END} {Colors.BOLD}{model:50}{Colors.END} {features_str}")
        
        print()
    
    # Summary
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'SUMMARY'.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")
    
    print(f"{Colors.BOLD}Total Providers:{Colors.END} {Colors.GREEN}{len(providers)}{Colors.END}")
    print(f"{Colors.BOLD}Total Models:{Colors.END} {Colors.GREEN}{total_count}{Colors.END}\n")
    
    print(f"{Colors.BOLD}Breakdown:{Colors.END}")
    for name, models in all_models.items():
        percentage = (len(models) / total_count * 100) if total_count > 0 else 0
        bar_length = int(percentage / 2)  # Scale to 50 chars max
        bar = f"{Colors.GREEN}{'█' * bar_length}{Colors.END}"
        
        print(f"  {Colors.CYAN}{name:12}{Colors.END}: {bar} {Colors.GREEN}{len(models):2d}{Colors.END} ({percentage:.1f}%)")
    
    # Model types summary
    print(f"\n{Colors.BOLD}Model Features:{Colors.END}")
    
    all_model_list = []
    for models in all_models.values():
        all_model_list.extend(models)
    
    thinking_count = sum(1 for m in all_model_list if "thinking" in m.lower())
    search_count = sum(1 for m in all_model_list if "search" in m.lower())
    vision_count = sum(1 for m in all_model_list if "vision" in m.lower() or "image" in m.lower())
    video_count = sum(1 for m in all_model_list if "video" in m.lower())
    long_count = sum(1 for m in all_model_list if "long" in m.lower())
    
    if thinking_count:
        print(f"  • {Colors.BLUE}🧠 Reasoning/Thinking:{Colors.END} {Colors.GREEN}{thinking_count}{Colors.END}")
    if search_count:
        print(f"  • {Colors.GREEN}🔍 Search/Web:{Colors.END} {Colors.GREEN}{search_count}{Colors.END}")
    if vision_count:
        print(f"  • {Colors.YELLOW}👁️  Vision/Image:{Colors.END} {Colors.GREEN}{vision_count}{Colors.END}")
    if video_count:
        print(f"  • {Colors.RED}🎬 Video:{Colors.END} {Colors.GREEN}{video_count}{Colors.END}")
    if long_count:
        print(f"  • {Colors.YELLOW}📜 Long Context:{Colors.END} {Colors.GREEN}{long_count}{Colors.END}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ All models discovered successfully!{Colors.END}\n")
    
    # Return data for assertions
    return {
        "total": total_count,
        "by_provider": {name: len(models) for name, models in all_models.items()},
        "models": all_models
    }


# ========================================
# Pytest Test Function
# ========================================

def test_model_discovery():
    """Pytest test for model discovery"""
    result = test_all_models_discovery()
    
    # Assertions
    assert result["total"] >= 43, f"Expected at least 43 models, got {result['total']}"
    assert result["by_provider"]["Z.AI"] == 7, "Z.AI should have exactly 7 models"
    assert result["by_provider"]["K2Think"] == 1, "K2Think should have exactly 1 model"
    assert result["by_provider"]["Qwen"] >= 35, "Qwen should have at least 35 models"


# ========================================
# Main Entry Point
# ========================================

if __name__ == "__main__":
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                  ALL MODELS DISCOVERY TEST                                   ║
║                                                                              ║
║  This test discovers and lists all models from all providers                ║
║                                                                              ║
║  No API server required - direct provider access                            ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}
    """)
    
    try:
        test_all_models_discovery()
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}\n")
        raise

