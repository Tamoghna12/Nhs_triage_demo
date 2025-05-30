# NHS Digital Triage System - Complete Setup Guide

## 🏥 System Overview

The NHS Digital Triage System is a comprehensive AI-powered medical assessment platform providing:

* **Chat Interface** : Natural conversation with AI medical assistant
* **Structured Triage** : Step-by-step comprehensive medical assessment
* **Staff Dashboard** : Healthcare professional monitoring and analytics
* **Real-time AI** : Powered by local Ollama language models
* **Secure Data** : Local SQLite storage with privacy protection

## 📋 Complete File Structure

Create the following directory structure:

```
nhs-digital-triage/
├── app.py                    # Enhanced Flask application
├── config.py                 # Configuration management
├── manage.py                 # Database management utility
├── test_app.py              # Comprehensive test suite
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Multi-container setup
├── deploy.sh                # Deployment script
├── monitor.py               # System monitoring
├── README.md                # Documentation
├── COMPLETE_SETUP_GUIDE.md  # This file
├── templates/               # HTML templates
│   ├── index.html           # Homepage
│   ├── chat.html            # Chat interface
│   ├── triage.html          # Structured triage
│   ├── dashboard.html       # Staff dashboard
│   └── errors/              # Error pages
│       ├── 404.html         # Not found
│       ├── 500.html         # Server error
│       └── 503.html         # Service unavailable
├── static/                  # Static assets (CSS, JS, images)
├── logs/                    # Application logs
├── data/                    # Data exports and backups
└── venv/                    # Python virtual environment
```

## 🚀 Quick Installation

### Option 1: Automated Setup (Recommended)

1. **Download all files to your project directory**
2. **Make deployment script executable:**
   ```bash
   chmod +x deploy.sh
   ```
3. **Run automated deployment:**
   ```bash
   ./deploy.sh
   ```
4. **Start the application:**
   ```bash
   python app.py
   ```

### Option 2: Manual Setup

1. **Create project directory:**
   ```bash
   mkdir nhs-digital-triage
   cd nhs-digital-triage
   ```
2. **Create Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Install Ollama:**
   ```bash
   # Linux/Mac
   curl -fsSL https://ollama.ai/install.sh | sh

   # Windows: Download from https://ollama.ai
   ```
5. **Start Ollama service:**
   ```bash
   ollama serve
   ```
6. **Download AI model (in a new terminal):**
   ```bash
   ollama pull llama3.2:3b
   ```
7. **Initialize database:**
   ```bash
   python manage.py init-db
   ```
8. **Create sample data (optional):**
   ```bash
   python manage.py create-sample-data
   ```
9. **Start the application:**
   ```bash
   python app.py
   ```

## 🐳 Docker Setup

### Option 1: Docker Compose (Recommended)

1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```
2. **For production with PostgreSQL:**
   ```bash
   docker-compose --profile production up --build
   ```

### Option 2: Single Container

1. **Build Docker image:**
   ```bash
   docker build -t nhs-digital-triage .
   ```
2. **Run container:**
   ```bash
   docker run -p 5000:5000 -p 11434:11434 nhs-digital-triage
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your configuration:

```bash
# Application Settings
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
HOST=0.0.0.0
PORT=5000

# Database Configuration
DATABASE_URL=sqlite:///nhs_triage.db
# For PostgreSQL: postgresql://user:pass@localhost/nhs_triage

# AI Configuration
OLLAMA_BASE_URL=http://localhost:11434
PRIMARY_MODEL=llama3.2:3b
BACKUP_MODEL=llama3.2:1b
AI_TIMEOUT=60
AI_TEMPERATURE=0.3

# Data Retention (days)
PATIENT_DATA_RETENTION_DAYS=30
CHAT_DATA_RETENTION_DAYS=7

# Security
WTF_CSRF_ENABLED=true
SESSION_COOKIE_SECURE=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/nhs_triage.log
```

### Advanced Configuration

Edit `config.py` to customize:

* Symptom categories and medical conditions
* Urgency level thresholds
* Emergency keyword detection
* Rate limiting settings

## 🧪 Testing

### Run Test Suite

```bash
# Run all tests
python test_app.py

# Run specific test categories
python -m unittest test_app.RoutesTestCase
python -m unittest test_app.ModelTestCase
python -m unittest test_app.SecurityTestCase
```

### Performance Testing

```bash
# Database performance test
python -m unittest test_app.PerformanceTestCase

# Load testing (requires additional tools)
pip install locust
locust -f load_test.py --host=http://localhost:5000
```

## 📊 Management Commands

### Database Management

```bash
# Initialize database
python manage.py init-db

# Reset database (WARNING: Deletes all data)
python manage.py reset-db

# Create sample data
python manage.py create-sample-data

# Clean up old data
python manage.py cleanup-data --days 30

# Export data
python manage.py export-data --format json --output backup.json
python manage.py export-data --format csv --output assessments.csv
```

### System Monitoring

```bash
# System health check
python manage.py check-health

# View statistics
python manage.py show-stats

# Continuous monitoring
python monitor.py --continuous --interval 60
```

## 🔒 Security Setup

### SSL/HTTPS Configuration

1. **Generate SSL certificates:**
   ```bash
   # Self-signed (development only)
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

   # Production: Use Let's Encrypt or proper CA certificates
   ```
2. **Configure Nginx (production):**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Authentication Setup

For production, implement authentication:

1. **Add user authentication system**
2. **Configure role-based access control**
3. **Set up staff authentication for dashboard**
4. **Implement audit logging**

## 🚑 Emergency Protocols

The system implements NHS emergency protocols:

* **999 Emergency** : Immediate life-threatening situations
* **NHS 111** : Urgent but non-emergency care
* **GP Appointment** : Standard medical concerns
* **Self-care** : Minor symptoms with guidance

### Emergency Keyword Detection

The system automatically detects emergency keywords and prioritizes assessments:

* Chest pain, difficulty breathing
* Unconsciousness, severe bleeding
* Heart attack, stroke symptoms
* Severe allergic reactions

## 📈 Monitoring and Alerting

### System Monitoring

```bash
# Real-time monitoring
python monitor.py --continuous

# One-time health check
python monitor.py

# Custom monitoring configuration
cp monitor_config.example.json monitor_config.json
# Edit configuration as needed
```

### Log Analysis

```bash
# View recent logs
tail -f logs/nhs_triage.log

# Search for errors
grep "ERROR" logs/nhs_triage.log

# Monitor system performance
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\".\").percent:.1f}%')
"
```

## 🔄 Backup and Recovery

### Database Backup

```bash
# Export all data
python manage.py export-data --format json --output "backup_$(date +%Y%m%d).json"

# SQLite backup
cp nhs_triage.db "nhs_triage_backup_$(date +%Y%m%d).db"

# PostgreSQL backup
pg_dump nhs_triage > "nhs_triage_backup_$(date +%Y%m%d).sql"
```

### Automated Backups

Add to crontab for daily backups:

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/project/venv/bin/python /path/to/project/manage.py export-data --output /backups/nhs_triage_$(date +\%Y\%m\%d).json
```

## 🐛 Troubleshooting

### Common Issues

1. **Ollama not responding:**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/version

   # Restart Ollama
   pkill ollama
   ollama serve

   # Pull model again
   ollama pull llama3.2:3b
   ```
2. **Database connection errors:**
   ```bash
   # Check database file permissions
   ls -la nhs_triage.db

   # Reinitialize database
   python manage.py reset-db
   ```
3. **Port conflicts:**
   ```bash
   # Check what's using port 5000
   lsof -i :5000

   # Kill conflicting process
   kill -9 <PID>

   # Or use different port
   export PORT=8000
   python app.py
   ```
4. **Memory issues:**
   ```bash
   # Check system resources
   free -h
   df -h

   # Use smaller AI model
   export PRIMARY_MODEL=llama3.2:1b
   ```

### Debug Mode

Run in debug mode for detailed error information:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   * Check system health: `python manage.py check-health`
   * Review error logs: `grep ERROR logs/nhs_triage.log`
   * Update AI models: `ollama pull llama3.2:3b`
2. **Monthly:**
   * Clean up old data: `python manage.py cleanup-data`
   * Export data backup: `python manage.py export-data`
   * Review system statistics: `python manage.py show-stats`
3. **Quarterly:**
   * Update dependencies: `pip install -r requirements.txt --upgrade`
   * Security audit and updates
   * Performance optimization review

### Getting Help

1. **Check logs first:**
   ```bash
   tail -n 100 logs/nhs_triage.log
   ```
2. **Run health check:**
   ```bash
   python manage.py check-health
   ```
3. **Test individual components:**
   ```bash
   # Test database
   python -c "from app import db; print('DB OK' if db else 'DB Error')"

   # Test Ollama
   curl http://localhost:11434/api/version

   # Test web service
   curl http://localhost:5000/api/system-status
   ```

## ⚠️ Important Disclaimers

1. **Medical Disclaimer** : This system is for demonstration purposes only and should not be used for actual medical diagnosis or treatment.
2. **Data Privacy** : Ensure compliance with GDPR, NHS data protection policies, and local healthcare regulations.
3. **Security** : This is a reference implementation. For production use, implement proper security measures, authentication, and encryption.
4. **Liability** : Users are responsible for ensuring the system meets their specific requirements and regulatory compliance.

## 🎯 Next Steps

After successful installation:

1. **Customize symptom categories** in `config.py`
2. **Add authentication system** for staff dashboard
3. **Implement proper logging and monitoring**
4. **Set up automated backups**
5. **Configure SSL/HTTPS for production**
6. **Add integration with existing NHS systems**
7. **Implement audit trails for compliance**

## 📝 License and Compliance

* Review local healthcare software regulations
* Ensure GDPR compliance for patient data
* Implement appropriate data retention policies
* Add proper medical disclaimers
* Consider medical device regulations if applicable

---

**🏥 NHS Digital Triage System v1.0**

For technical support or questions about this implementation, please review the troubleshooting section and check the application logs.
