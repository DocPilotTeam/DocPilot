#!/usr/bin/env python3
"""
Startup Validation Script for DocPilot Agent
Verifies all components are properly configured before starting
"""

import sys
import os
from pathlib import Path

def check_environment():
    """Check if .env file exists and required variables are set"""
    print("Checking environment configuration...")
    
    if not Path(".env").exists():
        print("⚠️  .env file not found. Copy from .env.example:")
        print("   cp .env.example .env")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
        "GITHUB_REDIRECT_URI",
        "neo4j_url",
        "neo4j_pass",
        "CELERY_BROKER_URL",
        "OPENAI_API_KEY",
        "gemini_api_key",
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✓ Environment variables configured")
    return True


def check_redis():
    """Check if Redis is accessible"""
    print("\nChecking Redis connection...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        r.ping()
        print("✓ Redis is running and accessible")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        print("   Start Redis server first:")
        print("   - macOS: brew services start redis")
        print("   - Linux: sudo systemctl start redis-server")
        print("   - Windows: redis-server.exe or WSL")
        return False


def check_neo4j():
    """Check if Neo4j is accessible"""
    print("\nChecking Neo4j connection...")
    
    try:
        from backend.db.neo4j_connect import driver
        driver.verify_connectivity()
        print("✓ Neo4j is running and accessible")
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {str(e)}")
        print("   Make sure Neo4j is running on the configured URL")
        return False


def check_imports():
    """Check if all required packages are importable"""
    print("\nChecking Python dependencies...")
    
    required_modules = [
        'fastapi',
        'celery',
        'redis',
        'neo4j',
        'openai',
        'google',
        'git',
        'pydantic',
        'dotenv',
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing Python packages: {', '.join(missing)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    print("✓ All dependencies installed")
    return True


def check_celery_config():
    """Check if Celery configuration is valid"""
    print("\nChecking Celery configuration...")
    
    try:
        from backend.celery_config import app
        
        # Try to get worker info
        from celery.app.control import Inspect
        insp = Inspect(app=app)
        
        print("✓ Celery configuration is valid")
        return True
    except Exception as e:
        print(f"❌ Celery configuration error: {str(e)}")
        return False


def check_github_config():
    """Check GitHub OAuth configuration"""
    print("\nChecking GitHub OAuth configuration...")
    
    from backend.core.config import settings
    
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        print("❌ GitHub OAuth credentials not configured")
        print("   Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env")
        return False
    
    print("✓ GitHub OAuth configured")
    return True


def main():
    """Run all checks"""
    print("=" * 50)
    print("DocPilot Agent - Startup Validation")
    print("=" * 50)
    
    checks = [
        ("Environment Variables", check_environment),
        ("Redis Connection", check_redis),
        ("Neo4j Connection", check_neo4j),
        ("Python Dependencies", check_imports),
        ("Celery Configuration", check_celery_config),
        ("GitHub OAuth Configuration", check_github_config),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"⚠️  Error checking {name}: {str(e)}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("Validation Summary")
    print("=" * 50)
    
    for name, result in results:
        status = "✓" if result else "❌"
        print(f"{status} {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! Ready to start the application.")
        print("\nStart with:")
        print("  Windows: start_all.bat")
        print("  Linux/macOS: bash start_all.sh")
        return 0
    else:
        print("\n❌ Some checks failed. Fix the issues above and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
