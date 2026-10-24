# Bug Diary API

A personal knowledge base of bugs you have already fixed: what broke, why, how you fixed it and how many minutes it cost you. Stop stepping on the same rake twice.

**Stack:** Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 16, Docker.

## Quick start

**Important:** .env variables are required to run the app.

```bash
docker compose up --build
```

| What | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

## Architecture

```
 host :8000 ──►  backend (FastAPI)  ──── app-net ────►  db (PostgreSQL 16)
                 built from                              named volume: bugdiary_db_data
                 backend/Dockerfile                      (no port published)
```

* **backend**: custom image built from `backend/Dockerfile` (slim base, cached dependency layer, `HEALTHCHECK`).
* **db**: official `postgres:16-alpine`. Its port is **not** published to the host; only the backend can reach it.
* **Network:** both services are on the user-defined bridge network `app-net`. The backend connects to the database using the service name `db` as the hostname (`POSTGRES_HOST=db`), never `localhost`.
* **Startup order:** the database has a `pg_isready` healthcheck and the backend uses `depends_on: condition: service_healthy`.
* **Persistence:** the named volume `bugdiary_db_data` is mounted at `/var/lib/postgresql/data`.

## Project structure

```
bug-diary/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # app, lifespan (wait for DB, create tables)
│       ├── config.py        # environment variables configuration
│       ├── database.py      # engine, session
│       ├── models.py        # SQLAlchemy model
│       ├── schemas.py       # Pydantic models and validation rules
│       └── routers/bugs.py  # CRUD + stats endpoints
├── docker-compose.yml
├── .env                     # Required environment variables
├── postman_collection.json
└── README.md                # Project docs.
```

## Useful commands

```bash
docker compose up                # start without app build
docker compose up --build        # start with app build
docker compose down              # stop, keep data
docker compose down -rmi --all   # stop and DELETE images
docker compose down -v           # stop and DELETE data
docker compose ps                # status
```

## Postman

1. Import `postman_collection.json` (Postman: *Import* > select the file).
2. Make sure the stack is running (`docker compose up`).
3. Run the requests in order, or use the *Collection Runner*.

The collection variable `baseUrl` is `http://localhost:8000`. The `Create bug` request saves the new ID into the variable `bugId` with a test script, so *Get*, *Update* and *Delete* work as a chain. Every request has test assertions on status codes and response shape.

## Documentation

### Data model: `bugs`

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Primary key, assigned automatically |
| `title` | string | Required, 1-120 characters |
| `error_message` | string | Required |
| `language` | enum | `python`, `javascript`, `typescript`, `java`, `go`, `sql`, `bash`, `docker`, `other` |
| `category` | enum | `syntax`, `logic`, `config`, `dependency`, `network`, `database`, `typo`, `other` |
| `severity` | integer | Required, 1-5 |
| `cause` | string | Optional, **required if `fixed` is true** |
| `solution` | string | Optional, **required if `fixed` is true** |
| `time_wasted_min` | integer | >= 0, default 0 |
| `fixed` | boolean | Default `false` |
| `tags` | array of strings | Max 10, normalized to lowercase and de-duplicated (stored as a PostgreSQL `ARRAY`) |
| `created_at` | datetime | Defaults to now. May be supplied on create. On PATCH, omitting it keeps the stored value |
| `fixed_at` | datetime | Only allowed if `fixed` is true. Defaults to now. Must not be earlier than `created_at`. On PATCH, omitting it keeps the stored value |

### API reference

Base URL: `http://localhost:8000`.

| Method | Path | Description | Success | Errors |
|---|---|---|---|---|
| `GET` | `/bugs` | List bugs (filters, sorting, pagination) | `200` | `422` |
| `GET` | `/bugs/{id}` | Get one bug | `200` | `404`, `422` |
| `POST` | `/bugs` | Create a bug | `201` | `422` |
| `PATCH` | `/bugs/{id}` | Replace a bug (all writable fields) | `200` | `404`, `422` |
| `DELETE` | `/bugs/{id}` | Delete a bug | `204` (no body) | `404` |
| `GET` | `/bugs/stats` | Aggregated statistics | `200` | none |
| `GET` | `/health` | Service and database health | `200` | `503` |

#### `GET /bugs`

Query parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `language` | enum | none | Exact match |
| `category` | enum | none | Exact match |
| `fixed` | boolean | none | `true` or `false` |
| `min_time_wasted` | integer | none | Only bugs with `time_wasted_min >=` this value |
| `q` | string | none | Case-insensitive search in `title`, `error_message`, `cause` |
| `sort` | string | `-created_at` | Field name, prefix `-` for descending. Allowed: `id`, `title`, `severity`, `time_wasted_min`, `created_at`, `fixed_at`, `language`, `category` |
| `limit` | integer | `20` | 1-100 |
| `offset` | integer | `0` | Items to skip |

Response `200`:

```json
{
  "items": [ { "id": 1, "title": "...", "...": "..." } ],
  "total": 8,
  "limit": 20,
  "offset": 0
}
```

#### `GET /bugs/{id}`

Response `200`: a bug object. Response `404`: `{"detail": "Bug 999 not found"}`.

#### `POST /bugs`

Request body:

```json
{
  "title": "CORS error when calling the API from the frontend",
  "error_message": "Access to fetch at 'http://localhost:8000/bugs' has been blocked by CORS policy",
  "language": "javascript",
  "category": "config",
  "severity": 2,
  "cause": "The backend did not send Access-Control-Allow-Origin headers",
  "solution": "Added CORSMiddleware with the frontend origin to the allowed list",
  "time_wasted_min": 35,
  "fixed": true,
  "tags": ["cors", "browser", "fastapi"]
}
```

Response `201`: the created bug including `id`, `created_at`, `fixed_at`. Response `422` on validation failure, for example `fixed: true` without `solution`.

#### `PATCH /bugs/{id}`

Same body as `POST`; every writable field is replaced. Response `200`: the updated bug. `404` if the ID does not exist, `422` on validation failure.

#### `DELETE /bugs/{id}`

Response `204` with an empty body. `404` if the ID does not exist.

#### `GET /bugs/stats`

Response `200`:

```json
{
  "total_bugs": 8,
  "fixed": 7,
  "unfixed": 1,
  "total_time_wasted_min": 355,
  "by_category": { "network": { "count": 1, "time_wasted_min": 45 } },
  "by_language": { "python": { "count": 3, "time_wasted_min": 255 } },
  "most_expensive_category": "logic"
}
```

#### `GET /health`

Response `200`: `{"status": "ok", "database": "up"}`. Response `503`: `{"detail": "Database is unreachable"}`.

### Error format

* `404`, `503`, and business-rule errors from the API: `{"detail": "message"}`
* `422` from request validation: `{"detail": [ { "loc": [...], "msg": "...", "type": "..." } ]}`
