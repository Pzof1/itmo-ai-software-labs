---
name: api-change
description: Implement or review a FastAPI endpoint change in this repository across route, schema, service, repository, migration, and API tests. Use for new task endpoints, changed task behavior, persistence changes, or API bug fixes.
---

# API change workflow

1. Read the existing route and its request/response schemas. Trace the call through service and repository before editing.
2. Write down the observable contract: response body, status codes, ownership, missing-resource behavior, pagination/filter effects, and empty cases.
3. Put HTTP wiring in `app/api/v1`, decisions and commits in `app/service`, and all SQLAlchemy statements in `app/repository`.
4. Scope task access by `owner_id`. Return the same `Task <id> not found` 404 for missing and foreign tasks.
5. Add a reversible Alembic migration when persistence changes. Existing rows must remain usable after upgrade.
6. Add API tests named `test_<scenario>_should_<expected_result>`. Cover success, unauthenticated access, foreign ownership, missing records, and state-sensitive edge cases.
7. Run focused tests first, then the full suite and `scripts/check_conventions.py`. Inspect the final diff for accidental database files or secrets.

For PATCH handlers, preserve omitted fields with `model_dump(exclude_unset=True)`. For JSON routes, declare `response_model`; status 204 routes have no response body.
