# 🚀 Quick Start Guide

## One-Command Deployment & Testing

This repository includes a single script that handles everything: installation, configuration, server startup, testing, and result viewing.

### Usage

```bash
# Interactive mode (recommended for first time)
./quick_deploy_test.sh

# Automatic mode (runs all steps without prompts)
./quick_deploy_test.sh --auto
```

### What It Does

The script automatically:

1. ✅ **Checks prerequisites** (Python, pip, curl)
2. ✅ **Creates virtual environment** (if needed for Python 3.12+)
3. ✅ **Installs all dependencies** (Python packages, Playwright browsers)
4. ✅ **Configures providers** (creates config from template if needed)
5. ✅ **Starts the server** on port 8080
6. ✅ **Runs health checks** to verify server is working
7. ✅ **Tests individual models** from each provider
8. ✅ **Runs comprehensive tests** on all 42+ models concurrently
9. ✅ **Displays detailed results** with error analysis

**Note**: On Python 3.12+ (PEP 668), the script automatically creates and uses a virtual environment to avoid system package conflicts.

### Example Output

```
═══════════════════════════════════════════════════════════════════════
  Z.AI2API - Automated Deployment & Testing
═══════════════════════════════════════════════════════════════════════

This script will:
  1. Install dependencies
  2. Configure providers
  3. Start the server
  4. Run health checks
  5. Run quick tests
  6. Run comprehensive tests
  7. Display results

Press Enter to continue or Ctrl+C to cancel...

═══════════════════════════════════════════════════════════════════════
  STEP 1: Installing Dependencies
═══════════════════════════════════════════════════════════════════════

▶ Installing Python dependencies...
✅ Python dependencies installed
▶ Installing Playwright browsers...
✅ Playwright browsers installed

═══════════════════════════════════════════════════════════════════════
  STEP 2: Configuring Providers
═══════════════════════════════════════════════════════════════════════

✅ config/providers.json found
✅ Configuration file is valid JSON

═══════════════════════════════════════════════════════════════════════
  STEP 3: Starting Server
═══════════════════════════════════════════════════════════════════════

▶ Starting server on port 8080...
▶ Waiting for server to start...
✅ Server is ready!
✅ Server started successfully (PID: 12345)
ℹ️  Server URL: http://localhost:8080
ℹ️  Server logs: /path/to/server.log

═══════════════════════════════════════════════════════════════════════
  STEP 4: Health Check
═══════════════════════════════════════════════════════════════════════

▶ Testing server connectivity...
✅ Server is responding
{
    "message": "OpenAI Compatible API Server"
}

▶ Listing available models...
✅ Found 42 models available

📋 Available Models:
  • GLM-4.5
  • GLM-4.5-Thinking
  • GLM-4.5-Search
  • GLM-4.5-Air
  • GLM-4.6
  • qwen-max
  • qwen-plus
  • MBZUAI-IFM/K2-Think
  • grok-3
  • grok-4
  ... and 32 more

═══════════════════════════════════════════════════════════════════════
  STEP 5: Running Quick Tests
═══════════════════════════════════════════════════════════════════════

▶ Testing GLM-4.5...
⚠️  GLM-4.5 - Authentication required
     Invalid API key
▶ Testing qwen-max...
⚠️  qwen-max - Authentication required
     Invalid API key

ℹ️  Quick Test Results: 0/3 successful
⚠️  No models responded successfully - authentication may be required
ℹ️  This is expected if providers haven't been authenticated yet

═══════════════════════════════════════════════════════════════════════
  STEP 6: Running Comprehensive Tests (AllCall.py)
═══════════════════════════════════════════════════════════════════════

▶ Running tests on all 42+ models concurrently...
ℹ️  This will test all models simultaneously and may take 1-2 minutes

[Test output showing all 42 models being tested...]

✅ Comprehensive tests completed!
ℹ️  Full results saved to: /path/to/test_results.log

═══════════════════════════════════════════════════════════════════════
  Deployment Complete!
═══════════════════════════════════════════════════════════════════════

Server is running at: http://localhost:8080

Useful commands:
  • View logs:        tail -f server.log
  • View test results: cat test_results.log
  • Stop server:      kill $(cat server.pid)
  • Test single model: curl -X POST http://localhost:8080/v1/chat/completions \
                         -H 'Content-Type: application/json' \
                         -H 'Authorization: Bearer sk-anything' \
                         -d '{"model": "GLM-4.5", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Interactive Menu

After deployment, you can optionally enter an interactive menu:

```
═══════════════════════════════════════════════════════════════════════
  Interactive Testing Menu
═══════════════════════════════════════════════════════════════════════

What would you like to do?

  1) Test a specific model
  2) Run comprehensive tests (all models)
  3) View server logs
  4) View test results
  5) Check server status
  6) Restart server
  7) Stop server and exit

Enter choice (1-7):
```

## Manual Testing After Deployment

Once the server is running, you can test models manually:

### Using curl

```bash
# Test Z.AI GLM model
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{
    "model": "GLM-4.5",
    "messages": [{"role": "user", "content": "What model are you?"}]
  }'

# Test Qwen model
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{
    "model": "qwen-max",
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
  }'

# Test K2Think model
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{
    "model": "MBZUAI-IFM/K2-Think",
    "messages": [{"role": "user", "content": "Solve: What is 15% of 240?"}]
  }'
```

### Using Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8080/v1"
)

# Test model
response = client.chat.completions.create(
    model="GLM-4.5",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### Using AllCall.py

```bash
# Run comprehensive tests on all models
python3 AllCall.py
```

## Configuration

Before running, ensure your credentials are set in `config/providers.json`:

```json
{
  "providers": [
    {
      "name": "zai",
      "enabled": true,
      "baseUrl": "https://chat.z.ai",
      "loginUrl": "https://chat.z.ai/auth",
      "chatUrl": "https://chat.z.ai",
      "email": "your-email@example.com",
      "password": "your-password"
    },
    {
      "name": "k2think",
      "enabled": true,
      "baseUrl": "https://www.k2think.ai",
      "loginUrl": "https://www.k2think.ai/login",
      "chatUrl": "https://www.k2think.ai/chat",
      "email": "your-email@example.com",
      "password": "your-password"
    },
    {
      "name": "qwen",
      "enabled": true,
      "baseUrl": "https://chat.qwen.ai",
      "loginUrl": "https://chat.qwen.ai/auth?action=signin",
      "chatUrl": "https://chat.qwen.ai",
      "email": "your-email@example.com",
      "password": "your-password"
    }
  ]
}
```

## Viewing Results

### Server Logs

```bash
# Real-time logs
tail -f server.log

# Last 50 lines
tail -50 server.log

# Search for errors
grep ERROR server.log
```

### Test Results

```bash
# View all test results
cat test_results.log

# View with pagination
less test_results.log

# Extract summary
grep -A 10 "SUMMARY" test_results.log
```

## Stopping the Server

```bash
# Using the PID file
kill $(cat server.pid)

# Or find and kill the process
pkill -f "python3 main.py"
```

## Troubleshooting

### Authentication Errors (401)

If you see "Invalid API key" errors:

1. Check credentials in `config/providers.json`
2. Verify accounts are active on provider websites
3. Ensure Playwright is installed: `playwright install chromium`
4. Check server logs: `tail -f server.log`

### Server Won't Start

1. Check if port 8080 is already in use: `lsof -i :8080`
2. Try a different port: `export LISTEN_PORT=8081 && ./quick_deploy_test.sh`
3. Check Python version: `python3 --version` (requires 3.11+)

### Models Not Responding

1. Restart server: `kill $(cat server.pid) && ./quick_deploy_test.sh`
2. Clear session cache: `rm -rf data/sessions/*`
3. Check internet connectivity

## Advanced Usage

### Custom Port

```bash
export LISTEN_PORT=8081
./quick_deploy_test.sh
```

### Enable Debug Logging

```bash
export DEBUG_LOGGING=true
./quick_deploy_test.sh
```

### Run Only Specific Steps

You can run individual functions from the script:

```bash
# Source the script
source quick_deploy_test.sh

# Run specific function
health_check
run_quick_tests
run_comprehensive_tests
```

## Full Documentation

For comprehensive documentation, see:

- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Complete deployment guide
- [README.md](./README.md) - Project overview and architecture
- [AllCall.py](./AllCall.py) - Comprehensive testing script

## Support

For issues or questions:

1. Check server logs: `tail -f server.log`
2. Check test results: `cat test_results.log`
3. Review [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
4. Open an issue on GitHub

## Summary

**TL;DR**: Just run `./quick_deploy_test.sh` and follow the prompts. The script handles everything from installation to testing and result viewing. Your server will be running on http://localhost:8080 with all 42+ models ready to test!
