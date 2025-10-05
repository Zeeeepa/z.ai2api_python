# Qwen Chat API Structure - Complete Reference

## Overview
This document provides the **exact** API structure required for Qwen Chat API, extracted from the working TypeScript reference implementation (`qwenchat2api`).

## Critical Discovery: The 9 Missing/Wrong Fields

### ❌ Issues in Original Python Implementation vs ✅ Correct Structure

| Field | Original Python | Correct Structure | Status |
|-------|----------------|-------------------|--------|
| `session_id` | ❌ Missing | ✅ UUID required | **CRITICAL** |
| `chat_id` | ❌ Missing | ✅ UUID required | **CRITICAL** |
| `parent_id` | ❌ Missing | ✅ `null` for new | **CRITICAL** |
| `chat_mode` | ❌ Missing | ✅ `"normal"` | **CRITICAL** |
| `timestamp` | ❌ Missing | ✅ `Date.now()` | **CRITICAL** |
| Message `chat_type` | ❌ Missing | ✅ `"text"` | **CRITICAL** |
| Message `extra` | ❌ Missing | ✅ `{}` | **CRITICAL** |
| `thinking_budget` | ❌ Wrong key `budget` | ✅ In `feature_config` | **CRITICAL** |
| `feature_config` | ❌ Incomplete | ✅ Full structure | **CRITICAL** |

---

## Correct Request Structure

### Text-to-Text Chat (Default)

```json
{
  "model": "qwen-max",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?",
      "chat_type": "text",
      "extra": {}
    }
  ],
  "stream": true,
  "incremental_output": true,
  "chat_type": "normal",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "chat_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "feature_config": {
    "output_schema": "phase",
    "thinking_enabled": false
  }
}
```

All details extracted from qwenchat2api/main.ts reference implementation.

