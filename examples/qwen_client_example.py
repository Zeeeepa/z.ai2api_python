#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Qwen Client Example
====================

Demonstrates how to use the Qwen standalone server with OpenAI SDK.
"""

from openai import OpenAI
import time

# Initialize client
client = OpenAI(
    api_key="sk-anything",  # Any string works
    base_url="http://localhost:8081/v1"
)


def example_basic_chat():
    """Basic chat completion"""
    print("\n" + "="*60)
    print("Example 1: Basic Chat Completion")
    print("="*60)
    
    response = client.chat.completions.create(
        model="qwen-turbo-latest",
        messages=[
            {"role": "user", "content": "What model are you?"}
        ]
    )
    
    print(f"Model: {response.model}")
    print(f"Response: {response.choices[0].message.content}")


def example_streaming():
    """Streaming completion"""
    print("\n" + "="*60)
    print("Example 2: Streaming Completion")
    print("="*60)
    
    print("Streaming response: ", end="", flush=True)
    
    stream = client.chat.completions.create(
        model="qwen-max-latest",
        messages=[
            {"role": "user", "content": "Count from 1 to 10"}
        ],
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print()  # New line


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Qwen Client Examples")
    print("="*60)
    print("\nMake sure the server is running:")
    print("  python qwen_server.py")
    print("\nStarting examples in 2 seconds...")
    time.sleep(2)
    
    try:
        example_basic_chat()
        time.sleep(1)
        
        example_streaming()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the server is running:")
        print("  python qwen_server.py")


if __name__ == "__main__":
    main()

