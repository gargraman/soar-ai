
#!/usr/bin/env python3
"""
Test runner script for the AI-Driven Agentic Cybersecurity Application
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests with proper configuration"""
    
    print("🧪 Running AI Cybersecurity Application Tests")
    print("=" * 50)
    
    # Set environment variables for testing
    os.environ["PYTHONPATH"] = "."
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    
    # Test commands to run
    test_commands = [
        # Unit tests
        ["python", "-m", "pytest", "tests/test_client/", "-v", "--tb=short"],
        ["python", "-m", "pytest", "tests/test_servers/", "-v", "--tb=short"],
        
        # Integration tests
        ["python", "-m", "pytest", "tests/test_integration/", "-v", "--tb=short"],
        
        # All tests with coverage (if coverage is installed)
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "--maxfail=5"]
    ]
    
    for i, cmd in enumerate(test_commands[:-1], 1):  # Skip the last comprehensive test
        print(f"\n📋 Running Test Suite {i}/{len(test_commands)-1}")
        print(f"Command: {' '.join(cmd)}")
        print("-" * 30)
        
        try:
            result = subprocess.run(cmd, capture_output=False, text=True)
            if result.returncode != 0:
                print(f"❌ Test suite {i} failed with return code {result.returncode}")
                return False
            else:
                print(f"✅ Test suite {i} passed")
        except FileNotFoundError:
            print(f"❌ pytest not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"])
            result = subprocess.run(cmd, capture_output=False, text=True)
            if result.returncode != 0:
                print(f"❌ Test suite {i} failed after installing pytest")
                return False
    
    # Run comprehensive test suite
    print(f"\n🎯 Running Comprehensive Test Suite")
    print("-" * 40)
    
    try:
        result = subprocess.run(test_commands[-1], capture_output=False, text=True)
        if result.returncode == 0:
            print("\n🎉 All tests passed successfully!")
            return True
        else:
            print(f"\n❌ Some tests failed (return code: {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def install_test_dependencies():
    """Install test dependencies if not present"""
    
    print("📦 Installing test dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pytest", "pytest-asyncio", "httpx"
        ], check=True)
        print("✅ Test dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

if __name__ == "__main__":
    print("AI-Driven Agentic Cybersecurity Application - Test Suite")
    print("=" * 60)
    
    # Check if we need to install dependencies
    try:
        import pytest
        import httpx
    except ImportError:
        if not install_test_dependencies():
            sys.exit(1)
    
    # Run the tests
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎊 Test run completed successfully!")
        print("\n📊 Test Coverage Summary:")
        print("   • Client components: MCPClient, EventProcessor")
        print("   • Server components: VirusTotal, ServiceNow, CyberReason, Custom REST")
        print("   • Integration flows: End-to-end workflows, conditional logic")
        print("   • Error handling: Dependency failures, API errors")
        sys.exit(0)
    else:
        print("💥 Test run failed!")
        print("\n🔍 Check the output above for specific test failures")
        print("   • Review failed assertions")
        print("   • Check mock configurations")
        print("   • Verify async/await patterns")
        sys.exit(1)
