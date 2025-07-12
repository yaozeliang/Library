#!/bin/bash

# Django Library Management System Deployment Script
# This script handles the deployment process for cloud environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings_production}
MANAGE_PY="python manage.py"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check if Python is available
    if ! command -v python &> /dev/null; then
        log_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    # Check if uv is available
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed or not in PATH"
        exit 1
    fi
    
    # Check if required environment variables are set
    if [ -z "$SECRET_KEY" ]; then
        log_error "SECRET_KEY environment variable is not set"
        exit 1
    fi
    
    if [ -z "$DATABASE_URL" ]; then
        log_warn "DATABASE_URL is not set, using default SQLite"
    fi
    
    log_info "Requirements check passed"
}

install_dependencies() {
    log_info "Installing dependencies..."
    uv sync --frozen
    log_info "Dependencies installed successfully"
}

run_migrations() {
    log_info "Running database migrations..."
    $MANAGE_PY migrate --noinput
    log_info "Migrations completed successfully"
}

collect_static() {
    log_info "Collecting static files..."
    $MANAGE_PY collectstatic --noinput --clear
    log_info "Static files collected successfully"
}

create_superuser() {
    log_info "Creating superuser..."
    if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        $MANAGE_PY createsuperuser --noinput --email "$DJANGO_SUPERUSER_EMAIL" || log_warn "Superuser already exists"
    else
        log_warn "DJANGO_SUPERUSER_EMAIL or DJANGO_SUPERUSER_PASSWORD not set, skipping superuser creation"
    fi
}

run_checks() {
    log_info "Running Django system checks..."
    $MANAGE_PY check --deploy
    log_info "System checks passed"
}

run_tests() {
    if [ "$RUN_TESTS" = "true" ]; then
        log_info "Running tests..."
        $MANAGE_PY test
        log_info "Tests passed"
    else
        log_info "Skipping tests (RUN_TESTS not set to true)"
    fi
}

compress_static() {
    log_info "Compressing static files..."
    if $MANAGE_PY help compress &> /dev/null; then
        $MANAGE_PY compress --force
        log_info "Static files compressed"
    else
        log_warn "django-compressor not installed, skipping compression"
    fi
}

warm_cache() {
    log_info "Warming up cache..."
    if $MANAGE_PY help warm_cache &> /dev/null; then
        $MANAGE_PY warm_cache
        log_info "Cache warmed up"
    else
        log_warn "Cache warming command not available"
    fi
}

main() {
    log_info "Starting deployment for environment: $ENVIRONMENT"
    
    # Set Django settings module
    export DJANGO_SETTINGS_MODULE
    
    # Run deployment steps
    check_requirements
    install_dependencies
    run_checks
    run_migrations
    collect_static
    compress_static
    create_superuser
    warm_cache
    
    if [ "$ENVIRONMENT" != "production" ]; then
        run_tests
    fi
    
    log_info "Deployment completed successfully!"
    log_info "Application is ready to start"
}

# Handle script arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    migrate)
        run_migrations
        ;;
    collectstatic)
        collect_static
        ;;
    check)
        run_checks
        ;;
    test)
        run_tests
        ;;
    *)
        echo "Usage: $0 {deploy|migrate|collectstatic|check|test}"
        exit 1
        ;;
esac 