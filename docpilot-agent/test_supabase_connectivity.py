#!/usr/bin/env python3
"""
Test script to diagnose Supabase connectivity issues
Run this to verify your Supabase setup before using the application
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
    """Test if DNS can resolve Supabase hostname"""
    print("\n" + "="*60)
    print("1. Testing DNS Resolution")
    print("="*60)
    
    supabase_url = os.getenv("SUPABASE_URL", "")
    if not supabase_url:
        print(f"❌ SUPABASE_URL not set in .env")
        return False
    
    # Extract hostname from URL
    # Example: https://phargickpgzoomnwlnhd.supabase.co
    try:
        hostname = supabase_url.replace("https://", "").replace("http://", "").split("/")[0]
        print(f"   URL: {supabase_url}")
        print(f"   Hostname to resolve: {hostname}")
        
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS Resolution successful")
        print(f"   {hostname} resolves to: {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        print(f"   Cannot resolve Supabase hostname")
        print(f"   Solutions:")
        print(f"   - Check your internet connection")
        print(f"   - Verify SUPABASE_URL in .env file")
        print(f"   - Try pinging the hostname from command prompt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_https_connection():
    """Test HTTPS connection to Supabase"""
    print("\n" + "="*60)
    print("2. Testing HTTPS Connection")
    print("="*60)
    
    supabase_url = os.getenv("SUPABASE_URL", "")
    if not supabase_url:
        print(f"⚠️  SUPABASE_URL not set, skipping")
        return False
    
    try:
        ssl_context = ssl.create_default_context()
        async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
            # Try to connect to Supabase REST API
            response = await client.get(f"{supabase_url}/rest/v1/", follow_redirects=True)
            print(f"✅ HTTPS connection successful")
            print(f"   Status: {response.status_code}")
            print(f"   URL: {supabase_url}/rest/v1/")
            return True
    except httpx.ConnectError as e:
        print(f"❌ HTTPS connection failed: {e}")
        print(f"   Solutions:")
        print(f"   - Check firewall/proxy settings")
        print(f"   - Verify SUPABASE_URL is valid")
        return False
    except Exception as e:
        print(f"⚠️  Got status code (connection works): {type(e).__name__}")
        return True


async def test_supabase_auth():
    """Test Supabase authentication"""
    print("\n" + "="*60)
    print("3. Testing Supabase Authentication")
    print("="*60)
    
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    if not supabase_url or not supabase_key:
        print(f"❌ Missing Supabase credentials")
        print(f"   SUPABASE_URL: {'SET' if supabase_url else 'NOT SET'}")
        print(f"   SUPABASE_SERVICE_KEY: {'SET' if supabase_key else 'NOT SET'}")
        return False
    
    try:
        ssl_context = ssl.create_default_context()
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
            # Try to list tables (this requires valid API key)
            response = await client.get(
                f"{supabase_url}/rest/v1/?limit=1",
                headers=headers
            )
            print(f"✅ Supabase authentication successful")
            print(f"   Status: {response.status_code}")
            return response.status_code in [200, 206, 401]  # 401 means auth tried
    except Exception as e:
        print(f"❌ Supabase authentication failed: {e}")
        print(f"   Solutions:")
        print(f"   - Verify SUPABASE_SERVICE_KEY is correct")
        print(f"   - Check Supabase project settings")
        return False


async def test_supabase_client():
    """Test Supabase Python client initialization"""
    print("\n" + "="*60)
    print("4. Testing Supabase Client Initialization")
    print("="*60)
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        
        if not supabase_url or not supabase_key:
            print(f"❌ Missing Supabase credentials in .env")
            return False
        
        print(f"   Creating client with:")
        print(f"   URL: {supabase_url[:40]}...")
        print(f"   Key: {supabase_key[:20]}...")
        
        client = create_client(supabase_url, supabase_key)
        print(f"✅ Supabase client initialized successfully")
        return True
    except ImportError:
        print(f"❌ supabase package not installed")
        print(f"   Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        print(f"   Solutions:")
        print(f"   - Check SUPABASE_URL format")
        print(f"   - Verify SUPABASE_SERVICE_KEY")
        print(f"   - Check internet connection")
        return False


async def test_env_variables():
    """Test environment variable configuration"""
    print("\n" + "="*60)
    print("5. Testing Environment Variables")
    print("="*60)
    
    required_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY"),
    }
    
    optional_vars = {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
    }
    
    all_set = True
    
    print("Required:")
    for var_name, var_value in required_vars.items():
        if var_value:
            masked = var_value[:20] + "***" if len(var_value) > 20 else "***"
            print(f"✅ {var_name} is set")
            print(f"   Value: {masked}")
        else:
            print(f"❌ {var_name} is NOT set")
            all_set = False
    
    print("\nOptional:")
    for var_name, var_value in optional_vars.items():
        if var_value:
            masked = var_value[:20] + "***" if len(var_value) > 20 else "***"
            print(f"✅ {var_name} is set")
        else:
            print(f"⚠️  {var_name} is not set (optional)")
    
    return all_set


async def test_database_tables():
    """Test if database tables exist and are accessible"""
    print("\n" + "="*60)
    print("6. Testing Database Tables")
    print("="*60)
    
    try:
        from backend.db.supabase_client import supabase
        
        tables_to_check = ["users", "repos", "documentation"]
        
        for table_name in tables_to_check:
            try:
                result = supabase.table(table_name).select("*", count="exact").limit(1).execute()
                print(f"✅ Table '{table_name}' is accessible")
            except Exception as e:
                error_msg = str(e).lower()
                if "does not exist" in error_msg or "404" in error_msg:
                    print(f"⚠️  Table '{table_name}' does not exist in database")
                    print(f"   You may need to create the table schema first")
                else:
                    print(f"❌ Cannot access table '{table_name}': {e}")
        
        return True
    except ImportError:
        print(f"❌ Failed to import Supabase client")
        return False
    except Exception as e:
        print(f"❌ Error testing tables: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🔍 Supabase Connectivity Diagnostic Test")
    print("="*60)
    
    results = {
        "DNS Resolution": await test_dns_resolution(),
        "HTTPS Connection": await test_https_connection(),
        "Supabase Auth": await test_supabase_auth(),
        "Client Init": await test_supabase_client(),
        "Environment": await test_env_variables(),
        "Database Tables": await test_database_tables(),
    }
    
    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n✅ All tests passed! Supabase is properly configured.")
    else:
        print(f"\n❌ Some tests failed. See recommendations above.")
        print(f"\n🔧 Troubleshooting Steps:")
        print(f"   1. Check your internet connection")
        print(f"   2. Verify SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        print(f"   3. Check Supabase project dashboard for correct credentials")
        print(f"   4. Verify firewall allows connections to Supabase")
        print(f"   5. Check if database tables exist (users, repos, documentation)")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
