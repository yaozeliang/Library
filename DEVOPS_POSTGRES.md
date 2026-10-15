# Library Postgres (Devops)

- Managed Postgres, **schema isolation only**
- Schema: `library`
- Role: `library_app` (USAGE+CREATE on `library`; no public schema)
- Role `search_path` set server-side to `library`
- App env: local/gitignored file with `DATABASE_URL` (never commit passwords)
- SSL: `sslmode=require`

Django tip: `dj_database_url` / `DATABASE_URL` with `options=-csearch_path=library`.

Note: if migrate fails from an untrusted IP, run migrate/seed from a host allowed by the database firewall.

## Demo seed (admin/staff + fake catalog)

Run from a host that can reach the DB:

```bash
cd /path/to/Library
# export DATABASE_URL=... (and DJANGO_SETTINGS_MODULE if using production settings)
python scripts/seed_library_demo.py
```

Creates/updates: `admin` (superuser) and `staff` (staff only), plus
6 categories, 4 publishers, 20 books, 12 members, 15 borrow records, 6 comments.
Seeded users get throwaway local development passwords. Set `DEMO_ADMIN_PASSWORD`
(placeholder only; see `env.example`) before seeding a shared host.
Re-running does not change existing passwords. Pass `--reset-passwords` or set
`DEMO_RESET_PASSWORDS=1` to rewrite the local defaults on purpose.
On a shared host, change every seeded password right after the first seed.
Idempotent-ish (`update_or_create`; seed borrows tagged `created_by=seed_demo` are replaced).
