# Gastor - Dockerfile para Hugging Face Spaces
# ============================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for some ML libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker cache optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY src/ ./src/
COPY assets/ ./assets/
COPY image/ ./image/

# Copy pre-trained model (if exists)
COPY model_latest.joblib ./model_latest.joblib

# Copy trades data (optional, for demo)
COPY trades.json ./trades.json

# Expose Streamlit default port (required by HF Spaces)
EXPOSE 7860

# Hugging Face Spaces requires port 7860
# Streamlit health check endpoint
HEALTHCHECK CMD curl --fail http://localhost:7860/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
