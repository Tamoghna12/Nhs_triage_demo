# chat_fix.sh - Fix NHS Digital Triage Chat
#!/bin/bash

echo "🔧 NHS Digital Triage Chat Fix"
echo "=============================="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "✅ Ollama is installed"
fi

# Check if Ollama service is running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🚀 Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!
    echo "Ollama started with PID: $OLLAMA_PID"
    
    # Wait for service to start
    echo "⏳ Waiting for Ollama to start..."
    sleep 10
else
    echo "✅ Ollama service is already running"
fi

# Check if the model is available
echo "🤖 Checking AI model..."
if ! ollama list | grep -q "gemma3:4b"; then
    echo "📥 Downloading AI model (this may take a few minutes)..."
    ollama pull gemma3:4b
else
    echo "✅ AI model is available"
fi

# Test Ollama connection
echo "🔍 Testing Ollama connection..."
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "✅ Ollama is responding correctly"
    
    # Test model generation
    echo "🧪 Testing AI model..."
    curl -s http://localhost:11434/api/generate -d '{
        "model": "gemma3:4b",
        "prompt": "Hello, how are you?",
        "stream": false
    }' | grep -q "response"
    
    if [ $? -eq 0 ]; then
        echo "✅ AI model is working correctly"
    else
        echo "⚠️ AI model test failed"
    fi
else
    echo "❌ Ollama is not responding"
    echo "Try restarting: killall ollama && ollama serve"
fi

echo ""
echo "🏥 NHS Chat Status:"
echo "- Ollama Service: $(pgrep -f 'ollama serve' > /dev/null && echo 'Running' || echo 'Not Running')"
echo "- API Endpoint: $(curl -s http://localhost:11434/api/version > /dev/null && echo 'Available' || echo 'Unavailable')"
echo "- AI Model: $(ollama list | grep -q 'gemma3:4b' && echo 'Ready' || echo 'Not Downloaded')"

echo ""
echo "🔄 Next steps:"
echo "1. Restart your Flask app: python app.py"
echo "2. Try the chat again at http://localhost:5000/chat"
echo "3. If still having issues, check the troubleshooting section below"

echo ""
echo "🚨 Troubleshooting:"
echo "- If port 11434 is busy: sudo lsof -i :11434"
echo "- Manual restart: killall ollama && ollama serve"
echo "- Check logs: journalctl -u ollama -f"# chat_fix.sh - Fix NHS Digital Triage Chat
#!/bin/bash

echo "🔧 NHS Digital Triage Chat Fix"
echo "=============================="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "✅ Ollama is installed"
fi

# Check if Ollama service is running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🚀 Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!
    echo "Ollama started with PID: $OLLAMA_PID"
    
    # Wait for service to start
    echo "⏳ Waiting for Ollama to start..."
    sleep 10
else
    echo "✅ Ollama service is already running"
fi

# Check if the model is available
echo "🤖 Checking AI model..."
if ! ollama list | grep -q "gemma3:4b"; then
    echo "📥 Downloading AI model (this may take a few minutes)..."
    ollama pull gemma3:4b
else
    echo "✅ AI model is available"
fi

# Test Ollama connection
echo "🔍 Testing Ollama connection..."
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "✅ Ollama is responding correctly"
    
    # Test model generation
    echo "🧪 Testing AI model..."
    curl -s http://localhost:11434/api/generate -d '{
        "model": "gemma3:4b",
        "prompt": "Hello, how are you?",
        "stream": false
    }' | grep -q "response"
    
    if [ $? -eq 0 ]; then
        echo "✅ AI model is working correctly"
    else
        echo "⚠️ AI model test failed"
    fi
else
    echo "❌ Ollama is not responding"
    echo "Try restarting: killall ollama && ollama serve"
fi

echo ""
echo "🏥 NHS Chat Status:"
echo "- Ollama Service: $(pgrep -f 'ollama serve' > /dev/null && echo 'Running' || echo 'Not Running')"
echo "- API Endpoint: $(curl -s http://localhost:11434/api/version > /dev/null && echo 'Available' || echo 'Unavailable')"
echo "- AI Model: $(ollama list | grep -q 'gemma3:4b' && echo 'Ready' || echo 'Not Downloaded')"

echo ""
echo "🔄 Next steps:"
echo "1. Restart your Flask app: python app.py"
echo "2. Try the chat again at http://localhost:5000/chat"
echo "3. If still having issues, check the troubleshooting section below"

echo ""
echo "🚨 Troubleshooting:"
echo "- If port 11434 is busy: sudo lsof -i :11434"
echo "- Manual restart: killall ollama && ollama serve"
echo "- Check logs: journalctl -u ollama -f"