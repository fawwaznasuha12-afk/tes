# OsD0S API

Small FastAPI service for user registration, JWT login, and a minimal admin panel for user moderation. Built as a practice project for auth flows and role based access control.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy ORM (SQLite by default, PostgreSQL when `DATABASE_URL` is set)
- passlib bcrypt password hashing
- python-jose JWT tokens

## Run locally

```
pip install -r requirements.txt
uvicorn main:app --reload --port 7860
```

Interactive docs are served at `http://localhost:7860/docs`.

## Run with Docker

```
docker build -t osdos-api .
docker run -p 7860:7860 osdos-api
```

## Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./osdos.db` | `postgres://` URLs are rewritten to `postgresql://` |
| `SECRET_KEY` | hardcoded in `main.py` | change it before deploying |

## Endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/register` | none | Create a user. The first account becomes admin. |
| POST | `/token` | none | OAuth2 password login, returns a JWT. |
| GET | `/me` | bearer | Current user profile. |
| GET | `/admin/users` | admin | List all users. |
| POST | `/admin/action` | admin | Set status to `banned`, `kicked`, `muted`, or `active`. |
| POST | `/admin/lock-feature` | admin | Store a locked feature flag on a user. |

## Notes

This is a learning project, not production ready. The secret key is hardcoded, tokens expire after 3000 minutes, and the feature lock is stored as a single string on the user row.
