FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p templates static logs

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV OLLAMA_BASE_URL=http://localhost:11434
ENV PRIMARY_MODEL=llama3.2:3b

# Expose ports
EXPOSE 5000 11434

# Create startup script
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=\$!

echo "Waiting for Ollama to be ready..."
sleep 10

echo "Pulling AI model..."
ollama pull \${PRIMARY_MODEL}

echo "Starting Flask application..."
python app.py &
FLASK_PID=\$!

echo "NHS Digital Triage System started successfully!"
echo "Ollama PID: \$OLLAMA_PID"
echo "Flask PID: \$FLASK_PID"

# Wait for both processes
wait \$OLLAMA_PID \$FLASK_PID
EOF

RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/system-status || exit 1

# Start the application
CMD ["/app/start.sh"]