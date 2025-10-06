#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Structure Validation Test Suite
Tests code structure without requiring actual Qwen credentials
"""

import sys
import asyncio
from typing import Dict, Any


class StructureValidator:
    """Validates code structure and API compatibility"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_total = 0
    
    def test_imports(self) -> bool:
        """Test 1: Verify all imports work"""
        print("\n" + "="*70)
        print("TEST 1: Import Validation")
        print("="*70)
        
        try:
            # Core imports
            from app.providers.qwen_provider import QwenProvider
            from app.providers.qwen_upload import QwenUploader, upload_file_to_qwen_oss
            from app.core.image_endpoints import (
                ImageGenerationRequest,
                ImageEditRequest,
                VideoGenerationRequest,
                DeepResearchRequest
            )
            from app.core import openai
            from main import app
            
            print("✅ All imports successful!")
            print("  - QwenProvider")
            print("  - QwenUploader")
            print("  - Image/Video endpoints")
            print("  - FastAPI app")
            return True
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            return False
    
    def test_provider_methods(self) -> bool:
        """Test 2: Verify provider has all required methods"""
        print("\n" + "="*70)
        print("TEST 2: Provider Method Validation")
        print("="*70)
        
        try:
            from app.providers.qwen_provider import QwenProvider
            
            required_methods = [
                'generate_image',
                'edit_image',
                'generate_video',
                'deep_research',
                'get_supported_models',
                'create_chat_session',
                'chat_completion'
            ]
            
            for method in required_methods:
                if not hasattr(QwenProvider, method):
                    print(f"❌ Missing method: {method}")
                    return False
                print(f"  ✓ {method}")
            
            print("✅ All required methods present!")
            return True
            
        except Exception as e:
            print(f"❌ Method validation failed: {e}")
            return False
    
    def test_uploader_structure(self) -> bool:
        """Test 3: Verify uploader structure"""
        print("\n" + "="*70)
        print("TEST 3: Uploader Structure Validation")
        print("="*70)
        
        try:
            from app.providers.qwen_upload import QwenUploader
            
            # Check class attributes
            attrs = [
                'STS_TOKEN_URL',
                'MAX_RETRIES',
                'TIMEOUT',
                'MAX_FILE_SIZE',
                'RETRY_DELAY',
                'SUPPORTED_TYPES'
            ]
            
            for attr in attrs:
                if not hasattr(QwenUploader, attr):
                    print(f"❌ Missing attribute: {attr}")
                    return False
                print(f"  ✓ {attr}")
            
            # Check methods
            methods = [
                'validate_file_size',
                'get_simple_file_type',
                'calculate_file_hash',
                'request_sts_token',
                'upload_to_oss',
                'upload_file'
            ]
            
            for method in methods:
                if not hasattr(QwenUploader, method):
                    print(f"❌ Missing method: {method}")
                    return False
                print(f"  ✓ {method}")
            
            print("✅ Uploader structure valid!")
            return True
            
        except Exception as e:
            print(f"❌ Uploader validation failed: {e}")
            return False
    
    def test_endpoints(self) -> bool:
        """Test 4: Verify API endpoints are registered"""
        print("\n" + "="*70)
        print("TEST 4: API Endpoint Registration")
        print("="*70)
        
        try:
            from main import app
            
            # Get all routes
            routes = [route.path for route in app.routes]
            
            required_endpoints = [
                '/v1/chat/completions',
                '/v1/models',
                '/v1/images/generations',
                '/v1/images/edits',
                '/v1/videos/generations',
                '/v1/research/deep'
            ]
            
            for endpoint in required_endpoints:
                if endpoint in routes:
                    print(f"  ✅ {endpoint}")
                else:
                    print(f"  ❌ Missing: {endpoint}")
                    return False
            
            print(f"\n✅ All {len(required_endpoints)} endpoints registered!")
            return True
            
        except Exception as e:
            print(f"❌ Endpoint validation failed: {e}")
            return False
    
    def test_model_variants(self) -> bool:
        """Test 5: Verify model variant generation"""
        print("\n" + "="*70)
        print("TEST 5: Model Variant Generation")
        print("="*70)
        
        try:
            from app.providers.qwen_provider import QwenProvider
            
            # Create provider without auth
            provider = QwenProvider(auth_config=None)
            models = provider.get_supported_models()
            
            print(f"  Generated {len(models)} model variants")
            
            # Check for expected variants
            expected_samples = [
                'qwen-max',
                'qwen-max-thinking',
                'qwen-max-search',
                'qwen-max-image',
                'qwen-max-image_edit',
                'qwen-max-video',
                'qwen-max-deep-research',
                'qwen-plus',
                'qwen-turbo',
                'qwen-long'
            ]
            
            for model in expected_samples:
                if model in models:
                    print(f"  ✓ {model}")
                else:
                    print(f"  ❌ Missing: {model}")
                    return False
            
            print(f"\n✅ Model variant generation working! ({len(models)} total)")
            return True
            
        except Exception as e:
            print(f"❌ Model variant test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_request_structure(self) -> bool:
        """Test 6: Verify request/response structures"""
        print("\n" + "="*70)
        print("TEST 6: Request/Response Structure Validation")
        print("="*70)
        
        try:
            from app.core.image_endpoints import (
                ImageGenerationRequest,
                ImageEditRequest,
                VideoGenerationRequest,
                DeepResearchRequest
            )
            
            # Test image generation request
            img_req = ImageGenerationRequest(
                prompt="test prompt",
                model="qwen-max-image",
                n=1,
                size="1024x1024"
            )
            print("  ✓ ImageGenerationRequest")
            
            # Test image edit request
            edit_req = ImageEditRequest(
                image="https://example.com/image.jpg",
                prompt="edit prompt"
            )
            print("  ✓ ImageEditRequest")
            
            # Test video generation request
            vid_req = VideoGenerationRequest(
                prompt="video prompt",
                duration=5
            )
            print("  ✓ VideoGenerationRequest")
            
            # Test deep research request
            research_req = DeepResearchRequest(
                query="research question",
                max_iterations=3
            )
            print("  ✓ DeepResearchRequest")
            
            print("\n✅ All request structures valid!")
            return True
            
        except Exception as e:
            print(f"❌ Request structure validation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_file_size_validation(self) -> bool:
        """Test 7: Verify file size validation"""
        print("\n" + "="*70)
        print("TEST 7: File Size Validation Logic")
        print("="*70)
        
        try:
            from app.providers.qwen_upload import QwenUploader
            
            # Test valid sizes
            assert QwenUploader.validate_file_size(1024) == True, "1KB should be valid"
            assert QwenUploader.validate_file_size(50 * 1024 * 1024) == True, "50MB should be valid"
            print("  ✓ Valid sizes accepted")
            
            # Test invalid sizes
            assert QwenUploader.validate_file_size(0) == False, "0 bytes should be invalid"
            assert QwenUploader.validate_file_size(-1) == False, "Negative should be invalid"
            assert QwenUploader.validate_file_size(200 * 1024 * 1024) == False, "200MB should be invalid"
            print("  ✓ Invalid sizes rejected")
            
            # Test file type detection
            assert QwenUploader.get_simple_file_type("image/jpeg") == "image"
            assert QwenUploader.get_simple_file_type("video/mp4") == "video"
            assert QwenUploader.get_simple_file_type("audio/mp3") == "audio"
            assert QwenUploader.get_simple_file_type("application/pdf") == "document"
            assert QwenUploader.get_simple_file_type("unknown/type") == "file"
            print("  ✓ File type detection working")
            
            print("\n✅ File validation logic correct!")
            return True
            
        except Exception as e:
            print(f"❌ File validation test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_aspect_ratio_calculation(self) -> bool:
        """Test 8: Verify aspect ratio calculation"""
        print("\n" + "="*70)
        print("TEST 8: Aspect Ratio Calculation")
        print("="*70)
        
        try:
            from app.providers.qwen_provider import QwenProvider
            
            # Create provider without auth
            provider = QwenProvider(auth_config=None)
            
            # Test common sizes
            test_cases = [
                ("1024x1024", "1:1"),
                ("1920x1080", "16:9"),
                ("1080x1920", "9:16"),
                ("1280x720", "16:9"),
                ("512x512", "1:1")
            ]
            
            for size, expected in test_cases:
                result = provider.calculate_aspect_ratio(size)
                if result == expected:
                    print(f"  ✓ {size} -> {result}")
                else:
                    print(f"  ❌ {size}: expected {expected}, got {result}")
                    return False
            
            print("\n✅ Aspect ratio calculation correct!")
            return True
            
        except Exception as e:
            print(f"❌ Aspect ratio test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all structure validation tests"""
        print("\n" + "="*70)
        print("🧪 Z.AI2API STRUCTURE VALIDATION TEST SUITE")
        print("="*70)
        print("Testing code structure without requiring credentials")
        print("="*70)
        
        tests = [
            ("Import Validation", self.test_imports),
            ("Provider Methods", self.test_provider_methods),
            ("Uploader Structure", self.test_uploader_structure),
            ("API Endpoints", self.test_endpoints),
            ("Model Variants", self.test_model_variants),
            ("Request Structures", self.test_request_structure),
            ("File Validation", self.test_file_size_validation),
            ("Aspect Ratio", self.test_aspect_ratio_calculation)
        ]
        
        results = []
        
        for name, test_func in tests:
            self.tests_total += 1
            try:
                result = test_func()
                if result:
                    self.tests_passed += 1
                else:
                    self.tests_failed += 1
                results.append((name, result))
            except Exception as e:
                print(f"\n❌ Test '{name}' crashed: {e}")
                import traceback
                traceback.print_exc()
                self.tests_failed += 1
                results.append((name, False))
        
        # Summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {name}")
        
        print(f"\n{'='*70}")
        print(f"Total: {self.tests_total} | Passed: {self.tests_passed} | Failed: {self.tests_failed}")
        
        if self.tests_failed == 0:
            print("🎉 ALL STRUCTURE TESTS PASSED!")
            print("="*70)
            return 0
        else:
            print(f"⚠️  {self.tests_failed} TEST(S) FAILED")
            print("="*70)
            return 1


def main():
    """Main entry point"""
    validator = StructureValidator()
    exit_code = validator.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
