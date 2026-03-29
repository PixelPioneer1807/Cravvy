# Contributing to Cravvy

## Branch Strategy

```
main (production) ← dev (staging) ← feat/* | fix/* | refactor/*
```

- `main`: Production-ready code only. Deploys to Azure.
- `dev`: Staging branch. All feature branches merge here first.
- `feat/*`: New features (`feat/auth-jwt`, `feat/meal-planner`)
- `fix/*`: Bug fixes (`fix/token-refresh-race`)
- `refactor/*`: Code improvements (`refactor/auth-middleware`)
- `chore/*`: Tooling, config, deps (`chore/update-deps`)

## Commit Messages

```
<type>: <description>
```

- Max 72 characters
- Lowercase, imperative mood
- Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`

Examples:
```
feat: add jwt access token generation
fix: handle expired refresh token in rotation
refactor: extract password hashing to shared utility
chore: update groq sdk to 0.18
docs: add auth flow diagram to architecture docs
test: add unit tests for meal plan optimizer
```

## Code Style

### Tools

- **ruff**: Formatting + linting (runs on save and pre-commit)
- **pyright**: Strict type checking
- **pre-commit**: Runs ruff + pyright before every commit

### Rules

1. Every file starts with a **module docstring** (one line)
2. Every class has a **docstring** explaining its responsibility
3. Every function has a **docstring** + full **type hints** (params + return)
4. All I/O is **async** by default
5. No `print()` — use `logging`
6. No hardcoded config — use `src/shared/config.py`
7. No `Any` types unless justified with a comment
8. Keep functions **under 30 lines**
9. Keep files **under 300 lines** — split if larger

### Naming Conventions

| Category         | Convention        | Example                    |
| ---------------- | ----------------- | -------------------------- |
| Protocol         | `*Protocol`       | `LLMProtocol`             |
| Pydantic Model   | `*Schema`         | `LoginRequestSchema`       |
| DB Model         | `*Model`          | `UserModel`                |
| Enum             | PascalCase        | `Role`, `Confidence`       |
| Implementation   | Vendor + Role     | `GroqLLM`, `MongoUserRepo` |
| Service          | `*Service`        | `AuthService`              |
| Repository       | `*Repository`     | `UserRepository`           |
| Exception        | `*Error`          | `AuthError`                |
| Middleware        | `*Middleware`      | `RateLimitMiddleware`      |
| Dependency       | `get_*` / `require_*` | `get_current_user`    |
| Files            | snake_case        | `auth_service.py`          |
| Functions / vars | snake_case        | `create_access_token()`    |
| Constants        | UPPER_SNAKE_CASE  | `MAX_RETRIES`              |

### Import Rules

```python
# Order: stdlib -> third-party -> local
import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.auth.service import AuthService as AuthService
from src.core.interfaces import LLMProtocol as LLMProtocol
```

- Import from package `__init__.py`, not deep internal paths
- One import per line for local imports
- Use `as` alias on re-exports in `__init__.py`

### `__init__.py` Convention

```python
"""Auth module — signup, login, JWT, OAuth, password reset."""

from src.auth.router import router as router
from src.auth.service import AuthService as AuthService

__all__ = [
    "router",
    "AuthService",
]
```

- Re-export public API only
- Explicit `as` alias on every re-export
- Define `__all__`

## Domain Module Structure

Each feature module follows this structure:

```
src/auth/
  __init__.py       → Re-exports public API
  router.py         → FastAPI route definitions (thin)
  service.py        → Business logic
  schemas.py        → Pydantic request/response schemas
  models.py         → MongoDB document models
  dependencies.py   → FastAPI Depends() callables
  exceptions.py     → Module-specific errors
```

### Responsibilities

- **router.py**: Validate input, call service, return response. No business logic.
- **service.py**: All business logic. Receives validated data, returns results or raises errors.
- **schemas.py**: Pydantic models for API input/output. Separate from DB models.
- **models.py**: MongoDB document structure. Separate from API schemas.
- **dependencies.py**: FastAPI `Depends()` functions (auth checks, DB connections, etc.)
- **exceptions.py**: Custom errors that extend `src/shared/exceptions.py` base classes.

## Testing

### Structure

```
tests/
  unit/           → Fast, mocked, no external services
  integration/    → Requires docker compose (MongoDB + Redis)
  eval/           → Quality evaluation (accuracy, relevance)
```

### Naming

```
test_<module>_<function>_<scenario>.py
```

Examples:
```
test_auth_service_login_success.py
test_auth_service_login_wrong_password.py
test_meal_optimizer_weekly_plan_under_budget.py
```

### Running

```bash
# Unit tests only
uv run pytest tests/unit/

# Integration tests (start docker compose first)
uv run pytest tests/integration/

# All tests
uv run pytest

# With coverage
uv run pytest --cov=src
```

## Pre-Commit Setup

```bash
uv run pre-commit install
```

Hooks run automatically on `git commit`:
1. ruff format
2. ruff lint (with auto-fix)
3. pyright type check
