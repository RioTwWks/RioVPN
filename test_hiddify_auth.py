"""Test Hiddify API with different auth methods."""

import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import ssl


async def test_hiddify_api():
    """Test Hiddify API with different authentication methods."""
    
    base_url = "https://rio2skadi.pro/aav6Vcx7HYsY6hnk5K2226jQ9ZDS2N/api/v2"
    
    # API key from .env
    api_key = "c2415201-e537-4681-8dea-febff35272cd"
    
    # Create proxy connector
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = ProxyConnector.from_url(
        "socks5://127.0.0.1:10808",
        ssl=ssl_context
    )
    
    print("Testing Hiddify API authentication methods...\n")
    
    # Test 1: Hiddify-API-Key header
    print("1. Testing 'Hiddify-API-Key' header...")
    headers1 = {"Hiddify-API-Key": api_key}
    async with aiohttp.ClientSession(headers=headers1, connector=connector) as session:
        async with session.get(f"{base_url}/admin/users/") as resp:
            print(f"   Status: {resp.status}")
            response = await resp.json()
            print(f"   Response: {response}\n")
    
    # Test 2: Authorization Bearer
    print("2. Testing 'Authorization: Bearer' header...")
    headers2 = {"Authorization": f"Bearer {api_key}"}
    async with aiohttp.ClientSession(headers=headers2, connector=connector) as session:
        async with session.get(f"{base_url}/admin/users/") as resp:
            print(f"   Status: {resp.status}")
            response = await resp.json()
            print(f"   Response: {response}\n")
    
    # Test 3: X-API-Key header
    print("3. Testing 'X-API-Key' header...")
    headers3 = {"X-API-Key": api_key}
    async with aiohttp.ClientSession(headers=headers3, connector=connector) as session:
        async with session.get(f"{base_url}/admin/users/") as resp:
            print(f"   Status: {resp.status}")
            response = await resp.json()
            print(f"   Response: {response}\n")
    
    # Test 4: No auth - check if endpoint exists
    print("4. Testing without auth (check endpoint)...")
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(f"{base_url}/admin/users/") as resp:
            print(f"   Status: {resp.status}")
            if resp.status == 401:
                print("   Response: Authentication required\n")
            else:
                response = await resp.json()
                print(f"   Response: {response}\n")
    
    print("Done!")


if __name__ == "__main__":
    asyncio.run(test_hiddify_api())
