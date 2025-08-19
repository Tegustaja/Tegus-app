#!/usr/bin/env python3
"""
Main test runner for the Tegus project
Runs all test suites including the new authentication tests
"""

import os
import sys
import subprocess
import importlib.util

def run_python_test(test_file):
    """Run a Python test file"""
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ {test_file} passed")
            return True
        else:
            print(f"❌ {test_file} failed")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_file} timed out")
        return False
    except Exception as e:
        print(f"💥 {test_file} crashed: {e}")
        return False

def run_authentication_tests():
    """Run the authentication test suite"""
    print("\n🔐 Running Authentication Tests...")
    print("=" * 50)
    
    auth_test_file = "tests/test_authentication.py"
    if os.path.exists(auth_test_file):
        return run_python_test(auth_test_file)
    else:
        print(f"⚠️ Authentication test file not found: {auth_test_file}")
        return False

def run_existing_tests():
    """Run existing test files"""
    print("\n🧪 Running Existing Tests...")
    print("=" * 50)
    
    test_files = [
        "test.py",
        "test_admin_system.py",
        "test_adaptive_learning.py",
        "test_supabase_connection.py",
        "test_table_structure.py",
        "test_signup.py"
    ]
    
    passed = 0
    total = 0
    
    for test_file in test_files:
        if os.path.exists(test_file):
            total += 1
            if run_python_test(test_file):
                passed += 1
        else:
            print(f"⚠️ Test file not found: {test_file}")
    
    print(f"\n📊 Existing Tests: {passed}/{total} passed")
    return passed, total

def main():
    """Run all tests"""
    print("🚀 Tegus Project Test Suite")
    print("=" * 50)
    
    # Run authentication tests
    auth_passed = run_authentication_tests()
    
    # Run existing tests
    existing_passed, existing_total = run_existing_tests()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = 1 + existing_total
    total_passed = (1 if auth_passed else 0) + existing_passed
    
    print(f"Authentication Tests: {'✅ PASSED' if auth_passed else '❌ FAILED'}")
    print(f"Existing Tests: {existing_passed}/{existing_total} passed")
    print(f"Overall: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n🎉 All test suites passed!")
        return True
    else:
        print("\n⚠️ Some test suites failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 