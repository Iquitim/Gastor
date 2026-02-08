# Build stage
FROM public.ecr.aws/docker/library/python:3.9-slim AS builder

WORKDIR /app

# Install system dependencies for building packages (if needed)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN uv venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt

# Runtime stage
FROM public.ecr.aws/docker/library/python:3.9-slim

WORKDIR /app

# Install runtime dependencies (libpq needed for postgres)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Entrypoint
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Production command
ENTRYPOINT ["./entrypoint.sh"]
