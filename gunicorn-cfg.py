# -*- encoding: utf-8 -*-
"""
Gunicorn configuration for Cloud Run deployment
"""
import os

# Cloud Run uses PORT environment variable
port = os.environ.get('PORT', '8000')
bind = f'0.0.0.0:{port}'

# Worker configuration
workers = 1
worker_class = 'sync'
timeout = 120

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
capture_output = True
enable_stdio_inheritance = True

# Preload the application
preload_app = True
