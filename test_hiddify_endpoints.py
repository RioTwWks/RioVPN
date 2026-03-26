"""Test Hiddify API endpoints."""

import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import ssl


async def test_endpoints():
    """Test different Hiddify API endpoints."""
    
    base_panel_url = "https://rio2skadi.pro/aav6Vcx7HYsY6hnk5K2226jQ9ZDS2N"
    api_key = "c2415201-e537-4681-8dea-febff35272cd"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = ProxyConnector.from_url("socks5://127.0.0.1:10808", ssl=ssl_context)
    
    headers = {"Hiddify-API-Key": api_key}
    
    endpoints_to_test = [
        "/api/v2/admin/users/",
        "/api/v2/admin/user/",
        "/admin/users/",
        "/admin/user/",
        "/api/admin/users/",
        "/openapi.json",
        "/",
    ]
    
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        for endpoint in endpoints_to_test:
            url = f"{base_panel_url}{endpoint}"
            try:
                async with session.get(url) as resp:
                    print(f"{endpoint:30s} -> {resp.status}")
                    if resp.status == 200:
                        print(f"   ✓ Working!")
                        if endpoint.endswith('.json'):
                            data = await resp.json()
                            print(f"   Keys: {list(data.keys())[:5]}")
            except Exception as e:
                print(f"{endpoint:30s} -> ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
