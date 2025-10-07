#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Qwen Server Test Script
========================

Tests all Qwen model families and features.

Usage:
    python test_qwen_server.py

Or with custom base URL:
    python test_qwen_server.py --base-url http://localhost:8081/v1
"""

import os
import sys
import time
import argparse
from openai import OpenAI
from typing import List, Dict, Any

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class QwenServerTester:
    """Test Qwen standalone server"""
    
    # All model families to test
    MODEL_FAMILIES = {
        "qwen-max": [
            "qwen-max",
            "qwen-max-latest",
            "qwen-max-0428",
            "qwen-max-thinking",
            "qwen-max-search",
            "qwen-max-deep-research",
            "qwen-max-video"
        ],
        "qwen-plus": [
            "qwen-plus",
            "qwen-plus-latest",
            "qwen-plus-thinking",
            "qwen-plus-search",
            "qwen-plus-deep-research",
            "qwen-plus-video"
        ],
        "qwen-turbo": [
            "qwen-turbo",
            "qwen-turbo-latest",
            "qwen-turbo-thinking",
            "qwen-turbo-search",
            "qwen-turbo-deep-research",
            "qwen-turbo-video"
        ],
        "qwen-long": [
            "qwen-long",
            "qwen-long-thinking",
            "qwen-long-search",
            "qwen-long-deep-research",
            "qwen-long-video"
        ],
        "special": [
            "qwen-deep-research",
            "qwen3-coder-plus",
            "qwen-coder-plus"
        ]
    }
    
    def __init__(self, base_url: str = "http://localhost:8081/v1"):
        """Initialize tester"""
        self.base_url = base_url
        self.client = OpenAI(
            api_key="sk-anything",
            base_url=base_url
        )
        self.results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
    
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{text:^60}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
    
    def print_test(self, test_name: str, status: str, message: str = ""):
        """Print test result"""
        if status == "PASS":
            symbol = f"{GREEN}✅{RESET}"
            status_text = f"{GREEN}PASS{RESET}"
        elif status == "FAIL":
            symbol = f"{RED}❌{RESET}"
            status_text = f"{RED}FAIL{RESET}"
        else:  # SKIP
            symbol = f"{YELLOW}⏭️{RESET}"
            status_text = f"{YELLOW}SKIP{RESET}"
        
        print(f"{symbol} {test_name:<40} [{status_text}]")
        if message:
            print(f"   {YELLOW}└─{RESET} {message}")
    
    def test_health(self) -> bool:
        """Test health endpoint"""
        self.print_header("Server Health Check")
        
        try:
            import requests
            response = requests.get(f"{self.base_url.replace('/v1', '')}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Health Check", "PASS", f"Status: {data.get('status')}")
                self.results["passed"] += 1
                return True
            else:
                self.print_test("Health Check", "FAIL", f"Status code: {response.status_code}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            self.print_test("Health Check", "FAIL", str(e))
            self.results["failed"] += 1
            return False
    
    def test_models_list(self) -> bool:
        """Test models list endpoint"""
        self.print_header("Models List")
        
        try:
            import requests
            response = requests.get(f"{self.base_url}/models", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                count = len(models)
                self.print_test("List Models", "PASS", f"Found {count} models")
                self.results["passed"] += 1
                return True
            else:
                self.print_test("List Models", "FAIL", f"Status code: {response.status_code}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            self.print_test("List Models", "FAIL", str(e))
            self.results["failed"] += 1
            return False
    
    def test_text_completion(self, model: str, mode: str = "normal") -> bool:
        """Test text completion for a model"""
        try:
            prompt = "What model are you?"
            if mode == "thinking":
                prompt = "Solve: What is 25 * 17? Think step by step."
            elif mode == "search":
                prompt = "What's the latest news about AI?"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                timeout=30
            )
            
            content = response.choices[0].message.content
            
            if content and len(content) > 0:
                preview = content[:50] + "..." if len(content) > 50 else content
                self.print_test(f"Text: {model}", "PASS", preview)
                self.results["passed"] += 1
                self.results["details"].append({
                    "model": model,
                    "mode": mode,
                    "status": "PASS",
                    "response": content
                })
                return True
            else:
                self.print_test(f"Text: {model}", "FAIL", "Empty response")
                self.results["failed"] += 1
                return False
        
        except Exception as e:
            self.print_test(f"Text: {model}", "FAIL", str(e))
            self.results["failed"] += 1
            return False
    
    def test_streaming(self, model: str) -> bool:
        """Test streaming completion"""
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Count to 5"}],
                stream=True,
                max_tokens=50,
                timeout=30
            )
            
            chunks = []
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunks.append(chunk.choices[0].delta.content)
            
            full_response = "".join(chunks)
            
            if len(chunks) > 0:
                self.print_test(f"Stream: {model}", "PASS", f"Received {len(chunks)} chunks")
                self.results["passed"] += 1
                return True
            else:
                self.print_test(f"Stream: {model}", "FAIL", "No chunks received")
                self.results["failed"] += 1
                return False
        
        except Exception as e:
            self.print_test(f"Stream: {model}", "FAIL", str(e))
            self.results["failed"] += 1
            return False
    
    def run_quick_test(self):
        """Run quick test with basic models"""
        self.print_header("Qwen Server Quick Test")
        
        # Health check
        if not self.test_health():
            print(f"\n{RED}Server is not healthy. Aborting tests.{RESET}")
            return
        
        # List models
        self.test_models_list()
        
        # Test basic models
        basic_models = [
            "qwen-turbo-latest",
            "qwen-max-latest",
            "qwen-plus-latest"
        ]
        
        self.print_header("Basic Text Completion")
        for model in basic_models:
            self.test_text_completion(model)
            time.sleep(1)  # Rate limiting
        
        # Test streaming
        self.print_header("Streaming Test")
        self.test_streaming("qwen-turbo-latest")
        
        # Print summary
        self.print_summary()
    
    def run_comprehensive_test(self):
        """Run comprehensive test of all models"""
        self.print_header("Qwen Server Comprehensive Test")
        
        # Health check
        if not self.test_health():
            print(f"\n{RED}Server is not healthy. Aborting tests.{RESET}")
            return
        
        # List models
        self.test_models_list()
        
        # Test all model families
        for family_name, models in self.MODEL_FAMILIES.items():
            self.print_header(f"Testing {family_name.upper()} Family")
            
            for model in models:
                # Determine mode
                mode = "normal"
                if "thinking" in model:
                    mode = "thinking"
                elif "search" in model:
                    mode = "search"
                elif "video" in model or "image" in model:
                    # Skip generative models in text test
                    self.print_test(f"Text: {model}", "SKIP", "Generative model")
                    self.results["skipped"] += 1
                    continue
                
                self.test_text_completion(model, mode)
                time.sleep(2)  # Rate limiting
        
        # Test streaming with representative models
        self.print_header("Streaming Tests")
        streaming_models = [
            "qwen-turbo-latest",
            "qwen-max-latest"
        ]
        
        for model in streaming_models:
            self.test_streaming(model)
            time.sleep(1)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        total = self.results["passed"] + self.results["failed"] + self.results["skipped"]
        pass_rate = (self.results["passed"] / total * 100) if total > 0 else 0
        
        print(f"  Total Tests:  {total}")
        print(f"  {GREEN}Passed:{RESET}       {self.results['passed']}")
        print(f"  {RED}Failed:{RESET}       {self.results['failed']}")
        print(f"  {YELLOW}Skipped:{RESET}      {self.results['skipped']}")
        print(f"  Pass Rate:    {pass_rate:.1f}%")
        print()
        
        if self.results["failed"] == 0:
            print(f"{GREEN}🎉 All tests passed!{RESET}")
        else:
            print(f"{RED}❌ Some tests failed. Check details above.{RESET}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Qwen standalone server")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8081/v1",
        help="Base URL of the Qwen server"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test (default: comprehensive)"
    )
    
    args = parser.parse_args()
    
    tester = QwenServerTester(base_url=args.base_url)
    
    if args.quick:
        tester.run_quick_test()
    else:
        tester.run_comprehensive_test()


if __name__ == "__main__":
    main()

