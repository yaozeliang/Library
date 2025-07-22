# Use Python 3.8 slim image for better compatibility
FROM python:3.8-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Create non-root user
RUN groupadd -r django && useradd -r -g django django

# Set working directory
WORKDIR /app

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock* README.md ./

# Create virtual environment and install dependencies
RUN uv venv && \
    uv pip install --system .[production]

# Copy project files
COPY --chown=django:django . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /var/log/django && \
    chown -R django:django /app /var/log/django

# Switch to non-root user
USER django

# Set default environment variables for build (use local storage)
ENV SECRET_KEY=build-secret-key \
    DEBUG=False \
    GS_BUCKET_NAME=local-build-storage \
    GS_PROJECT_ID=local-build

# Collect static files using local storage during build
RUN python manage.py collectstatic --noinput --settings=core.settings || true

# Health check (remove specific endpoint check for Cloud Run)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port (Cloud Run will override with PORT env var)
EXPOSE 8000
ENV PORT=8000
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "core.wsgi"]
