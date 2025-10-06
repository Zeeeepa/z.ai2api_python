#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI entrypoint with startup diagnostics, provider status, and model discovery
"""

import sys
import asyncio
import argparse
from typing import Dict, List, Any, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Warning: 'rich' library not installed. Install with: pip install rich")

from app import __version__
from app.core.config import settings
from app.providers.base import provider_registry
from app.providers import initialize_providers
from app.utils.logger import get_logger
from app.utils.flareprox_manager import get_flareprox_manager, initialize_flareprox

logger = get_logger()


class CLIDisplay:
    """Handles formatted console output"""
    
    def __init__(self, use_rich: bool = True):
        self.use_rich = use_rich and RICH_AVAILABLE
        if self.use_rich:
            self.console = Console()
    
    def print_banner(self):
        """Display startup banner"""
        if self.use_rich:
            banner_text = f"""
[bold cyan]z-ai2api-python[/bold cyan] [dim]v{__version__}[/dim]
[yellow]OpenAI-Compatible Multi-Provider API Server[/yellow]

[dim]Supporting: Z.AI, K2Think, LongCat, and more[/dim]
            """.strip()
            panel = Panel(
                banner_text,
                border_style="cyan",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print("=" * 60)
            print(f"  z-ai2api-python v{__version__}")
            print("  OpenAI-Compatible Multi-Provider API Server")
            print("  Supporting: Z.AI, K2Think, LongCat")
            print("=" * 60)
    
    def print_config_summary(self):
        """Display configuration summary"""
        config_info = [
            f"Host: {settings.HOST if hasattr(settings, 'HOST') else '0.0.0.0'}",
            f"Port: {settings.LISTEN_PORT}",
            f"Debug: {'Enabled' if settings.DEBUG_LOGGING else 'Disabled'}",
            f"Anonymous Mode: {'Enabled' if settings.ANONYMOUS_MODE else 'Disabled'}",
            f"Tool Support: {'Enabled' if settings.TOOL_SUPPORT else 'Disabled'}",
        ]
        
        if self.use_rich:
            self.console.print("\n[bold]📋 Configuration[/bold]")
            for info in config_info:
                self.console.print(f"  • {info}")
        else:
            print("\n📋 Configuration:")
            for info in config_info:
                print(f"  • {info}")
    
    def print_connection_info(self):
        """Display connection information"""
        host = settings.HOST if hasattr(settings, 'HOST') else '0.0.0.0'
        port = settings.LISTEN_PORT
        base_url = f"http://{host}:{port}"
        
        endpoints = [
            ("Chat Completions", f"{base_url}/v1/chat/completions"),
            ("List Models", f"{base_url}/v1/models"),
            ("API Docs", f"{base_url}/docs"),
        ]
        
        if self.use_rich:
            self.console.print("\n[bold]🌐 API Endpoints[/bold]")
            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Endpoint", style="cyan")
            table.add_column("URL", style="white")
            
            for name, url in endpoints:
                table.add_row(name, url)
            
            self.console.print(table)
            
            # Highlight base URL
            panel = Panel(
                f"[bold green]Server running at: {base_url}[/bold green]",
                border_style="green",
                padding=(0, 2)
            )
            self.console.print(panel)
            
            # Show FlareProx status if enabled
            flareprox = get_flareprox_manager()
            stats = flareprox.get_stats()
            if stats["enabled"] and stats["initialized"]:
                self.console.print(f"\n[bold yellow]🔥 FlareProx Status[/bold yellow]")
                flareprox_info = [
                    f"Status: [green]Active[/green]",
                    f"Proxies: {stats['proxy_count']}",
                    f"Requests: {stats['request_count']}/{stats['rotate_interval']}",
                    f"Auto-rotate: {'Enabled' if stats['auto_rotate'] else 'Disabled'}"
                ]
                for info in flareprox_info:
                    self.console.print(f"  • {info}")
        else:
            print("\n🌐 API Endpoints:")
            for name, url in endpoints:
                print(f"  {name}: {url}")
            print(f"\n✅ Server running at: {base_url}")
            
            # Show FlareProx status if enabled
            flareprox = get_flareprox_manager()
            stats = flareprox.get_stats()
            if stats["enabled"] and stats["initialized"]:
                print(f"\n🔥 FlareProx Status:")
                print(f"  • Status: Active")
                print(f"  • Proxies: {stats['proxy_count']}")
                print(f"  • Auto-rotate: {'Enabled' if stats['auto_rotate'] else 'Disabled'}")
    
    def print_provider_status(self, provider_data: List[Dict[str, Any]]):
        """Display provider status table"""
        if self.use_rich:
            self.console.print("\n[bold]🤖 Provider Status[/bold]")
            table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
            table.add_column("Provider", style="cyan", width=15)
            table.add_column("Status", style="white", width=12)
            table.add_column("Models", justify="right", style="yellow", width=8)
            table.add_column("Features", style="white")
            
            for provider in provider_data:
                status_icon = "✅" if provider["available"] else "❌"
                status = f"{status_icon} {provider['status']}"
                table.add_row(
                    provider["name"],
                    status,
                    str(provider["model_count"]),
                    provider["features"]
                )
            
            self.console.print(table)
        else:
            print("\n🤖 Provider Status:")
            print("-" * 70)
            for provider in provider_data:
                status_icon = "✅" if provider["available"] else "❌"
                print(f"  {provider['name']:<15} {status_icon} {provider['status']:<10} "
                      f"Models: {provider['model_count']:<3} {provider['features']}")
            print("-" * 70)
    
    def print_models_table(self, models_by_provider: Dict[str, List[str]]):
        """Display available models grouped by provider"""
        if self.use_rich:
            self.console.print("\n[bold]📚 Available Models[/bold]")
            
            for provider_name, models in models_by_provider.items():
                if models:
                    table = Table(
                        title=f"[cyan]{provider_name}[/cyan]",
                        show_header=True,
                        header_style="bold yellow",
                        box=box.SIMPLE_HEAD
                    )
                    table.add_column("#", justify="right", style="dim", width=4)
                    table.add_column("Model Name", style="green")
                    
                    for idx, model in enumerate(models, 1):
                        table.add_row(str(idx), model)
                    
                    self.console.print(table)
        else:
            print("\n📚 Available Models:")
            print("=" * 60)
            for provider_name, models in models_by_provider.items():
                if models:
                    print(f"\n  {provider_name}:")
                    for idx, model in enumerate(models, 1):
                        print(f"    {idx}. {model}")
            print("=" * 60)
    
    def print_error(self, message: str):
        """Display error message"""
        if self.use_rich:
            self.console.print(f"[bold red]❌ Error: {message}[/bold red]")
        else:
            print(f"❌ Error: {message}")
    
    def print_info(self, message: str):
        """Display info message"""
        if self.use_rich:
            self.console.print(f"[cyan]ℹ️  {message}[/cyan]")
        else:
            print(f"ℹ️  {message}")
    
    def print_success(self, message: str):
        """Display success message"""
        if self.use_rich:
            self.console.print(f"[bold green]✅ {message}[/bold green]")
        else:
            print(f"✅ {message}")


async def discover_provider_models() -> Dict[str, List[str]]:
    """Discover models from all registered providers"""
    models_by_provider = {}
    
    # Initialize providers first
    initialize_providers()
    
    # Get all providers from registry
    for provider_name in provider_registry.list_providers():
        provider = provider_registry.get_provider_by_name(provider_name)
        if provider:
            try:
                # Get supported models from provider
                models = provider.get_supported_models()
                models_by_provider[provider_name.upper()] = sorted(models)
            except Exception as e:
                logger.error(f"Error getting models from {provider_name}: {e}")
                models_by_provider[provider_name.upper()] = []
    
    return models_by_provider


def get_provider_features(provider_name: str) -> str:
    """Get feature summary for a provider"""
    features_map = {
        "zai": "Stream, Tools, Search, Thinking",
        "k2think": "Stream, Reasoning",
        "longcat": "Stream, Search",
    }
    return features_map.get(provider_name.lower(), "Unknown")


async def check_provider_status() -> List[Dict[str, Any]]:
    """Check status of all providers"""
    provider_data = []
    
    for provider_name in provider_registry.list_providers():
        provider = provider_registry.get_provider_by_name(provider_name)
        if provider:
            try:
                models = provider.get_supported_models()
                provider_data.append({
                    "name": provider_name.upper(),
                    "status": "Available",
                    "available": True,
                    "model_count": len(models),
                    "features": get_provider_features(provider_name)
                })
            except Exception as e:
                provider_data.append({
                    "name": provider_name.upper(),
                    "status": "Error",
                    "available": False,
                    "model_count": 0,
                    "features": str(e)[:30]
                })
    
    return provider_data


async def run_startup_diagnostics(display: CLIDisplay, verbose: bool = True):
    """Run complete startup diagnostics"""
    if verbose:
        display.print_banner()
        display.print_config_summary()
    
    # Initialize FlareProx if enabled
    await initialize_flareprox()
    
    # Check provider status
    if display.use_rich and verbose:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=display.console,
        ) as progress:
            task = progress.add_task("Checking providers...", total=None)
            provider_status = await check_provider_status()
            progress.update(task, completed=True)
    else:
        if verbose:
            display.print_info("Checking providers...")
        provider_status = await check_provider_status()
    
    if verbose:
        display.print_provider_status(provider_status)
    
    # Discover models
    if display.use_rich and verbose:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=display.console,
        ) as progress:
            task = progress.add_task("Discovering models...", total=None)
            models_by_provider = await discover_provider_models()
            progress.update(task, completed=True)
    else:
        if verbose:
            display.print_info("Discovering models...")
        models_by_provider = await discover_provider_models()
    
    if verbose:
        display.print_models_table(models_by_provider)
        display.print_connection_info()
    
    return provider_status, models_by_provider


async def async_main(args):
    """Async main function"""
    display = CLIDisplay(use_rich=not args.no_color)
    
    try:
        if args.check:
            # Health check mode - just check providers
            display.print_info("Running health check...")
            provider_status, models = await run_startup_diagnostics(display, verbose=True)
            
            # Check if any providers are available
            available_count = sum(1 for p in provider_status if p["available"])
            total_models = sum(len(m) for m in models.values())
            
            if available_count > 0:
                display.print_success(
                    f"Health check passed: {available_count} providers, {total_models} models"
                )
                return 0
            else:
                display.print_error("Health check failed: No providers available")
                return 1
        
        elif args.list_models:
            # Just list models
            models_by_provider = await discover_provider_models()
            display.print_models_table(models_by_provider)
            return 0
        
        else:
            # Normal startup - run diagnostics then start server
            await run_startup_diagnostics(display, verbose=True)
            
            # Import and start the server
            from main import run_server
            display.print_info("\nStarting server...\n")
            run_server()
            
    except KeyboardInterrupt:
        display.print_info("\n\nShutdown requested by user")
        return 0
    except Exception as e:
        display.print_error(f"Startup failed: {e}")
        logger.exception("Startup error")
        return 1


def main():
    """Main CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="z-ai2api-python: OpenAI-compatible multi-provider API server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Start the server
  %(prog)s --check            # Health check only
  %(prog)s --list-models      # List available models
  %(prog)s --no-color         # Disable colored output
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"z-ai2api-python {__version__}"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run health check and exit"
    )
    
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models and exit"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    args = parser.parse_args()
    
    # Run async main
    try:
        exit_code = asyncio.run(async_main(args))
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
