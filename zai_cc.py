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
                                `data: ${JSON.stringify(deltaRes)}\n\n`
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
                            `data: ${JSON.stringify(startRes)}\n\n`
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
                            `data: ${JSON.stringify(deltaRes)}\n\n`
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
                            `data: ${JSON.stringify(finishRes)}\n\n`
                          )
                        );

                        controller.enqueue(encoder.encode(`data: [DONE]\n\n`));
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
                      ? data.delta_content.split("</summary>\n>").pop().trim()
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
                        encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
                      );
                    }
                  }
                } else if (data.phase === "answer" && !hasToolCall) {
                  console.log(result.choices[0].message);
                  if (
                    data.edit_content &&
                    data.edit_content.includes("</details>\n")
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
                          encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
                        );
                        contentIndex++;
                      }
                    }
                    const content = data.edit_content
                      .split("</details>\n")
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
                          encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
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
                        encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
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
                        encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
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
          const lines = buffer.split("\n");
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
                controller.enqueue(encoder.encode(`data: [DONE]\n\n`));
                break;
              }

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");

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
                version = result.stdout.strip()
                print(f"✅ Node.js installed: {version}")
                return True
        except FileNotFoundError:
            pass
        print("❌ Node.js not found.")
        return False

    def install_nodejs_lts(self):
        """Install Node.js LTS using system package manager"""
        print("\n📦 Installing Node.js LTS...")

        system = platform.system().lower()

        try:
            if system == "linux":
                # Detect distribution
                try:
                    with open("/etc/os-release") as f:
                        os_info = f.read().lower()

                    if "ubuntu" in os_info or "debian" in os_info:
                        print("Detected: Ubuntu/Debian")
                        print("Installing Node.js LTS via NodeSource repository...")
                        subprocess.run(["curl", "-fsSL", "https://deb.nodesource.com/setup_lts.x", "-o", "/tmp/nodesource_setup.sh"], check=True)
                        subprocess.run(["sudo", "bash", "/tmp/nodesource_setup.sh"], check=True)
                        subprocess.run(["sudo", "apt-get", "install", "-y", "nodejs"], check=True)
                    elif "fedora" in os_info or "rhel" in os_info or "centos" in os_info:
                        print("Detected: Fedora/RHEL/CentOS")
                        subprocess.run(["sudo", "dnf", "install", "-y", "nodejs"], check=True)
                    else:
                        print("⚠️  Unknown Linux distribution. Please install Node.js manually.")
                        return False
                except Exception as e:
                    print(f"⚠️  Could not detect distribution: {e}")
                    return False

            elif system == "darwin":
                print("Detected: macOS")
                # Check if Homebrew is installed
                try:
                    subprocess.run(["brew", "--version"], capture_output=True, check=True)
                    print("Installing Node.js via Homebrew...")
                    subprocess.run(["brew", "install", "node"], check=True)
                except:
                    print("⚠️  Homebrew not found. Please install from https://brew.sh")
                    return False

            else:
                print(f"⚠️  Unsupported system: {system}")
                print("Please install Node.js LTS manually from: https://nodejs.org/")
                return False

            print("✅ Node.js LTS installed successfully!")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Node.js: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def install_npm_packages(self):
        """Install required npm packages globally"""
        print("\n📦 Installing npm packages...")

        packages = [
            ("claude-code-router", "Claude Code Router"),
            ("claude-code", "Claude Code")
        ]

        for package, name in packages:
            try:
                print(f"Installing {name}...")
                result = subprocess.run(
                    ["npm", "install", "-g", package],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    print(f"✅ {name} installed successfully")
                else:
                    print(f"⚠️  {name} installation had warnings (may still work)")
                    print(f"   Error: {result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                print(f"⚠️  {name} installation timed out")
            except Exception as e:
                print(f"❌ Failed to install {name}: {e}")

        return True

    def verify_installations(self):
        """Verify all required tools are installed"""
        print("\n🔍 Verifying installations...")

        checks = [
            ("node", "Node.js"),
            ("npm", "npm"),
            ("ccr", "Claude Code Router"),
            ("claude-code", "Claude Code")
        ]

        all_ok = True
        for cmd, name in checks:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                    print(f"✅ {name}: {version}")
                else:
                    print(f"⚠️  {name}: installed but version check failed")
            except FileNotFoundError:
                print(f"❌ {name}: not found")
                all_ok = False
            except Exception as e:
                print(f"⚠️  {name}: {e}")

        return all_ok

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

        # Step 1: Check and install Node.js if needed
        print("Step 1: Checking Node.js...")
        if not self.check_nodejs():
            print("\n📥 Node.js not found. Installing Node.js LTS...")
            user_input = input("Install Node.js LTS? (y/n): ").lower()
            if user_input == 'y':
                if not self.install_nodejs_lts():
                    print("\n❌ Failed to install Node.js. Please install manually:")
                    print("   https://nodejs.org/")
                    sys.exit(1)
                # Verify installation
                if not self.check_nodejs():
                    print("❌ Node.js installation verification failed")
                    sys.exit(1)
            else:
                print("❌ Node.js is required. Exiting...")
                sys.exit(1)

        # Step 2: Install npm packages
        print("\nStep 2: Installing npm packages...")
        self.install_npm_packages()

        # Step 3: Verify all installations
        print("\nStep 3: Verifying installations...")
        self.verify_installations()

        # Step 4: Create directories and files
        print("\nStep 4: Creating configuration files...")
        self.create_directories()
        self.create_plugin()

        # Get configuration from user or use defaults
        api_key = os.getenv("AUTH_TOKEN", "sk-your-api-key")
        self.create_config(api_key=api_key)

        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        print(f"\n📋 Configuration files:")
        print(f"   • Plugin: {self.plugin_file}")
        print(f"   • Config: {self.config_file}")

        print("\n📦 Installed packages:")
        print("   • Node.js LTS")
        print("   • npm (Node Package Manager)")
        print("   • claude-code-router (ccr command)")
        print("   • claude-code")

        print("\n🚀 Usage:")
        print("   1. Start the API server (optional):")
        print("      python main.py")
        print("\n   2. Use Claude Code Router:")
        print("      ccr \"fix code\"")
        print("      ccr \"analyze this file\"")
        print("      ccr \"what model are you?\"")

        print("\n💡 Models configured:")
        print("   • GLM-4.6 (default) - 200K context, best for coding")
        print("   • GLM-4.5V - Vision tasks, UI analysis")
        print("   • GLM-4.5-Air - Fast, lightweight tasks")

        print("\n" + "=" * 60)

def main():
    """Main entry point"""
    setup = ClaudeCodeSetup()
    setup.setup()

if __name__ == "__main__":
    main()
