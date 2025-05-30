# =============================================================================
# deploy.sh - Deployment script
# =============================================================================

#!/bin/bash
# deploy.sh - NHS Digital Triage Deployment Script

set -e  # Exit on any error

echo "🏥 NHS Digital Triage Deployment Script"
echo "========================================"

# Configuration
PROJECT_NAME="nhs-digital-triage"
PYTHON_VERSION="3.11"
OLLAMA_MODEL="gemma3:4b"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root."
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command_exists pip; then
    echo "❌ pip is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source fairdoc/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs templates/errors static data

# Set environment variables
export FLASK_ENV=production
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Initialize database
echo "🗄️ Initializing database..."
python manage.py init-db --env production

# Install and setup Ollama if not present
if ! command_exists ollama; then
    echo "🤖 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Start Ollama service
    echo "🚀 Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to start
    sleep 10
    
    # Pull the model
    echo "📥 Downloading AI model (this may take a while)..."
    ollama pull $OLLAMA_MODEL
else
    echo "✅ Ollama already installed"
    
    # Check if model exists
    if ! ollama list | grep -q $OLLAMA_MODEL; then
        echo "📥 Downloading AI model..."
        ollama pull $OLLAMA_MODEL
    else
        echo "✅ AI model already available"
    fi
fi

# Run health check
echo "🏥 Running health check..."
python manage.py check-health --env production

# Create systemd service file for production
if [ "$1" = "--systemd" ]; then
    echo "📋 Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/$PROJECT_NAME.service"
    
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=NHS Digital Triage System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
Environment=FLASK_ENV=production
ExecStart=$(pwd)/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable $PROJECT_NAME
    
    echo "✅ Systemd service created and enabled"
    echo "💡 Start with: sudo systemctl start $PROJECT_NAME"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   python app.py"
echo ""
echo "🌐 The application will be available at:"
echo "   http://localhost:5000"
echo ""
echo "📋 Management commands:"
echo "   python manage.py --help"
echo ""
echo "🔧 To stop Ollama (if started by this script):"
if [ ! -z "$OLLAMA_PID" ]; then
    echo "   kill $OLLAMA_PID"
fi