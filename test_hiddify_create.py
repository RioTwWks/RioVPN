"""Test Hiddify user creation."""

import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import ssl
import time
import uuid


async def test_create_user():
    """Test creating a Hiddify user."""
    
    base_panel_url = "https://rio2skadi.pro/aav6Vcx7HYsY6hnk5K2226jQ9ZDS2N"
    api_key = "c2415201-e537-4681-8dea-febff35272cd"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = ProxyConnector.from_url("socks5://127.0.0.1:10808", ssl=ssl_context)
    
    headers = {"Hiddify-API-Key": api_key}
    
    # Test user creation with minimal fields
    test_username = f"test_{uuid.uuid4().hex[:8]}"
    expiry_time = int(time.time() + 30 * 24 * 60 * 60)  # 30 days
    
    print(f"Testing user creation: {test_username}")
    print(f"Expiry: {expiry_time} ({time.strftime('%Y-%m-%d', time.localtime(expiry_time))})")
    
    # Try different request formats
    test_configs = [
        {
            "name": "Minimal (username only)",
            "data": {"username": test_username + "_min"}
        },
        {
            "name": "With enabled",
            "data": {"username": test_username + "_en", "enabled": True}
        },
        {
            "name": "With expiry",
            "data": {"username": test_username + "_exp", "expiry_time": expiry_time}
        },
        {
            "name": "Full config",
            "data": {
                "username": test_username + "_full",
                "enabled": True,
                "expiry_time": expiry_time,
                "data_limit": 0,
                "mode": "full"
            }
        },
    ]
    
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        for config in test_configs:
            print(f"\n{config['name']}:")
            print(f"  Data: {config['data']}")
            
            try:
                async with session.post(
                    f"{base_panel_url}/api/v2/admin/user/",
                    json=config['data']
                ) as resp:
                    print(f"  Status: {resp.status}")
                    response = await resp.json()
                    print(f"  Response: {response}")
                    
                    if resp.status == 200 or resp.status == 201:
                        print(f"  SUCCESS!")
                        # Clean up - delete the user
                        user_uuid = response.get('uuid') or response.get('data', {}).get('uuid')
                        if user_uuid:
                            print(f"  Deleting test user {user_uuid}...")
                            async with session.delete(f"{base_panel_url}/api/v2/admin/user/{user_uuid}") as del_resp:
                                print(f"  Delete status: {del_resp.status}")
                    
            except Exception as e:
                print(f"  ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_create_user())
