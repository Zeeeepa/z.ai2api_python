#!/usr/bin/env python3
"""
ZAI Claude Code Setup Script
Automatically installs and configures Claude Code with Z.AI integration
Supports both Windows and WSL2 Ubuntu environments
"""

import os
import sys
import json
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple

# Color codes for terminal output
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

def print_step(msg: str):
    """Print a step message"""
    print(f"{Colors.OKCYAN}➜ {msg}{Colors.ENDC}")

def print_success(msg: str):
    """Print a success message"""
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_error(msg: str):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

def print_warning(msg: str):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def run_command(cmd: str, shell: bool = True, check: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd if shell else cmd.split(),
            shell=shell,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr
    except Exception as e:
        return 1, "", str(e)


class SystemDetector:
    """Detect system type and configurations"""
    
    def __init__(self):
        self.is_wsl = self.detect_wsl()
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux" and not self.is_wsl
        self.home_dir = Path.home()
        
    def detect_wsl(self) -> bool:
        """Detect if running in WSL"""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except:
            return False
    
    def get_config_dir(self) -> Path:
        """Get Claude Code Router config directory"""
        return self.home_dir / ".claude-code-router"
    
    def get_zai_js_path(self) -> Path:
        """Get path for zai.js plugin"""
        if self.is_windows:
            # Windows: C:\Users\L\Desktop\PROJECTS\CC\zai.js
            return Path(os.environ.get('USERPROFILE', str(self.home_dir))) / "Desktop" / "PROJECTS" / "CC" / "zai.js"
        elif self.is_wsl:
            # WSL2: /home/l/zaicc/zai.js
            return Path("/home") / os.environ.get('USER', 'l') / "zaicc" / "zai.js"
        else:
            # Linux: ~/.zaicc/zai.js
            return self.home_dir / ".zaicc" / "zai.js"

class NodeInstaller:
    """Handle Node.js and npm installation"""
    
    @staticmethod
    def check_node() -> bool:
        """Check if Node.js is installed"""
        returncode, stdout, _ = run_command("node --version", check=False)
        return returncode == 0
    
    @staticmethod
    def check_npm() -> bool:
        """Check if npm is installed"""
        returncode, stdout, _ = run_command("npm --version", check=False)
        return returncode == 0
    
    @staticmethod
    def install_node_linux():
        """Install Node.js on Linux/WSL"""
        print_step("Installing Node.js via NodeSource...")
        
        # Install using NodeSource (recommended method)
        commands = [
            "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -",
            "sudo apt-get install -y nodejs"
        ]
        
        for cmd in commands:
            returncode, stdout, stderr = run_command(cmd)
            if returncode != 0:
                print_error(f"Failed to run: {cmd}")
                print_error(stderr)
                return False
        
        return True
    
    @staticmethod
    def install_node_windows():
        """Install Node.js on Windows"""
        print_step("Please install Node.js manually from: https://nodejs.org/")
        print_warning("After installation, restart this script.")
        sys.exit(1)
    
    def ensure_node_installed(self, system: SystemDetector):
        """Ensure Node.js and npm are installed"""
        if self.check_node() and self.check_npm():
            print_success("Node.js and npm are already installed")
            returncode, version, _ = run_command("node --version", check=False)
            print(f"  Node.js version: {version.strip()}")
            returncode, version, _ = run_command("npm --version", check=False)
            print(f"  npm version: {version.strip()}")
            return True
        
        print_step("Node.js or npm not found, installing...")
        
        if system.is_windows:
            self.install_node_windows()
        else:
            return self.install_node_linux()


class ClaudeCodeInstaller:
    """Handle Claude Code and Router installation"""
    
    @staticmethod
    def check_claude_code() -> bool:
        """Check if Claude Code is installed"""
        returncode, stdout, _ = run_command("claude-code --version", check=False)
        return returncode == 0
    
    @staticmethod
    def check_claude_code_router() -> bool:
        """Check if Claude Code Router is installed"""
        returncode, stdout, _ = run_command("claude-code-router --version", check=False)
        return returncode == 0
    
    @staticmethod
    def install_claude_code():
        """Install Claude Code globally"""
        print_step("Installing Claude Code...")
        returncode, stdout, stderr = run_command("npm install -g @anthropic-ai/claude-code", check=False)
        
        if returncode != 0:
            print_error("Failed to install Claude Code")
            print_error(stderr)
            return False
        
        print_success("Claude Code installed successfully")
        return True
    
    @staticmethod
    def install_claude_code_router():
        """Install Claude Code Router globally"""
        print_step("Installing Claude Code Router...")
        returncode, stdout, stderr = run_command("npm install -g claude-code-router", check=False)
        
        if returncode != 0:
            print_error("Failed to install Claude Code Router")
            print_error(stderr)
            return False
        
        print_success("Claude Code Router installed successfully")
        return True
    
    def ensure_installed(self):
        """Ensure both Claude Code and Router are installed"""
        cc_installed = self.check_claude_code()
        ccr_installed = self.check_claude_code_router()
        
        if cc_installed:
            print_success("Claude Code is already installed")
        else:
            if not self.install_claude_code():
                return False
        
        if ccr_installed:
            print_success("Claude Code Router is already installed")
        else:
            if not self.install_claude_code_router():
                return False
        
        return True


class ZAIConfigurator:
    """Configure ZAI plugin and Claude Code Router"""
    
    ZAI_JS_CONTENT = '''const crypto = require("crypto");

function generateUUID() {
  const bytes = crypto.randomBytes(16);

  // 设置版本号 (4)
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  // 设置变体 (10)
  bytes[8] = (bytes[8] & 0x3f) | 0x80;

  // 转换为UUID格式: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  const hex = bytes.toString("hex");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(
    12,
    16
  )}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

class ZAITransformer {
  name = "zai";

  constructor(options) {
    this.options = options;
  }

  async getToken() {
    return fetch("https://chat.z.ai/api/v1/auths/", {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        Referer: "https://chat.z.ai/",
      },
    })
      .then((res) => res.json())
      .then((res) => res.token);
  }

  async transformRequestIn(request, provider) {
    const token = await this.getToken();
    const messages = [];
    for (const origMsg of request.messages || []) {
      const msg = { ...origMsg };
      if (msg.role === "system") {
        msg.role = "user";
        if (Array.isArray(msg.content)) {
          msg.content = [
            {
              type: "text",
              text: "This is a system command, you must enforce compliance.",
            },
            ...msg.content,
          ];
        } else if (typeof msg.content === "string") {
          msg.content = `This is a system command, you must enforce compliance.${msg.content}`;
        }
      } else if (msg.role === "user") {
        if (Array.isArray(msg.content)) {
          const newContent = [];
          for (const part of msg.content) {
            if (
              part?.type === "image_url" &&
              part?.image_url?.url &&
              typeof part.image_url.url === "string" &&
              !part.image_url.url.startsWith("http")
            ) {
              // 上传图片
              newContent.push(part);
            } else {
              newContent.push(part);
            }
          }
          msg.content = newContent;
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
          enable_thinking: !!request.reasoning,
        },
        variables: {
          "{{USER_NAME}}": "Guest",
          "{{USER_LOCATION}}": "Unknown",
          "{{CURRENT_DATETIME}}": new Date()
            .toISOString()
            .slice(0, 19)
            .replace("T", " "),
          "{{CURRENT_DATE}}": new Date().toISOString().slice(0, 10),
          "{{CURRENT_TIME}}": new Date().toISOString().slice(11, 19),
          "{{CURRENT_WEEKDAY}}": new Date().toLocaleDateString("en-US", {
            weekday: "long",
          }),
          "{{CURRENT_TIMEZONE}":
            Intl.DateTimeFormat().resolvedOptions().timeZone,
          "{{USER_LANGUAGE}}": "zh-CN",
        },
        model_item: {},
        tools:
          !request.reasoning && request.tools?.length
            ? request.tools
            : undefined,
        chat_id: generateUUID(),
        id: generateUUID(),
      },
      config: {
        url: new URL("https://chat.z.ai/api/chat/completions"),
        headers: {
          Accept: "*/*",
          "Accept-Language": "zh-CN",
          Authorization: `Bearer ${token || ""}`,
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
          "Content-Type": "application/json",
          Origin: "https://chat.z.ai",
          Pragma: "no-cache",
          Referer: "https://chat.z.ai/",
          "Sec-Fetch-Dest": "empty",
          "Sec-Fetch-Mode": "cors",
          "Sec-Fetch-Site": "same-origin",
          "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
          "X-FE-Version": "prod-fe-1.0.77",
        },
      },
    };
  }

  async transformResponseOut(response, context) {
    if (response.headers.get("Content-Type")?.includes("application/json")) {
      let jsonResponse = await response.json();
      const res = {
        id: jsonResponse.id,
        choices: [
          {
            finish_reason: jsonResponse.choices[0].finish_reason || null,
            index: 0,
            message: {
              content: jsonResponse.choices[0].message?.content || "",
              role: "assistant",
              tool_calls:
                jsonResponse.choices[0].message?.tool_calls || undefined,
            },
          },
        ],
        created: parseInt(new Date().getTime() / 1000 + "", 10),
        model: jsonResponse.model,
        object: "chat.completion",
        usage: jsonResponse.usage || {
          completion_tokens: 0,
          prompt_tokens: 0,
          total_tokens: 0,
        },
      };
      return new Response(JSON.stringify(res), {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
      });
    } else if (response.headers.get("Content-Type")?.includes("stream")) {
      if (!response.body) {
        return response;
      }
      const isStream = !!context.req.body.stream;
      const result = {
        id: "",
        choices: [
          {
            finish_reason: null,
            index: 0,
            message: {
              content: "",
              role: "assistant",
            },
          },
        ],
        created: parseInt(new Date().getTime() / 1000 + "", 10),
        model: "",
        object: "chat.completion",
        usage: {
          completion_tokens: 0,
          prompt_tokens: 0,
          total_tokens: 0,
        },
      };

      const decoder = new TextDecoder();
      const encoder = new TextEncoder();

      let currentId = "";
      let currentModel = context?.req?.body?.model || "";

      let hasToolCall = false;
      let toolArgs = "";
      let toolId = "";
      let toolCallUsage = null;
      let contentIndex = 0;
      let hasThinking = false;

      const processLine = (line, controller, reader) => {
        console.log(line);

        if (line.startsWith("data:")) {
          const chunkStr = line.slice(5).trim();
          if (chunkStr) {
            try {
              let chunk = JSON.parse(chunkStr);

              if (chunk.type === "chat:completion") {
                const data = chunk.data;

                // 保存ID和模型信息
                if (data.id) currentId = data.id;
                if (data.model) currentModel = data.model;

                if (data.phase === "tool_call") {
                  if (!hasToolCall) hasToolCall = true;
                  const blocks = data.edit_content.split("<glm_block >");
                  blocks.forEach((block, index) => {
                    if (!block.includes("</glm_block>")) return;
                    if (index === 0) {
                      toolArgs += data.edit_content.slice(
                        0,
                        data.edit_content.indexOf('"result') - 3
                      );
                    } else {
                      if (toolId) {
                        try {
                          toolArgs += '"';
                          const params = JSON.parse(toolArgs);
                          if (!isStream) {
                            result.choices[0].message.tool_calls.slice(
                              -1
                            )[0].function.arguments = params;
                          } else {
                            const deltaRes = {
                              choices: [
                                {
                                  delta: {
                                    role: "assistant",
                                    content: null,
                                    tool_calls: [
                                      {
                                        id: toolId,
                                        type: "function",
                                        function: {
                                          name: null,
                                          arguments: params,
                                        },
                                      },
                                    ],
                                  },
                                  finish_reason: null,
                                  index: contentIndex,
                                  logprobs: null,
                                },
                              ],
                              created: parseInt(
                                new Date().getTime() / 1000 + "",
                                10
                              ),
                              id: currentId || "",
                              model: currentModel || "",
                              object: "chat.completion.chunk",
                              system_fingerprint: "fp_zai_001",
                            };
                            controller.enqueue(
                              encoder.encode(
                                `data: ${JSON.stringify(deltaRes)}\\n\\n`
                              )
                            );
                          }
                        } catch (e) {
                          console.log("解析错误", toolArgs);
                        } finally {
                          toolArgs = "";
                          toolId = "";
                        }
                      }
                      contentIndex += 1;
                      const content = JSON.parse(block.slice(0, -12));
                      toolId = content.data.metadata.id;
                      toolArgs += JSON.stringify(
                        content.data.metadata.arguments
                      ).slice(0, -1);

                      if (!isStream) {
                        if (!result.choices[0].message.tool_calls) {
                          result.choices[0].message.tool_calls = [];
                        }
                        result.choices[0].message.tool_calls.push({
                          id: toolId,
                          type: "function",
                          function: {
                            name: content.data.metadata.name,
                            arguments: "",
                          },
                        });
                      } else {
                        const startRes = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                content: null,
                                tool_calls: [
                                  {
                                    id: toolId,
                                    type: "function",
                                    function: {
                                      name: content.data.metadata.name,
                                      arguments: "",
                                    },
                                  },
                                ],
                              },
                              finish_reason: null,
                              index: contentIndex,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(
                            `data: ${JSON.stringify(startRes)}\\n\\n`
                          )
                        );
                      }
                    }
                  });
                } else if (data.phase === "other") {
                  if (hasToolCall && data.usage) {
                    toolCallUsage = data.usage;
                  }
                  if (hasToolCall && data.edit_content?.startsWith("null,")) {
                    toolArgs += '"';
                    hasToolCall = false;
                    try {
                      const params = JSON.parse(toolArgs);
                      if (!isStream) {
                        result.choices[0].message.tool_calls.slice(
                          -1
                        )[0].function.arguments = params;
                        result.usage = toolCallUsage;
                        result.choices[0].finish_reason = "tool_calls";
                      } else {
                        const toolCallDelta = {
                          id: toolId,
                          type: "function",
                          function: {
                            name: null,
                            arguments: params,
                          },
                        };
                        const deltaRes = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                content: null,
                                tool_calls: [toolCallDelta],
                              },
                              finish_reason: null,
                              index: 0,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(
                            `data: ${JSON.stringify(deltaRes)}\\n\\n`
                          )
                        );

                        const finishRes = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                content: null,
                                tool_calls: [],
                              },
                              finish_reason: "tool_calls",
                              index: 0,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          usage: toolCallUsage || undefined,
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(
                            `data: ${JSON.stringify(finishRes)}\\n\\n`
                          )
                        );

                        controller.enqueue(encoder.encode(`data: [DONE]\\n\\n`));
                      }

                      reader.cancel();
                    } catch (e) {
                      console.log("错误", toolArgs);
                    }
                  }
                } else if (data.phase === "thinking") {
                  if (!hasThinking) hasThinking = true;
                  if (data.delta_content) {
                    const content = data.delta_content.startsWith("<details")
                      ? data.delta_content.split("</summary>\\n>").pop().trim()
                      : data.delta_content;
                    if (!isStream) {
                      if (!result.choices[0].message?.thinking?.content) {
                        result.choices[0].message.thinking = {
                          content,
                        };
                      } else {
                        result.choices[0].message.thinking.content += content;
                      }
                    } else {
                      const msg = {
                        choices: [
                          {
                            delta: {
                              role: "assistant",
                              thinking: {
                                content,
                              },
                            },
                            finish_reason: null,
                            index: 0,
                            logprobs: null,
                          },
                        ],
                        created: parseInt(new Date().getTime() / 1000 + "", 10),
                        id: currentId || "",
                        model: currentModel || "",
                        object: "chat.completion.chunk",
                        system_fingerprint: "fp_zai_001",
                      };
                      controller.enqueue(
                        encoder.encode(`data: ${JSON.stringify(msg)}\\n\\n`)
                      );
                    }
                  }
                } else if (data.phase === "answer" && !hasToolCall) {
                  console.log(result.choices[0].message);
                  if (
                    data.edit_content &&
                    data.edit_content.includes("</details>\\n")
                  ) {
                    if (hasThinking) {
                      const signature = Date.now().toString();
                      if (!isStream) {
                        result.choices[0].message.thinking.signature =
                          signature;
                      } else {
                        const msg = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                thinking: {
                                  content: "",
                                  signature,
                                },
                              },
                              finish_reason: null,
                              index: 0,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(`data: ${JSON.stringify(msg)}\\n\\n`)
                        );
                        contentIndex++;
                      }
                    }
                    const content = data.edit_content
                      .split("</details>\\n")
                      .pop();
                    if (content) {
                      if (!isStream) {
                        result.choices[0].message.content += content;
                      } else {
                        const msg = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                content,
                              },
                              finish_reason: null,
                              index: 0,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(`data: ${JSON.stringify(msg)}\\n\\n`)
                        );
                      }
                    }
                  }
                  if (data.delta_content) {
                    if (!isStream) {
                      result.choices[0].message.content += data.delta_content;
                    } else {
                      const msg = {
                        choices: [
                          {
                            delta: {
                              role: "assistant",
                              content: data.delta_content,
                            },
                            finish_reason: null,
                            index: 0,
                            logprobs: null,
                          },
                        ],
                        created: parseInt(new Date().getTime() / 1000 + "", 10),
                        id: currentId || "",
                        model: currentModel || "",
                        object: "chat.completion.chunk",
                        system_fingerprint: "fp_zai_001",
                      };
                      controller.enqueue(
                        encoder.encode(`data: ${JSON.stringify(msg)}\\n\\n`)
                      );
                    }
                  }
                  if (data.usage && !hasToolCall) {
                    if (!isStream) {
                      result.choices[0].finish_reason = "stop";
                      result.choices[0].usage = data.usage;
                    } else {
                      const msg = {
                        choices: [
                          {
                            delta: {
                              role: "assistant",
                              content: "",
                            },
                            finish_reason: "stop",
                            index: 0,
                            logprobs: null,
                          },
                        ],
                        usage: data.usage,
                        created: parseInt(new Date().getTime() / 1000 + "", 10),
                        id: currentId || "",
                        model: currentModel || "",
                        object: "chat.completion.chunk",
                        system_fingerprint: "fp_zai_001",
                      };
                      controller.enqueue(
                        encoder.encode(`data: ${JSON.stringify(msg)}\\n\\n`)
                      );
                    }
                  }
                }
              }
            } catch (error) {
              console.error(error);
            }
          }
        }
      };

      if (!isStream) {
        const reader = response.body.getReader();
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            processLine(line, null, reader);
          }
        }

        return new Response(JSON.stringify(result), {
          status: response.status,
          statusText: response.statusText,
          headers: {
            "Content-Type": "application/json",
          },
        });
      }

      const stream = new ReadableStream({
        start: async (controller) => {
          const reader = response.body.getReader();
          let buffer = "";
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) {
                // 发送[DONE]消息并清理状态
                controller.enqueue(encoder.encode(`data: [DONE]\\n\\n`));
                break;
              }

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\\n");

              buffer = lines.pop() || "";

              for (const line of lines) {
                processLine(line, controller, reader);
              }
            }
          } catch (error) {
            controller.error(error);
          } finally {
            controller.close();
          }
        },
      });

      return new Response(stream, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    }
    return response;
  }
}

module.exports = ZAITransformer;
'''

    def __init__(self, system: SystemDetector):
        self.system = system
        self.zai_js_path = system.get_zai_js_path()
        self.config_dir = system.get_config_dir()
        self.plugins_dir = self.config_dir / "plugins"
    
    def create_zai_js(self):
        """Create zai.js plugin file"""
        print_step(f"Creating zai.js plugin at: {self.zai_js_path}")
        
        # Create directory if it doesn't exist
        self.zai_js_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write zai.js content
        with open(self.zai_js_path, 'w', encoding='utf-8') as f:
            f.write(self.ZAI_JS_CONTENT)
        
        print_success(f"zai.js created successfully at: {self.zai_js_path}")
    
    def create_config(self):
        """Create Claude Code Router config.json"""
        print_step("Creating Claude Code Router config...")
        
        # Create config directory and plugins directory
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert path to string based on platform
        zai_js_path_str = str(self.zai_js_path)
        if self.system.is_windows:
            # Windows path format
            zai_js_path_str = zai_js_path_str.replace("/", "\\\\")
        
        config = {
            "LOG": False,
            "LOG_LEVEL": "debug",
            "CLAUDE_PATH": "",
            "HOST": "127.0.0.1",
            "PORT": 3456,
            "APIKEY": "",
            "API_TIMEOUT_MS": "600000",
            "PROXY_URL": "",
            "transformers": [
                {
                    "name": "zai",
                    "path": zai_js_path_str,
                    "options": {}
                }
            ],
            "Providers": [
                {
                    "name": "GLM",
                    "api_base_url": "http://127.0.0.1:8080/v1/chat/completions",
                    "api_key": "sk-your-api-key",
                    "models": ["GLM-4.6", "GLM-4.5V"],
                    "transformers": {
                        "use": ["zai"]
                    }
                }
            ],
            "StatusLine": {
                "enabled": False,
                "currentStyle": "default",
                "default": {
                    "modules": []
                },
                "powerline": {
                    "modules": []
                }
            },
            "Router": {
                "default": "GLM,GLM-4.6",
                "background": "GLM,GLM-4.6",
                "think": "GLM,GLM-4.6",
                "longContext": "GLM,GLM-4.6",
                "longContextThreshold": 80000,
                "webSearch": "GLM,GLM-4.6",
                "image": "GLM,GLM-4.5V"
            },
            "CUSTOM_ROUTER_PATH": ""
        }
        
        config_file = self.config_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print_success(f"Config created at: {config_file}")
    
    def configure(self):
        """Configure ZAI plugin and router"""
        self.create_zai_js()
        self.create_config()


class ZAIServerManager:
    """Manage Z.AI API Server"""
    
    def __init__(self):
        self.server_process = None
    
    def check_server_running(self) -> bool:
        """Check if server is already running"""
        returncode, stdout, _ = run_command("curl -s http://127.0.0.1:8080/ || echo 'not running'", check=False)
        return "not running" not in stdout
    
    def start_server(self):
        """Start Z.AI API server in background"""
        if self.check_server_running():
            print_success("Z.AI API server is already running")
            return True
        
        print_step("Starting Z.AI API server...")
        
        # Start server in background
        try:
            import subprocess
            self.server_process = subprocess.Popen(
                ["python3", "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent)
            )
            
            # Wait a bit for server to start
            import time
            time.sleep(3)
            
            if self.check_server_running():
                print_success("Z.AI API server started successfully on http://127.0.0.1:8080")
                return True
            else:
                print_error("Failed to start Z.AI API server")
                return False
                
        except Exception as e:
            print_error(f"Error starting server: {e}")
            return False

def main():
    """Main setup function"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 60)
    print("  ZAI Claude Code Setup Script")
    print("  Supports Windows & WSL2 Ubuntu")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    
    # Detect system
    print_step("Detecting system...")
    system = SystemDetector()
    
    if system.is_windows:
        print_success("Detected: Windows")
    elif system.is_wsl:
        print_success("Detected: WSL2 Ubuntu")
    else:
        print_success("Detected: Linux")
    
    print()
    
    # Install Node.js and npm
    print_step("Step 1: Checking Node.js and npm installation...")
    node_installer = NodeInstaller()
    if not node_installer.ensure_node_installed(system):
        print_error("Failed to install Node.js/npm")
        sys.exit(1)
    print()
    
    # Install Claude Code and Router
    print_step("Step 2: Installing Claude Code and Claude Code Router...")
    cc_installer = ClaudeCodeInstaller()
    if not cc_installer.ensure_installed():
        print_error("Failed to install Claude Code or Router")
        sys.exit(1)
    print()
    
    # Configure ZAI plugin and router
    print_step("Step 3: Configuring ZAI plugin and Claude Code Router...")
    configurator = ZAIConfigurator(system)
    configurator.configure()
    print()
    
    # Start Z.AI API server
    print_step("Step 4: Starting Z.AI API server...")
    server_manager = ZAIServerManager()
    if not server_manager.start_server():
        print_warning("Server start failed, but you can start it manually with: python3 main.py")
    print()
    
    # Final instructions
    print(f"{Colors.OKGREEN}{Colors.BOLD}")
    print("=" * 60)
    print("  Setup Complete! 🎉")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    print()
    print(f"{Colors.OKCYAN}Next steps:{Colors.ENDC}")
    print(f"  1. Ensure Z.AI API server is running on http://127.0.0.1:8080")
    print(f"  2. Start Claude Code Router: {Colors.BOLD}claude-code-router{Colors.ENDC}")
    print(f"  3. In a new terminal, start Claude Code: {Colors.BOLD}claude-code{Colors.ENDC}")
    print()
    print(f"{Colors.WARNING}Configuration files:{Colors.ENDC}")
    print(f"  • ZAI plugin: {configurator.zai_js_path}")
    print(f"  • Router config: {configurator.config_dir}/config.json")
    print()
    print(f"{Colors.OKCYAN}To customize settings:{Colors.ENDC}")
    print(f"  • Edit .env file in this directory")
    print(f"  • Edit {configurator.config_dir}/config.json for router settings")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Setup interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
