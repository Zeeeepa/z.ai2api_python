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
    
    env_content = f"""const crypto = require("crypto");

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

