"""
Gunicorn configuration for Cloud Run deployment
"""

import os

# Cloud Run injects PORT. The demo container (Docker behind Caddy) uses 8082.
port = os.environ.get("PORT", "8082")
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 1
worker_class = "sync"
timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Preload the application
preload_app = True
