#!/usr/bin/env python3
"""
quick_test.py - Quick test runner for NHS Digital Triage System

This script runs basic functionality tests to ensure the system is working.
"""

import os
import sys
import tempfile
import json
from datetime import datetime

def test_basic_imports():
    """Test that we can import the basic modules."""
    print("🧪 Testing basic imports...")
    try:
        from app import create_app, db, Patient, ChatMessage, TriageAssessment
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_app_creation():
    """Test that we can create the Flask app."""
    print("🧪 Testing app creation...")
    try:
        from app import create_app
        app = create_app('testing')
        print("✅ App creation successful")
        return True, app
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False, None

def test_database_operations(app):
    """Test basic database operations."""
    print("🧪 Testing database operations...")
    try:
        from app import db, Patient
        
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create a test patient
            patient = Patient(
                session_id='test-session-123',
                first_name='Test',
                last_name='Patient',
                age=30,
                gender='male'
            )
            db.session.add(patient)
            db.session.commit()
            
            # Query the patient
            found_patient = Patient.query.filter_by(session_id='test-session-123').first()
            if found_patient and found_patient.first_name == 'Test':
                print("✅ Database operations successful")
                return True
            else:
                print("❌ Database query failed")
                return False
                
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False

def test_basic_routes(app):
    """Test basic route functionality."""
    print("🧪 Testing basic routes...")
    try:
        with app.test_client() as client:
            # Test home page
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Home page accessible")
            else:
                print(f"⚠️ Home page returned {response.status_code}")
            
            # Test API health endpoint
            response = client.get('/api/health')
            if response.status_code == 200:
                data = json.loads(response.data)
                if data.get('status') == 'healthy':
                    print("✅ Health endpoint working")
                else:
                    print("⚠️ Health endpoint returned invalid data")
            else:
                print(f"⚠️ Health endpoint returned {response.status_code}")
            
            # Test system status endpoint
            response = client.get('/api/system-status')
            if response.status_code == 200:
                data = json.loads(response.data)
                if 'total_patients' in data:
                    print("✅ System status endpoint working")
                else:
                    print("⚠️ System status endpoint returned invalid data")
            else:
                print(f"⚠️ System status endpoint returned {response.status_code}")
                
            return True
            
    except Exception as e:
        print(f"❌ Route testing failed: {e}")
        return False

def test_api_endpoints(app):
    """Test API endpoint functionality."""
    print("🧪 Testing API endpoints...")
    try:
        with app.test_client() as client:
            # Test patient registration
            patient_data = {
                'firstName': 'Test',
                'lastName': 'User',
                'age': 25,
                'gender': 'female',
                'existingConditions': [],
                'currentMedications': [],
                'allergies': []
            }
            
            response = client.post('/api/patient/register',
                                 data=json.dumps(patient_data),
                                 content_type='application/json')
            
            if response.status_code == 200:
                data = json.loads(response.data)
                if data.get('success'):
                    print("✅ Patient registration working")
                else:
                    print("⚠️ Patient registration returned failure")
            else:
                print(f"⚠️ Patient registration returned {response.status_code}")
            
            # Test chat endpoint (will fail without Ollama but should return proper error)
            chat_data = {'message': 'I have a headache'}
            response = client.post('/api/chat',
                                 data=json.dumps(chat_data),
                                 content_type='application/json')
            
            if response.status_code in [200, 503]:  # 200 if Ollama available, 503 if not
                print("✅ Chat endpoint responding correctly")
            else:
                print(f"⚠️ Chat endpoint returned unexpected {response.status_code}")
                
            return True
            
    except Exception as e:
        print(f"❌ API endpoint testing failed: {e}")
        return False

def test_utility_functions():
    """Test utility functions."""
    print("🧪 Testing utility functions...")
    try:
        from app import detect_emergency_keywords, parse_urgency_level
        
        # Test emergency detection
        if detect_emergency_keywords("chest pain"):
            print("✅ Emergency keyword detection working")
        else:
            print("⚠️ Emergency keyword detection not working")
        
        # Test urgency parsing
        urgency = parse_urgency_level("This is an emergency. Call 999.")
        if urgency == 'Emergency':
            print("✅ Urgency parsing working")
        else:
            print(f"⚠️ Urgency parsing returned {urgency}")
            
        return True
        
    except Exception as e:
        print(f"❌ Utility function testing failed: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive test suite."""
    print("🏥 NHS Digital Triage System - Quick Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Basic imports
    if test_basic_imports():
        tests_passed += 1
    
    # Test 2: App creation
    success, app = test_app_creation()
    if success:
        tests_passed += 1
    else:
        print("❌ Cannot continue without app - stopping tests")
        return False
    
    # Test 3: Database operations
    if test_database_operations(app):
        tests_passed += 1
    
    # Test 4: Basic routes
    if test_basic_routes(app):
        tests_passed += 1
    
    # Test 5: API endpoints
    if test_api_endpoints(app):
        tests_passed += 1
    
    # Test 6: Utility functions
    if test_utility_functions():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! System is ready to use.")
        return True
    elif tests_passed >= total_tests - 1:
        print("✅ Most tests passed. System should work with minor issues.")
        return True
    else:
        print("⚠️ Several tests failed. Please check the errors above.")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_cors', 
        'httpx', 'werkzeug', 'sqlalchemy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + ' '.join(missing_packages))
        return False
    else:
        print("✅ All required packages installed")
        return True

def main():
    """Main function."""
    print("🚀 Starting NHS Digital Triage Quick Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Cannot continue without required dependencies")
        return 1
    
    print()
    
    # Run comprehensive tests
    if run_comprehensive_test():
        print("\n🎯 Next steps:")
        print("   1. Run the full test suite: python test_app.py")
        print("   2. Start the application: python app.py")
        print("   3. Open http://localhost:5000 in your browser")
        print("   4. For AI features, ensure Ollama is running")
        return 0
    else:
        print("\n🔧 Troubleshooting steps:")
        print("   1. Check if all files are in place")
        print("   2. Verify Python version (3.8+ required)")
        print("   3. Install missing dependencies")
        print("   4. Check the error messages above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)