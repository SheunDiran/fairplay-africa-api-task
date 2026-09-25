# FairPlay Africa Content Registration API

A compact demonstration REST API for account authentication and registering/retrieving content records. This is an internship technical-task project—not a production FairPlay Africa service.

## Features

- Account registration with case-insensitive unique email addresses and securely hashed passwords.
- Login with short-lived JWT access tokens.
- Authenticated content registration with a generated `FPA-...` reference.
- Paginated content retrieval scoped to the authenticated user.
- Record-level ownership checks; another user's record is returned as `404`.
- Input validation, consistent JSON errors, migration support, and automated tests.

## Tech stack

Python 3.12+, Flask, Flask-SQLAlchemy/SQLAlchemy, Flask-Migrate (Alembic), Flask-JWT-Extended, SQLite for local development, PostgreSQL support through Psycopg, and pytest.

## Architecture

```text
Client --JSON + Bearer JWT--> Flask routes --SQLAlchemy--> relational database
                                  |                         |
                             JWT identity              users 1-to-many content
```

Registration/login routes validate inputs and use Werkzeug password hashing. Protected routes validate the JWT, derive the user ID from its identity claim (never from a client-supplied owner ID), and constrain queries by that user. The database enforces unique email/reference values and a foreign key from content to its owner.

## Quick start

Requirements: Python 3.10+ and Git. SQLite is bundled with Python; PostgreSQL is optional.

```bash
git clone https://github.com/SheunDiran/fairplay-africa-api-task.git
cd fairplay-africa-api-task
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and replace **both** signing-secret values with independent random values. For example, generate each using `python -c "import secrets; print(secrets.token_hex(32))"`. Never commit `.env` or reuse these values in source control.

The default database is SQLite (`instance/fairplay.db`, managed by Flask-SQLAlchemy). To use PostgreSQL, create a database and set `DATABASE_URL` in `.env`, for example:

```dotenv
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/fairplay_api
```

Apply schema migrations and start the development server:

```bash
flask --app run.py db upgrade
python run.py
```

The API is available at `http://127.0.0.1:5000`. `GET /api/health` is a public health check. For production-like hosting, use the included `Procfile`/Gunicorn command and set strong secrets and a managed PostgreSQL URL through the host's secret/environment settings. Do not use Flask's development server or SQLite for a public production deployment.

### Database migrations

Existing schema: `flask --app run.py db upgrade`

After changing models:

```bash
flask --app run.py db migrate -m "describe the schema change"
flask --app run.py db upgrade
```

Review generated migration scripts before committing them.

## API conventions

Successful responses use `{"success": true, "data": ...}`; errors use `{"success": false, "error": {"code": "...", "message": "..."}}`. Protected routes require `Authorization: Bearer <access_token>`. JSON request bodies must have `Content-Type: application/json`.

### `POST /api/auth/register` — public

Request:

```json
{"name":"Ada Lovelace","email":"ada@example.com","password":"correct-horse-9"}
```

Returns `201 Created` with the public user fields; never returns the password hash:

```json
{"success":true,"data":{"id":1,"name":"Ada Lovelace","email":"ada@example.com","created_at":"2026-09-25T12:00:00+00:00"}}
```

Duplicate email returns `409`; invalid or missing fields return `422`. Example error:

```json
{"success":false,"error":{"code":"email_taken","message":"An account with this email already exists."}}
```

### `POST /api/auth/login` — public

Request:

```json
{"email":"ada@example.com","password":"correct-horse-9"}
```

Returns `200 OK`:

```json
{"success":true,"data":{"access_token":"<JWT>","token_type":"Bearer"}}
```

Incorrect credentials return `401`; missing credentials return `422`.

### `POST /api/content` — Bearer token required

Request:

```json
{"title":"My Short Film","description":"An original short film.","content_type":"video"}
```

Returns `201 Created` with the created record, its integer `id`, timestamps, and generated `registration_reference`. The authenticated account is assigned as owner by the server:

```json
{"success":true,"data":{"id":1,"title":"My Short Film","description":"An original short film.","content_type":"video","registration_reference":"FPA-8C541DA57B3B4D3AA0981E43B07C4B8A","created_at":"2026-09-25T12:00:00+00:00","updated_at":"2026-09-25T12:00:00+00:00"}}
```

Invalid fields return `422`; missing/invalid authentication returns `401`.

### `GET /api/content` — Bearer token required

Returns only the current user's records, newest first, plus pagination metadata. Optional query parameters are `page` (default `1`) and `per_page` (default `20`, maximum `100`). Example: `GET /api/content?page=1&per_page=20`.

```json
{"success":true,"data":[{"id":1,"title":"My Short Film","description":"An original short film.","content_type":"video","registration_reference":"FPA-8C541DA57B3B4D3AA0981E43B07C4B8A","created_at":"2026-09-25T12:00:00+00:00","updated_at":"2026-09-25T12:00:00+00:00"}],"meta":{"page":1,"per_page":20,"total":1,"pages":1}}
```

Invalid pagination returns `400`.

### `GET /api/content/<id>` — Bearer token required

Returns a single record only if it belongs to the authenticated user. Example `200 OK` response:

```json
{"success":true,"data":{"id":1,"title":"My Short Film","description":"An original short film.","content_type":"video","registration_reference":"FPA-8C541DA57B3B4D3AA0981E43B07C4B8A","created_at":"2026-09-25T12:00:00+00:00","updated_at":"2026-09-25T12:00:00+00:00"}}
```

Missing and other-user records both return `404` to avoid disclosing ownership/existence; missing/invalid authentication returns `401`.

### `GET /api/health` — public

Returns `200 OK` and `{"success":true,"data":{"status":"ok"}}` when the app is serving requests.

### Common error codes

| Status | Code | Meaning |
| --- | --- | --- |
| 400 | `invalid_json`, `invalid_pagination` | Malformed JSON or pagination values |
| 401 | `authentication_required`, `invalid_token`, `token_expired`, `invalid_credentials` | Authentication failed or is missing |
| 404 | `not_found` | Record is missing or not owned by this user |
| 409 | `email_taken`, `conflict` | Duplicate account or database conflict |
| 415 | `unsupported_media_type` | Request is not JSON |
| 422 | `validation_error` | Request fields are invalid |

## Try it with curl

After registering and logging in, store the token in `TOKEN` (do not paste real tokens into shared logs):

```bash
curl -s http://127.0.0.1:5000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ada Lovelace","email":"ada@example.com","password":"correct-horse-9"}'

TOKEN=$(curl -s http://127.0.0.1:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ada@example.com","password":"correct-horse-9"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["data"]["access_token"])')

curl -s http://127.0.0.1:5000/api/content \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"My Short Film","description":"An original short film.","content_type":"video"}'

curl -s http://127.0.0.1:5000/api/content -H "Authorization: Bearer $TOKEN"
```

Registration returns `409` on a repeated email; use a fresh address or reset the local SQLite database when repeating the full example.

## Tests

```bash
pytest -q
```

The suite exercises registration, duplicate and invalid input handling, password hashing, login success/failure, required/invalid/expired tokens, content creation and listing, ownership isolation, single-record access, nonexistent content, malformed/non-JSON bodies, and pagination validation. Tests use an isolated in-memory SQLite database.

## Design decisions and scope

- **JWT:** stateless Bearer-token authentication suited to a small REST API; access tokens expire after 30 minutes by default.
- **Ownership:** every content query filters by the user ID in the verified token, including single-record retrieval. The client cannot choose `user_id`.
- **References:** each record gets a high-entropy UUID-based, human-readable `FPA-` reference; the database enforces uniqueness.
- **Database:** SQLite keeps local evaluation friction low; SQLAlchemy and Psycopg support PostgreSQL with an environment-variable change and migrations.
- **Scope:** this API registers content metadata only; it does not upload/store media files, provide refresh tokens, or implement a production account-recovery flow.

## Submission/deployment status

The source repository is public at https://github.com/SheunDiran/fairplay-africa-api-task. The API has been tested locally but has not been deployed to a live hosting provider. Deploy only after configuring secrets and a database on a hosting provider; no paid infrastructure is included or required for local evaluation.
