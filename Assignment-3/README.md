# Football REST API

Stack: Python 3.12, FastAPI, SQLAlchemy 2 (ORM), PostgreSQL 16, Docker Compose.

## Data models

| Model      | Fields                                                              |
|------------|---------------------------------------------------------------------|
| **League** | `id`, `name`, `country`                                             |
| **Team**   | `id`, `name`, `city`, `founded_year`, `league_id` (FK)              |
| **Player** | `id`, `name`, `position`, `age`, `shirt_number`, `team_id` (FK)     |

Relationships:

* **League 1 → N Team** (one league has many teams)
* **Team 1 → N Player** (one team has many players)

Deleting a league also deletes its teams and their players (cascade).

## Quick start

Create `.env` from `.env.example` and fill in the values, then run:

```
docker compose up --build
```

Tables are created automatically on startup.

| What       | URL                        |
|------------|----------------------------|
| API        | http://localhost:8000      |
| Swagger UI | http://localhost:8000/docs |

## Postman

1. Import `postman/postman_collection.json`.
2. Make sure the application is running.
3. Run the collection top to bottom (or use the Collection Runner).

The `base_url` variable is `http://localhost:8000`. The "Create" requests save the new IDs into `league_id`, `team_id` and `player_id`, so the following requests work as a chain.

## Errors

| Status | When                                                                |
|--------|---------------------------------------------------------------------|
| `404`  | Resource (or the related league/team) does not exist                |
| `422`  | Request validation failed (missing field, wrong type, out of range) |

Error body: `{"detail": "League not found"}`. For `422`, `detail` is a list describing each invalid field.

## Endpoints

### Leagues

| Method | URL                         | Body     | Responses                              |
|--------|-----------------------------|----------|----------------------------------------|
| GET    | `/api/leagues`              | –        | `200` list of leagues                  |
| GET    | `/api/leagues/{id}`         | –        | `200` league, `404`                    |
| POST   | `/api/leagues`              | LeagueIn | `201` created league, `422`            |
| PUT    | `/api/leagues/{id}`         | LeagueIn | `200` updated league, `404`, `422`     |
| DELETE | `/api/leagues/{id}`         | –        | `204` no content, `404`                |
| GET    | `/api/leagues/{id}/teams`   | –        | `200` list of the league's teams, `404`|

**LeagueIn**

```json
{ "name": "Premier League", "country": "England" }
```

* `name` – string, required, 1–255 chars
* `country` – string, required, 1–100 chars

**League response**

```json
{ "id": 1, "name": "Premier League", "country": "England" }
```

### Teams

| Method | URL                         | Body         | Responses                                  |
|--------|-----------------------------|--------------|--------------------------------------------|
| GET    | `/api/teams`                | –            | `200` list of teams                        |
| GET    | `/api/teams/{id}`           | –            | `200` team, `404`                          |
| POST   | `/api/teams`                | TeamIn       | `201` created team, `404` (league), `422`  |
| PUT    | `/api/teams/{id}`           | TeamIn       | `200` updated team, `404`, `422`           |
| DELETE | `/api/teams/{id}`           | –            | `204` no content, `404`                    |
| GET    | `/api/teams/{id}/players`   | –            | `200` list of the team's players, `404`    |
| POST   | `/api/teams/{id}/players`   | PlayerCreate | `201` created player, `404`, `422`         |

**TeamIn**

```json
{ "name": "Arsenal", "city": "London", "founded_year": 1886, "league_id": 1 }
```

* `name` – string, required, 1–255 chars
* `city` – string, required, 1–100 chars
* `founded_year` – integer, optional, 1800–2100
* `league_id` – integer, required, must be an existing league

**Team response**

```json
{ "id": 1, "name": "Arsenal", "city": "London", "founded_year": 1886, "league_id": 1 }
```

### Players

| Method | URL                   | Body         | Responses                           |
|--------|-----------------------|--------------|-------------------------------------|
| GET    | `/api/players/{id}`   | –            | `200` player, `404`                 |
| PATCH  | `/api/players/{id}`   | PlayerUpdate | `200` updated player, `404`, `422`  |
| DELETE | `/api/players/{id}`   | –            | `204` no content, `404`             |

**PlayerCreate** (used by `POST /api/teams/{id}/players`)

```json
{ "name": "Bukayo Saka", "position": "FW", "age": 25, "shirt_number": 7 }
```

* `name` – string, required, 1–255 chars
* `position` – required, one of `GK`, `DF`, `MF`, `FW`
* `age` – integer, required, 15–50
* `shirt_number` – integer, required, 1–99

**PlayerUpdate** – same fields as PlayerCreate, all optional; only sent fields are changed

```json
{ "age": 26, "shirt_number": 10 }
```

**Player response**

```json
{ "id": 1, "team_id": 1, "name": "Bukayo Saka", "position": "FW", "age": 25, "shirt_number": 7 }
```

## Useful commands

```
docker compose up --build    # start with build
docker compose down          # stop, keep data
docker compose down -v       # stop and DELETE data
```
