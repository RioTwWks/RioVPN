#!/usr/bin/env python3
"""
RioVPN Web Routes
"""

from aiohttp import web
from logger import logger


async def register_web_routes(router):
    """
    Register web routes for the application
    """
    try:
        # Add basic health check route
        async def health_check(request):
            return web.json_response({
                "status": "ok",
                "service": "riovpn-bot",
                "timestamp": "2024-01-01T00:00:00Z"
            })
        
        router.add_get('/health', health_check)
        
        # Add basic info route
        async def info(request):
            return web.json_response({
                "name": "RioVPN Bot",
                "version": "1.0.0",
                "description": "Telegram bot for VPN service management"
            })
        
        router.add_get('/info', info)
        
        logger.info("✅ Web routes registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to register web routes: {e}")
        return False


if __name__ == "__main__":
    # Test the function
    app = web.Application()
    register_web_routes(app.router)
    print("Web routes module loaded successfully")
