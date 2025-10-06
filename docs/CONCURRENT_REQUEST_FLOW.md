# Concurrent Request Flow Explanation

## 📖 **Overview**

This document explains how the system handles **concurrent requests** to different providers when multiple clients make simultaneous API calls.

---

## 🎯 **Your Scenario**

You start the server and make **2 concurrent calls**:

### **Request 1 (Client A):**
```python
from openai import OpenAI
client = OpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8080/v1"
)
response = client.chat.completions.create(
    model="GLM-4.6",  # ZAI Provider
    messages=[{"role": "user", "content": "what is your model!"}]
)
print(response.choices[0].message.content)
```

### **Request 2 (Client B):**
```python
from openai import OpenAI
client = OpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8080/v1"
)
response = client.chat.completions.create(
    model="qwen-turbo",  # Qwen Provider
    messages=[{"role": "user", "content": "what is your model!"}]
)
print(response.choices[0].message.content)
```

---

## 🔄 **What Happens: Step-by-Step**

### **Phase 1: Server Startup**

```
1. Server starts: python main.py
2. FastAPI initializes on port 8080
3. ProviderFactory loads provider configurations
4. SessionStore instances created for each provider:
   - ZAI SessionStore (.sessions/zai_session.json)
   - K2Think SessionStore (.sessions/k2think_session.json)
   - Qwen SessionStore (.sessions/qwen_session.json)
5. Server ready to accept requests
```

---

### **Phase 2: Request 1 Arrives (GLM-4.6 / ZAI)**

**Timeline: T=0ms**

```
┌─────────────────────────────────────────────────────────┐
│ Request 1: POST /v1/chat/completions                    │
│ Model: GLM-4.6 (ZAI Provider)                           │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ FastAPI receives request (async handler)                │
│ - Creates new async task for this request              │
│ - No blocking - FastAPI can accept more requests       │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ chat_completions() handler                              │
│ 1. Validates auth (if enabled)                          │
│ 2. Gets ProviderRouter instance                         │
│ 3. Calls: router.route_request(request)                 │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ ProviderRouter.route_request()                          │
│ 1. Maps "GLM-4.6" → ZAI Provider                        │
│ 2. Calls: zai_provider.chat_completion(request)         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ ZAI Provider - Check Authentication                     │
│ 1. SessionStore checks: .sessions/zai_session.json      │
│ 2. Status: No session found (first request)             │
│ 3. Decision: Need to authenticate                       │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ ZAI Authentication (Playwright)                         │
│ 1. Launch headless Chromium browser                     │
│ 2. Navigate to: https://chat.z.ai/login                 │
│ 3. Enter credentials:                                   │
│    - Email: developer@pixelium.uk                       │
│    - Password: developer123?                            │
│ 4. Extract session data:                                │
│    - Cookies from browser context                       │
│    - Tokens from localStorage/sessionStorage            │
│ 5. Save to: .sessions/zai_session.json (encrypted)      │
│ 6. Close browser                                        │
│                                                          │
│ ⏱️ Duration: ~5-8 seconds                               │
└─────────────────────────────────────────────────────────┘
```

**🚨 IMPORTANT:** While Request 1 is authenticating (5-8 seconds), the server is **NOT BLOCKED**!
- FastAPI uses `async/await`
- Other requests can be processed simultaneously
- This is where Request 2 comes in...

---

### **Phase 3: Request 2 Arrives (qwen-turbo / Qwen)**

**Timeline: T=50ms (arrives during Request 1's authentication)**

```
┌─────────────────────────────────────────────────────────┐
│ Request 2: POST /v1/chat/completions                    │
│ Model: qwen-turbo (Qwen Provider)                       │
│                                                          │
│ 📍 This arrives while Request 1 is still authenticating │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ FastAPI receives request (new async task)               │
│ - Creates separate async task                           │
│ - Runs independently from Request 1                     │
│ - No waiting for Request 1                              │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ chat_completions() handler (new instance)               │
│ 1. Validates auth                                       │
│ 2. Gets ProviderRouter instance (shared)                │
│ 3. Calls: router.route_request(request)                 │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ ProviderRouter.route_request()                          │
│ 1. Maps "qwen-turbo" → Qwen Provider                    │
│ 2. Calls: qwen_provider.chat_completion(request)        │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Qwen Provider - Check Authentication                    │
│ 1. SessionStore checks: .sessions/qwen_session.json     │
│ 2. Status: No session found                             │
│ 3. Decision: Need to authenticate                       │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Qwen Authentication (Playwright)                        │
│ 1. Launch SEPARATE headless Chromium browser            │
│    (Different from Request 1's browser!)                │
│ 2. Navigate to: https://chat.qwen.ai/login              │
│ 3. Enter credentials:                                   │
│    - Email: developer@pixelium.uk                       │
│    - Password: developer1?                              │
│ 4. Extract session data                                 │
│ 5. Save to: .sessions/qwen_session.json (encrypted)     │
│ 6. Close browser                                        │
│                                                          │
│ ⏱️ Duration: ~5-8 seconds                               │
└─────────────────────────────────────────────────────────┘
```

**✅ KEY POINT:** Both authentication processes run **in parallel**!
- Request 1 authenticating to ZAI
- Request 2 authenticating to Qwen
- **No interference between them**

---

### **Phase 4: Both Complete Authentication**

**Timeline: T=~6 seconds**

```
Request 1 (ZAI):
┌─────────────────────────────────────────────────────────┐
│ ✅ Authentication complete                              │
│ - Session saved: .sessions/zai_session.json             │
│ - Valid for: 12 hours                                   │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Make Actual API Request to ZAI                          │
│ POST https://chat.z.ai/api/v1/chat                      │
│ Headers:                                                │
│   - Cookie: <session_cookies>                           │
│   - Authorization: Bearer <token>                       │
│ Body:                                                   │
│   {                                                     │
│     "model": "GLM-4.6",                                 │
│     "messages": [{"role": "user", "content": "..."}]    │
│   }                                                     │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ ZAI Responds                                            │
│ - Model: GLM-4.6                                        │
│ - Response: "I am GLM-4.6, developed by Zhipu AI..."   │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Transform to OpenAI Format                              │
│ - Convert ZAI response structure                        │
│ - Add OpenAI-compatible fields                          │
│ - Return JSON response to Client A                      │
└─────────────────────────────────────────────────────────┘


Request 2 (Qwen):
┌─────────────────────────────────────────────────────────┐
│ ✅ Authentication complete                              │
│ - Session saved: .sessions/qwen_session.json            │
│ - Valid for: 12 hours                                   │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Make Actual API Request to Qwen                         │
│ POST https://chat.qwen.ai/api/v1/chat                   │
│ Headers:                                                │
│   - Cookie: <session_cookies>                           │
│   - Authorization: Bearer <token>                       │
│ Body:                                                   │
│   {                                                     │
│     "model": "qwen-turbo",                              │
│     "messages": [{"role": "user", "content": "..."}]    │
│   }                                                     │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Qwen Responds                                           │
│ - Model: qwen-turbo                                     │
│ - Response: "我是通义千问..."                              │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Transform to OpenAI Format                              │
│ - Convert Qwen response structure                       │
│ - Add OpenAI-compatible fields                          │
│ - Return JSON response to Client B                      │
└─────────────────────────────────────────────────────────┘
```

---

### **Phase 5: Subsequent Requests (Session Reuse)**

**Timeline: Request 3 arrives (GLM-4.6 again)**

```
┌─────────────────────────────────────────────────────────┐
│ Request 3: POST /v1/chat/completions                    │
│ Model: GLM-4.6 (ZAI Provider)                           │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ ZAI Provider - Check Authentication                     │
│ 1. SessionStore checks: .sessions/zai_session.json      │
│ 2. Status: ✅ Valid session found!                      │
│ 3. Session age: 2 minutes (< 12 hours)                  │
│ 4. Decision: Reuse existing session                     │
│                                                          │
│ ⚡ No authentication needed! Direct API call!           │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Make API Request with Cached Session                    │
│ - Load cookies from session file                        │
│ - Load token from session file                          │
│ - Make request immediately                              │
│                                                          │
│ ⏱️ Duration: ~500ms (no auth delay!)                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ **System Architecture**

### **1. Concurrency Model**

```
FastAPI (ASGI Server - Uvicorn)
├── Async Event Loop
├── Request 1 (Task 1) ──→ ZAI Provider ──→ Playwright (Browser 1)
├── Request 2 (Task 2) ──→ Qwen Provider ──→ Playwright (Browser 2)
├── Request 3 (Task 3) ──→ K2Think Provider ──→ Playwright (Browser 3)
└── All running concurrently, no blocking!
```

**Key Points:**
- ✅ Each request runs in its own **async task**
- ✅ No request blocks another request
- ✅ Multiple Playwright browsers can run simultaneously
- ✅ Each provider has its own SessionStore

---

### **2. Session Management**

```
.sessions/
├── zai_session.json       (ZAI cookies + token)
├── k2think_session.json   (K2Think cookies + token)
└── qwen_session.json      (Qwen cookies + token)

Each session contains:
{
  "cookies": {
    "session_id": "abc123...",
    "auth_token": "xyz789...",
    ...
  },
  "token": "bearer_token_here",
  "timestamp": 1696612345,  // Creation time
  "expires_at": 1696655545, // Expiry time (12 hours later)
  "extra_data": {...}
}

Encrypted with Fernet (AES-128)
```

**Session Lifetime:**
- **Valid for:** 12 hours from creation
- **Checked on:** Every request
- **Refreshed:** Automatically when expired
- **Concurrent-safe:** File locking prevents race conditions

---

### **3. Provider Isolation**

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   ZAI Provider   │  │  Qwen Provider   │  │ K2Think Provider │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ - Own Auth       │  │ - Own Auth       │  │ - Own Auth       │
│ - Own Session    │  │ - Own Session    │  │ - Own Session    │
│ - Own Playwright │  │ - Own Playwright │  │ - Own Playwright │
│ - Own Config     │  │ - Own Config     │  │ - Own Config     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        ↓                      ↓                      ↓
  No interference!      No interference!      No interference!
```

**Benefits:**
- ✅ Provider failures are isolated
- ✅ Sessions don't conflict
- ✅ Authentication can happen in parallel
- ✅ Easy to add new providers

---

## ⚡ **Performance Characteristics**

### **First Request (Cold Start):**
```
Request arrives
  ↓ ~10ms  (routing + validation)
  ↓ ~5000ms (Playwright authentication)
  ↓ ~500ms (actual API call)
  ↓ ~10ms  (response transformation)
──────────────────────────────────────
Total: ~5520ms (~5.5 seconds)
```

### **Subsequent Requests (Warm Start):**
```
Request arrives
  ↓ ~10ms  (routing + validation)
  ↓ ~0ms   (session reused! no auth!)
  ↓ ~500ms (actual API call)
  ↓ ~10ms  (response transformation)
──────────────────────────────────────
Total: ~520ms (~0.5 seconds)
```

### **Concurrent Requests:**
```
Request 1 (ZAI) + Request 2 (Qwen) arrive simultaneously
  ↓ Both start at T=0
  ↓ Both authenticate in parallel
  ↓ Both complete at T~5.5s
──────────────────────────────────────
No waiting! Both finish ~same time!
```

---

## 🔒 **Thread Safety & Concurrency**

### **1. File Locking (Session Store)**

```python
# Atomic file operations
with open(session_file, 'w') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
    json.dump(session_data, f)
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
```

**Prevents:**
- ❌ Race conditions when saving sessions
- ❌ Corrupted session files
- ❌ Lost writes

---

### **2. Provider Isolation**

```python
# Each provider instance is independent
zai_provider = ZAIProvider(config)   # Has own SessionStore
qwen_provider = QwenProvider(config) # Has own SessionStore
k2_provider = K2ThinkProvider(config) # Has own SessionStore

# No shared state between providers!
```

**Benefits:**
- ✅ No mutex needed for provider switching
- ✅ Parallel authentication possible
- ✅ No deadlocks

---

### **3. Async/Await Pattern**

```python
# Non-blocking I/O
async def chat_completion(request):
    # This doesn't block other requests
    result = await httpx_client.post(url, ...)
    return result

# Multiple requests can await simultaneously
await asyncio.gather(
    request1,  # ZAI
    request2,  # Qwen
    request3,  # K2Think
)
```

---

## 📊 **Example Timeline Diagram**

```
Time (seconds)
0s ───────────────────────────────────────────────────────→ 10s
│
│ Request 1 (GLM-4.6 / ZAI)
│ ├─ Start auth ──────────────────┐
│ │                    Auth        │
│ │                    5s          │
│ └───────────────────────────────┼─ API call ─┬─ Response
│                                   (0.5s)       (T=5.5s)
│
│ Request 2 (qwen-turbo / Qwen)   [50ms delay]
│   ├─ Start auth ──────────────────┐
│   │                    Auth        │
│   │                    5s          │
│   └───────────────────────────────┼─ API call ─┬─ Response
│                                     (0.5s)       (T=5.6s)
│
│ Request 3 (GLM-4.6 / ZAI again)  [8s delay]
│                                      ├─ Session reused! ─┬─ Response
│                                         (0.5s)            (T=8.5s)
```

**Key Observations:**
1. Request 1 & 2 authenticate in parallel (~5.5s for both)
2. Request 3 reuses Request 1's session (instant auth, ~0.5s total)
3. No blocking between requests

---

## 🎯 **Your Specific Question: What Happens?**

When you make those 2 concurrent calls:

### **Timeline:**

```
T=0ms:    Request 1 (GLM-4.6) arrives at server
          ↓ Start ZAI authentication (Playwright)

T=50ms:   Request 2 (qwen-turbo) arrives at server
          ↓ Start Qwen authentication (Playwright)
          
          Both authenticate IN PARALLEL! ⚡

T=5500ms: Request 1 completes
          ↓ Client A receives: "I am GLM-4.6..."

T=5600ms: Request 2 completes
          ↓ Client B receives: "我是通义千问..."
```

### **Result:**

✅ **Both clients get their responses almost simultaneously (~5.5 seconds each)**

❌ **NOT sequential:** Doesn't take 11 seconds (5.5 + 5.5)

✅ **Session cached:** Next GLM-4.6 or qwen-turbo requests will be instant (~0.5s)

---

## 🚀 **Performance Tips**

### **1. Pre-warm Sessions**

Run this before serving traffic:

```bash
# Pre-authenticate all providers
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "GLM-4.6", "messages": [{"role": "user", "content": "hi"}]}'

curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-turbo", "messages": [{"role": "user", "content": "hi"}]}'

curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "K2-Think", "messages": [{"role": "user", "content": "hi"}]}'
```

Now all sessions are cached for 12 hours!

---

### **2. Session Refresh Script**

```python
# refresh_sessions.py
import asyncio
from openai import AsyncOpenAI

async def refresh_all():
    client = AsyncOpenAI(
        api_key="sk-anything",
        base_url="http://localhost:8080/v1"
    )
    
    models = ["GLM-4.6", "qwen-turbo", "K2-Think"]
    
    tasks = [
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}]
        )
        for model in models
    ]
    
    await asyncio.gather(*tasks)
    print("✅ All sessions refreshed!")

asyncio.run(refresh_all())
```

Run this every 11 hours to keep sessions fresh!

---

## 📝 **Summary**

**Your 2 concurrent requests will:**

1. ✅ Both arrive at the server (~same time)
2. ✅ Both start authentication in parallel
3. ✅ Both complete in ~5.5 seconds
4. ✅ Both sessions cached for 12 hours
5. ✅ Future requests to same models: instant (~0.5s)

**The system handles concurrency via:**
- ✅ FastAPI's async architecture
- ✅ Independent provider instances
- ✅ Separate SessionStore per provider
- ✅ File locking for thread safety
- ✅ Parallel Playwright authentication

**No blocking, no race conditions, no deadlocks!** 🎉

