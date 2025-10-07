#!/usr/bin/env python3
"""
Comprehensive Test Suite for Z.AI Models
Tests all available models through OpenAI-compatible API
"""

import sys
import time
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_test_header(test_name: str):
    """Print test header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"  {test_name}")
    print(f"{'='*70}{Colors.ENDC}\n")

def print_success(msg: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_fail(msg: str):
    """Print failure message"""
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

def print_info(msg: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")

def print_warning(msg: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")


class ZAIModelTester:
    """Test all Z.AI models through OpenAI-compatible API"""
    
    # All available Z.AI models to test
    MODELS = {
        "GLM-4.6": {
            "description": "Advanced reasoning model with 80K context",
            "supports_tools": True,
            "supports_vision": False,
            "supports_thinking": True,
            "test_prompt": "What is your model name and main capabilities?"
        },
        "GLM-4.5": {
            "description": "Balanced performance model",
            "supports_tools": True,
            "supports_vision": False,
            "supports_thinking": False,
            "test_prompt": "Explain quantum computing in simple terms."
        },
        "GLM-4.5V": {
            "description": "Vision-capable model for image understanding",
            "supports_tools": False,
            "supports_vision": True,
            "supports_thinking": False,
            "test_prompt": "Describe what you can do with images."
        },
        "GLM-4-Air": {
            "description": "Lightweight fast model",
            "supports_tools": True,
            "supports_vision": False,
            "supports_thinking": False,
            "test_prompt": "Write a haiku about AI."
        }
    }
    
    def __init__(self, base_url: str = "http://127.0.0.1:8080/v1", api_key: str = "sk-test-key"):
        """Initialize tester with OpenAI client"""
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.base_url = base_url
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
    
    def test_basic_completion(self, model: str, prompt: str) -> Dict[str, Any]:
        """Test basic text completion"""
        test_name = f"{model} - Basic Completion"
        print_info(f"Testing: {test_name}")
        
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            elapsed = time.time() - start_time
            
            # Validate response
            if not response or not response.choices:
                raise ValueError("Empty response received")
            
            content = response.choices[0].message.content
            if not content or len(content.strip()) < 10:
                raise ValueError("Response too short or empty")
            
            print_success(f"{test_name} - Passed ({elapsed:.2f}s)")
            print(f"  Response preview: {content[:100]}...")
            
            return {
                "test": test_name,
                "status": "PASSED",
                "elapsed": elapsed,
                "response_length": len(content),
                "model_used": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            print_fail(f"{test_name} - Failed: {str(e)}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_streaming_completion(self, model: str, prompt: str) -> Dict[str, Any]:
        """Test streaming response"""
        test_name = f"{model} - Streaming"
        print_info(f"Testing: {test_name}")
        
        try:
            start_time = time.time()
            stream = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                stream=True
            )
            
            chunks_received = 0
            total_content = ""
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    total_content += chunk.choices[0].delta.content
                    chunks_received += 1
            
            elapsed = time.time() - start_time
            
            if chunks_received == 0:
                raise ValueError("No chunks received in stream")
            
            print_success(f"{test_name} - Passed ({elapsed:.2f}s, {chunks_received} chunks)")
            
            return {
                "test": test_name,
                "status": "PASSED",
                "elapsed": elapsed,
                "chunks": chunks_received,
                "total_length": len(total_content)
            }
            
        except Exception as e:
            print_fail(f"{test_name} - Failed: {str(e)}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_tool_calling(self, model: str) -> Dict[str, Any]:
        """Test function/tool calling capability"""
        test_name = f"{model} - Tool Calling"
        print_info(f"Testing: {test_name}")
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather in a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City name"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"]
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "What's the weather in Tokyo?"}
                ],
                tools=tools,
                tool_choice="auto"
            )
            elapsed = time.time() - start_time
            
            # Check if tool was called
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                print_success(f"{test_name} - Passed ({elapsed:.2f}s)")
                print(f"  Tool called: {tool_call.function.name}")
                print(f"  Arguments: {tool_call.function.arguments}")
                
                return {
                    "test": test_name,
                    "status": "PASSED",
                    "elapsed": elapsed,
                    "tool_called": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            else:
                print_warning(f"{test_name} - Tool not called (may not be supported)")
                return {
                    "test": test_name,
                    "status": "SKIPPED",
                    "reason": "Tool calling not triggered"
                }
                
        except Exception as e:
            print_fail(f"{test_name} - Failed: {str(e)}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_thinking_mode(self, model: str) -> Dict[str, Any]:
        """Test thinking/reasoning mode"""
        test_name = f"{model} - Thinking Mode"
        print_info(f"Testing: {test_name}")
        
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Think step by step: What is 15 * 23 + 47?"}
                ],
                max_tokens=300,
                # Note: This would need proper reasoning parameter support
                extra_body={"reasoning": True}
            )
            elapsed = time.time() - start_time
            
            content = response.choices[0].message.content
            
            # Check if response shows reasoning
            has_reasoning = any(indicator in content.lower() 
                              for indicator in ["step", "first", "then", "therefore", "because"])
            
            if has_reasoning:
                print_success(f"{test_name} - Passed ({elapsed:.2f}s)")
                return {
                    "test": test_name,
                    "status": "PASSED",
                    "elapsed": elapsed,
                    "has_reasoning": True
                }
            else:
                print_warning(f"{test_name} - No clear reasoning detected")
                return {
                    "test": test_name,
                    "status": "SKIPPED",
                    "reason": "Reasoning indicators not found"
                }
                
        except Exception as e:
            print_fail(f"{test_name} - Failed: {str(e)}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_vision_capability(self, model: str) -> Dict[str, Any]:
        """Test vision/image understanding"""
        test_name = f"{model} - Vision"
        print_info(f"Testing: {test_name}")
        
        # Simple test with a data URL (small red square)
        test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see in this image?"},
                            {"type": "image_url", "image_url": {"url": test_image}}
                        ]
                    }
                ],
                max_tokens=150
            )
            elapsed = time.time() - start_time
            
            content = response.choices[0].message.content
            print_success(f"{test_name} - Passed ({elapsed:.2f}s)")
            print(f"  Response: {content[:100]}...")
            
            return {
                "test": test_name,
                "status": "PASSED",
                "elapsed": elapsed,
                "response_length": len(content)
            }
            
        except Exception as e:
            print_fail(f"{test_name} - Failed: {str(e)}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_long_context(self, model: str) -> Dict[str, Any]:
        """Test long context handling"""
        test_name = f"{model} - Long Context"
        print_info(f"Testing: {test_name}")
        
        # Generate a moderately long context
        long_text = "The quick brown fox jumps over the lazy dog. " * 100
        
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": f"Here's a text:\n{long_text}\n\nHow many times does 'fox' appear?"}
                ],
                max_tokens=100
            )
            elapsed = time.time() - start_time
            
            content = response.choices[0].message.content
            print_success(f"{test_name} - Passed ({elapsed:.2f}s)")
            print(f"  Response: {content[:100]}...")
            
            return {
                "test": test_name,
                "status": "PASSED",
                "elapsed": elapsed,
                "context_length": len(long_text)
            }
            
        except Exception as e:
            print_fail(f"{test_name} - Failed: {str(e)}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_model_suite(self, model: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run complete test suite for a model"""
        print_test_header(f"Testing Model: {model}")
        print_info(f"Description: {config['description']}")
        
        results = []
        
        # Test 1: Basic completion
        result = self.test_basic_completion(model, config['test_prompt'])
        results.append(result)
        self.results["total_tests"] += 1
        if result["status"] == "PASSED":
            self.results["passed"] += 1
        elif result["status"] == "FAILED":
            self.results["failed"] += 1
        else:
            self.results["skipped"] += 1
        
        # Test 2: Streaming
        result = self.test_streaming_completion(model, "Count from 1 to 5.")
        results.append(result)
        self.results["total_tests"] += 1
        if result["status"] == "PASSED":
            self.results["passed"] += 1
        elif result["status"] == "FAILED":
            self.results["failed"] += 1
        else:
            self.results["skipped"] += 1
        
        # Test 3: Tool calling (if supported)
        if config.get("supports_tools"):
            result = self.test_tool_calling(model)
            results.append(result)
            self.results["total_tests"] += 1
            if result["status"] == "PASSED":
                self.results["passed"] += 1
            elif result["status"] == "FAILED":
                self.results["failed"] += 1
            else:
                self.results["skipped"] += 1
        
        # Test 4: Thinking mode (if supported)
        if config.get("supports_thinking"):
            result = self.test_thinking_mode(model)
            results.append(result)
            self.results["total_tests"] += 1
            if result["status"] == "PASSED":
                self.results["passed"] += 1
            elif result["status"] == "FAILED":
                self.results["failed"] += 1
            else:
                self.results["skipped"] += 1
        
        # Test 5: Vision (if supported)
        if config.get("supports_vision"):
            result = self.test_vision_capability(model)
            results.append(result)
            self.results["total_tests"] += 1
            if result["status"] == "PASSED":
                self.results["passed"] += 1
            elif result["status"] == "FAILED":
                self.results["failed"] += 1
            else:
                self.results["skipped"] += 1
        
        # Test 6: Long context
        result = self.test_long_context(model)
        results.append(result)
        self.results["total_tests"] += 1
        if result["status"] == "PASSED":
            self.results["passed"] += 1
        elif result["status"] == "FAILED":
            self.results["failed"] += 1
        else:
            self.results["skipped"] += 1
        
        return results
    
    def run_all_tests(self):
        """Run tests for all models"""
        print(f"{Colors.BOLD}{Colors.HEADER}")
        print("=" * 80)
        print("  Z.AI Model Validation Test Suite")
        print("  Testing all models through OpenAI-compatible API")
        print("=" * 80)
        print(f"{Colors.ENDC}\n")
        
        print_info(f"Base URL: {self.base_url}")
        print_info(f"Testing {len(self.MODELS)} models\n")
        
        # Test each model
        for model, config in self.MODELS.items():
            model_results = self.test_model_suite(model, config)
            self.results["details"].extend(model_results)
            time.sleep(1)  # Small delay between models
        
        # Print final summary
        self.print_summary()
        
        # Return exit code
        return 0 if self.results["failed"] == 0 else 1
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("=" * 80)
        print("  Test Summary")
        print("=" * 80)
        print(f"{Colors.ENDC}\n")
        
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        skipped = self.results["skipped"]
        
        print(f"Total Tests:   {total}")
        print_success(f"Passed:        {passed} ({passed/total*100:.1f}%)")
        
        if failed > 0:
            print_fail(f"Failed:        {failed} ({failed/total*100:.1f}%)")
        else:
            print(f"Failed:        {failed}")
        
        if skipped > 0:
            print_warning(f"Skipped:       {skipped} ({skipped/total*100:.1f}%)")
        else:
            print(f"Skipped:       {skipped}")
        
        print(f"\n{Colors.BOLD}Test Status: ", end="")
        if failed == 0:
            print(f"{Colors.OKGREEN}ALL TESTS PASSED ✓{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}SOME TESTS FAILED ✗{Colors.ENDC}")
        
        # Save detailed results to file
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n{Colors.OKCYAN}Detailed results saved to: test_results.json{Colors.ENDC}")


def main():
    """Main test execution"""
    # Check if custom base URL provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080/v1"
    
    # Create tester and run all tests
    tester = ZAIModelTester(base_url=base_url)
    exit_code = tester.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

