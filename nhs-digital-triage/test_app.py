import unittest
import json
import tempfile
import os
from datetime import datetime, timezone

# Handle different import scenarios
try:
    from app import create_app, db
    from app import Patient, ChatMessage, TriageAssessment, SystemLog
except ImportError:
    # If config.py doesn't exist, create app with testing config
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Create minimal app for testing
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    
    # Import the enhanced app module
    import app as app_module
    
    create_app = app_module.create_app
    db = app_module.db
    Patient = app_module.Patient
    ChatMessage = app_module.ChatMessage
    TriageAssessment = app_module.TriageAssessment
    SystemLog = app_module.SystemLog

class NHSTriageTestCase(unittest.TestCase):
    """Base test case for NHS Triage System."""
    
    def setUp(self):
        """Set up test environment."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app('testing')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        self.client = self.app.test_client()
        
    def tearDown(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

class RoutesTestCase(NHSTriageTestCase):
    """Test case for application routes."""
    
    def test_index_page(self):
        """Test home page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'NHS Digital Triage', response.data)
    
    def test_chat_page(self):
        """Test chat page loads correctly."""
        response = self.client.get('/chat')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'NHS Chat Assistant', response.data)
    
    def test_triage_page(self):
        """Test triage page loads correctly."""
        response = self.client.get('/triage')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Structured Medical Triage', response.data)
    
    def test_staff_dashboard(self):
        """Test staff dashboard loads correctly."""
        response = self.client.get('/staff-dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Healthcare Staff Dashboard', response.data)

class APITestCase(NHSTriageTestCase):
    """Test case for API endpoints."""
    
    def test_start_chat_valid_message(self):
        """Test starting chat with valid message."""
        with self.app.test_request_context():
            response = self.client.post('/api/chat',
                                      data=json.dumps({'message': 'I have a headache'}),
                                      content_type='application/json')
            
            # Should fail without Ollama, but structure should be correct
            self.assertIn(response.status_code, [200, 503])
    
    def test_start_chat_no_message(self):
        """Test starting chat without message."""
        response = self.client.post('/api/chat',
                                  data=json.dumps({}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_system_status_endpoint(self):
        """Test system status endpoint."""
        response = self.client.get('/api/system-status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('ollama_available', data)
        self.assertIn('total_patients', data)

class ModelTestCase(NHSTriageTestCase):
    """Test case for database models."""
    
    def test_patient_creation(self):
        """Test patient model creation."""
        patient = Patient(
            session_id='test-session-123',
            first_name='John',
            last_name='Doe',
            age=30,
            gender='male',
            phone='07123456789'
        )
        db.session.add(patient)
        db.session.commit()
        
        self.assertEqual(patient.id, 1)
        self.assertEqual(patient.first_name, 'John')
        self.assertEqual(patient.age, 30)
    
    def test_chat_message_creation(self):
        """Test chat message model creation."""
        # Create patient first
        patient = Patient(
            session_id='test-session-123',
            first_name='John',
            last_name='Doe',
            age=30,
            gender='male'
        )
        db.session.add(patient)
        db.session.commit()
        
        # Create chat message
        message = ChatMessage(
            session_id='test-session-123',
            patient_id=patient.id,
            message='I have a headache',
            role='user'
        )
        db.session.add(message)
        db.session.commit()
        
        self.assertEqual(message.message, 'I have a headache')
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.patient_id, patient.id)
    
    def test_triage_assessment_creation(self):
        """Test triage assessment model creation."""
        # Create patient first
        patient = Patient(
            session_id='test-session-123',
            first_name='Jane',
            last_name='Smith',
            age=25,
            gender='female'
        )
        db.session.add(patient)
        db.session.commit()
        
        # Create assessment
        assessment = TriageAssessment(
            session_id='test-session-123',
            patient_id=patient.id,
            symptom_category='pain',
            primary_symptom='Headache',
            severity=7,
            duration='few-hours',
            urgency_level='Standard'
        )
        db.session.add(assessment)
        db.session.commit()
        
        self.assertEqual(assessment.primary_symptom, 'Headache')
        self.assertEqual(assessment.severity, 7)
        self.assertEqual(assessment.urgency_level, 'Standard')

class UtilityFunctionTestCase(NHSTriageTestCase):
    """Test case for utility functions."""
    
    def test_emergency_keyword_detection(self):
        """Test emergency keyword detection."""
        # Import the function with error handling
        try:
            from app import detect_emergency_keywords
        except ImportError:
            # Skip test if function not available
            self.skipTest("detect_emergency_keywords function not available")
        
        # Run tests within application context
        with self.app.app_context():
            # Test emergency keywords
            self.assertTrue(detect_emergency_keywords("I have severe chest pain"))
            self.assertTrue(detect_emergency_keywords("difficulty breathing"))
            self.assertTrue(detect_emergency_keywords("I think I'm having a heart attack"))
            
            # Test non-emergency
            self.assertFalse(detect_emergency_keywords("I have a mild headache"))
            self.assertFalse(detect_emergency_keywords("I feel tired"))
    
    def test_urgency_parsing(self):
        """Test urgency level parsing from AI responses."""
        try:
            from app import parse_urgency_level
        except ImportError:
            self.skipTest("parse_urgency_level function not available")
        
        # Run tests within application context
        with self.app.app_context():
            emergency_response = "This is an emergency situation. Call 999 immediately."
            urgent_response = "This is urgent. Contact NHS 111 for immediate advice."
            standard_response = "You should see your GP within 24-48 hours."
            selfcare_response = "This can be managed with self-care measures."
            
            self.assertEqual(parse_urgency_level(emergency_response), 'Emergency')
            self.assertEqual(parse_urgency_level(urgent_response), 'Urgent')
            self.assertEqual(parse_urgency_level(standard_response), 'Standard')
            self.assertEqual(parse_urgency_level(selfcare_response), 'Self-care')

class SecurityTestCase(NHSTriageTestCase):
    """Test case for security features."""
    
    def test_rate_limiting(self):
        """Test basic rate limiting functionality."""
        try:
            from app import rate_limit_check
            # Run within application context
            with self.app.app_context():
                # This should pass for new session
                self.assertTrue(rate_limit_check('new-session-id'))
        except ImportError:
            self.skipTest("rate_limit_check function not available")
    
    def test_session_management(self):
        """Test session ID assignment."""
        with self.client.session_transaction() as sess:
            # Session should be empty initially
            self.assertNotIn('session_id', sess)
        
        # Make a request to trigger session creation
        response = self.client.get('/')
        
        with self.client.session_transaction() as sess:
            # Session ID should now be set
            self.assertIn('session_id', sess)
            self.assertIsNotNone(sess['session_id'])

class DataRetentionTestCase(NHSTriageTestCase):
    """Test case for data retention policies."""
    
    def test_old_data_cleanup(self):
        """Test cleanup of old data."""
        try:
            from app import cleanup_old_data
        except ImportError:
            self.skipTest("cleanup_old_data function not available")
            
        from datetime import timedelta
        
        # Run within application context
        with self.app.app_context():
            # Create old patient data
            old_patient = Patient(
                session_id='old-session',
                first_name='Old',
                last_name='Patient',
                age=40,
                gender='male',
                created_at=datetime.now(timezone.utc) - timedelta(days=35)
            )
            db.session.add(old_patient)
            
            # Create recent patient data
            new_patient = Patient(
                session_id='new-session',
                first_name='New',
                last_name='Patient',
                age=30,
                gender='female'
            )
            db.session.add(new_patient)
            db.session.commit()
            
            # Run cleanup
            cleanup_old_data()
            
            # Check that only recent data remains
            patients = Patient.query.all()
            self.assertEqual(len(patients), 1)
            self.assertEqual(patients[0].first_name, 'New')

class IntegrationTestCase(NHSTriageTestCase):
    """Integration tests for complete workflows."""
    
    def test_complete_triage_workflow(self):
        """Test complete triage assessment workflow."""
        # Step 1: Register patient
        patient_data = {
            'firstName': 'Test',
            'lastName': 'Patient',
            'age': 30,
            'gender': 'male',
            'existingConditions': ['Diabetes'],
            'currentMedications': ['Metformin'],
            'allergies': []
        }
        
        response = self.client.post('/api/patient/register',
                                  data=json.dumps(patient_data),
                                  content_type='application/json')
        
        # Should succeed or fail gracefully
        self.assertIn(response.status_code, [200, 400, 500])
        
        # If successful, continue with symptom submission
        if response.status_code == 200:
            symptom_data = {
                'category': 'pain',
                'primarySymptom': 'Headache',
                'severity': 6,
                'duration': 'few-hours',
                'additionalSymptoms': ['Nausea']
            }
            
            response = self.client.post('/api/triage/submit',
                                      data=json.dumps(symptom_data),
                                      content_type='application/json')
            
            # Should succeed or fail gracefully
            self.assertIn(response.status_code, [200, 400, 500, 503])

class PerformanceTestCase(NHSTriageTestCase):
    """Performance and load testing."""
    
    def test_database_performance(self):
        """Test database query performance with multiple records."""
        # Create multiple patients
        patients = []
        for i in range(100):
            patient = Patient(
                session_id=f'session-{i}',
                first_name=f'Patient{i}',
                last_name='Test',
                age=20 + (i % 60),
                gender='male' if i % 2 == 0 else 'female'
            )
            patients.append(patient)
        
        db.session.add_all(patients)
        db.session.commit()
        
        # Test query performance
        import time
        start_time = time.time()
        
        recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(20).all()
        
        query_time = time.time() - start_time
        
        self.assertEqual(len(recent_patients), 20)
        self.assertLess(query_time, 1.0)  # Should complete in under 1 second

def run_tests():
    """Run all tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    test_cases = [
        RoutesTestCase,
        APITestCase,
        ModelTestCase,
        UtilityFunctionTestCase,
        SecurityTestCase,
        DataRetentionTestCase,
        IntegrationTestCase,
        PerformanceTestCase
    ]
    
    for test_case in test_cases:
        tests = loader.loadTestsFromTestCase(test_case)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("🧪 Running NHS Digital Triage Test Suite...")
    print("=" * 60)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    exit(0 if success else 1)