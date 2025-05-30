#!/usr/bin/env python3
"""
test_emergency_fix.py - Quick test to verify emergency keyword detection fix
"""

def test_emergency_keywords_standalone():
    """Test emergency keywords without Flask context."""
    print("🧪 Testing emergency keyword detection standalone...")
    
    # Test the function directly
    from app import detect_emergency_keywords
    
    test_cases = [
        ("I have severe chest pain", True),
        ("difficulty breathing", True),
        ("I think I'm having a heart attack", True),
        ("I have unconscious episodes", True),
        ("severe bleeding", True),
        ("allergic reaction", True),
        ("stroke symptoms", True),
        ("I have a mild headache", False),
        ("I feel tired", False),
        ("minor cut", False)
    ]
    
    passed = 0
    failed = 0
    
    for text, expected in test_cases:
        result = detect_emergency_keywords(text)
        if result == expected:
            print(f"✅ '{text}' -> {result} (expected {expected})")
            passed += 1
        else:
            print(f"❌ '{text}' -> {result} (expected {expected})")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0

def test_emergency_keywords_with_app():
    """Test emergency keywords with Flask app context."""
    print("\n🧪 Testing emergency keyword detection with Flask context...")
    
    from app import create_app, detect_emergency_keywords
    
    app = create_app('testing')
    
    with app.app_context():
        test_cases = [
            ("I have severe chest pain", True),
            ("difficulty breathing", True),
            ("I think I'm having a heart attack", True),
            ("I have a mild headache", False),
            ("I feel tired", False)
        ]
        
        passed = 0
        failed = 0
        
        for text, expected in test_cases:
            result = detect_emergency_keywords(text)
            if result == expected:
                print(f"✅ '{text}' -> {result} (expected {expected})")
                passed += 1
            else:
                print(f"❌ '{text}' -> {result} (expected {expected})")
                failed += 1
        
        print(f"\n📊 Results: {passed} passed, {failed} failed")
        return failed == 0

def main():
    """Main test function."""
    print("🔍 Emergency Keyword Detection Fix Verification")
    print("=" * 50)
    
    # Test without Flask context
    standalone_success = test_emergency_keywords_standalone()
    
    # Test with Flask context
    app_context_success = test_emergency_keywords_with_app()
    
    print("\n" + "=" * 50)
    if standalone_success and app_context_success:
        print("🎉 All emergency keyword tests passed!")
        print("✅ The fix is working correctly.")
        return 0
    else:
        print("❌ Some tests failed.")
        if not standalone_success:
            print("   - Standalone test failed")
        if not app_context_success:
            print("   - App context test failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())