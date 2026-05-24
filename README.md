# 📝 TaskFlow API

A RESTful API for personal task management. Pet project built with FastAPI, SQLAlchemy 2.0, PostgreSQL.

## 🚀 Key Features

- **Clean Architecture:** Strict separation of concerns using **Router -> Service -> Repository** pattern.
- **Robust Authentication:** Secure OAuth2 password flow with **JWT** tokens and **Bcrypt** password hashing.
- **Hybrid Authentication:** Supports both standard OAuth2 password flow and Silent S2S (Service-to-Service) Authentication for Telegram clients via secure internal secret validation.
- **Advanced CRUD:** Full support for pagination, complex filtering (by status), and partial updates (**PATCH**).
- **Data Integrity:** Validation with **Pydantic v2** and **SQLAlchemy 2.0** (Mapped/mapped_column style).
- **Modern Infrastructure:** Fully containerized with **Docker** and automated database schema management via **Alembic**.

## 🛠 Tech Stack

- **Backend:** [FastAPI](https://tiangolo.com) (Python 3.12+)
- **Database:** [PostgreSQL](https://postgresql.org) (Production: port 5432 | Standalone Dev: port 5433), SQLite (Testing)
- **ORM:** [SQLAlchemy 2.0](https://sqlalchemy.org)
- **Migrations:** [Alembic](https://sqlalchemy.org)
- **Containerization:** [Docker](https://docker.com) & Docker Compose
- **Validation:** [Pydantic v2](https://pydantic.dev)
- **Security:** JWT, Passlib (Bcrypt)

## 📦 Quick Start (Docker)

The fastest way to get the project up and running is using Docker Compose. It automatically configures the database, applies migrations, and starts the API.

> 💡 **Note:** If you want to spin up the entire ecosystem (API + Telegram Bot + Redis + PostgreSQL), please use the main `docker-compose.yml` located in the **FastAPI-todo-Telegram-Bot** repository root.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/vintikzq/FastAPI-todo-API.git
    cd FastAPI-todo-API
    ```
2.  **Configure environment variables:**
    Create a `.env` file in the root directory based on `.env.example`:
    ```bash
    cp .env.example .env
    ```
3.  **Spin up the services:**
    ```bash
    docker-compose up --build
    ```

- **API URL:** `http://localhost:8000`
- **Interactive Docs (Swagger UI):** `http://localhost:8000/docs`

## 🛠 Local Development

To run the project locally for development purposes:

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Start the Database:**
    Ensure PostgreSQL is running (e.g., `docker-compose up -d db`). Update `DB_HOST=localhost` and `DB_PORT=5433` in your `.env`.
3.  **Apply Migrations:**
    ```bash
    alembic upgrade head
    ```
4.  **Run the Server:**
    ```bash
    uvicorn app.main:app --reload
    ```

## 📂 Project Structure

The project follows the **Service-Repository Pattern**, ensuring maintainability and ease of testing.

- **app/api/** — API Route handlers (Routers) and HTTP logic.
- **app/service/** — Business logic layer (validation and orchestration).
- **app/repository/** — Data access layer (SQLAlchemy queries).
- **app/models.py** — SQLAlchemy database models.
- **app/schemas.py** — Pydantic validation schemas (DTOs).
- **app/config.py** — Settings management via Pydantic Settings.
- **app/database.py** — SQLAlchemy engine and session configuration.
- **app/auth.py** — Security utilities (password hashing and JWT token logic).
- **app/dependency.py** — FastAPI dependencies (e.g., database sessions, security headers validation).
- **app/main.py** — FastAPI application entry point.
- **migrations/** — Database version control (Alembic scripts).
- **docker-compose.yml** — Multi-container orchestration (API + PostgreSQL).
- **Dockerfile** — Instructions for building the FastAPI container.

## 🧪 Testing & Coverage

The project uses **Pytest** for integration testing with an isolated SQLite database.

**Run tests:**

```bash
pytest
```

**Generate Coverage Report:**

```bash
pytest --cov=app --cov-report=term-missing
```

Developed by [vintikzq](https://github.com/vintikzq)
