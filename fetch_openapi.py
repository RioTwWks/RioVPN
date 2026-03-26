"""Fetch Hiddify OpenAPI schema."""

import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import ssl
import json


async def fetch_openapi():
    """Fetch and save OpenAPI schema."""
    
    base_panel_url = "https://rio2skadi.pro/aav6Vcx7HYsY6hnk5K2226jQ9ZDS2N"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = ProxyConnector.from_url("socks5://127.0.0.1:10808", ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Try different OpenAPI endpoints
        endpoints = [
            "/api/openapi.json",
            "/api/v2/openapi.json",
            "/openapi.json",
            "/api/docs/json",
        ]
        
        for endpoint in endpoints:
            url = f"{base_panel_url}{endpoint}"
            print(f"Trying {endpoint}...")
            
            try:
                async with session.get(url) as resp:
                    print(f"  Status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        filename = f"hiddify_openapi_{endpoint.replace('/', '_')}.json"
                        with open(filename, 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"  Saved to {filename}")
                        
                        # Show available endpoints
                        if 'paths' in data:
                            print(f"  Available paths: {list(data['paths'].keys())[:10]}")
                        
                        # Show UserCreate schema
                        if 'components' in data and 'schemas' in data['components']:
                            schemas = data['components']['schemas']
                            if 'UserCreate' in schemas:
                                print(f"\n  UserCreate schema:")
                                user_create = schemas['UserCreate']
                                if 'properties' in user_create:
                                    for prop, details in user_create['properties'].items():
                                        required = prop in user_create.get('required', [])
                                        prop_type = details.get('type', 'unknown')
                                        print(f"    {prop}: {prop_type} {'(required)' if required else '(optional)'}")
                        return
                        
            except Exception as e:
                print(f"  ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(fetch_openapi())
