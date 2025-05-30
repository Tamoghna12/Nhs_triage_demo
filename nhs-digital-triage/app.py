import os
import uuid
import json
import logging
import time
import importlib.util
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

import httpx
from flask import (
    Flask, Response, jsonify, render_template, request, session, 
    stream_with_context, redirect, url_for, flash, abort, current_app
)
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

# Import configuration
try:
    from config import config, SYMPTOM_CATEGORIES, MEDICAL_CONDITIONS, URGENCY_LEVELS
except ImportError:
    # Fallback configuration if config.py is not available
    config = {
        'development': type('Config', (), {
            'SECRET_KEY': 'dev-secret-nhs-triage-2025',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///nhs_triage.db',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'OLLAMA_BASE_URL': 'http://localhost:11434',
            'PRIMARY_MODEL': 'gemma3:4b',
            'AI_TIMEOUT': 60,
            'AI_TEMPERATURE': 0.3,
            'AI_TOP_P': 0.9,
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'logs/nhs_triage.log',
            'EMERGENCY_KEYWORDS': ['chest pain', 'difficulty breathing', 'unconscious'],
            'PATIENT_DATA_RETENTION_DAYS': 30,
            'CHAT_DATA_RETENTION_DAYS': 7,
            'DEBUG': True
        })(),
        'testing': type('Config', (), {
            'SECRET_KEY': 'test-secret',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'TESTING': True,
            'OLLAMA_BASE_URL': 'http://localhost:11434',
            'PRIMARY_MODEL': 'gemma3:4b',
            'EMERGENCY_KEYWORDS': ['chest pain', 'difficulty breathing'],
            'PATIENT_DATA_RETENTION_DAYS': 1,
            'CHAT_DATA_RETENTION_DAYS': 1
        })(),
        'default': type('Config', (), {
            'SECRET_KEY': 'dev-secret-nhs-triage-2025',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///nhs_triage.db',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'OLLAMA_BASE_URL': 'http://localhost:11434',
            'PRIMARY_MODEL': 'gemma3:4b'
        })()
    }
    
    SYMPTOM_CATEGORIES = {
        "pain": {"name": "Pain & Discomfort", "icon": "🤕", "symptoms": ["Headache", "Back pain", "Chest pain"]},
        "respiratory": {"name": "Breathing & Respiratory", "icon": "🫁", "symptoms": ["Shortness of breath", "Cough"]},
        "other": {"name": "Other Concerns", "icon": "❓", "symptoms": ["Fever", "Fatigue"]}
    }
    
    MEDICAL_CONDITIONS = ["Diabetes", "High blood pressure", "Heart disease", "Asthma"]

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints/routes
    register_routes(app)
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Only run cleanup if not in testing mode
        if not app.config.get('TESTING', False):
            try:
                cleanup_old_data()
            except Exception as e:
                app.logger.error(f"Initial cleanup failed: {e}")
    
    return app

# Initialize extensions
db = SQLAlchemy()

def setup_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler(app.config['LOG_FILE'])
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('NHS Digital Triage startup')

# Enhanced Models with better relationships and constraints
class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    postcode = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    existing_conditions = db.Column(db.JSON, default=list)
    current_medications = db.Column(db.JSON, default=list)
    allergies = db.Column(db.JSON, default=list)
    emergency_contact = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    chat_messages = db.relationship('ChatMessage', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    assessments = db.relationship('TriageAssessment', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Patient {self.first_name} {self.last_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': f"{self.first_name} {self.last_name}",
            'age': self.age,
            'gender': self.gender,
            'phone': self.phone,
            'created_at': self.created_at.isoformat()
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    tokens_used = db.Column(db.Integer, default=0)
    response_time = db.Column(db.Float, default=0.0)  # Response time in seconds
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.role}>'

class TriageAssessment(db.Model):
    __tablename__ = 'triage_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    # Symptom data
    symptom_category = db.Column(db.String(50), index=True)
    primary_symptom = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.Integer, nullable=False)  # 1-10
    duration = db.Column(db.String(50), nullable=False)
    additional_symptoms = db.Column(db.JSON, default=list)
    
    # Assessment results
    ai_response = db.Column(db.Text)
    urgency_level = db.Column(db.String(20), index=True)  # Emergency/Urgent/Standard/Self-care
    recommendations = db.Column(db.Text)
    confidence_score = db.Column(db.Float, default=0.0)  # AI confidence 0-1
    
    # Metadata
    assessment_duration = db.Column(db.Integer, default=0)  # Duration in seconds
    ai_model_used = db.Column(db.String(50))
    reviewed_by_staff = db.Column(db.Boolean, default=False)
    staff_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<TriageAssessment {self.id}: {self.urgency_level}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient': self.patient.to_dict() if self.patient else None,
            'symptom_category': self.symptom_category,
            'primary_symptom': self.primary_symptom,
            'severity': self.severity,
            'urgency_level': self.urgency_level,
            'created_at': self.created_at.isoformat()
        }

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50))
    session_id = db.Column(db.String(36))
    user_agent = db.Column(db.String(200))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

# Utility functions
def log_system_event(level, message, module=None, session_id=None):
    """Log system events to database."""
    try:
        log = SystemLog(
            level=level,
            message=message,
            module=module or 'system',
            session_id=session_id or session.get('session_id'),
            user_agent=request.headers.get('User-Agent', '') if request else '',
            ip_address=request.remote_addr if request else ''
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # Use app logger if available, otherwise print
        if current_app:
            current_app.logger.error(f"Failed to log system event: {e}")
        else:
            print(f"Failed to log system event: {e}")

def check_ollama():
    """Check if Ollama service is available."""
    try:
        # Get base URL from current app config or use default
        base_url = getattr(current_app.config, 'OLLAMA_BASE_URL', 'http://localhost:11434') if current_app else 'http://localhost:11434'
        response = httpx.get(f"{base_url}/api/version", timeout=3)
        return response.status_code == 200
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Ollama health check failed: {e}")
        return False

def rate_limit_check(session_id, limit=10, window=3600):
    """Simple rate limiting based on session."""
    try:
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(seconds=window)
        
        recent_messages = ChatMessage.query.filter(
            ChatMessage.session_id == session_id,
            ChatMessage.created_at > cutoff_time,
            ChatMessage.role == 'user'
        ).count()
        
        return recent_messages < limit
    except Exception:
        return True  # Allow on error

def cleanup_old_data():
    """Clean up old data based on retention policies."""
    try:
        current_time = datetime.now(timezone.utc)
        
        # Get retention periods with fallbacks
        chat_retention_days = getattr(current_app.config, 'CHAT_DATA_RETENTION_DAYS', 7) if current_app else 7
        patient_retention_days = getattr(current_app.config, 'PATIENT_DATA_RETENTION_DAYS', 30) if current_app else 30
        
        # Clean up old chat messages
        chat_cutoff = current_time - timedelta(days=chat_retention_days)
        old_chats = ChatMessage.query.filter(ChatMessage.created_at < chat_cutoff)
        chat_count = old_chats.count()
        old_chats.delete()
        
        # Clean up old patient data (if no recent assessments)
        patient_cutoff = current_time - timedelta(days=patient_retention_days)
        old_patients = Patient.query.filter(Patient.created_at < patient_cutoff)
        patient_count = old_patients.count()
        old_patients.delete()
        
        db.session.commit()
        
        if chat_count > 0 or patient_count > 0:
            if current_app:
                current_app.logger.info(f"Cleaned up {chat_count} old chat messages and {patient_count} old patients")
            else:
                print(f"Cleaned up {chat_count} old chat messages and {patient_count} old patients")
            
    except Exception as e:
        db.session.rollback()
        if current_app:
            current_app.logger.error(f"Data cleanup failed: {e}")
        else:
            print(f"Data cleanup failed: {e}")

def detect_emergency_keywords(text):
    """Detect emergency keywords in user input."""
    text_lower = text.lower()
    
    # Default emergency keywords
    default_keywords = [
        'chest pain', 'difficulty breathing', 'unconscious', 'severe bleeding',
        'allergic reaction', 'stroke symptoms', 'heart attack', 'suicide'
    ]
    
    # Try to get keywords from app config, fall back to defaults
    emergency_keywords = default_keywords
    try:
        if current_app and hasattr(current_app, 'config'):
            emergency_keywords = current_app.config.get('EMERGENCY_KEYWORDS', default_keywords)
    except RuntimeError:
        # Outside application context, use defaults
        emergency_keywords = default_keywords
    
    for keyword in emergency_keywords:
        if keyword in text_lower:
            return True
    return False

def create_enhanced_triage_prompt(patient_data, symptom_data):
    """Create enhanced AI prompt for triage assessment."""
    emergency_detected = detect_emergency_keywords(symptom_data.get('primary_symptom', ''))
    
    prompt = f"""You are an NHS-trained medical triage AI assistant. Provide a thorough but concise assessment.

PATIENT PROFILE:
- Age: {patient_data.get('age', 'unknown')} years
- Gender: {patient_data.get('gender', 'unknown')}
- Medical Conditions: {', '.join(patient_data.get('existing_conditions', [])) or 'None reported'}
- Current Medications: {', '.join(patient_data.get('current_medications', [])) or 'None reported'}
- Known Allergies: {', '.join(patient_data.get('allergies', [])) or 'None reported'}

CURRENT SYMPTOMS:
- Primary Concern: {symptom_data.get('primary_symptom', 'Not specified')}
- Severity Level: {symptom_data.get('severity', 0)}/10
- Duration: {symptom_data.get('duration', 'Unknown')}
- Additional Symptoms: {', '.join(symptom_data.get('additional_symptoms', [])) or 'None'}

{'⚠️ EMERGENCY KEYWORDS DETECTED - PRIORITIZE URGENCY ASSESSMENT' if emergency_detected else ''}

Provide a structured assessment with:

**URGENCY LEVEL:** [Emergency/Urgent/Standard/Self-care]

**CLINICAL ASSESSMENT:**
Brief clinical reasoning based on symptoms and patient history.

**IMMEDIATE ACTIONS:**
What the patient should do right now.

**WARNING SIGNS:**
Red flag symptoms that require immediate medical attention.

**FOLLOW-UP:**
When and how to seek further care if symptoms persist or worsen.

**SELF-CARE ADVICE:**
If appropriate, safe self-management strategies.

Be concise but thorough. Always err on the side of caution for serious symptoms."""
    
    return prompt

def stream_ollama_response(prompt, record_id, endpoint_type):
    """Stream response from Ollama with error handling and logging."""
    def generate():
        start_time = datetime.now()
        full_response = ""
        
        try:
            # Get configuration values with fallbacks
            base_url = getattr(current_app.config, 'OLLAMA_BASE_URL', 'http://localhost:11434') if current_app else 'http://localhost:11434'
            model = getattr(current_app.config, 'PRIMARY_MODEL', 'gemma3:4b') if current_app else 'gemma3:4b'
            temperature = getattr(current_app.config, 'AI_TEMPERATURE', 0.3) if current_app else 0.3
            top_p = getattr(current_app.config, 'AI_TOP_P', 0.9) if current_app else 0.9
            timeout = getattr(current_app.config, 'AI_TIMEOUT', 60) if current_app else 60
            
            with httpx.stream(
                'POST',
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p
                    }
                },
                timeout=timeout
            ) as resp:
                if resp.status_code != 200:
                    yield f"data: {json.dumps({'error': 'AI service error'})}\n\n"
                    return
                
                for chunk in resp.iter_text():
                    if chunk.strip():
                        try:
                            data = json.loads(chunk)
                            if data.get('response'):
                                full_response += data['response']
                                yield f"data: {json.dumps({'chunk': data['response']})}\n\n"
                            if data.get('done'):
                                # Save assistant response
                                response_time = (datetime.now() - start_time).total_seconds()
                                save_ai_response(record_id, full_response, response_time, endpoint_type)
                                yield f"data: {json.dumps({'done': True})}\n\n"
                                return
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.TimeoutException:
            log_system_event('ERROR', 'AI request timeout', endpoint_type)
            yield f"data: {json.dumps({'error': 'Request timeout'})}\n\n"
        except Exception as e:
            log_system_event('ERROR', f'AI streaming error: {str(e)}', endpoint_type)
            yield f"data: {json.dumps({'error': 'Unexpected error'})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )

def save_ai_response(record_id, response, response_time, endpoint_type):
    """Save AI response to database."""
    try:
        if endpoint_type == 'chat':
            # Save chat assistant response
            assistant_msg = ChatMessage(
                session_id=session['session_id'],
                patient_id=ChatMessage.query.get(record_id).patient_id,
                message=response,
                role='assistant',
                response_time=response_time
            )
            db.session.add(assistant_msg)
        elif endpoint_type == 'triage':
            # Update triage assessment
            assessment = TriageAssessment.query.get(record_id)
            if assessment:
                assessment.ai_response = response
                assessment.urgency_level = parse_urgency_level(response)
                assessment.ai_model_used = getattr(current_app.config, 'PRIMARY_MODEL', 'gemma3:4b') if current_app else 'gemma3:4b'
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if current_app:
            current_app.logger.error(f"Failed to save AI response: {e}")

def parse_urgency_level(response):
    """Parse urgency level from AI response."""
    response_lower = response.lower()
    
    if any(keyword in response_lower for keyword in ['emergency', '999', 'life-threatening']):
        return 'Emergency'
    elif any(keyword in response_lower for keyword in ['urgent', '111', 'immediate']):
        return 'Urgent'
    elif any(keyword in response_lower for keyword in ['gp', 'doctor', 'appointment']):
        return 'Standard'
    else:
        return 'Self-care'

# Route registration and error handlers
def register_routes(app):
    """Register all application routes."""
    
    @app.before_request
    def before_request():
        """Execute before each request."""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        session.permanent = True
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/chat')
    def chat():
        return render_template('chat.html', 
                             session_id=session['session_id'],
                             ollama_available=check_ollama())
    
    @app.route('/triage')
    def triage():
        return render_template('triage.html',
                             session_id=session['session_id'],
                             ollama_available=check_ollama(),
                             symptom_categories=SYMPTOM_CATEGORIES,
                             medical_conditions=MEDICAL_CONDITIONS)
    
    @app.route('/staff-dashboard')
    def staff_dashboard():
        # In a real implementation, add authentication here
        assessments = TriageAssessment.query.order_by(
            TriageAssessment.created_at.desc()
        ).limit(50).all()
        return render_template('dashboard.html', assessments=assessments)
    
    # API Routes
    @app.route('/api/system-status')
    def system_status():
        """Get system status and statistics."""
        try:
            total_patients = Patient.query.count()
            total_assessments = TriageAssessment.query.count()
            total_chat_messages = ChatMessage.query.count()
            
            return jsonify({
                'ollama_available': check_ollama(),
                'total_patients': total_patients,
                'total_assessments': total_assessments,
                'total_chat_messages': total_chat_messages,
                'system_uptime': 'Available',
                'ai_model': app.config.get('PRIMARY_MODEL', 'gemma3:4b'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            app.logger.error(f"System status error: {e}")
            return jsonify({'error': 'System status unavailable'}), 500

    @app.route('/api/health')
    def health_check():
        """Simple health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    @app.route('/api/patient/register', methods=['POST'])
    def register_patient():
        """Register or update patient information."""
        data = request.get_json()
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'No session'}), 400
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'age', 'gender']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate age
        try:
            age = int(data.get('age'))
            if age < 1 or age > 120:
                return jsonify({'error': 'Age must be between 1 and 120'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Age must be a valid number'}), 400
        
        # Validate gender
        valid_genders = ['male', 'female', 'other', 'prefer-not-to-say']
        if data.get('gender') not in valid_genders:
            return jsonify({'error': 'Invalid gender'}), 400
        
        try:
            patient = Patient.query.filter_by(session_id=session_id).first()
            if patient:
                # Update existing patient
                patient.first_name = data.get('firstName', '')
                patient.last_name = data.get('lastName', '')
                patient.age = age
                patient.gender = data.get('gender', '')
                patient.postcode = data.get('postcode', '')
                patient.phone = data.get('phone', '')
                patient.email = data.get('email', '')
                patient.existing_conditions = data.get('existingConditions', [])
                patient.current_medications = data.get('currentMedications', [])
                patient.allergies = data.get('allergies', [])
                patient.emergency_contact = data.get('emergencyContact', '')
                patient.updated_at = datetime.now(timezone.utc)
            else:
                # Create new patient
                patient = Patient(
                    session_id=session_id,
                    first_name=data.get('firstName', ''),
                    last_name=data.get('lastName', ''),
                    age=age,
                    gender=data.get('gender', ''),
                    postcode=data.get('postcode', ''),
                    phone=data.get('phone', ''),
                    email=data.get('email', ''),
                    existing_conditions=data.get('existingConditions', []),
                    current_medications=data.get('currentMedications', []),
                    allergies=data.get('allergies', []),
                    emergency_contact=data.get('emergencyContact', '')
                )
                db.session.add(patient)
            
            db.session.commit()
            return jsonify({'success': True, 'patient_id': patient.id})
            
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Patient registration error: {e}")
            return jsonify({'error': 'Registration failed'}), 500

    @app.route('/api/chat', methods=['POST'])
    def start_chat():
        data = request.get_json()
        if not data or not data.get('message'):
            return jsonify({'error': 'No message provided'}), 400
        
        if not check_ollama():
            log_system_event('ERROR', 'AI service unavailable', 'chat')
            return jsonify({'error': 'AI service unavailable'}), 503
        
        session_id = session['session_id']
        
        # Rate limiting
        if not rate_limit_check(session_id):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Check for emergency keywords
        if detect_emergency_keywords(data['message']):
            log_system_event('WARNING', f'Emergency keywords detected: {data["message"][:100]}', 'chat', session_id)
        
        try:
            # Get or create patient
            patient = Patient.query.filter_by(session_id=session_id).first()
            if not patient:
                patient = Patient(
                    session_id=session_id,
                    first_name='Anonymous',
                    last_name='User',
                    age=0,
                    gender='unknown'
                )
                db.session.add(patient)
                db.session.commit()
            
            # Save message
            msg = ChatMessage(
                session_id=session_id,
                patient_id=patient.id,
                message=data['message'],
                role='user'
            )
            db.session.add(msg)
            db.session.commit()
            
            return jsonify({'success': True, 'message_id': msg.id})
            
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Database error in start_chat: {e}")
            return jsonify({'error': 'Database error'}), 500
    
    @app.route('/api/chat/stream/<int:message_id>')
    def stream_chat(message_id):
        msg = ChatMessage.query.get_or_404(message_id)
        
        emergency_warning = ""
        if detect_emergency_keywords(msg.message):
            emergency_warning = "⚠️ **EMERGENCY ALERT**: Your symptoms may require immediate medical attention. If this is a life-threatening emergency, please call 999 immediately.\n\n"
        
        prompt = f"""{emergency_warning}You are an NHS medical assistant. Provide helpful, concise medical guidance (2-3 sentences).

Previous context: This is a chat conversation about health concerns.

User message: {msg.message}

Respond professionally and ask ONE specific follow-up question if appropriate. Always include appropriate medical disclaimers."""
        
        return stream_ollama_response(prompt, msg.id, 'chat')

    @app.route('/api/triage/submit', methods=['POST'])
    def submit_triage():
        """Submit triage assessment data."""
        data = request.get_json()
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'No session'}), 400
        
        if not check_ollama():
            return jsonify({'error': 'AI service unavailable'}), 503
        
        # Validate required fields
        required_fields = ['category', 'primarySymptom', 'severity', 'duration']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate severity
        try:
            severity = int(data.get('severity'))
            if severity < 1 or severity > 10:
                return jsonify({'error': 'Severity must be between 1 and 10'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Severity must be a valid number'}), 400
        
        # Validate category
        valid_categories = ['pain', 'respiratory', 'digestive', 'neurological', 'skin', 'other']
        if data.get('category') not in valid_categories:
            return jsonify({'error': 'Invalid symptom category'}), 400
        
        try:
            patient = Patient.query.filter_by(session_id=session_id).first()
            if not patient:
                return jsonify({'error': 'Patient not found'}), 404
            
            # Create assessment
            assessment = TriageAssessment(
                session_id=session_id,
                patient_id=patient.id,
                symptom_category=data.get('category'),
                primary_symptom=data.get('primarySymptom'),
                severity=severity,
                duration=data.get('duration'),
                additional_symptoms=data.get('additionalSymptoms', [])
            )
            
            db.session.add(assessment)
            db.session.commit()
            
            return jsonify({'success': True, 'assessment_id': assessment.id})
            
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Triage submission error: {e}")
            return jsonify({'error': 'Submission failed'}), 500

    @app.route('/api/triage/stream/<int:assessment_id>')
    def stream_triage(assessment_id):
        """Stream triage assessment from AI."""
        assessment = TriageAssessment.query.get_or_404(assessment_id)
        patient = assessment.patient_id and Patient.query.get(assessment.patient_id)
        
        # Prepare data for AI prompt
        patient_data = {
            'age': patient.age if patient else None,
            'gender': patient.gender if patient else None,
            'existing_conditions': patient.existing_conditions if patient else [],
            'current_medications': patient.current_medications if patient else [],
            'allergies': patient.allergies if patient else []
        }
        
        symptom_data = {
            'primary_symptom': assessment.primary_symptom,
            'severity': assessment.severity,
            'duration': assessment.duration,
            'additional_symptoms': assessment.additional_symptoms or []
        }
        
        prompt = create_enhanced_triage_prompt(patient_data, symptom_data)
        return stream_ollama_response(prompt, assessment.id, 'triage')

    @app.route('/api/triage/save/<int:assessment_id>', methods=['POST'])
    def save_triage_result(assessment_id):
        """Save triage assessment result."""
        data = request.get_json()
        
        try:
            assessment = TriageAssessment.query.get_or_404(assessment_id)
            ai_response = data.get('response', '')
            
            assessment.ai_response = ai_response
            assessment.urgency_level = parse_urgency_level(ai_response)
            assessment.recommendations = ai_response[:500]  # First 500 chars
            assessment.confidence_score = data.get('confidence_score', 0.0)
            assessment.ai_model_used = app.config.get('PRIMARY_MODEL', 'gemma3:4b')
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'urgency_level': assessment.urgency_level,
                'assessment_id': assessment.id
            })
            
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Save triage error: {e}")
            return jsonify({'error': 'Save failed'}), 500

def register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(503)
    def service_unavailable_error(error):
        return render_template('errors/503.html'), 503

def stream_ollama_response(prompt, record_id, endpoint_type):
    """Stream response from Ollama with error handling and logging."""
    def generate():
        start_time = datetime.now()
        full_response = ""
        
        try:
            with httpx.stream(
                'POST',
                f"{current_app.config['OLLAMA_BASE_URL']}/api/generate",
                json={
                    "model": current_app.config['PRIMARY_MODEL'],
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": current_app.config['AI_TEMPERATURE'],
                        "top_p": current_app.config['AI_TOP_P']
                    }
                },
                timeout=current_app.config['AI_TIMEOUT']
            ) as resp:
                if resp.status_code != 200:
                    yield f"data: {json.dumps({'error': 'AI service error'})}\n\n"
                    return
                
                for chunk in resp.iter_text():
                    if chunk.strip():
                        try:
                            data = json.loads(chunk)
                            if data.get('response'):
                                full_response += data['response']
                                yield f"data: {json.dumps({'chunk': data['response']})}\n\n"
                            if data.get('done'):
                                # Save assistant response
                                response_time = (datetime.now() - start_time).total_seconds()
                                save_ai_response(record_id, full_response, response_time, endpoint_type)
                                yield f"data: {json.dumps({'done': True})}\n\n"
                                return
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.TimeoutException:
            log_system_event('ERROR', 'AI request timeout', endpoint_type)
            yield f"data: {json.dumps({'error': 'Request timeout'})}\n\n"
        except Exception as e:
            log_system_event('ERROR', f'AI streaming error: {str(e)}', endpoint_type)
            yield f"data: {json.dumps({'error': 'Unexpected error'})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )

def save_ai_response(record_id, response, response_time, endpoint_type):
    """Save AI response to database."""
    try:
        if endpoint_type == 'chat':
            # Save chat assistant response
            assistant_msg = ChatMessage(
                session_id=session['session_id'],
                patient_id=ChatMessage.query.get(record_id).patient_id,
                message=response,
                role='assistant',
                response_time=response_time
            )
            db.session.add(assistant_msg)
        elif endpoint_type == 'triage':
            # Update triage assessment
            assessment = TriageAssessment.query.get(record_id)
            if assessment:
                assessment.ai_response = response
                assessment.urgency_level = parse_urgency_level(response)
                assessment.ai_model_used = current_app.config['PRIMARY_MODEL']
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to save AI response: {e}")

def parse_urgency_level(response):
    """Parse urgency level from AI response."""
    response_lower = response.lower()
    
    if any(keyword in response_lower for keyword in ['emergency', '999', 'life-threatening']):
        return 'Emergency'
    elif any(keyword in response_lower for keyword in ['urgent', '111', 'immediate']):
        return 'Urgent'
    elif any(keyword in response_lower for keyword in ['gp', 'doctor', 'appointment']):
        return 'Standard'
    else:
        return 'Self-care'

# Application factory
app = None

def get_app():
    """Get or create the Flask application."""
    global app
    if app is None:
        app = create_app()
    return app

if __name__ == '__main__':
    app = create_app()
    print("🏥 NHS Digital Triage System Starting...")
    print(f"🤖 Ollama: {'✅ Available' if check_ollama() else '❌ Not Available'}")
    print("🌐 Interfaces:")
    print("   🏠 Home: http://localhost:5000")
    print("   💬 Chat: http://localhost:5000/chat")
    print("   📋 Triage: http://localhost:5000/triage")
    print("   👨‍⚕️ Dashboard: http://localhost:5000/staff-dashboard")
    
    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
else:
    # For testing and other imports
    app = get_app()