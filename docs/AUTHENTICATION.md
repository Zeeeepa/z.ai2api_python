# Authentication Guide

## Overview

The API server supports multiple authentication methods for different providers and API access.

See the full documentation in the main README.md file.

## Quick Start

### API Authentication

Set your API key in `.env`:
```bash
AUTH_TOKEN=sk-your-secret-key
```

Use in requests:
```bash
curl -H "Authorization: Bearer sk-your-secret-key" \
  http://localhost:8080/v1/models
```

### Provider Credentials

Configure in `config/providers.json`:
```json
{
  "providers": [
    {
      "name": "zai",
      "email": "your-email@example.com",
      "password": "your-password",
      "enabled": true
    }
  ]
}
```

For complete authentication documentation, see README.md.
