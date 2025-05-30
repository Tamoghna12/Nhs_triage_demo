#!/usr/bin/env python3
"""
chat_diagnostics.py - NHS Digital Triage Chat Diagnostics

This script helps diagnose and fix chat issues.
"""

import subprocess
import requests
import json
import time
import sys
import os

def check_ollama_installation():
    """Check if Ollama is installed."""
    print("🔍 Checking Ollama installation...")
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama not found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Ollama not installed")
        return False

def check_ollama_service():
    """Check if Ollama service is running."""
    print("🔍 Checking Ollama service...")
    try:
        response = requests.get('http://localhost:11434/api/version', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ollama service running: v{data.get('version', 'unknown')}")
            return True
        else:
            print(f"❌ Ollama service responding with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama service not responding: {e}")
        return False

def check_ollama_models():
    """Check if required models are available."""
    print("🔍 Checking AI models...")
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            models = result.stdout
            if 'gemma3:4b' in models:
                print("✅ Required model (gemma3:4b) is available")
                return True
            else:
                print("❌ Required model (gemma3:4b) not found")
                print("Available models:")
                print(models)
                return False
        else:
            print("❌ Could not list models")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Timeout while checking models")
        return False

def test_ai_generation():
    """Test AI model generation."""
    print("🔍 Testing AI generation...")
    try:
        response = requests.post('http://localhost:11434/api/generate', 
                               json={
                                   'model': 'gemma3:4b',
                                   'prompt': 'Hello, how are you?',
                                   'stream': False
                               }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'response' in data and data['response'].strip():
                print(f"✅ AI generation working: '{data['response'][:50]}...'")
                return True
            else:
                print("❌ AI generation returned empty response")
                return False
        else:
            print(f"❌ AI generation failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ AI generation test failed: {e}")
        return False

def check_flask_app():
    """Check if Flask app is running."""
    print("🔍 Checking Flask application...")
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print("✅ Flask application is healthy")
                return True
            else:
                print("❌ Flask application is unhealthy")
                return False
        else:
            print(f"❌ Flask application responding with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Flask application not responding: {e}")
        return False

def test_chat_endpoint():
    """Test the chat API endpoint."""
    print("🔍 Testing chat endpoint...")
    try:
        # First create a session
        session = requests.Session()
        
        # Test chat endpoint
        response = session.post('http://localhost:5000/api/chat',
                              json={'message': 'Hello, this is a test'},
                              timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Chat endpoint working")
                return True
            else:
                print(f"❌ Chat endpoint returned error: {data.get('error')}")
                return False
        elif response.status_code == 503:
            print("⚠️ Chat endpoint reports AI service unavailable")
            return False
        else:
            print(f"❌ Chat endpoint failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat endpoint test failed: {e}")
        return False

def fix_ollama_issues():
    """Attempt to fix common Ollama issues."""
    print("\n🔧 Attempting to fix Ollama issues...")
    
    # Check if Ollama is installed
    if not check_ollama_installation():
        print("📥 Installing Ollama...")
        try:
            subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh'], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            subprocess.run(['sh'], input=open('install.sh', 'rb').read(), check=True)
            print("✅ Ollama installation completed")
        except Exception as e:
            print(f"❌ Ollama installation failed: {e}")
            return False
    
    # Start Ollama service
    if not check_ollama_service():
        print("🚀 Starting Ollama service...")
        try:
            # Kill any existing Ollama processes
            subprocess.run(['pkill', '-f', 'ollama'], stderr=subprocess.DEVNULL)
            time.sleep(2)
            
            # Start Ollama service
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait for service to start
            print("⏳ Waiting for service to start...")
            for i in range(10):
                time.sleep(2)
                if check_ollama_service():
                    print("✅ Ollama service started")
                    break
            else:
                print("❌ Ollama service failed to start")
                return False
        except Exception as e:
            print(f"❌ Failed to start Ollama service: {e}")
            return False
    
    # Download required model
    if not check_ollama_models():
        print("📥 Downloading required AI model...")
        try:
            result = subprocess.run(['ollama', 'pull', 'gemma3:4b'], 
                                  timeout=600, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ AI model downloaded successfully")
            else:
                print(f"❌ Model download failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Model download timed out")
            return False
    
    return True

def main():
    """Main diagnostic function."""
    print("🏥 NHS Digital Triage Chat Diagnostics")
    print("=" * 50)
    
    issues_found = []
    fixes_needed = []
    
    # Run all checks
    if not check_ollama_installation():
        issues_found.append("Ollama not installed")
        fixes_needed.append("install_ollama")
    
    if not check_ollama_service():
        issues_found.append("Ollama service not running")
        fixes_needed.append("start_ollama")
    
    if not check_ollama_models():
        issues_found.append("Required AI model missing")
        fixes_needed.append("download_model")
    
    if not test_ai_generation():
        issues_found.append("AI generation not working")
    
    if not check_flask_app():
        issues_found.append("Flask application not running")
        fixes_needed.append("start_flask")
    
    if not test_chat_endpoint():
        issues_found.append("Chat endpoint not working")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Diagnostic Summary")
    print("=" * 50)
    
    if not issues_found:
        print("🎉 All checks passed! Chat should be working.")
        print("\n🔗 Try the chat at: http://localhost:5000/chat")
        return 0
    else:
        print(f"❌ Found {len(issues_found)} issues:")
        for issue in issues_found:
            print(f"   • {issue}")
        
        if fixes_needed:
            print(f"\n🔧 Attempting automatic fixes...")
            if fix_ollama_issues():
                print("\n✅ Fixes applied successfully!")
                print("🔄 Please restart your Flask app: python app.py")
                print("🔗 Then try the chat at: http://localhost:5000/chat")
                return 0
            else:
                print("\n❌ Some fixes failed. Manual intervention needed.")
        
        print("\n📋 Manual fix steps:")
        print("1. Kill any existing processes: pkill -f ollama")
        print("2. Start Ollama: ollama serve")
        print("3. Download model: ollama pull gemma3:4b")
        print("4. Restart Flask: python app.py")
        print("5. Test chat: http://localhost:5000/chat")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())