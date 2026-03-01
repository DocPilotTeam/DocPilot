#!/usr/bin/env python3
"""
Test script to diagnose GitHub API connectivity issues
Run this to verify your network setup before using GitHub OAuth
"""

import asyncio
import httpx
import ssl
import socket
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

async def test_dns_resolution():
    """Test if DNS can resolve github.com"""
    print("\n" + "="*60)
    print("1. Testing DNS Resolution")
    print("="*60)
    
    try:
        ip = socket.gethostbyname("github.com")
        print(f"✅ DNS Resolution successful")
        print(f"   github.com resolves to: {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        print(f"   Error code 11001: Cannot resolve github.com")
        print(f"   Solutions:")
        print(f"   - Check your internet connection")
        print(f"   - Try pinging github.com from command prompt")
        print(f"   - Check firewall/proxy settings")
        return False


async def test_https_connection():
    """Test basic HTTPS connection to GitHub"""
    print("\n" + "="*60)
    print("2. Testing HTTPS Connection")
    print("="*60)
    
    try:
        ssl_context = ssl.create_default_context()
        async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
            response = await client.get("https://api.github.com", follow_redirects=True)
            print(f"✅ HTTPS connection successful")
            print(f"   Status: {response.status_code}")
            return True
    except httpx.ConnectError as e:
        print(f"❌ HTTPS connection failed: {e}")
        print(f"   Solutions:")
        print(f"   - Check firewall/proxy settings")
        print(f"   - Try https://github.com in browser")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_github_oauth_endpoint():
    """Test GitHub OAuth endpoint"""
    print("\n" + "="*60)
    print("3. Testing GitHub OAuth Endpoint")
    print("="*60)
    
    try:
        ssl_context = ssl.create_default_context()
        async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": "test",
                    "client_secret": "test",
                    "code": "test"
                }
            )
            print(f"✅ OAuth endpoint reachable")
            print(f"   Status: {response.status_code}")
            return True
    except httpx.ConnectError as e:
        print(f"❌ Cannot reach OAuth endpoint: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Got response (endpoint reachable): {type(e).__name__}")
        return True


async def test_github_config():
    """Test GitHub configuration"""
    print("\n" + "="*60)
    print("4. Testing GitHub Configuration")
    print("="*60)
    
    from backend.core.config import settings
    
    required_vars = {
        "GITHUB_CLIENT_ID": settings.GITHUB_CLIENT_ID,
        "GITHUB_CLIENT_SECRET": settings.GITHUB_CLIENT_SECRET,
        "GITHUB_REDIRECT_URI": settings.GITHUB_REDIRECT_URI,
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            masked = var_value[:10] + "***" if len(var_value) > 10 else "***"
            print(f"✅ {var_name} is set")
            print(f"   Value: {masked}")
        else:
            print(f"❌ {var_name} is NOT set")
            all_set = False
    
    return all_set


async def test_proxy_settings():
    """Check if there's a system proxy configured"""
    print("\n" + "="*60)
    print("5. Testing Proxy Settings")
    print("="*60)
    
    proxy_env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"]
    has_proxy = False
    
    for var in proxy_env_vars:
        value = os.environ.get(var) or os.environ.get(var.lower())
        if value:
            print(f"⚠️  {var} is set: {value}")
            has_proxy = True
    
    if not has_proxy:
        print(f"✅ No proxy environment variables detected")
    
    return not has_proxy or "github" in os.environ.get("NO_PROXY", "").lower()


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🔍 GitHub Connectivity Diagnostic Test")
    print("="*60)
    
    results = {
        "DNS Resolution": await test_dns_resolution(),
        "HTTPS Connection": await test_https_connection(),
        "OAuth Endpoint": await test_github_oauth_endpoint(),
        "GitHub Config": await test_github_config(),
        "Proxy Settings": await test_proxy_settings(),
    }
    
    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n✅ All tests passed! GitHub OAuth should work.")
    else:
        print(f"\n❌ Some tests failed. See recommendations above.")
        print(f"\n🔧 Troubleshooting Steps:")
        print(f"   1. Check internet connection")
        print(f"   2. Verify firewall allows github.com")
        print(f"   3. Check corporate proxy settings")
        print(f"   4. Try accessing https://github.com in browser")
        print(f"   5. Verify GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
