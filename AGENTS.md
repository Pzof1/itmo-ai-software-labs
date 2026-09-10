# FastAPI Todo API: project instructions

## Project map

- `app/api/v1/` defines HTTP routes, dependencies, status codes, and response models.
- `app/service/` owns use-case decisions, HTTP errors, Pydantic conversion, and transaction commits.
- `app/repository/` is the only application layer that builds or executes SQLAlchemy statements.
- `app/models.py` and `app/schemas.py` define persistence and public contracts.
- `migrations/versions/` contains reversible Alembic migrations.
- `tests/test_api/` contains behavioral API tests.

For API changes, use the reusable `api-change` skill in `.agents/skills/api-change/SKILL.md`.

## Commands

Run from the repository root:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_conventions.py
.venv/bin/ruff check app tests
```

## Conventions

1. Keep SQLAlchemy queries and ORM writes in `app/repository/`. API and service code call repository functions instead of `select`, `update`, `delete`, `execute`, `add`, or `flush`.
2. Commit or roll back transactions in `app/service/`. Repository functions may flush when a generated ID is needed, but they do not commit.
3. Keep repositories independent from FastAPI. They return models, sequences, counts, or row counts; services translate those results into `HTTPException` responses.
4. Give every task route that returns JSON an explicit `response_model`. A route with status 204 is the exception.
5. Obtain the database session and current user in task routes through `Depends(get_db)` and `Depends(get_current_user)`.
6. For a missing task or one owned by somebody else, task services return status 404 with `detail=f"Task {task_id} not found"`. This deliberately avoids revealing whether another user's task exists.
7. Name API tests `test_<scenario>_should_<expected_result>`.

Preserve partial-update behavior by using `model_dump(exclude_unset=True)`. Scope every task query to `owner_id`. Add a reversible migration for schema changes and test both the new behavior and authorization boundaries.
