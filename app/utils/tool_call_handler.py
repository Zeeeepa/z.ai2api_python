#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具调用处理模块
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from app.utils.logger import get_logger

logger = get_logger()


def generate_tool_prompt(tools: Optional[List[Dict[str, Any]]]) -> str:
    """
    生成工具调用提示词
    将 OpenAI tools 定义转换为 Markdown 格式的说明文档

    Args:
        tools: OpenAI 格式的工具定义列表

    Returns:
        str: Markdown 格式的工具使用说明
    """
    if not tools or len(tools) == 0:
        return ""

    tool_definitions = []

    for tool in tools:
        if tool.get("type") != "function":
            continue

        function_spec = tool.get("function", {})
        function_name = function_spec.get("name", "unknown")
        function_description = function_spec.get("description", "")
        parameters = function_spec.get("parameters", {})

        # 创建结构化的工具定义
        tool_info = [
            f"## {function_name}",
            f"**Purpose**: {function_description}"
        ]

        # 添加参数详情
        parameter_properties = parameters.get("properties", {})
        required_parameters = set(parameters.get("required", []))

        if parameter_properties:
            tool_info.append("**Parameters**:")
            for param_name, param_info in parameter_properties.items():
                param_type = param_info.get("type", "string")
                param_desc = param_info.get("description", "")
                is_required = param_name in required_parameters
                required_str = " (required)" if is_required else " (optional)"
                tool_info.append(f"- `{param_name}` ({param_type}){required_str}: {param_desc}")

        tool_definitions.append("\n".join(tool_info))

    # 组合完整的提示词
    prompt = (
        "\n\n---\n"
        "# Available Tools\n\n"
        + "\n\n".join(tool_definitions) +
        "\n\n"
        "**Tool Invocation Format**:\n"
        "To use a tool, include a JSON block with this structure:\n"
        '{"tool_calls": [{"id": "call_ID", "type": "function", "function": {"name": "TOOL_NAME", "arguments": "JSON_STRING"}}]}\n\n'
        "**Rules**:\n"
        "- Use tool ONLY when user explicitly requests an action that matches a tool's purpose\n"
        "- For normal conversation, respond naturally WITHOUT any tool calls\n"
        "- The `arguments` must be a JSON string, not an object\n"
        "- Multiple tools can be called by adding more items to the array\n"
        "---\n\n"
    )

    logger.debug(f"生成工具提示词,包含 {len(tool_definitions)} 个工具定义")
    return prompt


def process_messages_with_tools(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]],
    tool_choice: str = "auto"
) -> List[Dict[str, Any]]:
    """
    将工具定义注入到消息列表中

    Args:
        messages: 原始消息列表
        tools: 工具定义列表
        tool_choice: 工具选择策略 ("auto", "none", 等)

    Returns:
        List[Dict]: 处理后的消息列表
    """
    if not tools or tool_choice == "none":
        return messages

    tools_prompt = generate_tool_prompt(tools)
    if not tools_prompt:
        return messages

    processed = []
    has_system = any(m.get("role") == "system" for m in messages)

    if has_system:
        # 如果有 system 消息,将工具提示追加到第一个 system 消息
        for msg in messages:
            if msg.get("role") == "system":
                new_msg = msg.copy()
                content = new_msg.get("content", "")
                if isinstance(content, list):
                    # 多模态内容
                    content_str = " ".join([
                        item.get("text", "") if item.get("type") == "text" else ""
                        for item in content
                    ])
                else:
                    content_str = str(content)
                new_msg["content"] = content_str + tools_prompt
                processed.append(new_msg)
            else:
                processed.append(msg)
    else:
        # 没有 system 消息,创建一个新的 system 消息
        processed.append({
            "role": "system",
            "content": f"You are a helpful assistant with access to tools.{tools_prompt}"
        })
        processed.extend(messages)

    logger.debug(f"工具提示已注入到消息列表,共 {len(processed)} 条消息")
    return processed


def parse_and_extract_tool_calls(content: str) -> Tuple[Optional[List[Dict[str, Any]]], str]:
    """
    从响应内容中提取 tool_calls JSON
    
    Args:
        content: 模型返回的文本内容

    Returns:
        Tuple[Optional[List], str]: (提取的 tool_calls 列表, 清理后的内容)
    """
    if not content or not content.strip():
        return None, content

    tool_calls = None
    cleaned_content = content

    # 方法1: 尝试解析 JSON 代码块中的 tool_calls
    # 匹配 ```json ... ``` 或 ```...```
    json_block_pattern = r'```(?:json)?\s*\n?(\{[\s\S]*?\})\s*\n?```'
    json_blocks = re.findall(json_block_pattern, content)

    for json_str in json_blocks:
        try:
            parsed_data = json.loads(json_str)
            if "tool_calls" in parsed_data:
                tool_calls = parsed_data["tool_calls"]
                if tool_calls and isinstance(tool_calls, list):
                    # 确保 arguments 字段是字符串
                    for tc in tool_calls:
                        if tc.get("function"):
                            func = tc["function"]
                            if func.get("arguments"):
                                if isinstance(func["arguments"], dict):
                                    # 转换对象为 JSON 字符串
                                    func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)
                                elif not isinstance(func["arguments"], str):
                                    func["arguments"] = str(func["arguments"])
                    logger.debug(f"从 JSON 代码块中提取到 {len(tool_calls)} 个工具调用")
                    break
        except json.JSONDecodeError:
            continue

    # 方法2: 尝试从文本中直接查找 JSON 对象
    if not tool_calls:
        # 查找包含 "tool_calls" 的 JSON 对象
        i = 0
        scannable_text = content
        while i < len(scannable_text):
            if scannable_text[i] == '{':
                # 尝试找到匹配的闭合括号
                brace_count = 1
                j = i + 1
                in_string = False
                escape_next = False

                while j < len(scannable_text) and brace_count > 0:
                    if escape_next:
                        escape_next = False
                    elif scannable_text[j] == '\\':
                        escape_next = True
                    elif scannable_text[j] == '"':
                        in_string = not in_string
                    elif not in_string:
                        if scannable_text[j] == '{':
                            brace_count += 1
                        elif scannable_text[j] == '}':
                            brace_count -= 1
                    j += 1

                if brace_count == 0:
                    # 找到完整的 JSON 对象
                    json_candidate = scannable_text[i:j]
                    try:
                        parsed_data = json.loads(json_candidate)
                        if "tool_calls" in parsed_data:
                            tool_calls = parsed_data["tool_calls"]
                            if tool_calls and isinstance(tool_calls, list):
                                # 确保 arguments 字段是字符串
                                for tc in tool_calls:
                                    if tc.get("function"):
                                        func = tc["function"]
                                        if func.get("arguments"):
                                            if isinstance(func["arguments"], dict):
                                                func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)
                                            elif not isinstance(func["arguments"], str):
                                                func["arguments"] = str(func["arguments"])
                                logger.debug(f"从内联 JSON 中提取到 {len(tool_calls)} 个工具调用")
                                break
                    except json.JSONDecodeError:
                        pass

                i = j
            else:
                i += 1

    # 清理内容 - 移除包含 tool_calls 的 JSON
    if tool_calls:
        cleaned_content = remove_tool_json_content(content)

    return tool_calls, cleaned_content


def remove_tool_json_content(content: str) -> str:
    """
    从响应内容中移除工具调用 JSON

    Args:
        content: 原始响应内容

    Returns:
        str: 清理后的内容
    """
    if not content:
        return content

    # 步骤1: 移除 JSON 代码块中包含 tool_calls 的部分
    cleaned_text = content

    # 匹配 ```json ... ``` 或 ```...```
    def replace_json_block(match):
        json_content = match.group(1)
        try:
            parsed_data = json.loads(json_content)
            if "tool_calls" in parsed_data:
                return ""  # 移除整个代码块
        except json.JSONDecodeError:
            pass
        return match.group(0)  # 保留原文

    json_block_pattern = r'```(?:json)?\s*\n?(\{[\s\S]*?\})\s*\n?```'
    cleaned_text = re.sub(json_block_pattern, replace_json_block, cleaned_text)

    # 步骤2: 移除内联的 tool JSON - 使用括号平衡方法
    result = []
    i = 0

    while i < len(cleaned_text):
        if cleaned_text[i] == '{':
            # 尝试找到匹配的闭合括号
            brace_count = 1
            j = i + 1
            in_string = False
            escape_next = False

            while j < len(cleaned_text) and brace_count > 0:
                if escape_next:
                    escape_next = False
                elif cleaned_text[j] == '\\':
                    escape_next = True
                elif cleaned_text[j] == '"':
                    in_string = not in_string
                elif not in_string:
                    if cleaned_text[j] == '{':
                        brace_count += 1
                    elif cleaned_text[j] == '}':
                        brace_count -= 1
                j += 1

            if brace_count == 0:
                # 找到完整的 JSON 对象,检查是否包含 tool_calls
                json_candidate = cleaned_text[i:j]
                try:
                    parsed = json.loads(json_candidate)
                    if "tool_calls" in parsed:
                        # 这是一个工具调用,跳过它
                        i = j
                        continue
                except json.JSONDecodeError:
                    pass

            # 不是工具调用或无法解析,保留这个字符
            result.append(cleaned_text[i])
            i += 1
        else:
            result.append(cleaned_text[i])
            i += 1

    cleaned_result = "".join(result).strip()

    # 移除多余的空白行
    cleaned_result = re.sub(r'\n{3,}', '\n\n', cleaned_result)

    logger.debug(f"内容清理完成,原始长度: {len(content)}, 清理后长度: {len(cleaned_result)}")
    return cleaned_result


def content_to_string(content: Any) -> str:
    """
    将消息内容转换为字符串

    Args:
        content: 消息内容,可能是字符串或列表(多模态)

    Returns:
        str: 字符串格式的内容
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # 多模态内容,提取文本部分
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        return " ".join(text_parts)
    else:
        return str(content)
