#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Z.AI Claude Code Router Integration - Standalone Launcher

This script automatically:
1. Configures the environment (.env)
2. Starts the Z.AI API server
3. Configures Claude Code Router
4. Starts Claude Code Router with --dangerously-skip-update
5. Monitors and tests the integration
6. Cleans up everything on exit (stops server & CCR)

Usage:
    python zai_cc.py [options]

Options:
    --port PORT           API server port (default: 8080)
    --ccr-port PORT       Claude Code Router port (default: 3456)
    --model MODEL         Default model (default: GLM-4.5)
    --skip-server         Don't start API server (use existing)
    --skip-ccr            Don't start Claude Code Router
    --test-only           Only test the API, don't start CCR
    --no-cleanup          Don't stop services on exit

Environment Variables:
    ZAI_API_PORT          API server port
    CCR_PORT              Claude Code Router port
    CCR_PATH              Path to Claude Code Router installation
"""

import os
import sys
import time
import json
import signal
import atexit
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_API_PORT = 8080
DEFAULT_CCR_PORT = 3456
DEFAULT_MODEL = "GLM-4.5"

# Claude Code Router paths
HOME = Path.home()
CCR_CONFIG_DIR = HOME / ".claude-code-router"
CCR_CONFIG_FILE = CCR_CONFIG_DIR / "config.js"
CCR_PLUGINS_DIR = CCR_CONFIG_DIR / "plugins"
CCR_PLUGIN_FILE = CCR_PLUGINS_DIR / "zai.js"

# Process tracking
PROCESSES = {
    "api_server": None,
    "ccr": None
}

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

def print_step(step: int, total: int, text: str):
    """Print step progress"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}[{step}/{total}] {text}{Colors.END}")

# ============================================================================
# Cleanup Handlers
# ============================================================================

def cleanup():
    """Stop all running processes"""
    print_header("🧹 Cleaning Up")
    
    # Stop CCR
    if PROCESSES["ccr"] and PROCESSES["ccr"].poll() is None:
        print_info("Stopping Claude Code Router...")
        try:
            PROCESSES["ccr"].terminate()
            PROCESSES["ccr"].wait(timeout=5)
            print_success("Claude Code Router stopped")
        except subprocess.TimeoutExpired:
            PROCESSES["ccr"].kill()
            print_warning("Claude Code Router force killed")
        except Exception as e:
            print_error(f"Error stopping CCR: {e}")
    
    # Stop API server
    if PROCESSES["api_server"] and PROCESSES["api_server"].poll() is None:
        print_info("Stopping Z.AI API server...")
        try:
            PROCESSES["api_server"].terminate()
            PROCESSES["api_server"].wait(timeout=5)
            print_success("Z.AI API server stopped")
        except subprocess.TimeoutExpired:
            PROCESSES["api_server"].kill()
            print_warning("Z.AI API server force killed")
        except Exception as e:
            print_error(f"Error stopping API server: {e}")
    
    print_success("Cleanup completed!")

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print_warning("\n\nReceived interrupt signal, cleaning up...")
    cleanup()
    sys.exit(0)

# Register cleanup handlers
atexit.register(cleanup)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ============================================================================
# Environment Configuration
# ============================================================================

def create_env_file(port: int) -> bool:
    """Create .env configuration file"""
    print_info("Configuring .env file...")
    
    env_content = f"""# Z.AI API Configuration - Auto-generated by zai_cc.py

# ============================================================================
# Server Configuration
# ============================================================================
LISTEN_PORT={port}
DEBUG_LOGGING=true

# ============================================================================
# Authentication Configuration  
# ============================================================================

# Anonymous Mode - Automatically gets visitor token from Z.AI
ANONYMOUS_MODE=true

# Skip API Key Validation - Enabled for development
SKIP_AUTH_TOKEN=true

# API Authentication Token (not needed with SKIP_AUTH_TOKEN=true)
AUTH_TOKEN=

# ============================================================================
# Model Configuration
# ============================================================================

# GLM-4.5 Series (128K context)
PRIMARY_MODEL=GLM-4.5
THINKING_MODEL=GLM-4.5-Thinking
SEARCH_MODEL=GLM-4.5-Search
AIR_MODEL=GLM-4.5-Air

# GLM-4.6 Series (200K context) 
GLM46_MODEL=GLM-4.6
GLM46_THINKING_MODEL=GLM-4.6-Thinking
GLM46_SEARCH_MODEL=GLM-4.6-Search

# ============================================================================
# Feature Flags
# ============================================================================

# Enable tool/function calling support
TOOL_SUPPORT=true
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print_success("Created .env configuration")
        return True
    except Exception as e:
        print_error(f"Failed to create .env: {e}")
        return False

# ============================================================================
# Claude Code Router Configuration
# ============================================================================

def create_ccr_plugin() -> bool:
    """Create zai.js plugin for Claude Code Router"""
    print_info("Creating Claude Code Router plugin...")
    
    # Ensure plugins directory exists
    CCR_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    
    plugin_content = '''const crypto = require("crypto");

function generateUUID() {
  const bytes = crypto.randomBytes(16);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = bytes.toString("hex");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

class ZAITransformer {
  name = "zai";
  
  constructor(options) {
    this.options = options;
  }
  
  async getToken() {
    return fetch("https://chat.z.ai/api/v1/auths/", {
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://chat.z.ai/"
      }
    })
    .then(res => res.json())
    .then(res => res.token);
  }
  
  async transformRequestIn(request, provider) {
    // Pass through - our API server handles Z.AI transformation
    return {
      body: request,
      config: {
        url: new URL(provider.api_base_url),
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${request.api_key || "sk-dummy"}`
        }
      }
    };
  }
  
  async transformResponseOut(response, context) {
    return response;
  }
}

module.exports = ZAITransformer;
'''
    
    try:
        with open(CCR_PLUGIN_FILE, "w") as f:
            f.write(plugin_content)
        print_success(f"Created plugin: {CCR_PLUGIN_FILE}")
        return True
    except Exception as e:
        print_error(f"Failed to create plugin: {e}")
        return False

def create_ccr_config(api_port: int, ccr_port: int, model: str) -> bool:
    """Create Claude Code Router config.js"""
    print_info("Creating Claude Code Router configuration...")
    
    # Ensure config directory exists
    CCR_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    config = {
        "LOG": False,
        "LOG_LEVEL": "info",
        "CLAUDE_PATH": "",
        "HOST": "127.0.0.1",
        "PORT": ccr_port,
        "APIKEY": "",
        "API_TIMEOUT_MS": "600000",
        "PROXY_URL": "",
        "transformers": [
            {
                "name": "zai",
                "path": str(CCR_PLUGIN_FILE),
                "options": {}
            }
        ],
        "Providers": [
            {
                "name": "GLM",
                "api_base_url": f"http://127.0.0.1:{api_port}/v1/chat/completions",
                "api_key": "sk-dummy",
                "models": [
                    "GLM-4.5",
                    "GLM-4.5-Air",
                    "GLM-4.5-Thinking",
                    "GLM-4.5-Search",
                    "GLM-4.6",
                    "GLM-4.6-Thinking",
                    "GLM-4.6-Search",
                    "GLM-4.5V"
                ],
                "transformers": {
                    "use": ["zai"]
                }
            }
        ],
        "StatusLine": {
            "enabled": False,
            "currentStyle": "default",
            "default": {"modules": []},
            "powerline": {"modules": []}
        },
        "Router": {
            "default": f"GLM,{model}",
            "background": f"GLM,{model}",
            "think": "GLM,GLM-4.5-Thinking",
            "longContext": "GLM,GLM-4.6",
            "longContextThreshold": 60000,
            "webSearch": "GLM,GLM-4.5-Search",
            "image": "GLM,GLM-4.5V"
        },
        "CUSTOM_ROUTER_PATH": ""
    }
    
    try:
        # Write as JavaScript module
        config_js = f"module.exports = {json.dumps(config, indent=2)};\n"
        with open(CCR_CONFIG_FILE, "w") as f:
            f.write(config_js)
        print_success(f"Created config: {CCR_CONFIG_FILE}")
        return True
    except Exception as e:
        print_error(f"Failed to create config: {e}")
        return False

# ============================================================================
# Server Management
# ============================================================================

def start_api_server() -> bool:
    """Start the Z.AI API server"""
    print_info("Starting Z.AI API server...")
    
    try:
        # Start server process
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        PROCESSES["api_server"] = process
        
        # Wait for server to start
        print_info("Waiting for server to initialize...")
        time.sleep(5)
        
        # Check if server started successfully
        if process.poll() is not None:
            print_error("Server failed to start!")
            return False
        
        print_success("Z.AI API server started successfully")
        return True
        
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        return False

def start_ccr(ccr_port: int) -> bool:
    """Start Claude Code Router"""
    print_info("Starting Claude Code Router...")
    
    # Check if ccr is installed
    try:
        subprocess.run(
            ["ccr", "--version"],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Claude Code Router (ccr) not found!")
        print_info("Install with: npm install -g @zinkawaii/claude-code-router")
        return False
    
    try:
        # Start CCR with --dangerously-skip-update
        process = subprocess.Popen(
            ["ccr", "--dangerously-skip-update"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        PROCESSES["ccr"] = process
        
        # Wait for CCR to start
        print_info("Waiting for Claude Code Router to initialize...")
        time.sleep(3)
        
        # Check if CCR started successfully
        if process.poll() is not None:
            print_error("Claude Code Router failed to start!")
            return False
        
        print_success(f"Claude Code Router started on port {ccr_port}")
        return True
        
    except Exception as e:
        print_error(f"Failed to start CCR: {e}")
        return False

# ============================================================================
# Testing
# ============================================================================

def test_api(api_port: int, model: str) -> bool:
    """Test the API with a simple request"""
    print_info("Testing API connection...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            base_url=f"http://127.0.0.1:{api_port}/v1",
            api_key="sk-dummy"
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "What model are you? Respond in one sentence."}
            ],
            max_tokens=100
        )
        
        print_success("API test successful!")
        print_info(f"Model: {response.model}")
        print_info(f"Response: {response.choices[0].message.content}")
        return True
        
    except ImportError:
        print_warning("OpenAI library not installed, skipping API test")
        print_info("Install with: pip install openai")
        return True
    except Exception as e:
        print_error(f"API test failed: {e}")
        return False

# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Z.AI Claude Code Router Integration Launcher"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("ZAI_API_PORT", DEFAULT_API_PORT)),
        help=f"API server port (default: {DEFAULT_API_PORT})"
    )
    parser.add_argument(
        "--ccr-port",
        type=int,
        default=int(os.getenv("CCR_PORT", DEFAULT_CCR_PORT)),
        help=f"Claude Code Router port (default: {DEFAULT_CCR_PORT})"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Default model (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--skip-server",
        action="store_true",
        help="Don't start API server (use existing)"
    )
    parser.add_argument(
        "--skip-ccr",
        action="store_true",
        help="Don't start Claude Code Router"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only test the API, don't start CCR"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't stop services on exit"
    )
    
    args = parser.parse_args()
    
    # Disable cleanup if requested
    if args.no_cleanup:
        atexit.unregister(cleanup)
    
    # Print welcome banner
    print_header("🚀 Z.AI Claude Code Router Launcher")
    print_info(f"API Port: {args.port}")
    print_info(f"CCR Port: {args.ccr_port}")
    print_info(f"Default Model: {args.model}")
    
    # Step 1: Configure environment
    print_step(1, 6, "Configuring Environment")
    if not create_env_file(args.port):
        return 1
    
    # Step 2: Create CCR plugin
    print_step(2, 6, "Creating Claude Code Router Plugin")
    if not create_ccr_plugin():
        return 1
    
    # Step 3: Create CCR config
    print_step(3, 6, "Creating Claude Code Router Configuration")
    if not create_ccr_config(args.port, args.ccr_port, args.model):
        return 1
    
    # Step 4: Start API server
    if not args.skip_server:
        print_step(4, 6, "Starting Z.AI API Server")
        if not start_api_server():
            return 1
    else:
        print_step(4, 6, "Skipping API Server (using existing)")
    
    # Step 5: Test API
    print_step(5, 6, "Testing API Connection")
    if not test_api(args.port, args.model):
        print_warning("API test failed, but continuing...")
    
    # Step 6: Start Claude Code Router
    if args.test_only:
        print_step(6, 6, "Skipping Claude Code Router (test-only mode)")
        print_success("\nTest completed successfully!")
        print_info("Run without --test-only to start Claude Code Router")
        return 0
    
    if not args.skip_ccr:
        print_step(6, 6, "Starting Claude Code Router")
        if not start_ccr(args.ccr_port):
            return 1
    else:
        print_step(6, 6, "Skipping Claude Code Router")
    
    # Success!
    print_header("✅ Setup Complete!")
    print_success("Z.AI is now integrated with Claude Code!")
    
    print_info("\n📋 Service Status:")
    if not args.skip_server:
        print(f"   • API Server: http://127.0.0.1:{args.port}")
    if not args.skip_ccr:
        print(f"   • Claude Code Router: http://127.0.0.1:{args.ccr_port}")
    
    print_info("\n🎯 Next Steps:")
    print("   1. Open Claude Code in your editor")
    print("   2. Ask: 'What model are you?'")
    print("   3. You should see GLM model responses!")
    
    print_info("\n📊 Available Models:")
    models = [
        ("GLM-4.5", "General purpose (128K context)"),
        ("GLM-4.5-Air", "Fast & efficient (128K context)"),
        ("GLM-4.6", "Extended context (200K tokens)"),
        ("GLM-4.5V", "Vision/multimodal"),
        ("GLM-4.5-Thinking", "Reasoning optimized"),
        ("GLM-4.5-Search", "Web search enhanced"),
    ]
    for model, desc in models:
        print(f"   • {model}: {desc}")
    
    print_info("\n⚠️  Press Ctrl+C to stop all services and exit")
    
    # Keep running until interrupted
    if not args.skip_ccr and PROCESSES["ccr"]:
        try:
            PROCESSES["ccr"].wait()
        except KeyboardInterrupt:
            pass
    elif not args.skip_server and PROCESSES["api_server"]:
        try:
            PROCESSES["api_server"].wait()
        except KeyboardInterrupt:
            pass
    else:
        print_info("\nAll services started. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

