import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-nhs-triage-2025'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Database Settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # AI/Ollama Settings
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL') or 'http://localhost:11434'
    PRIMARY_MODEL = os.environ.get('PRIMARY_MODEL') or 'llama3.2:3b'
    BACKUP_MODEL = os.environ.get('BACKUP_MODEL') or 'llama3.2:1b'
    AI_TIMEOUT = int(os.environ.get('AI_TIMEOUT', 60))
    AI_TEMPERATURE = float(os.environ.get('AI_TEMPERATURE', 0.3))
    AI_TOP_P = float(os.environ.get('AI_TOP_P', 0.9))
    
    # Security Settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Logging Settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/nhs_triage.log')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Medical Settings
    MAX_ASSESSMENT_DURATION = int(os.environ.get('MAX_ASSESSMENT_DURATION', 3600))  # 1 hour
    EMERGENCY_KEYWORDS = [
        'chest pain', 'difficulty breathing', 'unconscious', 'severe bleeding',
        'allergic reaction', 'stroke symptoms', 'heart attack', 'suicide'
    ]
    
    # Data Retention
    PATIENT_DATA_RETENTION_DAYS = int(os.environ.get('PATIENT_DATA_RETENTION_DAYS', 30))
    CHAT_DATA_RETENTION_DAYS = int(os.environ.get('CHAT_DATA_RETENTION_DAYS', 7))
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///nhs_triage_dev.db'
    
    # Development-specific settings
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Testing-specific settings
    AI_TIMEOUT = 10  # Shorter timeout for tests
    PATIENT_DATA_RETENTION_DAYS = 1

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///nhs_triage.db'
    
    # Production-specific security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Enhanced logging
    LOG_LEVEL = 'WARNING'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class HerokuConfig(ProductionConfig):
    """Heroku-specific configuration."""
    SSL_REDIRECT = True
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Handle proxy headers
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'default': DevelopmentConfig
}

# Medical configuration constants
SYMPTOM_CATEGORIES = {
    "pain": {
        "name": "Pain & Discomfort",
        "icon": "🤕",
        "priority": "high",
        "symptoms": [
            "Headache", "Back pain", "Chest pain", "Abdominal pain", 
            "Joint pain", "Muscle pain", "Tooth pain", "Ear pain",
            "Neck pain", "Leg pain", "Arm pain"
        ],
        "emergency_symptoms": ["Chest pain", "Severe headache", "Abdominal pain"]
    },
    "respiratory": {
        "name": "Breathing & Respiratory", 
        "icon": "🫁",
        "priority": "high",
        "symptoms": [
            "Shortness of breath", "Cough", "Wheezing", "Chest tightness", 
            "Sore throat", "Runny nose", "Congestion", "Loss of smell/taste",
            "Difficulty breathing", "Persistent cough"
        ],
        "emergency_symptoms": ["Shortness of breath", "Difficulty breathing", "Severe chest tightness"]
    },
    "digestive": {
        "name": "Digestive & Stomach",
        "icon": "🍽️", 
        "priority": "medium",
        "symptoms": [
            "Nausea", "Vomiting", "Diarrhea", "Constipation", 
            "Heartburn", "Loss of appetite", "Bloating", "Stomach cramps",
            "Blood in stool", "Severe vomiting"
        ],
        "emergency_symptoms": ["Severe vomiting", "Blood in stool", "Severe abdominal pain"]
    },
    "neurological": {
        "name": "Neurological & Mental",
        "icon": "🧠",
        "priority": "high",
        "symptoms": [
            "Dizziness", "Confusion", "Memory problems", "Weakness", 
            "Numbness", "Anxiety", "Depression", "Sleep problems",
            "Severe headache", "Loss of consciousness", "Seizure"
        ],
        "emergency_symptoms": ["Loss of consciousness", "Seizure", "Severe confusion", "Stroke symptoms"]
    },
    "skin": {
        "name": "Skin & External",
        "icon": "🩹", 
        "priority": "low",
        "symptoms": [
            "Rash", "Itching", "Swelling", "Bruising", 
            "Cut/wound", "Burn", "Insect bite", "Unusual mole",
            "Severe allergic reaction", "Deep wound"
        ],
        "emergency_symptoms": ["Severe allergic reaction", "Deep wound", "Severe burn"]
    },
    "other": {
        "name": "Other Concerns",
        "icon": "❓",
        "priority": "medium",
        "symptoms": [
            "Fever", "Fatigue", "Weight loss", "Weight gain", 
            "Frequent urination", "Blood in urine", "Vision problems", "Hearing problems",
            "High fever", "Severe fatigue", "Sudden vision loss"
        ],
        "emergency_symptoms": ["High fever", "Sudden vision loss", "Blood in urine"]
    }
}

MEDICAL_CONDITIONS = [
    "Diabetes", "High blood pressure", "Heart disease", "Asthma", "COPD",
    "Kidney disease", "Liver disease", "Cancer", "Arthritis", "Depression",
    "Anxiety", "Epilepsy", "Stroke", "Blood clots", "Allergies",
    "Thyroid disease", "Osteoporosis", "Migraine", "Fibromyalgia"
]

# Urgency level configurations
URGENCY_LEVELS = {
    'Emergency': {
        'color': '#f44336',
        'icon': '🚨',
        'action': 'Call 999 immediately',
        'wait_time': 'Immediate',
        'description': 'Life-threatening condition requiring immediate emergency care'
    },
    'Urgent': {
        'color': '#ff9800',
        'icon': '⚡',
        'action': 'Call NHS 111 or visit A&E',
        'wait_time': 'Within 1 hour',
        'description': 'Urgent medical attention needed but not immediately life-threatening'
    },
    'Standard': {
        'color': '#2196f3',
        'icon': '🏥',
        'action': 'See your GP within 24-48 hours',
        'wait_time': '1-2 days',
        'description': 'Medical attention needed but can wait for GP appointment'
    },
    'Self-care': {
        'color': '#4caf50',
        'icon': '💚',
        'action': 'Self-care measures recommended',
        'wait_time': 'Monitor symptoms',
        'description': 'Symptoms can likely be managed with self-care and monitoring'
    }
}