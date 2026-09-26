# Python 3.12 matches Django 5.2 LTS.
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# git + ca-certificates: django-notifications-hq is pinned to a git URL.
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Create non-root user
RUN groupadd -r django && useradd -r -g django django

# Set working directory
WORKDIR /app

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock* README.md ./

# Install dependencies system-wide
RUN uv pip install --system --no-cache-dir .[production] && \
    which gunicorn && \
    gunicorn --version

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

# gunicorn-cfg.py binds 0.0.0.0:$PORT. The demo container listens on 8082
# (Caddy in front). Probing 8000 made Docker mark the container unhealthy.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8082/ || exit 1

# Cloud Run injects its own PORT at runtime. The demo image defaults to 8082.
EXPOSE 8082
ENV PORT=8082
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "core.wsgi"]
