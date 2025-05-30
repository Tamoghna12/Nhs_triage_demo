# NHS Digital Triage System

A comprehensive AI-powered medical triage system providing intelligent symptom assessment and medical guidance through both conversational chat and structured assessment interfaces.

## 🏥 Features

### Patient Interface

* **Chat Assistant** : Natural conversation with AI for quick medical guidance
* **Structured Triage** : Step-by-step comprehensive medical assessment
* **Symptom Categories** : Organized symptom selection (Pain, Respiratory, Digestive, etc.)
* **Urgency Classification** : AI-powered urgency level assessment
* **Real-time Streaming** : Live AI responses with typing indicators

### Healthcare Staff Dashboard

* **Patient Monitoring** : View all patient assessments and details
* **Assessment Analytics** : Real-time statistics and trends
* **Filtering & Search** : Advanced filtering by urgency, symptoms, dates
* **Contact Integration** : Direct patient contact capabilities
* **Assessment Details** : Comprehensive view of AI assessments

### Technical Features

* **AI Integration** : Powered by Ollama local AI models
* **Responsive Design** : Mobile-friendly interface
* **Real-time Updates** : Server-sent events for live AI streaming
* **Secure Storage** : SQLite database with patient privacy protection
* **Modern UI** : Clean, accessible NHS-style design

## 🚀 Quick Start

### Prerequisites

* Python 3.8+
* Ollama installed and running
* Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nhs-digital-triage
   ```
2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install and setup Ollama**
   ```bash
   # Install Ollama (visit https://ollama.ai for platform-specific instructions)
   # Then pull the required model
   ollama pull llama3.2:3b
   ```
4. **Create templates directory structure**
   ```bash
   mkdir -p templates
   ```
5. **Add the HTML templates**
   * Save `index.html` in the `templates/` directory
   * Save `chat.html` in the `templates/` directory
   * Save `triage.html` in the `templates/` directory
   * Save `dashboard.html` in the `templates/` directory
6. **Run the application**
   ```bash
   python app.py
   ```
7. **Access the system**
   * Homepage: http://localhost:5000
   * Chat Interface: http://localhost:5000/chat
   * Structured Triage: http://localhost:5000/triage
   * Staff Dashboard: http://localhost:5000/staff-dashboard

## 📁 Project Structure

```
nhs-digital-triage/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── index.html        # Homepage
│   ├── chat.html         # Chat interface
│   ├── triage.html       # Structured triage
│   └── dashboard.html    # Staff dashboard
└── nhs_triage.db         # SQLite database (created automatically)
```

## 🔧 Configuration

### Environment Variables

The application can be configured through environment variables:

* `OLLAMA_BASE_URL`: URL for Ollama API (default: http://localhost:11434)
* `PRIMARY_MODEL`: AI model to use (default: llama3.2:3b)
* `SECRET_KEY`: Flask secret key for sessions

### Database Configuration

The system uses SQLite by default. For production, update the `SQLALCHEMY_DATABASE_URI` in `app.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/nhs_triage'
```

## 🩺 Usage Guide

### For Patients

1. **Chat Assistant**
   * Visit `/chat` for natural conversation
   * Type symptoms or health concerns
   * Receive instant AI guidance
   * Get urgency recommendations
2. **Structured Triage**
   * Visit `/triage` for comprehensive assessment
   * Complete 4-step process:
     * Personal information
     * Symptom category selection
     * Detailed symptom information
     * AI assessment and recommendations

### For Healthcare Staff

1. **Dashboard Access**
   * Visit `/staff-dashboard`
   * View patient assessments
   * Filter by urgency, symptoms, dates
   * Contact patients directly
2. **Assessment Monitoring**
   * Real-time statistics
   * Emergency case alerts
   * Detailed patient information
   * AI assessment reviews

## 🔒 Security & Privacy

* Patient data stored locally in SQLite database
* Session-based user tracking
* No external data transmission (except to local Ollama)
* Configurable data retention policies
* Secure form handling and validation

## 🤖 AI Model Setup

### Default Model

The system uses `llama3.2:3b` by default, optimized for:

* Medical knowledge
* Conversational responses
* Triage assessment
* Safety recommendations

### Alternative Models

You can use other Ollama models by updating the `PRIMARY_MODEL` configuration:

```python
app.config['PRIMARY_MODEL'] = 'llama3:8b'  # For better accuracy
app.config['PRIMARY_MODEL'] = 'mistral'     # Alternative model
```

### Model Requirements

* Minimum 4GB RAM for 3B models
* 8GB+ RAM recommended for larger models
* GPU acceleration optional but recommended

## 📊 API Endpoints

### Patient Endpoints

* `POST /api/patient/register` - Register patient information
* `POST /api/chat` - Start chat conversation
* `GET /api/chat/stream/<message_id>` - Stream chat responses

### Triage Endpoints

* `POST /api/triage/submit` - Submit triage assessment
* `GET /api/triage/stream/<assessment_id>` - Stream AI assessment
* `POST /api/triage/save/<assessment_id>` - Save assessment results

### System Endpoints

* `GET /api/system-status` - System health and statistics

## 🚑 Emergency Protocols

The system implements NHS emergency protocols:

* **999 Emergency** : Life-threatening situations
* **NHS 111** : Urgent but non-emergency care
* **GP Appointment** : Standard medical concerns
* **Self-care** : Minor symptoms and guidance

## 🔧 Development

### Local Development

```bash
# Run in debug mode
export FLASK_ENV=development
python app.py
```

### Adding New Features

1. Update database models in `app.py`
2. Add new routes and API endpoints
3. Update HTML templates as needed
4. Test with various AI models

### Customization

* Modify symptom categories in `SYMPTOM_CATEGORIES`
* Update medical conditions in `MEDICAL_CONDITIONS`
* Customize AI prompts in `create_triage_prompt()`
* Adjust styling in template CSS

## 📝 License

This project is developed for educational and demonstration purposes. For production use in healthcare settings, ensure compliance with relevant medical software regulations and data protection laws.

## ⚠️ Disclaimer

This system is for demonstration purposes only and should not be used for actual medical diagnosis or treatment. Always consult qualified healthcare professionals for medical advice.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## 📞 Support

For technical support or questions:

* Check the console logs for error messages
* Ensure Ollama is running: `ollama serve`
* Verify model is installed: `ollama list`
* Check port availability (5000, 11434)

## 🔄 Updates

To update the system:

1. Pull latest changes
2. Install new dependencies: `pip install -r requirements.txt`
3. Update Ollama models: `ollama pull llama3.2:3b`
4. Restart the application
