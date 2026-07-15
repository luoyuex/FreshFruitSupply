# Fruit Quote API

FastAPI backend for the fruit quotation mini-program.

## Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Create a MySQL database, for example:

```sql
CREATE DATABASE fruit_quote CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Update `DATABASE_URL` in `.env`, then initialize tables and the default admin account:

```bash
python -m app.db.init_db
```

Start the API:

```bash
uvicorn app.main:app --reload
or
uvicorn app.main:app --host 0.0.0.0 --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.

Default seeded admin account: `admin` / `admin123456`.
Change it before production.
