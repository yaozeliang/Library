# Library Management System

Django 2.2 monolith for a small library: catalog, members, borrowing, and staff login. Local development uses SQLite. Demo and staging can use Postgres on a shared personal-site database, isolated in schema `library`.

## Features

- Books, categories, and publishers
- Members and library cards
- Borrow and return records
- Login, signup, and user profiles (`/auth/`)
- Comments
- Django admin
- JSON API under `/api/`
- Bootstrap 4 and Tailwind templates (django-crispy-forms, CKEditor, Flatpickr)

## Stack

- **Python:** 3.8. Django 2.2 does not run reliably on Python 3.13.
- **Django:** 2.2.10
- **Database:** SQLite by default. Optional Postgres through `DATABASE_URL` (see below).
- **Other:** Django REST Framework, WhiteNoise, and (in the production extra) Gunicorn and `psycopg2`.

Dependencies live in `pyproject.toml`. There is no root `requirements.txt`.

## Quick start

From a Python 3.8 environment:

```bash
git clone https://github.com/yaozeliang/Library.git
cd Library
python3.8 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/. The home page requires a login, so you are sent to http://127.0.0.1:8000/auth/login/.

`uv` is optional and matches CI: `uv sync --dev`, then `uv run python manage.py migrate` and `uv run python manage.py runserver`.

`psycopg2` is a direct dependency, so a normal install can open Postgres. The production extra adds Gunicorn, Redis, and Sentry:

```bash
pip install -e ".[production]"
```

### Demo data

After `migrate`, seed demo users and a fake catalog (local or demo/staging only):

```bash
python scripts/seed_library_demo.py
```

Do not run that script against a production database. For a private local superuser instead of the demo accounts, use `python manage.py createsuperuser`.

## Demo accounts

These accounts are for local demo data and the staging/demo site only. Do not use them in production.

| Username | Password | Role |
| --- | --- | --- |
| `admin` | `admin` | superuser |
| `staff` | `staff` | staff |

`scripts/seed_library_demo.py` creates them, along with the fake catalog. Sign in at `/auth/login/`.

Changing an avatar (including clearing it) should not 500 the home or profile page. `HomeView` treats an empty `profile_pic` as “no avatar” instead of reading `.url` on a missing file. The book tests cover that regression.

## Optional Postgres

Leave `DATABASE_URL` unset to keep SQLite (`db.sqlite3` via `core.settings`).

`DATABASE_URL` is supported in both `core.settings` and `core.settings_production` through `core/db_config.py`. An empty value keeps SQLite. Postgres uses `core.postgresql_backend`, because Django 2.2 only looks up constraints in schema `public` and this project keeps tables in schema `library` via `search_path`. The variable and a placeholder shape are in `env.example`. Set `DJANGO_SETTINGS_MODULE=core.settings_production` for the production configuration.

Demo/staging Postgres is **schema isolation on the shared personal-site database**, not a separate database named `library`. Tables belong in schema `library`. The application role is `library_app`. Set the connection `search_path` to `library` (URL-encoded `options=-csearch_path%3Dlibrary`).

```bash
# Placeholder only. Do not commit a real password, .env, or connection string.
export DJANGO_SETTINGS_MODULE=core.settings_production
export DATABASE_URL='postgres://library_app:<password>@<host>:<port>/<database>?sslmode=require&options=-csearch_path%3Dlibrary'
python manage.py migrate
python scripts/seed_library_demo.py
```

Schema creation, grants, and the rest of the ops steps are in [DEVOPS_POSTGRES.md](DEVOPS_POSTGRES.md).

## Testing

```bash
python manage.py test
```

Book tests include the empty-avatar regression (home/profile after an avatar change). CI runs the same command on Python 3.8.

## Demo / staging

The current public demo is an independent sslip.io host, not fillerwiki.

- Site: https://library.167-172-169-210.sslip.io/
- Login: https://library.167-172-169-210.sslip.io/auth/login/
- Accounts: `admin` / `admin` and `staff` / `staff` (demo only; see above)

## Configuration

Copy `env.example` to `.env` for local overrides (`SECRET_KEY`, `DEBUG`, `SERVER`, and optionally `DATABASE_URL`). `.env` is local only. Do not commit it or any real database password.

`core.settings` (what `manage.py` uses by default) turns `DEBUG` on and uses SQLite unless `DATABASE_URL` is set. Production settings read `ALLOWED_HOSTS`, `DATABASE_URL`, and the other variables listed in `env.example`.

## Project layout

```
Library/
├── core/                  # settings, URLs, WSGI
├── book/                  # catalog, members, borrow records, home
├── authentication/        # /auth/ login, signup, profile
├── comment/               # comments
├── Api/                   # /api/ JSON endpoints
├── scripts/               # seed_library_demo.py
├── templates/             # HTML
├── static/                # CSS, JS, images
├── pyproject.toml         # dependencies
├── env.example            # variable names, no real secrets
└── DEVOPS_POSTGRES.md     # schema and role setup for ops
```

## API

Base path `/api/`. Useful routes include:

- `/api/` overview
- `/api/book-list/`, `/api/book-detail/<id>/`
- `/api/members/`
- `/api/category-list/`, `/api/publisher-list/`

Django admin is `/admin/`.

## Deployment

The image in `Dockerfile` is Python 3.8 and is the container path in this repo (`gunicorn`, production extra). `core/settings_production.py` is the production settings module.

Older Heroku and Railway command lists are not how this demo is hosted. The current demo is https://library.167-172-169-210.sslip.io/. Postgres setup is in [DEVOPS_POSTGRES.md](DEVOPS_POSTGRES.md).

## License

MIT. See [LICENSE.md](LICENSE.md).
