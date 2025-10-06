#!/usr/bin/env python3
"""
FlareProx - Simple URL Redirection via Cloudflare Workers
Redirect all traffic through Cloudflare Workers for any provided URL
"""

import argparse
import getpass
import json
import os
import random
import requests
import string
import time
from typing import Dict, List, Optional


class FlareProxError(Exception):
    """Custom exception for FlareProx-specific errors."""
    pass


class CloudflareManager:
    """Manages Cloudflare Worker deployments for FlareProx."""

    def __init__(self, api_token: str, account_id: str, zone_id: Optional[str] = None):
        self.api_token = api_token
        self.account_id = account_id
        self.zone_id = zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self._account_subdomain = None

    @property
    def worker_subdomain(self) -> str:
        """Get the worker subdomain for workers.dev URLs."""
        if self._account_subdomain:
            return self._account_subdomain

        # Try to get configured subdomain
        url = f"{self.base_url}/accounts/{self.account_id}/workers/subdomain"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                subdomain = data.get("result", {}).get("subdomain")
                if subdomain:
                    self._account_subdomain = subdomain
                    return subdomain
        except requests.RequestException:
            pass

        # Fallback: use account ID as subdomain
        self._account_subdomain = self.account_id.lower()
        return self._account_subdomain

    def _generate_worker_name(self) -> str:
        """Generate a unique worker name."""
        timestamp = str(int(time.time()))
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        return f"flareprox-{timestamp}-{random_suffix}"

    def _get_worker_script(self) -> str:
        """Return the optimized Cloudflare Worker script."""
        return '''/**
 * FlareProx - Cloudflare Worker URL Redirection Script
 */
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  try {
    const url = new URL(request.url)
    const targetUrl = getTargetUrl(url, request.headers)

    if (!targetUrl) {
      return createErrorResponse('No target URL specified', {
        usage: {
          query_param: '?url=https://example.com',
          header: 'X-Target-URL: https://example.com',
          path: '/https://example.com'
        }
      }, 400)
    }

    let targetURL
    try {
      targetURL = new URL(targetUrl)
    } catch (e) {
      return createErrorResponse('Invalid target URL', { provided: targetUrl }, 400)
    }

    // Build target URL with filtered query parameters
    const targetParams = new URLSearchParams()
    for (const [key, value] of url.searchParams) {
      if (!['url', '_cb', '_t'].includes(key)) {
        targetParams.append(key, value)
      }
    }
    if (targetParams.toString()) {
      targetURL.search = targetParams.toString()
    }

    // Create proxied request
    const proxyRequest = createProxyRequest(request, targetURL)
    const response = await fetch(proxyRequest)

    // Process and return response
    return createProxyResponse(response, request.method)

  } catch (error) {
    return createErrorResponse('Proxy request failed', {
      message: error.message,
      timestamp: new Date().toISOString()
    }, 500)
  }
}

function getTargetUrl(url, headers) {
  // Priority: query param > header > path
  let targetUrl = url.searchParams.get('url')

  if (!targetUrl) {
    targetUrl = headers.get('X-Target-URL')
  }

  if (!targetUrl && url.pathname !== '/') {
    const pathUrl = url.pathname.slice(1)
    if (pathUrl.startsWith('http')) {
      targetUrl = pathUrl
    }
  }

  return targetUrl
}

function createProxyRequest(request, targetURL) {
  const proxyHeaders = new Headers()
  const allowedHeaders = [
    'accept', 'accept-language', 'accept-encoding', 'authorization',
    'cache-control', 'content-type', 'origin', 'referer', 'user-agent'
  ]

  // Copy allowed headers
  for (const [key, value] of request.headers) {
    if (allowedHeaders.includes(key.toLowerCase())) {
      proxyHeaders.set(key, value)
    }
  }

  proxyHeaders.set('Host', targetURL.hostname)

  // Set X-Forwarded-For header
  const customXForwardedFor = request.headers.get('X-My-X-Forwarded-For')
  if (customXForwardedFor) {
    proxyHeaders.set('X-Forwarded-For', customXForwardedFor)
  } else {
    proxyHeaders.set('X-Forwarded-For', generateRandomIP())
  }

  return new Request(targetURL.toString(), {
    method: request.method,
    headers: proxyHeaders,
    body: ['GET', 'HEAD'].includes(request.method) ? null : request.body
  })
}

function createProxyResponse(response, requestMethod) {
  const responseHeaders = new Headers()

  // Copy response headers (excluding problematic ones)
  for (const [key, value] of response.headers) {
    if (!['content-encoding', 'content-length', 'transfer-encoding'].includes(key.toLowerCase())) {
      responseHeaders.set(key, value)
    }
  }

  // Add CORS headers
  responseHeaders.set('Access-Control-Allow-Origin', '*')
  responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD')
  responseHeaders.set('Access-Control-Allow-Headers', '*')

  if (requestMethod === 'OPTIONS') {
    return new Response(null, { status: 204, headers: responseHeaders })
  }

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders
  })
}

function createErrorResponse(error, details, status) {
  return new Response(JSON.stringify({ error, ...details }), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

function generateRandomIP() {
  return [1, 2, 3, 4].map(() => Math.floor(Math.random() * 255) + 1).join('.')
}'''

    def create_deployment(self, name: Optional[str] = None) -> Dict:
        """Deploy a new Cloudflare Worker."""
        if not name:
            name = self._generate_worker_name()

        script_content = self._get_worker_script()
        url = f"{self.base_url}/accounts/{self.account_id}/workers/scripts/{name}"

        files = {
            'metadata': (None, json.dumps({
                "body_part": "script",
                "main_module": "worker.js"
            })),
            'script': ('worker.js', script_content, 'application/javascript')
        }

        headers = {"Authorization": f"Bearer {self.api_token}"}

        try:
            response = requests.put(url, headers=headers, files=files, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            raise FlareProxError(f"Failed to create worker: {e}")

        worker_data = response.json()

        # Enable subdomain
        subdomain_url = f"{self.base_url}/accounts/{self.account_id}/workers/scripts/{name}/subdomain"
        try:
            requests.post(subdomain_url, headers=self.headers, json={"enabled": True}, timeout=30)
        except requests.RequestException:
            pass  # Subdomain enabling is not critical

        worker_url = f"https://{name}.{self.worker_subdomain}.workers.dev"

        return {
            "name": name,
            "url": worker_url,
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "id": worker_data.get("result", {}).get("id", name)
        }

    def list_deployments(self) -> List[Dict]:
        """List all FlareProx deployments."""
        url = f"{self.base_url}/accounts/{self.account_id}/workers/scripts"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise FlareProxError(f"Failed to list workers: {e}")

        data = response.json()
        workers = []

        for script in data.get("result", []):
            name = script.get("id", "")
            if name.startswith("flareprox-"):
                workers.append({
                    "name": name,
                    "url": f"https://{name}.{self.worker_subdomain}.workers.dev",
                    "created_at": script.get("created_on", "unknown")
                })

        return workers

    def cleanup_all(self) -> None:
        """Delete all FlareProx workers."""
        workers = self.list_deployments()

        for worker in workers:
            url = f"{self.base_url}/accounts/{self.account_id}/workers/scripts/{worker['name']}"
            try:
                response = requests.delete(url, headers=self.headers, timeout=30)
                if response.status_code in [200, 404]:
                    print(f"Deleted worker: {worker['name']}")
            except requests.RequestException:
                pass


class FlareProx:
    """Main FlareProx manager class."""

    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.cloudflare = self._setup_cloudflare()
        self.endpoints_file = "flareprox_endpoints.json"

    def _load_config(self, config_file: Optional[str] = None) -> Dict:
        """Load configuration from file or environment."""
        config = {"cloudflare": {}}

        # Load from environment variables first
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")

        if api_token and account_id:
            config["cloudflare"] = {
                "api_token": api_token,
                "account_id": account_id
            }
            return config

        # Try config file
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    if "cloudflare" in file_config:
                        config["cloudflare"].update(file_config["cloudflare"])
            except (json.JSONDecodeError, IOError):
                pass

        return config

    def _setup_cloudflare(self) -> Optional[CloudflareManager]:
        """Setup Cloudflare manager if credentials are available."""
        cf_config = self.config.get("cloudflare", {})
        api_token = cf_config.get("api_token")
        account_id = cf_config.get("account_id")

        if api_token and account_id:
            return CloudflareManager(
                api_token=api_token,
                account_id=account_id
            )
        return None

    @property
    def is_configured(self) -> bool:
        """Check if FlareProx is properly configured."""
        return self.cloudflare is not None

    def _save_endpoints(self, endpoints: List[Dict]) -> None:
        """Save endpoints to local file."""
        try:
            with open(self.endpoints_file, 'w') as f:
                json.dump(endpoints, f, indent=2)
        except IOError:
            pass

    def _load_endpoints(self) -> List[Dict]:
        """Load endpoints from local file."""
        if os.path.exists(self.endpoints_file):
            try:
                with open(self.endpoints_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def sync_endpoints(self) -> List[Dict]:
        """Sync local endpoints with remote deployments."""
        if not self.cloudflare:
            return []

        try:
            endpoints = self.cloudflare.list_deployments()
            self._save_endpoints(endpoints)
            return endpoints
        except FlareProxError:
            return self._load_endpoints()

    def create_proxies(self, count: int = 1) -> Dict:
        """Create proxy endpoints."""
        if not self.cloudflare:
            raise FlareProxError("FlareProx not configured")

        print(f"\nCreating {count} FlareProx endpoint{'s' if count != 1 else ''}...")

        results = {"created": [], "failed": 0}

        for i in range(count):
            try:
                endpoint = self.cloudflare.create_deployment()
                results["created"].append(endpoint)
                print(f"  [{i+1}/{count}] {endpoint['name']} -> {endpoint['url']}")
            except FlareProxError as e:
                print(f"  Failed to create endpoint {i+1}: {e}")
                results["failed"] += 1

        # Update local cache
        self.sync_endpoints()

        total_created = len(results["created"])
        print(f"\nCreated: {total_created}, Failed: {results['failed']}")

        return results

    def list_proxies(self) -> List[Dict]:
        """List all proxy endpoints."""
        endpoints = self.sync_endpoints()

        if not endpoints:
            print("No FlareProx endpoints found")
            return []

        print(f"\nFlareProx Endpoints ({len(endpoints)} total):")
        for endpoint in endpoints:
            print(f"  - {endpoint['url']}")

        return endpoints

    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy URL in rotation."""
        endpoints = self._load_endpoints()
        if not endpoints:
            return None

        # Simple round-robin selection
        import random
        return random.choice(endpoints)["url"]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="FlareProx - Cloudflare Workers Proxy Manager")
    parser.add_argument("command", choices=["create", "list", "cleanup", "config"],
                       help="Command to execute")
    parser.add_argument("--count", type=int, default=3, help="Number of proxies to create")

    args = parser.parse_args()

    flareprox = FlareProx()

    if args.command == "config":
        print("FlareProx Configuration:")
        print("Set these environment variables:")
        print("  CLOUDFLARE_API_TOKEN=your_token")
        print("  CLOUDFLARE_ACCOUNT_ID=your_account_id")
        return

    if not flareprox.is_configured:
        print("FlareProx not configured. Set environment variables or run 'config' command.")
        return

    try:
        if args.command == "create":
            flareprox.create_proxies(args.count)
        elif args.command == "list":
            flareprox.list_proxies()
        elif args.command == "cleanup":
            confirm = input("Delete ALL FlareProx endpoints? (y/N): ")
            if confirm.lower() == 'y':
                flareprox.cloudflare.cleanup_all()
    except FlareProxError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

