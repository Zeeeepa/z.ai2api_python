#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Z.AI 提供商适配器
"""

import json
import time
import uuid
import httpx
import hmac
import hashlib
import base64
from urllib.parse import urlencode
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator, Union

from app.providers.base import BaseProvider, ProviderConfig
from app.models.schemas import OpenAIRequest, Message
from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.token_pool import get_token_pool
from app.core.zai_transformer import generate_uuid, get_zai_dynamic_headers
from app.utils.sse_tool_handler import SSEToolHandler

logger = get_logger()


def _urlsafe_b64decode(data: str) -> bytes:
    """Decode a URL-safe base64 string with proper padding."""
    if isinstance(data, str):
        data_bytes = data.encode("utf-8")
    else:
        data_bytes = data
    padding = b"=" * (-len(data_bytes) % 4)
    return base64.urlsafe_b64decode(data_bytes + padding)


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    """Decode JWT payload without verification to extract metadata."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload_raw = _urlsafe_b64decode(parts[1])
        return json.loads(payload_raw.decode("utf-8", errors="ignore"))
    except Exception:
        return {}


def _extract_user_id_from_token(token: str) -> str:
    """Extract user_id from a JWT's payload. Fallback to 'guest'."""
    payload = _decode_jwt_payload(token) if token else {}
    for key in ("id", "user_id", "uid", "sub"):
        val = payload.get(key)
        if isinstance(val, (str, int)) and str(val):
            return str(val)
    return "guest"


def generate_signature(message_text: str, request_id: str, timestamp_ms: int, user_id: str, secret: str = "junjie") -> str:
    """Dual-layer HMAC-SHA256 signature.

    Layer1: derived key = HMAC(secret, window_index)
    Layer2: signature = HMAC(derived_key, canonical_string)
    canonical_string = "requestId,<id>,timestamp,<ts>,user_id,<uid>|<msg>|<ts>"
    """
    r = str(timestamp_ms)
    e = f"requestId,{request_id},timestamp,{timestamp_ms},user_id,{user_id}"
    t = message_text or ""
    # Add content_base64 processing for new signature algorithm
    content_base64 = base64.b64encode(t.encode('utf-8')).decode('ascii')
    i = f"{e}|{content_base64}|{r}"

    window_index = timestamp_ms // (5 * 60 * 1000)
    root_key = (secret or "junjie").encode("utf-8")
    derived_hex = hmac.new(root_key, str(window_index).encode("utf-8"), hashlib.sha256).hexdigest()
    signature = hmac.new(derived_hex.encode("utf-8"), i.encode("utf-8"), hashlib.sha256).hexdigest()
    return signature


class ZAIProvider(BaseProvider):
    """Z.AI 提供商"""
    
    def __init__(self):
        config = ProviderConfig(
            name="zai",
            api_endpoint=settings.API_ENDPOINT,
            timeout=30,
            headers=get_zai_dynamic_headers()
        )
        super().__init__(config)
        
        # Z.AI 特定配置
        self.base_url = "https://chat.z.ai"
        self.auth_url = f"{self.base_url}/api/v1/auths/"
        
        # 模型映射
        self.model_mapping = {
            settings.PRIMARY_MODEL: "0727-360B-API",  # GLM-4.5
            settings.THINKING_MODEL: "0727-360B-API",  # GLM-4.5-Thinking
            settings.SEARCH_MODEL: "0727-360B-API",  # GLM-4.5-Search
            settings.AIR_MODEL: "0727-106B-API",  # GLM-4.5-Air
            settings.GLM46_MODEL: "GLM-4-6-API-V1",  # GLM-4.6
            settings.GLM46_THINKING_MODEL: "GLM-4-6-API-V1",  # GLM-4.6-Thinking
            settings.GLM46_SEARCH_MODEL: "GLM-4-6-API-V1",  # GLM-4.6-Search
        }
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            settings.PRIMARY_MODEL,
            settings.THINKING_MODEL,
            settings.SEARCH_MODEL,
            settings.AIR_MODEL,
            settings.GLM46_MODEL,
            settings.GLM46_THINKING_MODEL,
            settings.GLM46_SEARCH_MODEL,
        ]
    
    async def get_token(self) -> str:
        """获取认证令牌"""
        # 如果启用匿名模式，只尝试获取访客令牌
        if settings.ANONYMOUS_MODE:
            try:
                headers = get_zai_dynamic_headers()
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.auth_url, headers=headers, timeout=10.0)
                    if response.status_code == 200:
                        data = response.json()
                        token = data.get("token", "")
                        if token:
                            # 判断令牌类型（通过检查邮箱或user_id）
                            email = data.get("email", "")
                            is_guest = "@guest.com" in email or "Guest-" in email
                            token_type = "匿名用户" if is_guest else "认证用户"
                            self.logger.debug(f"获取令牌成功 ({token_type}): {token[:20]}...")
                            return token
            except Exception as e:
                self.logger.warning(f"异步获取访客令牌失败: {e}")

            # 匿名模式下，如果获取访客令牌失败，直接返回空
            self.logger.error("❌ 匿名模式下获取访客令牌失败")
            return ""

        # 非匿名模式：首先使用token池获取备份令牌
        token_pool = get_token_pool()
        if token_pool:
            token = token_pool.get_next_token()
            if token:
                self.logger.debug(f"从token池获取令牌: {token[:20]}...")
                return token

        # 如果token池为空或没有可用token，使用配置的AUTH_TOKEN
        if settings.AUTH_TOKEN and settings.AUTH_TOKEN != "sk-your-api-key":
            self.logger.debug(f"使用配置的AUTH_TOKEN")
            return settings.AUTH_TOKEN

        self.logger.error("❌ 无法获取有效的认证令牌")
        return ""
    
    def mark_token_failure(self, token: str, error: Exception = None):
        """标记token使用失败"""
        token_pool = get_token_pool()
        if token_pool:
            token_pool.mark_token_failure(token, error)
    
    async def transform_request(self, request: OpenAIRequest) -> Dict[str, Any]:
        """转换OpenAI请求为Z.AI格式"""
        self.logger.info(f"🔄 转换 OpenAI 请求到 Z.AI 格式: {request.model}")
        
        # 获取认证令牌
        token = await self.get_token()
        
        # 处理消息格式
        messages = []
        for msg in request.messages:
            if isinstance(msg.content, str):
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, list):
                # 处理多模态内容
                content_parts = []
                for part in msg.content:
                    if hasattr(part, 'type') and hasattr(part, 'text'):
                        content_parts.append({
                            "type": part.type,
                            "text": part.text
                        })
                messages.append({
                    "role": msg.role,
                    "content": content_parts
                })
        
        # 确定请求的模型特性
        # Extract last user message text for signing
        last_user_text = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                content = m.get("content")
                if isinstance(content, str):
                    last_user_text = content
                    break
                elif isinstance(content, list):
                    texts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
                    last_user_text = "\n".join([t for t in texts if t])
                    break
        requested_model = request.model
        is_thinking = "-thinking" in requested_model.casefold()
        is_search = "-search" in requested_model.casefold()
        is_air = "-air" in requested_model.casefold()
        
        # 获取上游模型ID
        upstream_model_id = self.model_mapping.get(requested_model, "0727-360B-API")
        
        # 构建MCP服务器列表
        mcp_servers = []
        if is_search and "-4.5" in requested_model:
            mcp_servers.append("deep-web-search")
            self.logger.info("🔍 检测到搜索模型，添加 deep-web-search MCP 服务器")
        
        # 构建上游请求体
        chat_id = generate_uuid()
        
        body = {
            "stream": True,  # 总是使用流式
            "model": upstream_model_id,
            "messages": messages,
            "params": {},
            "features": {
                "image_generation": False,
                "web_search": is_search,
                "auto_web_search": is_search,
                "preview_mode": False,
                "flags": [],
                "features": [
                    {
                        "type": "mcp",
                        "server": "vibe-coding",
                        "status": "hidden"
                    },
                    {
                        "type": "mcp",
                        "server": "ppt-maker",
                        "status": "hidden"
                    },
                    {
                        "type": "mcp",
                        "server": "image-search",
                        "status": "hidden"
                    },
                    {
                        "type": "mcp",
                        "server": "deep-research",
                        "status": "hidden"
                    },
                    {
                        "type": "tool_selector",
                        "server": "tool_selector",
                        "status": "hidden"
                    },
                    {
                        "type": "mcp",
                        "server": "advanced-search",
                        "status": "hidden"
                    }
                ],
                "enable_thinking": is_thinking,
            },
            "background_tasks": {
                "title_generation": False,
                "tags_generation": False,
            },
            "mcp_servers": mcp_servers,
            "variables": {
                "{{USER_NAME}}": "Guest",
                "{{USER_LOCATION}}": "Unknown",
                "{{CURRENT_DATETIME}}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "{{CURRENT_DATE}}": datetime.now().strftime("%Y-%m-%d"),
                "{{CURRENT_TIME}}": datetime.now().strftime("%H:%M:%S"),
                "{{CURRENT_WEEKDAY}}": datetime.now().strftime("%A"),
                "{{CURRENT_TIMEZONE}}": "Asia/Shanghai",
                "{{USER_LANGUAGE}}": "zh-CN",
            },
            "model_item": {
                "id": upstream_model_id,
                "name": requested_model,
                "owned_by": "z.ai"
            },
            "chat_id": chat_id,
            "id": generate_uuid(),
        }
        
        # 处理工具支持
        if settings.TOOL_SUPPORT and not is_thinking and request.tools:
            body["tools"] = request.tools
            self.logger.info(f"启用工具支持: {len(request.tools)} 个工具")
        else:
            body["tools"] = None
        
        # 处理其他参数
        if request.temperature is not None:
            body["params"]["temperature"] = request.temperature
        if request.max_tokens is not None:
            body["params"]["max_tokens"] = request.max_tokens
        
        # 构建请求头
        headers = get_zai_dynamic_headers(chat_id)
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Dual-layer HMAC signing metadata and header
        user_id = _extract_user_id_from_token(token)
        timestamp_ms = int(time.time() * 1000)
        request_id = generate_uuid()
        secret = os.getenv("ZAI_SIGNING_SECRET", "junjie") or "junjie"
        signature = generate_signature(
            message_text=last_user_text,
            request_id=request_id,
            timestamp_ms=timestamp_ms,
            user_id=user_id,
            secret=secret,
        )
        query_params = {
            "timestamp": timestamp_ms,
            "requestId": request_id,
            "user_id": user_id,
            "token": token or "",
            "current_url": f"https://chat.z.ai/c/{chat_id}",
            "pathname": f"/c/{chat_id}",
            "signature_timestamp": timestamp_ms,
        }
        signed_url = f"{self.config.api_endpoint}?{urlencode(query_params)}"
        headers["X-Signature"] = signature
        
        # 存储当前token用于错误处理
        self._current_token = token

        return {
            "url": signed_url,
            "headers": headers,
            "body": body,
            "token": token,
            "chat_id": chat_id,
            "model": requested_model
        }
    
    async def chat_completion(
        self,
        request: OpenAIRequest,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """聊天完成接口"""
        self.log_request(request)

        try:
            # 转换请求
            transformed = await self.transform_request(request)

            # 根据请求类型返回响应
            if request.stream:
                # 流式响应
                return self._create_stream_response(request, transformed)
            else:
                # 非流式响应
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        transformed["url"],
                        headers=transformed["headers"],
                        json=transformed["body"]
                    )

                    if not response.is_success:
                        error_msg = f"Z.AI API 错误: {response.status_code}"
                        self.log_response(False, error_msg)
                        return self.handle_error(Exception(error_msg))

                    return await self.transform_response(response, request, transformed)

        except Exception as e:
            self.log_response(False, str(e))
            return self.handle_error(e, "请求处理")

    
    async def _create_stream_response(
        self,
        request: OpenAIRequest,
        transformed: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:

        current_token = transformed.get("token", "")
        try:
            async with httpx.AsyncClient(
                timeout=60.0,
                http2=True,
            ) as client:
                self.logger.info(f"🎯 发送请求到 Z.AI: {transformed['url']}")
                async with client.stream(
                    "POST",
                    transformed["url"],
                    json=transformed["body"],
                    headers=transformed["headers"],
                ) as response:
                    if response.status_code != 200:
                        self.logger.error(f"❌ 上游返回错误: {response.status_code}")
                        error_text = await response.aread()
                        error_msg = error_text.decode('utf-8', errors='ignore')
                        if error_msg:
                            self.logger.error(f"❌ 错误详情: {error_msg}")
                        error_response = {
                            "error": {
                                "message": f"Upstream error: {response.status_code}",
                                "type": "upstream_error",
                                "code": response.status_code
                            }
                        }
                        yield f"data: {json.dumps(error_response)}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    if current_token and not settings.ANONYMOUS_MODE:
                        token_pool = get_token_pool()
                        if token_pool:
                            token_pool.mark_token_success(current_token)

                    chat_id = transformed["chat_id"]
                    model = transformed["model"]
                    async for chunk in self._handle_stream_response(response, chat_id, model, request, transformed):
                        yield chunk
                    return
        except Exception as e:
            self.logger.error(f"❌ 流处理错误: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            if current_token and not settings.ANONYMOUS_MODE:
                self.mark_token_failure(current_token, e)
            error_response = {
                "error": {
                    "message": str(e),
                    "type": "stream_error"
                }
            }
            yield f"data: {json.dumps(error_response)}\n\n"
            yield "data: [DONE]\n\n"
            return

    async def transform_response(
        self, 
        response: httpx.Response, 
        request: OpenAIRequest,
        transformed: Dict[str, Any]
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """转换Z.AI响应为OpenAI格式"""
        chat_id = transformed["chat_id"]
        model = transformed["model"]
        
        if request.stream:
            return self._handle_stream_response(response, chat_id, model, request, transformed)
        else:
            return await self._handle_non_stream_response(response, chat_id, model)
    
    async def _handle_stream_response(
        self,
        response: httpx.Response,
        chat_id: str,
        model: str,
        request: OpenAIRequest,
        transformed: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """处理Z.AI流式响应"""
        self.logger.info(f"✅ Z.AI 响应成功，开始处理 SSE 流")

        # 初始化工具处理器（如果需要）
        has_tools = transformed["body"].get("tools") is not None
        tool_handler = None
        # Early ack: send an assistant role chunk immediately so the client sees progress
        try:
            role_chunk = self.create_openai_chunk(
                chat_id,
                model,
                {"role": "assistant"}
            )
            yield await self.format_sse_chunk(role_chunk)
        except Exception:
            pass

        if has_tools:
            tool_handler = SSEToolHandler(model, stream=True)
            self.logger.info(f"🔧 初始化工具处理器: {len(transformed['body'].get('tools', []))} 个工具")

        # 处理状态
        has_thinking = False
        thinking_signature = None

        # 处理SSE流
        buffer = ""
        line_count = 0
        self.logger.debug("📡 开始接收 SSE 流数据...")

        try:
            async for line in response.aiter_lines():
                line_count += 1
                if not line:
                    continue

                # 累积到buffer处理完整的数据行
                buffer += line + "\n"

                # 检查是否有完整的data行
                while "\n" in buffer:
                    current_line, buffer = buffer.split("\n", 1)
                    if not current_line.strip():
                        continue

                    if current_line.startswith("data:"):
                        chunk_str = current_line[5:].strip()
                        if not chunk_str or chunk_str == "[DONE]":
                            if chunk_str == "[DONE]":
                                yield "data: [DONE]\n\n"
                            continue

                        self.logger.debug(f"📦 解析数据块: {chunk_str[:1000]}..." if len(chunk_str) > 1000 else f"📦 解析数据块: {chunk_str}")

                        try:
                            chunk = json.loads(chunk_str)

                            if chunk.get("type") == "chat:completion":
                                data = chunk.get("data", {})
                                phase = data.get("phase")

                                # 记录每个阶段（只在阶段变化时记录）
                                if phase and phase != getattr(self, '_last_phase', None):
                                    self.logger.info(f"📈 SSE 阶段: {phase}")
                                    self._last_phase = phase

                                # 使用工具处理器处理所有阶段
                                if tool_handler:
                                    # 构建 SSE 数据块，包含所有必要字段
                                    sse_chunk = {
                                        "phase": phase,
                                        "edit_content": data.get("edit_content", ""),
                                        "delta_content": data.get("delta_content", ""),
                                        "edit_index": data.get("edit_index"),
                                        "usage": data.get("usage", {})
                                    }

                                    # 处理工具调用并输出结果
                                    for output in tool_handler.process_sse_chunk(sse_chunk):
                                        yield output

                                # 非工具调用模式 - 处理思考内容
                                elif phase == "thinking":
                                    if not has_thinking:
                                        has_thinking = True
                                        # 发送初始角色
                                        role_chunk = self.create_openai_chunk(
                                            chat_id,
                                            model,
                                            {"role": "assistant"}
                                        )
                                        yield await self.format_sse_chunk(role_chunk)

                                    delta_content = data.get("delta_content", "")
                                    if delta_content:
                                        # 处理思考内容格式
                                        if delta_content.startswith("<details"):
                                            content = (
                                                delta_content.split("</summary>\n>")[-1].strip()
                                                if "</summary>\n>" in delta_content
                                                else delta_content
                                            )
                                        else:
                                            content = delta_content

                                        thinking_chunk = self.create_openai_chunk(
                                            chat_id,
                                            model,
                                            {
                                                "role": "assistant",
                                                "reasoning_content": content
                                            }
                                        )
                                        yield await self.format_sse_chunk(thinking_chunk)

                                # 处理答案内容
                                elif phase == "answer":
                                    edit_content = data.get("edit_content", "")
                                    delta_content = data.get("delta_content", "")

                                    # 处理思考结束和答案开始
                                    if edit_content and "</details>\n" in edit_content:
                                        if has_thinking:
                                            # 发送思考签名
                                            thinking_signature = str(int(time.time() * 1000))
                                            sig_chunk = self.create_openai_chunk(
                                                chat_id,
                                                model,
                                                {
                                                    "role": "assistant",
                                                    "thinking": {
                                                        "content": "",
                                                        "signature": thinking_signature,
                                                    }
                                                }
                                            )
                                            yield await self.format_sse_chunk(sig_chunk)

                                        # 提取答案内容
                                        content_after = edit_content.split("</details>\n")[-1]
                                        if content_after:
                                            content_chunk = self.create_openai_chunk(
                                                chat_id,
                                                model,
                                                {
                                                    "role": "assistant",
                                                    "content": content_after
                                                }
                                            )
                                            yield await self.format_sse_chunk(content_chunk)

                                    # 处理增量内容
                                    elif delta_content:
                                        # 如果还没有发送角色
                                        if not has_thinking:
                                            role_chunk = self.create_openai_chunk(
                                                chat_id,
                                                model,
                                                {"role": "assistant"}
                                            )
                                            yield await self.format_sse_chunk(role_chunk)

                                        content_chunk = self.create_openai_chunk(
                                            chat_id,
                                            model,
                                            {
                                                "role": "assistant",
                                                "content": delta_content
                                            }
                                        )
                                        output_data = await self.format_sse_chunk(content_chunk)
                                        self.logger.debug(f"➡️ 输出内容块到客户端: {output_data}")
                                        yield output_data

                                    # 处理完成
                                    if data.get("usage"):
                                        self.logger.info(f"📦 完成响应 - 使用统计: {json.dumps(data['usage'])}")

                                        # 只有在非工具调用模式下才发送普通完成信号
                                        if not tool_handler:
                                            finish_chunk = self.create_openai_chunk(
                                                chat_id,
                                                model,
                                                {"role": "assistant", "content": ""},
                                                "stop"
                                            )
                                            finish_chunk["usage"] = data["usage"]

                                            finish_output = await self.format_sse_chunk(finish_chunk)
                                            self.logger.debug(f"➡️ 发送完成信号: {finish_output[:1000]}...")
                                            yield finish_output
                                            self.logger.debug("➡️ 发送 [DONE]")
                                            yield "data: [DONE]\n\n"

                        except json.JSONDecodeError as e:
                            self.logger.debug(f"❌ JSON解析错误: {e}, 内容: {chunk_str[:1000]}")
                        except Exception as e:
                            self.logger.error(f"❌ 处理chunk错误: {e}")

            # 工具处理器会自动发送结束信号，这里不需要重复发送
            if not tool_handler:
                self.logger.debug("📤 发送最终 [DONE] 信号")
                yield "data: [DONE]\n\n"

            self.logger.info(f"✅ SSE 流处理完成，共处理 {line_count} 行数据")

        except Exception as e:
            self.logger.error(f"❌ 流式响应处理错误: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            # 发送错误结束块
            yield await self.format_sse_chunk(
                self.create_openai_chunk(chat_id, model, {}, "stop")
            )
            yield "data: [DONE]\n\n"
    
    async def _handle_non_stream_response(
        self, 
        response: httpx.Response, 
        chat_id: str, 
        model: str
    ) -> Dict[str, Any]:
        """处理非流式响应

        说明：上游始终以 SSE 形式返回（transform_request 固定 stream=True），
        因此这里需要聚合 aiter_lines() 的 data: 块，提取 usage、思考内容与答案内容，
        并最终产出一次性 OpenAI 格式响应。
        """
        final_content = ""
        reasoning_content = ""
        usage_info: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        try:
            async for line in response.aiter_lines():
                if not line:
                    continue

                line = line.strip()

                # 仅处理以 data: 开头的 SSE 行，其余行尝试作为错误/JSON 忽略
                if not line.startswith("data:"):
                    # 尝试解析为错误 JSON
                    try:
                        maybe_err = json.loads(line)
                        if isinstance(maybe_err, dict) and (
                            "error" in maybe_err or "code" in maybe_err or "message" in maybe_err
                        ):
                            # 统一错误处理
                            msg = (
                                (maybe_err.get("error") or {}).get("message")
                                if isinstance(maybe_err.get("error"), dict)
                                else maybe_err.get("message")
                            ) or "上游返回错误"
                            return self.handle_error(Exception(msg), "API响应")
                    except Exception:
                        pass
                    continue

                data_str = line[5:].strip()
                if not data_str or data_str in ("[DONE]", "DONE", "done"):
                    continue

                # 解析 SSE 数据块
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if chunk.get("type") != "chat:completion":
                    continue

                data = chunk.get("data", {})
                phase = data.get("phase")
                delta_content = data.get("delta_content", "")
                edit_content = data.get("edit_content", "")

                # 记录用量（通常在最后块中出现，但这里每次覆盖保持最新）
                if data.get("usage"):
                    try:
                        usage_info = data["usage"]
                    except Exception:
                        pass

                # 思考阶段聚合（去除 <details><summary>... 包裹头）
                if phase == "thinking":
                    if delta_content:
                        if delta_content.startswith("<details"):
                            cleaned = (
                                delta_content.split("</summary>\n>")[-1].strip()
                                if "</summary>\n>" in delta_content
                                else delta_content
                            )
                        else:
                            cleaned = delta_content
                        reasoning_content += cleaned

                # 答案阶段聚合
                elif phase == "answer":
                    # 当 edit_content 同时包含思考结束标记与答案时，提取答案部分
                    if edit_content and "</details>\n" in edit_content:
                        content_after = edit_content.split("</details>\n")[-1]
                        if content_after:
                            final_content += content_after
                    elif delta_content:
                        final_content += delta_content

        except Exception as e:
            self.logger.error(f"❌ 非流式响应处理错误: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            # 返回统一错误响应
            return self.handle_error(e, "非流式聚合")

        # 清理并返回
        final_content = (final_content or "").strip()
        reasoning_content = (reasoning_content or "").strip()

        # 若没有聚合到答案，但有思考内容，则保底返回思考内容
        if not final_content and reasoning_content:
            final_content = reasoning_content

        # 返回包含推理内容的标准响应（若无推理则不会携带）
        return self.create_openai_response_with_reasoning(
            chat_id,
            model,
            final_content,
            reasoning_content,
            usage_info,
        )
