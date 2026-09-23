# Library Postgres (Devops)

- Cluster: personal-site managed Postgres (DO, fra1)
- Database: shared with personal site — **schema isolation only**
- Schema: `library`
- Role: `library_app` (USAGE+CREATE on `library`; no public schema)
- Role `search_path` set server-side to `library`
- App env: local/gitignored file with `DATABASE_URL` (never commit passwords)
- SSL: `sslmode=require`

Django tip: `dj_database_url` / `DATABASE_URL` with `options=-csearch_path=library`.

Note: some agent/box egress to managed Postgres ports times out. If migrate fails from an untrusted IP, allow that egress IP on the DB firewall or run migrate/seed from a droplet already trusted by the firewall.

## Demo seed (admin/staff + fake catalog)

Run from a host that can reach the DB:

```bash
cd /path/to/Library
# export DATABASE_URL=... (and DJANGO_SETTINGS_MODULE if using production settings)
python scripts/seed_library_demo.py
```

Creates/updates: `admin`/`admin` (superuser), `staff`/`staff` (staff only),
6 categories, 4 publishers, 20 books, 12 members, 15 borrow records, 6 comments.
Idempotent-ish (`update_or_create`; seed borrows tagged `created_by=seed_demo` are replaced).
