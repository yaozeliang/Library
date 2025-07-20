# Library Management System

A comprehensive Django-based library management system with modern code quality standards.
## 🚀 Features

- **Book Management**: Add, edit, delete, and search books
- **Member Management**: Manage library members with card system
- **Borrowing System**: Track book borrowing and returns
- **User Authentication**: Secure login and registration
- **Admin Interface**: Full Django admin integration
- **Comments System**: User feedback and discussions
- **Modern UI**: Bootstrap-based responsive design
- **Code Quality**: Ruff-formatted and linted codebase

## 🛠️ Technology Stack

- **Backend**: Django 2.2.10
- **Database**: SQLite (configurable for production)
- **Frontend**: Bootstrap 4, Tailwind CSS
- **Code Quality**: Ruff (replacing Black, isort, flake8, mypy)
- **Forms**: Django Crispy Forms
- **Rich Text**: CKEditor
- **Date/Time**: Flatpickr
- **API**: Django REST Framework

## 📋 Requirements

- Python 3.8+
- Django 2.2.10
- See `pyproject.toml` for complete dependencies

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Library
```

### 2. Set Up Virtual Environment

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using uv (recommended)
uv venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using uv
uv pip install -e .
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to access the application.

## 🎯 Code Quality with Ruff

This project uses **Ruff** for code formatting and linting, providing:

- **Fast Performance**: 10-100x faster than traditional tools
- **Comprehensive Rules**: Combines Black, isort, flake8, and more
- **Auto-fixing**: Automatically fixes many issues
- **Modern Standards**: Enforces PEP 8 and modern Python practices

### Running Ruff

```bash
# Format code
ruff format .

# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Or use the provided script
python run_ruff.py
```

### Ruff Configuration

The project includes comprehensive Ruff configuration in `pyproject.toml`:

- **Line Length**: 88 characters (Black standard)
- **Target Python**: 3.8+
- **Quote Style**: Double quotes
- **Import Sorting**: Automatic with first-party module recognition
- **Comprehensive Rules**: 50+ rule sets enabled

## 📁 Project Structure

```
Library/
├── core/                   # Django project settings
├── book/                   # Book management app
│   ├── models.py          # Book, Member, BorrowRecord models
│   ├── views.py           # Book management views
│   ├── forms.py           # Book-related forms
│   └── admin.py           # Admin interface
├── authentication/         # User authentication app
├── comment/               # Comments system
├── util/                  # Utility functions
├── templates/             # HTML templates
├── static/                # Static files (CSS, JS, images)
├── media/                 # User-uploaded files
├── pyproject.toml         # Project configuration and dependencies
└── run_ruff.py           # Ruff execution script
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
SERVER=127.0.0.1
```

### Database Configuration

The project uses SQLite by default. For production, update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚀 Deployment

### Pre-deployment Preparation

1. **Clean up unnecessary files**:
   ```bash
   python cleanup.py
   ```

2. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your production settings
   ```

3. **Install production dependencies**:
   ```bash
   uv sync --extra production
   ```

### Deployment Options

#### Docker Deployment
```bash
# Build the Docker image
docker build -t library-management .

# Run with environment variables
docker run -p 8000:8000 --env-file .env library-management

# Or use Docker Compose
docker-compose up --build
```

#### Heroku Deployment
```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=your-database-url
git push heroku main
```

#### Railway Deployment
```bash
# Install Railway CLI
railway login
railway init
railway add postgresql
railway deploy
```

#### AWS ECS/Fargate
1. Build and push Docker image to ECR
2. Create ECS task definition
3. Deploy to ECS service

### Environment Variables

Required environment variables for production:
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: Database connection string
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `REDIS_URL`: Redis connection string (optional)
- `EMAIL_HOST_USER`: SMTP email username
- `EMAIL_HOST_PASSWORD`: SMTP email password

### Security Considerations

1. **Change default admin URL** in production
2. **Use HTTPS** in production
3. **Set up proper CORS** if needed
4. **Configure CSP headers**
5. **Use environment variables** for sensitive data
6. **Enable security middleware**
7. **Set up monitoring** with Sentry

### Manual Deployment

1. Set `DEBUG = False` in settings
2. Configure production database
3. Collect static files: `python manage.py collectstatic`
4. Set up web server (nginx + gunicorn)

## 📊 API Documentation

The project includes Django REST Framework for API access:

- **Books API**: `/api/books/`
- **Members API**: `/api/members/`
- **Borrow Records API**: `/api/borrow-records/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run Ruff: `python run_ruff.py`
5. Submit a pull request

## 📝 Code Style

This project follows strict Python code quality standards:

- **PEP 8**: Python style guide compliance
- **Type Hints**: Full type annotation
- **Docstrings**: Comprehensive documentation
- **Import Sorting**: Automatic import organization
- **Line Length**: 88 characters maximum

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🆘 Support

For support and questions:

1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**Built with ❤️ using Django and Ruff**
