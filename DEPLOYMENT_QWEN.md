# Qwen Standalone Deployment Guide

Complete guide for deploying the Qwen standalone server in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [FlareProx Setup](#flareprox-setup)
6. [Monitoring & Logging](#monitoring--logging)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required
- Python 3.11+
- pip
- Qwen account (get from https://chat.qwen.ai)

### Optional (for Docker)
- Docker 20.10+
- Docker Compose 2.0+

### Optional (for FlareProx)
- Cloudflare account
- Cloudflare API token with Workers access

## Local Development

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python

# Checkout qwen branch
git checkout pr-1

# Install in editable mode
pip install -e .

# Install additional dependencies
pip install uvicorn[standard]
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.qwen.example .env.qwen

# Edit configuration
nano .env.qwen
```

Required settings:
```env
QWEN_EMAIL=your@email.com
QWEN_PASSWORD=your_password
PORT=8081
```

### 3. Run Server

```bash
# Direct Python
python qwen_server.py

# Or using Makefile
make -f Makefile.qwen run
```

Server will start on `http://localhost:8081`

### 4. Test

```bash
# Quick test (3 models)
python test_qwen_server.py --quick

# Full test (all models)
python test_qwen_server.py

# Health check
curl http://localhost:8081/health
```

## Docker Deployment

### Simple Deployment

```bash
# 1. Configure environment
nano .env.qwen

# 2. Build and start
docker-compose -f docker-compose.qwen.yml up -d

# 3. Check logs
docker-compose -f docker-compose.qwen.yml logs -f

# 4. Test
curl http://localhost:8081/health
```

### Using Makefile

```bash
# Build image
make -f Makefile.qwen docker-build

# Start container
make -f Makefile.qwen docker-up

# View logs
make -f Makefile.qwen docker-logs

# Stop container
make -f Makefile.qwen docker-down
```

### Manual Docker Commands

```bash
# Build
docker build -f Dockerfile.qwen -t qwen-api:latest .

# Run
docker run -d \
  --name qwen-api \
  -p 8081:8081 \
  --env-file .env.qwen \
  qwen-api:latest

# View logs
docker logs -f qwen-api

# Stop
docker stop qwen-api
docker rm qwen-api
```

## Production Deployment

### Recommended Stack

**nginx** → **qwen-api** → **FlareProx Workers**

### 1. Prepare Environment

```bash
# Create production environment file
cat > .env.qwen.prod << EOF
PORT=8081
QWEN_EMAIL=prod@email.com
QWEN_PASSWORD=secure_password
DEBUG=false
ENABLE_FLAREPROX=true
CLOUDFLARE_API_KEY=your_api_key
CLOUDFLARE_ACCOUNT_ID=your_account_id
EOF
```

### 2. Deploy with Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  qwen-api:
    image: qwen-api:latest
    container_name: qwen-api-prod
    restart: always
    ports:
      - "127.0.0.1:8081:8081"
    env_file:
      - .env.qwen.prod
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
    networks:
      - qwen-network

  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - qwen-api
    networks:
      - qwen-network

networks:
  qwen-network:
    driver: bridge
```

### 3. nginx Configuration

```nginx
# nginx.conf
http {
    upstream qwen_backend {
        server qwen-api:8081;
        keepalive 32;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Proxy settings
        location / {
            proxy_pass http://qwen_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Streaming support
        location /v1/chat/completions {
            proxy_pass http://qwen_backend;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_buffering off;
            proxy_cache off;
            chunked_transfer_encoding on;
        }
    }
}
```

### 4. Deploy

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## FlareProx Setup

FlareProx provides unlimited scaling through Cloudflare Workers.

### 1. Get Cloudflare Credentials

1. Sign up at https://cloudflare.com
2. Go to https://dash.cloudflare.com/profile/api-tokens
3. Click "Create Token"
4. Use "Edit Cloudflare Workers" template
5. Set permissions:
   - Account Resources: All accounts
   - Zone Resources: All zones
6. Click "Continue to Summary"
7. Click "Create Token"
8. Copy the API token and your Account ID

### 2. Configure FlareProx

```bash
# Interactive setup
python flareprox.py config

# Or manually edit .env.qwen
nano .env.qwen
```

Add:
```env
ENABLE_FLAREPROX=true
CLOUDFLARE_API_KEY=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
CLOUDFLARE_EMAIL=your@email.com
```

### 3. Create Workers

```bash
# Create 3 proxy workers
python flareprox.py create --count 3

# Verify
python flareprox.py list

# Test workers
python flareprox.py test
```

### 4. Enable in Server

The server will automatically use FlareProx workers if:
- `ENABLE_FLAREPROX=true`
- Valid Cloudflare credentials provided
- Workers exist

### 5. Manage Workers

```bash
# List active workers
python flareprox.py list

# Test all workers
python flareprox.py test

# Add more workers
python flareprox.py create --count 5

# Remove all workers
python flareprox.py cleanup
```

## Monitoring & Logging

### Health Checks

```bash
# Basic health
curl http://localhost:8081/health

# Detailed health (with auth)
curl -H "Authorization: Bearer sk-anything" \
  http://localhost:8081/health
```

### Logs

```bash
# Docker logs
docker logs -f qwen-api

# Docker Compose logs
docker-compose -f docker-compose.qwen.yml logs -f

# Filter by service
docker-compose -f docker-compose.qwen.yml logs -f qwen-api

# Last 100 lines
docker logs --tail 100 qwen-api
```

### Metrics

```bash
# Container stats
docker stats qwen-api

# Resource usage
docker exec qwen-api ps aux

# Disk usage
docker exec qwen-api df -h
```

### Monitoring Tools

**Prometheus + Grafana** (recommended):

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Troubleshooting

### Server won't start

**Problem**: Container exits immediately

```bash
# Check logs
docker logs qwen-api

# Common issues:
# 1. Missing environment variables
docker exec qwen-api env | grep QWEN

# 2. Port already in use
lsof -i :8081

# 3. Invalid credentials
# Verify at https://chat.qwen.ai
```

### Authentication errors

**Problem**: 401/403 errors

```bash
# Test credentials
curl -X POST https://chat.qwen.ai/auth \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpass"}'

# Check environment
docker exec qwen-api env | grep QWEN

# Restart with fresh auth
docker restart qwen-api
```

### Model not found

**Problem**: Model name not recognized

```bash
# List available models
curl http://localhost:8081/v1/models

# Use exact model name from list
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-turbo-latest",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

### Slow responses

**Problem**: High latency

```bash
# Enable FlareProx
# Edit .env.qwen:
ENABLE_FLAREPROX=true

# Create workers
python flareprox.py create --count 5

# Restart server
docker restart qwen-api

# Monitor performance
docker stats qwen-api
```

### Memory issues

**Problem**: Out of memory

```bash
# Check usage
docker stats qwen-api

# Increase limit in docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 4G  # Increase from 2G

# Restart
docker-compose restart qwen-api
```

### Connection timeouts

**Problem**: Requests timing out

```bash
# Increase timeouts in nginx.conf:
proxy_connect_timeout 120s;
proxy_send_timeout 120s;
proxy_read_timeout 120s;

# Reload nginx
docker exec nginx nginx -s reload
```

## Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use secrets management in production
   - Rotate credentials regularly

2. **Network**
   - Use HTTPS in production
   - Restrict access with firewall
   - Use API keys for authentication

3. **Docker**
   - Run as non-root user
   - Limit resources
   - Keep images updated
   - Use read-only filesystems where possible

4. **Monitoring**
   - Set up alerts
   - Monitor resource usage
   - Track error rates
   - Log all requests

## Performance Tuning

### Server Configuration

```env
# .env.qwen
PORT=8081
WORKERS=4  # CPU cores
TIMEOUT=60
MAX_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=75
```

### Docker Resources

```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '4.0'
    reservations:
      memory: 2G
      cpus: '2.0'
```

### FlareProx Workers

```bash
# Create more workers for higher throughput
python flareprox.py create --count 10

# Workers scale horizontally - each handles 100k req/day
# 10 workers = 1M requests/day
```

## Support

- **GitHub Issues**: https://github.com/Zeeeepa/z.ai2api_python/issues
- **Documentation**: See QWEN_STANDALONE_README.md
- **Email**: support@pixelium.uk

---

Last updated: 2025-01-07

