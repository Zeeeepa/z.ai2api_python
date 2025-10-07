#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive All-Models Identity Test
Tests ALL models across ALL providers simultaneously with the same prompt
"""

import os
import sys
import asyncio
import httpx
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.zai_provider import ZAIProvider
from app.providers.k2think_provider import K2ThinkProvider
from app.providers.qwen_provider import QwenProvider


# ========================================
# Configuration
# ========================================

BASE_URL = "http://localhost:8080/v1"
TEST_PROMPT = "Hello! What model are you? Please identify yourself briefly."
TIMEOUT = 90.0


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


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")


def print_provider_header(provider: str, count: int):
    """Print provider section header"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}┌{'─'*78}┐{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}│ {provider.upper()} - {count} Models{' '*(66-len(provider)-len(str(count)))}│{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}└{'─'*78}┘{Colors.END}\n")


def print_model_response(index: int, model: str, response: str, success: bool, duration: float):
    """Print individual model response"""
    status = f"{Colors.GREEN}✅{Colors.END}" if success else f"{Colors.RED}❌{Colors.END}"
    
    print(f"{status} {Colors.BOLD}Model #{index}{Colors.END}: {Colors.CYAN}{model}{Colors.END}")
    print(f"   {Colors.BOLD}Duration:{Colors.END} {duration:.2f}s")
    
    if success:
        # Truncate response to fit nicely
        response_lines = response.split('\n')
        first_line = response_lines[0][:150] if response_lines else response[:150]
        print(f"   {Colors.BOLD}Response:{Colors.END} {Colors.GREEN}{first_line}...{Colors.END}")
    else:
        print(f"   {Colors.BOLD}Error:{Colors.END} {Colors.RED}{response}{Colors.END}")
    
    print()


# ========================================
# Get All Models
# ========================================

def get_all_models() -> Dict[str, List[str]]:
    """Get all models from all providers"""
    providers = {
        "Z.AI": ZAIProvider(),
        "K2Think": K2ThinkProvider(),
        "Qwen": QwenProvider()
    }
    
    all_models = {}
    for name, provider in providers.items():
        models = provider.get_supported_models()
        all_models[name] = models
    
    return all_models


# ========================================
# Test Single Model
# ========================================

async def test_model(
    client: httpx.AsyncClient,
    provider: str,
    model: str,
    index: int
) -> Dict[str, Any]:
    """Test a single model with the identity prompt"""
    
    start_time = datetime.now()
    
    try:
        request = {
            "model": model,
            "messages": [
                {"role": "user", "content": TEST_PROMPT}
            ],
            "stream": False,
            "max_tokens": 100
        }
        
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            json=request
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            return {
                "provider": provider,
                "model": model,
                "index": index,
                "success": True,
                "response": content,
                "duration": duration,
                "status_code": 200
            }
        else:
            return {
                "provider": provider,
                "model": model,
                "index": index,
                "success": False,
                "response": f"HTTP {response.status_code}: {response.text[:100]}",
                "duration": duration,
                "status_code": response.status_code
            }
    
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return {
            "provider": provider,
            "model": model,
            "index": index,
            "success": False,
            "response": str(e)[:150],
            "duration": duration,
            "status_code": 0
        }


# ========================================
# Test All Models
# ========================================

async def test_all_models():
    """Test all models across all providers"""
    
    print_header("ALL MODELS IDENTITY TEST")
    
    print(f"{Colors.BOLD}Test Configuration:{Colors.END}")
    print(f"  • Prompt: {Colors.CYAN}\"{TEST_PROMPT}\"{Colors.END}")
    print(f"  • API Endpoint: {Colors.CYAN}{BASE_URL}{Colors.END}")
    print(f"  • Timeout: {Colors.CYAN}{TIMEOUT}s{Colors.END}")
    print(f"  • Execution: {Colors.CYAN}Concurrent (asyncio){Colors.END}")
    
    # Get all models
    print(f"\n{Colors.BOLD}Discovering models...{Colors.END}")
    all_models = get_all_models()
    
    total_models = sum(len(models) for models in all_models.values())
    print(f"  • Found {Colors.GREEN}{total_models}{Colors.END} models across {Colors.GREEN}{len(all_models)}{Colors.END} providers")
    
    for provider, models in all_models.items():
        print(f"    - {Colors.CYAN}{provider}{Colors.END}: {Colors.GREEN}{len(models)}{Colors.END} models")
    
    # Create HTTP client
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        
        # Create tasks for all models
        print(f"\n{Colors.BOLD}Sending concurrent requests to all {total_models} models...{Colors.END}")
        start_time = datetime.now()
        
        tasks = []
        model_index = 1
        
        for provider, models in all_models.items():
            for model in models:
                tasks.append(test_model(client, provider, model, model_index))
                model_index += 1
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = (datetime.now() - start_time).total_seconds()
    
    # Process and display results by provider
    results_by_provider = {}
    for result in results:
        if isinstance(result, dict):
            provider = result["provider"]
            if provider not in results_by_provider:
                results_by_provider[provider] = []
            results_by_provider[provider].append(result)
    
    print_header("RESULTS BY PROVIDER")
    
    # Display results for each provider
    for provider, provider_results in results_by_provider.items():
        print_provider_header(provider, len(provider_results))
        
        for result in sorted(provider_results, key=lambda x: x["index"]):
            print_model_response(
                result["index"],
                result["model"],
                result["response"],
                result["success"],
                result["duration"]
            )
    
    # Summary statistics
    print_header("SUMMARY STATISTICS")
    
    successful = [r for r in results if isinstance(r, dict) and r["success"]]
    failed = [r for r in results if isinstance(r, dict) and not r["success"]]
    
    success_rate = (len(successful) / total_models * 100) if total_models > 0 else 0
    avg_duration = sum(r["duration"] for r in successful) / len(successful) if successful else 0
    
    print(f"{Colors.BOLD}Total Models Tested:{Colors.END} {Colors.CYAN}{total_models}{Colors.END}")
    print(f"{Colors.BOLD}Successful:{Colors.END} {Colors.GREEN}{len(successful)}{Colors.END}")
    print(f"{Colors.BOLD}Failed:{Colors.END} {Colors.RED}{len(failed)}{Colors.END}")
    print(f"{Colors.BOLD}Success Rate:{Colors.END} {Colors.GREEN if success_rate >= 80 else Colors.RED}{success_rate:.1f}%{Colors.END}")
    print(f"{Colors.BOLD}Total Duration:{Colors.END} {Colors.CYAN}{total_duration:.2f}s{Colors.END}")
    print(f"{Colors.BOLD}Avg Response Time:{Colors.END} {Colors.CYAN}{avg_duration:.2f}s{Colors.END}")
    
    # Provider breakdown
    print(f"\n{Colors.BOLD}Provider Breakdown:{Colors.END}")
    for provider, provider_results in results_by_provider.items():
        provider_success = [r for r in provider_results if r["success"]]
        provider_rate = len(provider_success) / len(provider_results) * 100
        
        status_color = Colors.GREEN if provider_rate >= 80 else Colors.YELLOW if provider_rate >= 50 else Colors.RED
        
        print(f"  • {Colors.CYAN}{provider:12}{Colors.END}: {status_color}{len(provider_success):2}/{len(provider_results):2}{Colors.END} ({status_color}{provider_rate:.0f}%{Colors.END})")
    
    # Failed models details
    if failed:
        print(f"\n{Colors.BOLD}{Colors.RED}Failed Models:{Colors.END}")
        for result in failed:
            print(f"  • {Colors.RED}{result['provider']:12} - {result['model']}{Colors.END}")
            print(f"    Error: {result['response'][:100]}...")
    
    print()


# ========================================
# Pytest Test Function
# ========================================

async def test_all_models_identity_pytest():
    """Pytest wrapper for all models identity test"""
    await test_all_models()


# ========================================
# Main Entry Point
# ========================================

async def main():
    """Main entry point for standalone execution"""
    try:
        await test_all_models()
        print(f"{Colors.BOLD}{Colors.GREEN}Test completed successfully!{Colors.END}\n")
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}\n")
        raise


if __name__ == "__main__":
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                     ALL MODELS IDENTITY TEST                                 ║
║                                                                              ║
║  This test sends the same prompt to ALL models across ALL providers         ║
║  and displays each model's response.                                         ║
║                                                                              ║
║  Requirements:                                                               ║
║    • API server running at http://localhost:8080                            ║
║    • All providers configured                                                ║
║                                                                              ║
║  Press Ctrl+C to interrupt                                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}
    """)
    
    asyncio.run(main())

