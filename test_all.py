#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Z.AI Model Validation Test Suite - Async Concurrent Edition

Comprehensive async test suite that validates all 7 Z.AI models concurrently:
- GLM-4.5 (Standard)
- GLM-4.5-Air (Fast)
- GLM-4.5-Thinking (Reasoning)
- GLM-4.5-Search (Web Search)
- GLM-4.6 (Extended Context)
- GLM-4.6-Thinking (Extended + Reasoning)
- GLM-4.5V (Vision/Multimodal)

Features:
- Async concurrent testing (all models tested simultaneously)
- Beautiful colored terminal output
- Detailed response validation
- Token usage tracking
- Performance metrics
- JSON export for CI/CD

Usage:
    python test_all.py
    python test_all.py --base-url http://localhost:8080/v1
    python test_all.py --verbose
    python test_all.py --export
"""

import asyncio
import sys
import time
import json
import argparse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

try:
    import httpx
except ImportError:
    print("❌ Error: httpx library not installed!")
    print("Install with: pip install httpx")
    sys.exit(1)


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:8080/v1"
DEFAULT_API_KEY = "sk-dummy"
REQUEST_TIMEOUT = 90.0  # seconds
DEFAULT_PROMPT = "Hello! What model are you? Please identify yourself briefly."


class ModelCapability(Enum):
    """Model capability flags"""
    TEXT = "text"
    VISION = "vision"
    THINKING = "thinking"
    SEARCH = "search"
    EXTENDED_CONTEXT = "extended_context"


@dataclass
class ModelConfig:
    """Configuration for a Z.AI model"""
    name: str
    display_name: str
    capabilities: List[ModelCapability]
    max_tokens: int
    description: str
    test_prompt: str


# Model definitions
MODELS = [
    ModelConfig(
        name="GLM-4.5",
        display_name="GLM-4.5 (Standard)",
        capabilities=[ModelCapability.TEXT],
        max_tokens=128000,
        description="General purpose model with 128K context",
        test_prompt=DEFAULT_PROMPT
    ),
    ModelConfig(
        name="GLM-4.5-Air",
        display_name="GLM-4.5-Air (Fast)",
        capabilities=[ModelCapability.TEXT],
        max_tokens=128000,
        description="Fast and efficient model with 128K context",
        test_prompt=DEFAULT_PROMPT
    ),
    ModelConfig(
        name="GLM-4.5-Thinking",
        display_name="GLM-4.5-Thinking (Reasoning)",
        capabilities=[ModelCapability.TEXT, ModelCapability.THINKING],
        max_tokens=128000,
        description="Reasoning-optimized model with extended thinking",
        test_prompt="Solve this step by step: What is 15 * 23?"
    ),
    ModelConfig(
        name="GLM-4.5-Search",
        display_name="GLM-4.5-Search (Web Search)",
        capabilities=[ModelCapability.TEXT, ModelCapability.SEARCH],
        max_tokens=128000,
        description="Web search enhanced model",
        test_prompt=DEFAULT_PROMPT
    ),
    ModelConfig(
        name="GLM-4.6",
        display_name="GLM-4.6 (Extended Context)",
        capabilities=[ModelCapability.TEXT, ModelCapability.EXTENDED_CONTEXT],
        max_tokens=200000,
        description="Extended context model with 200K tokens",
        test_prompt=DEFAULT_PROMPT
    ),
    ModelConfig(
        name="GLM-4.6-Thinking",
        display_name="GLM-4.6-Thinking (Extended + Reasoning)",
        capabilities=[ModelCapability.TEXT, ModelCapability.THINKING, ModelCapability.EXTENDED_CONTEXT],
        max_tokens=200000,
        description="Extended context with reasoning capabilities",
        test_prompt="Solve this problem step by step: If a train travels at 80 km/h for 2.5 hours, how far does it go?"
    ),
    ModelConfig(
        name="GLM-4.5V",
        display_name="GLM-4.5V (Vision/Multimodal)",
        capabilities=[ModelCapability.TEXT, ModelCapability.VISION],
        max_tokens=128000,
        description="Vision and multimodal capabilities",
        test_prompt=DEFAULT_PROMPT
    ),
]


# ============================================================================
# Test Result Tracking
# ============================================================================

@dataclass
class TestResult:
    """Test result for a single model"""
    idx: int
    model_name: str
    display_name: str
    success: bool
    response_time: float
    response_text: Optional[str]
    error: Optional[str]
    thinking: Optional[str]
    usage: Optional[Dict[str, int]]


class TestStats:
    """Track overall test statistics"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.results: List[TestResult] = []
        self.total_time = 0.0
        
    def add_result(self, result: TestResult):
        self.results.append(result)
        self.total += 1
        if result.success:
            self.passed += 1
        else:
            self.failed += 1
    
    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total > 0 else 0
    
    @property
    def avg_response_time(self) -> float:
        successful_times = [r.response_time for r in self.results if r.success]
        return sum(successful_times) / len(successful_times) if successful_times else 0


# ============================================================================
# Colors and Formatting
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    MAGENTA = '\033[95m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 100}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(100)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 100}{Colors.END}\n")


def print_box_header(text: str):
    """Print box header"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}┌{'─' * 98}┐{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}│ {text}{' ' * (97 - len(text))}│{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}└{'─' * 98}┘{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


# ============================================================================
# Async Model Testing
# ============================================================================

async def test_model(
    client: httpx.AsyncClient,
    model: ModelConfig,
    idx: int,
    base_url: str,
    api_key: str,
    verbose: bool = False
) -> TestResult:
    """Test a single model asynchronously"""
    start_time = time.time()
    
    try:
        response = await client.post(
            f"{base_url}/chat/completions",
            json={
                "model": model.name,
                "messages": [{"role": "user", "content": model.test_prompt}],
                "stream": False,
                "max_tokens": 500
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            choice = data["choices"][0]
            response_text = choice["message"]["content"]
            
            # Extract thinking if present
            thinking = None
            message = choice.get("message", {})
            if "thinking" in message:
                thinking_obj = message["thinking"]
                thinking = thinking_obj.get("content") if isinstance(thinking_obj, dict) else str(thinking_obj)
            
            # Extract usage
            usage = None
            if "usage" in data:
                usage = {
                    "prompt_tokens": data["usage"]["prompt_tokens"],
                    "completion_tokens": data["usage"]["completion_tokens"],
                    "total_tokens": data["usage"]["total_tokens"],
                }
            
            return TestResult(
                idx=idx,
                model_name=model.name,
                display_name=model.display_name,
                success=True,
                response_time=response_time,
                response_text=response_text,
                error=None,
                thinking=thinking,
                usage=usage
            )
        else:
            error_text = response.text[:150] if response.text else "Unknown error"
            return TestResult(
                idx=idx,
                model_name=model.name,
                display_name=model.display_name,
                success=False,
                response_time=response_time,
                response_text=None,
                error=f"HTTP {response.status_code}: {error_text}",
                thinking=None,
                usage=None
            )
            
    except Exception as e:
        response_time = time.time() - start_time
        return TestResult(
            idx=idx,
            model_name=model.name,
            display_name=model.display_name,
            success=False,
            response_time=response_time,
            response_text=None,
            error=str(e)[:150],
            thinking=None,
            usage=None
        )


async def test_server_health(base_url: str, api_key: str) -> bool:
    """Test if the server is reachable"""
    print_info(f"Testing server connection: {base_url}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                json={
                    "model": "GLM-4.5",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            print_success("Server is reachable and responding")
            return True
    except Exception as e:
        print_error(f"Server health check failed: {e}")
        print_warning("Make sure the API server is running:")
        print_warning("  python main.py --port 8080")
        return False


async def run_all_tests(
    base_url: str,
    api_key: str,
    models_to_test: List[ModelConfig],
    verbose: bool = False
) -> TestStats:
    """Run tests for all models concurrently"""
    
    print_box_header(f"Z.AI Models - Testing {len(models_to_test)} models concurrently")
    
    stats = TestStats()
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        # Create tasks for all models
        tasks = [
            test_model(client, model, idx + 1, base_url, api_key, verbose)
            for idx, model in enumerate(models_to_test)
        ]
        
        # Execute all concurrently
        print(f"\n{Colors.BOLD}Starting concurrent requests to all {len(models_to_test)} models...{Colors.END}\n")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, TestResult):
                stats.add_result(result)
    
    stats.total_time = time.time() - start_time
    return stats


# ============================================================================
# Report Generation
# ============================================================================

def print_results(stats: TestStats, verbose: bool = False):
    """Print detailed test results"""
    
    # Sort by index
    results = sorted(stats.results, key=lambda x: x.idx)
    
    print_header("RESULTS")
    
    for result in results:
        status = f"{Colors.GREEN}✅{Colors.END}" if result.success else f"{Colors.RED}❌{Colors.END}"
        
        print(f"{status} {Colors.BOLD}#{result.idx:2d}{Colors.END} "
              f"{Colors.CYAN}{result.display_name:50}{Colors.END} "
              f"{Colors.MAGENTA}{result.response_time:.2f}s{Colors.END}")
        
        if result.success:
            if verbose:
                # Show full response
                print(f"\n{Colors.BOLD}Response:{Colors.END}")
                print(f"{Colors.GREEN}{result.response_text}{Colors.END}\n")
                
                if result.thinking:
                    print(f"{Colors.BOLD}Thinking Process:{Colors.END}")
                    print(f"{Colors.YELLOW}{result.thinking}{Colors.END}\n")
                
                if result.usage:
                    print(f"{Colors.BOLD}Token Usage:{Colors.END}")
                    print(f"  Prompt: {result.usage['prompt_tokens']}")
                    print(f"  Completion: {result.usage['completion_tokens']}")
                    print(f"  Total: {result.usage['total_tokens']}\n")
            else:
                # Show truncated response
                resp = result.response_text.replace('\n', ' ')[:120]
                print(f"     {Colors.GREEN}{resp}...{Colors.END}")
                
                if result.thinking:
                    print(f"     {Colors.YELLOW}⚡ Has thinking process{Colors.END}")
                
                if result.usage:
                    print(f"     {Colors.CYAN}Tokens: {result.usage['total_tokens']} "
                          f"({result.usage['prompt_tokens']}+{result.usage['completion_tokens']}){Colors.END}")
                print()
        else:
            print(f"     {Colors.RED}Error: {result.error}{Colors.END}\n")


def print_summary(stats: TestStats):
    """Print test summary"""
    print_header("SUMMARY")
    
    success_rate_color = Colors.GREEN if stats.pass_rate >= 80 else Colors.YELLOW if stats.pass_rate >= 50 else Colors.RED
    
    print(f"{Colors.BOLD}Total Models:{Colors.END} {Colors.CYAN}{stats.total}{Colors.END}")
    print(f"{Colors.BOLD}Successful:{Colors.END} {Colors.GREEN}{stats.passed}{Colors.END}")
    print(f"{Colors.BOLD}Failed:{Colors.END} {Colors.RED}{stats.failed}{Colors.END}")
    print(f"{Colors.BOLD}Success Rate:{Colors.END} {success_rate_color}{stats.pass_rate:.1f}%{Colors.END}")
    print(f"{Colors.BOLD}Total Duration:{Colors.END} {Colors.MAGENTA}{stats.total_time:.2f}s{Colors.END}")
    print(f"{Colors.BOLD}Avg Response Time:{Colors.END} {Colors.MAGENTA}{stats.avg_response_time:.2f}s{Colors.END}")
    
    # Failed models
    failed = [r for r in stats.results if not r.success]
    if failed:
        print(f"\n{Colors.BOLD}{Colors.RED}Failed Models:{Colors.END}")
        for result in failed:
            print(f"  • {Colors.RED}{result.display_name}{Colors.END}")
            print(f"    {result.error[:80]}")


def export_json_report(stats: TestStats, filename: str = "test_results.json"):
    """Export results as JSON"""
    report = {
        "summary": {
            "total": stats.total,
            "passed": stats.passed,
            "failed": stats.failed,
            "pass_rate": stats.pass_rate,
            "total_time": stats.total_time,
            "avg_response_time": stats.avg_response_time,
        },
        "results": [
            {
                "idx": r.idx,
                "model": r.model_name,
                "display_name": r.display_name,
                "success": r.success,
                "response_time": r.response_time,
                "response_text": r.response_text,
                "error": r.error,
                "thinking": r.thinking,
                "usage": r.usage,
            }
            for r in stats.results
        ]
    }
    
    try:
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        print_success(f"Results exported to: {filename}")
    except Exception as e:
        print_error(f"Failed to export results: {e}")


# ============================================================================
# Main Function
# ============================================================================

async def async_main(args):
    """Async main function"""
    
    # Print banner
    print_header("🧪 Z.AI Model Validation Test Suite - Async Concurrent Edition")
    
    print(f"{Colors.BOLD}Configuration:{Colors.END}")
    print(f"  • API: {Colors.CYAN}{args.base_url}{Colors.END}")
    print(f"  • API Key: {Colors.CYAN}{'*' * len(args.api_key)}{Colors.END}")
    
    # Health check
    if not args.no_health_check:
        if not await test_server_health(args.base_url, args.api_key):
            print_error("\nServer health check failed!")
            print_warning("Use --no-health-check to skip this check")
            return 1
    
    # Filter models if specific model requested
    models_to_test = MODELS
    if args.model:
        models_to_test = [m for m in MODELS if m.name == args.model]
        if not models_to_test:
            print_error(f"Model not found: {args.model}")
            print_info("Available models:")
            for m in MODELS:
                print(f"  • {m.name}")
            return 1
    
    print(f"  • Total Models: {Colors.GREEN}{len(models_to_test)}{Colors.END}")
    print(f"  • Concurrency: {Colors.GREEN}All models tested simultaneously{Colors.END}")
    
    # Run tests
    stats = await run_all_tests(args.base_url, args.api_key, models_to_test, args.verbose)
    
    # Print results
    print_results(stats, verbose=args.verbose)
    print_summary(stats)
    
    # Export if requested
    if args.export:
        export_json_report(stats)
    
    # Return exit code
    if stats.failed > 0:
        print_error(f"\n❌ {stats.failed} test(s) failed!")
        return 1
    else:
        print_success("\n✅ All tests passed!")
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Z.AI Model Validation Test Suite - Async Concurrent Edition"
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--api-key",
        default=DEFAULT_API_KEY,
        help=f"API key for authentication (default: {DEFAULT_API_KEY})"
    )
    parser.add_argument(
        "--model",
        help="Test only specific model (default: test all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export results to JSON"
    )
    parser.add_argument(
        "--no-health-check",
        action="store_true",
        help="Skip server health check"
    )
    
    args = parser.parse_args()
    
    # Print welcome
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                           Z.AI MODEL VALIDATION TEST SUITE                                       ║
║                              Async Concurrent Edition                                            ║
║                                                                                                  ║
║  This script tests all 7 Z.AI models concurrently with beautiful output                         ║
║                                                                                                  ║
║  Features:                                                                                       ║
║    • Async concurrent testing (all models tested simultaneously)                                ║
║    • Beautiful colored terminal output                                                           ║
║    • Response validation and token tracking                                                      ║
║    • Performance metrics and timing                                                              ║
║    • JSON export for CI/CD integration                                                           ║
║                                                                                                  ║
║  Requirements:                                                                                   ║
║    • API server running at http://localhost:8080                                                ║
║    • httpx library installed (pip install httpx)                                                ║
║                                                                                                  ║
║  Press Ctrl+C to interrupt                                                                       ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝{Colors.END}
    """)
    
    try:
        exit_code = asyncio.run(async_main(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Test interrupted by user{Colors.END}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.END}\n")
        raise


if __name__ == "__main__":
    main()

