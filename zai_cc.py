#!/usr/bin/env python3
"""
Z.AI Claude Code Router Deployment Script
Automatically sets up Claude Code with Z.AI integration
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, Optional

class ClaudeCodeSetup:
    def __init__(self):
        self.home = Path.home()
        self.ccr_dir = self.home / ".claude-code-router"
        self.plugins_dir = self.ccr_dir / "plugins"
        self.config_file = self.ccr_dir / "config.js"
        self.plugin_file = self.plugins_dir / "zai.js"
        
    def create_directories(self):
        """Create necessary directories"""
        print("📁 Creating directories...")
        self.ccr_dir.mkdir(exist_ok=True)
        self.plugins_dir.mkdir(exist_ok=True)
        print(f"✅ Directories created at {self.ccr_dir}")
        
    def create_plugin(self):
        """Create the zai.js plugin file"""
        print("🔌 Creating Z.AI plugin...")
        
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
  constructor(options) { this.options = options; }
  
  async getToken() {
    return fetch("https://chat.z.ai/api/v1/auths/", {
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        Referer: "https://chat.z.ai/"
      }
    }).then(res => res.json()).then(res => res.token);
  }

  async transformRequestIn(request, provider) {
    const token = await this.getToken();
    const messages = [];
    for (const origMsg of request.messages || []) {
      const msg = { ...origMsg };
      if (msg.role === "system") {
        msg.role = "user";
        if (Array.isArray(msg.content)) {
          msg.content = [{ type: "text", text: "System command - enforce compliance." }, ...msg.content];
        } else if (typeof msg.content === "string") {
          msg.content = `System command - enforce compliance.${msg.content}`;
        }
      }
      messages.push(msg);
    }
    return {
      body: {
        stream: true,
        model: request.model,
        messages: messages,
        params: {},
        features: {
          image_generation: false,
          web_search: false,
          auto_web_search: false,
          preview_mode: false,
          flags: [],
          features: [],
          enable_thinking: !!request.reasoning
        },
        variables: {
          "{{CURRENT_DATETIME}}": new Date().toISOString().slice(0, 19).replace("T", " "),
          "{{CURRENT_DATE}}": new Date().toISOString().slice(0, 10),
          "{{USER_LANGUAGE}}": "en-US"
        },
        model_item: {},
        tools: !request.reasoning && request.tools?.length ? request.tools : undefined,
        chat_id: generateUUID(),
        id: generateUUID()
      },
      config: {
        url: new URL("https://chat.z.ai/api/chat/completions"),
        headers: {
          Accept: "*/*",
          "Accept-Language": "en-US",
          Authorization: `Bearer ${token || ""}`,
          "Content-Type": "application/json",
          Origin: "https://chat.z.ai",
          Referer: "https://chat.z.ai/",
          "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
          "X-FE-Version": "prod-fe-1.0.77"
        }
      }
    };
  }

  async transformResponseOut(response, context) {
    if (response.headers.get("Content-Type")?.includes("application/json")) {
      let jsonResponse = await response.json();
      return new Response(JSON.stringify({
        id: jsonResponse.id,
        choices: [{
          finish_reason: jsonResponse.choices[0].finish_reason || null,
          index: 0,
          message: {
            content: jsonResponse.choices[0].message?.content || "",
            role: "assistant",
            tool_calls: jsonResponse.choices[0].message?.tool_calls || undefined
          }
        }],
        created: parseInt(new Date().getTime() / 1000, 10),
        model: jsonResponse.model,
        object: "chat.completion",
        usage: jsonResponse.usage || { completion_tokens: 0, prompt_tokens: 0, total_tokens: 0 }
      }), {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers
      });
    }
    return response;
  }
}

module.exports = ZAITransformer;'''
        
        self.plugin_file.write_text(plugin_content)
        print(f"✅ Plugin created at {self.plugin_file}")
        
    def create_config(self, api_key: str = "sk-your-api-key", host: str = "127.0.0.1", port: int = 8080):
        """Create the config.js file"""
        print("⚙️  Creating configuration...")
        
        config = {
            "LOG": False,
            "LOG_LEVEL": "debug",
            "CLAUDE_PATH": "",
            "HOST": "127.0.0.1",
            "PORT": 3456,
            "APIKEY": "",
            "API_TIMEOUT_MS": "600000",
            "PROXY_URL": "",
            "transformers": [{
                "name": "zai",
                "path": str(self.plugin_file.absolute()),
                "options": {}
            }],
            "Providers": [{
                "name": "GLM",
                "api_base_url": f"http://{host}:{port}/v1/chat/completions",
                "api_key": api_key,
                "models": [
                    "GLM-4.6",        # Latest flagship model with 200K context
                    "GLM-4.5",        # Previous flagship model
                    "GLM-4.5-Air",    # Lightweight variant
                    "GLM-4.5V"        # Vision/multimodal model
                ],
                "transformers": {
                    "use": ["zai"]
                }
            }],
            "StatusLine": {
                "enabled": False,
                "currentStyle": "default",
                "default": {"modules": []},
                "powerline": {"modules": []}
            },
            "Router": {
                "default": "GLM,GLM-4.6",              # Use latest GLM-4.6 by default
                "background": "GLM,GLM-4.5-Air",       # Use Air for background tasks
                "think": "GLM,GLM-4.6",                # Use GLM-4.6 for reasoning
                "longContext": "GLM,GLM-4.6",          # GLM-4.6 has 200K context window
                "longContextThreshold": 100000,        # Increased for GLM-4.6's capability
                "webSearch": "GLM,GLM-4.6",            # Use GLM-4.6 for search tasks
                "image": "GLM,GLM-4.5V"                # Use GLM-4.5V for vision tasks
            },
            "CUSTOM_ROUTER_PATH": ""
        }
        
        config_js = f"module.exports = {json.dumps(config, indent=2)};"
        self.config_file.write_text(config_js)
        print(f"✅ Configuration created at {self.config_file}")
        
    def check_nodejs(self):
        """Check if Node.js is installed"""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        print("❌ Node.js not found. Please install Node.js first.")
        return False
        
    def check_claude_code(self):
        """Check if Claude Code is installed"""
        try:
            result = subprocess.run(["claude-code", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Claude Code installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        print("⚠️  Claude Code not found. Install with: npm install -g claude-code")
        return False
        
    def start_api_server(self):
        """Start the Z.AI API server"""
        print("\n🚀 Starting Z.AI API server...")
        try:
            # Check if server is already running
            result = subprocess.run(
                ["curl", "-s", "http://127.0.0.1:8080/"],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                print("✅ API server already running at http://127.0.0.1:8080")
                return True
        except:
            pass
            
        # Start the server
        print("Starting server with: python main.py")
        subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        import time
        print("⏳ Waiting for server to start...")
        for i in range(10):
            time.sleep(1)
            try:
                result = subprocess.run(
                    ["curl", "-s", "http://127.0.0.1:8080/"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    print("✅ API server started successfully!")
                    return True
            except:
                pass
        
        print("❌ Failed to start API server")
        return False
        
    def run_claude_code(self):
        """Run Claude Code and test"""
        print("\n🤖 Starting Claude Code...")
        print("=" * 60)
        print("Claude Code will now start. Ask it: 'What model are you?'")
        print("Expected response should mention GLM-4.5 or similar.")
        print("=" * 60)
        
        try:
            subprocess.run(["claude-code"], check=True)
        except KeyboardInterrupt:
            print("\n👋 Claude Code session ended")
        except Exception as e:
            print(f"❌ Error running Claude Code: {e}")
            
    def setup(self):
        """Run complete setup"""
        print("\n" + "=" * 60)
        print("🎯 Z.AI Claude Code Setup")
        print("=" * 60 + "\n")
        
        # Check prerequisites
        if not self.check_nodejs():
            sys.exit(1)
            
        # Create directories and files
        self.create_directories()
        self.create_plugin()
        
        # Get configuration from user or use defaults
        api_key = os.getenv("AUTH_TOKEN", "sk-your-api-key")
        self.create_config(api_key=api_key)
        
        print("\n✅ Setup complete!")
        print(f"\n📋 Configuration files:")
        print(f"   • Plugin: {self.plugin_file}")
        print(f"   • Config: {self.config_file}")
        
        # Check Claude Code
        if not self.check_claude_code():
            print("\n💡 Install Claude Code with: npm install -g claude-code")
            sys.exit(0)
            
        # Start API server
        if self.start_api_server():
            # Run Claude Code
            print("\n" + "=" * 60)
            input("Press Enter to start Claude Code...")
            self.run_claude_code()
        else:
            print("\n❌ Please start the API server manually: python main.py")

def main():
    """Main entry point"""
    setup = ClaudeCodeSetup()
    setup.setup()

if __name__ == "__main__":
    main()
