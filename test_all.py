#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Z.AI Model Validation Test Suite

Comprehensive test suite that validates all Z.AI models through OpenAI-compatible API:
- GLM-4.5 (Standard)
- GLM-4.5-Air (Fast)
- GLM-4.5-Thinking (Reasoning)
- GLM-4.5-Search (Web Search)
- GLM-4.6 (Extended Context)
- GLM-4.6-Thinking (Extended + Reasoning)
- GLM-4.5V (Vision/Multimodal)

Usage:
    python test_all.py
    python test_all.py --base-url http://localhost:8080/v1
    python test_all.py --api-key sk-your-key
    python test_all.py --verbose
"""

import sys
import time
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from openai import OpenAI
except ImportError:
    print("❌ Error: openai library not installed!")
    print("Install with: pip install openai")
    sys.exit(1)


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:8080/v1"
DEFAULT_API_KEY = "sk-dummy"
REQUEST_TIMEOUT = 60  # seconds


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
        test_prompt="What is your model name and version? Respond in one sentence."
    ),
    ModelConfig(
        name="GLM-4.5-Air",
        display_name="GLM-4.5-Air (Fast)",
        capabilities=[ModelCapability.TEXT],
        max_tokens=128000,
        description="Fast and efficient model with 128K context",
        test_prompt="What is your model name? Answer briefly."
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
        test_prompt="What is your model name and main capability?"
    ),
    ModelConfig(
        name="GLM-4.6",
        display_name="GLM-4.6 (Extended Context)",
        capabilities=[ModelCapability.TEXT, ModelCapability.EXTENDED_CONTEXT],
        max_tokens=200000,
        description="Extended context model with 200K tokens",
        test_prompt="What is your model name and context length?"
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
        test_prompt="What is your model name and can you process images?"
    ),
]


# ============================================================================
# Test Result Tracking
# ============================================================================

@dataclass
class TestResult:
    """Test result for a single model"""
    model_name: str
    success: bool
    response_time: float
    response_text: Optional[str]
    error: Optional[str]
    thinking: Optional[str]
    usage: Optional[Dict[str, int]]
    raw_response: Optional[Any]


class TestStats:
    """Track overall test statistics"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.results: List[TestResult] = []
        
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


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}\n")


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
# Model Testing
# ============================================================================

def test_model(
    client: OpenAI,
    model: ModelConfig,
    verbose: bool = False
) -> TestResult:
    """Test a single model"""
    print(f"\n{Colors.BOLD}Testing: {model.display_name}{Colors.END}")
    print(f"Model: {model.name}")
    print(f"Capabilities: {', '.join([c.value for c in model.capabilities])}")
    print(f"Description: {model.description}")
    
    start_time = time.time()
    
    try:
        # Create the request
        print(f"Sending request: '{model.test_prompt[:50]}...'")
        
        response = client.chat.completions.create(
            model=model.name,
            messages=[
                {"role": "user", "content": model.test_prompt}
            ],
            max_tokens=500,
            timeout=REQUEST_TIMEOUT
        )
        
        response_time = time.time() - start_time
        
        # Extract response data
        choice = response.choices[0]
        response_text = choice.message.content
        thinking = getattr(choice.message, 'thinking', None)
        if thinking:
            thinking = getattr(thinking, 'content', str(thinking))
        
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        } if response.usage else None
        
        # Validate response
        if not response_text or len(response_text.strip()) == 0:
            raise ValueError("Empty response received")
        
        # Print results
        print_success(f"Response received in {response_time:.2f}s")
        
        if verbose:
            print(f"\n{Colors.BOLD}Response:{Colors.END}")
            print(f"{response_text}\n")
            
            if thinking:
                print(f"{Colors.BOLD}Thinking Process:{Colors.END}")
                print(f"{thinking}\n")
            
            if usage:
                print(f"{Colors.BOLD}Token Usage:{Colors.END}")
                print(f"  Prompt: {usage['prompt_tokens']}")
                print(f"  Completion: {usage['completion_tokens']}")
                print(f"  Total: {usage['total_tokens']}")
        else:
            # Show truncated response
            truncated = response_text[:100] + "..." if len(response_text) > 100 else response_text
            print(f"Response: {truncated}")
        
        if usage:
            print(f"Tokens: {usage['total_tokens']} ({usage['prompt_tokens']}+{usage['completion_tokens']})")
        
        return TestResult(
            model_name=model.name,
            success=True,
            response_time=response_time,
            response_text=response_text,
            error=None,
            thinking=thinking,
            usage=usage,
            raw_response=response
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = str(e)
        
        print_error(f"Test failed after {response_time:.2f}s")
        print_error(f"Error: {error_msg}")
        
        return TestResult(
            model_name=model.name,
            success=False,
            response_time=response_time,
            response_text=None,
            error=error_msg,
            thinking=None,
            usage=None,
            raw_response=None
        )


def test_server_health(client: OpenAI, base_url: str) -> bool:
    """Test if the server is reachable"""
    print_info(f"Testing server connection: {base_url}")
    
    try:
        # Try a simple request with a common model
        response = client.chat.completions.create(
            model="GLM-4.5",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10,
            timeout=10
        )
        print_success("Server is reachable and responding")
        return True
    except Exception as e:
        print_error(f"Server health check failed: {e}")
        print_warning("Make sure the API server is running:")
        print_warning("  python main.py --port 8080")
        return False


# ============================================================================
# Report Generation
# ============================================================================

def print_summary(stats: TestStats):
    """Print test summary"""
    print_header("📊 Test Summary")
    
    print(f"Total Tests: {stats.total}")
    print_success(f"Passed: {stats.passed}")
    
    if stats.failed > 0:
        print_error(f"Failed: {stats.failed}")
    else:
        print(f"Failed: {stats.failed}")
    
    print(f"\n{Colors.BOLD}Pass Rate: {stats.pass_rate:.1f}%{Colors.END}")
    
    # Show average response time for successful tests
    successful_times = [r.response_time for r in stats.results if r.success]
    if successful_times:
        avg_time = sum(successful_times) / len(successful_times)
        print(f"Average Response Time: {avg_time:.2f}s")


def print_detailed_results(stats: TestStats):
    """Print detailed test results"""
    print_header("📋 Detailed Results")
    
    # Successful tests
    successful = [r for r in stats.results if r.success]
    if successful:
        print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Successful Tests ({len(successful)}):{Colors.END}")
        for result in successful:
            model = next((m for m in MODELS if m.name == result.model_name), None)
            display = model.display_name if model else result.model_name
            print(f"  • {display}")
            print(f"    Time: {result.response_time:.2f}s")
            if result.usage:
                print(f"    Tokens: {result.usage['total_tokens']}")
            if result.thinking:
                print(f"    ⚡ Has thinking process")
    
    # Failed tests
    failed = [r for r in stats.results if not r.success]
    if failed:
        print(f"\n{Colors.BOLD}{Colors.RED}❌ Failed Tests ({len(failed)}):{Colors.END}")
        for result in failed:
            model = next((m for m in MODELS if m.name == result.model_name), None)
            display = model.display_name if model else result.model_name
            print(f"  • {display}")
            print(f"    Error: {result.error}")


def export_json_report(stats: TestStats, filename: str = "test_results.json"):
    """Export results as JSON"""
    report = {
        "summary": {
            "total": stats.total,
            "passed": stats.passed,
            "failed": stats.failed,
            "pass_rate": stats.pass_rate,
        },
        "results": [
            {
                "model": r.model_name,
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

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Z.AI Model Validation Test Suite"
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
    
    # Print banner
    print_header("🧪 Z.AI Model Validation Test Suite")
    print(f"Base URL: {args.base_url}")
    print(f"API Key: {'*' * len(args.api_key)}")
    
    # Initialize OpenAI client
    client = OpenAI(
        base_url=args.base_url,
        api_key=args.api_key
    )
    
    # Health check
    if not args.no_health_check:
        if not test_server_health(client, args.base_url):
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
    
    # Run tests
    print_header(f"🚀 Running Tests ({len(models_to_test)} models)")
    
    stats = TestStats()
    
    for i, model in enumerate(models_to_test, 1):
        print(f"\n{Colors.BOLD}[{i}/{len(models_to_test)}]{Colors.END}")
        result = test_model(client, model, verbose=args.verbose)
        stats.add_result(result)
        
        # Add delay between tests
        if i < len(models_to_test):
            time.sleep(1)
    
    # Print results
    print_summary(stats)
    print_detailed_results(stats)
    
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


if __name__ == "__main__":
    sys.exit(main())

