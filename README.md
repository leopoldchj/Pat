# Personal Website for Me and My Girlfriend ❤️🌸

This project consists of a **frontend** developed with **React** and a **backend** powered by **Django**.  
It allows for an easy production deployment via **Docker Compose** or local development.

---

## Quick Start (Production / Docker)

The easiest way to run the application is using Docker Compose.

### 1. Configure Environment Variables
Create a **single** `.env` file in the root directory (copy `.env.example` as a starting point: `cp .env.example .env`).
This unified configuration file is used by both the **Backend** (Django) and the **Frontend** (React/Docker).
See the [Environment Variables](#environment-variables) section below for details.

### 2. Run with Docker Compose
```bash
docker-compose up --build -d
```
The application will be accessible at `http://localhost:3000` (frontend) and `http://localhost:8000` (backend).

---

## Local Development (Without Docker)

If you prefer running services locally for development:

### Prerequisites
- **Node.js** (v20+)
- **Python** (v3.12+)
- **uv** (Fast Python package installer and resolver)
- **Redis** (Required for WebSocket/Channels functionality)

### 1. Database & Redis
Ensure you have a Postgres (or your configured DB) and Redis running.  
You can quickly start Redis with Docker if needed:
```bash
docker run -d -p 6379:6379 redis:7
```

### 2. Backend Setup
We use `uv` for blazing fast dependency management.

```bash
# From project root
uv sync

uv run python manage.py migrate

uv run python manage.py runserver
```

### 3. Frontend Setup

```bash
# From project root
npm run install-all

npm start
```

`npm start` injects the root `.env` (including the `REACT_APP_*` variables) into the React dev server — no separate `frontend/.env` is needed.

### 4. Run Both at Once

```bash
npm run dev
```

Starts the Django backend and the React frontend together (requires backend setup from step 2).

### 5. Code Quality
- **Backend Tests**: `uv run pytest`
- **Frontend Lint**: `npm run lint` or `npm run lint:fix`

---

## CI/CD & Automated Reports

This project uses **GitHub Actions** for Continuous Integration.
On every push or pull request to the `main` branch, the following checks are performed:

1.  **Backend Tests**: Runs the Django test suite with coverage analysis.
2.  **Frontend Lint & Build**: Checks code style and builds the React application.
3.  **Key Feature**: Automatic generation of a **PDF Test Report**.
    - A detailed PDF report (`test-report.pdf`) is generated after every backend test run.
    - It includes execution statistics, a list of all executed tests with timings, and details on any failures.
    - You can download this report from the **Artifacts** section of the GitHub Actions workflow summary.

---

## Environment Variables

Required variables for both Docker and local setups:

| Variable | Description | Example |
|---|---|---|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | `super-secret-key` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `ALLOWED_CORS` | Allowed CORS origins | `http://localhost:3000` |
| `DATABASE_NAME` | Database name | `al_db` |
| `DATABASE_USERNAME`| Database username | `postgres` |
| `DATABASE_PASSWORD`| Database password | `password` |
| `DATABASE_HOST` | Database host | `localhost` (or `db` in docker) |
| `DATABASE_PORT` | Database port | `5432` |
| `REDIS_HOST` | Redis host | `localhost` (or `redis` in docker)|
| `MAIL_HOST` | SMTP server host | `smtp.example.com` |
| `MAIL_PORT` | SMTP server port | `587` |
| `MAIL_USERNAME` | SMTP username | `user@example.com` |
| `MAIL_PASSWORD` | SMTP password | `password` |
| `AWS_ACCESS_KEY` | AWS Access Key | `AKI...` |
| `AWS_ACCESS_SECRET`| AWS Secret Key | `secret...` |
| `AWS_REGION` | AWS Region | `eu-west-3` |
| `AWS_BUCKET_NAME` | S3 Bucket Name | `my-bucket` |
| `REACT_APP_API_URL` | Backend API URL (local dev only) | `http://127.0.0.1:8000/api/` |
| `REACT_APP_WS_URL` | Backend WebSocket URL (local dev only) | `ws://127.0.0.1:8000/ws/` |

### Optional Build Arguments (Docker)
| Variable | Description |
|---|---|
| `RELEASE_TAG` | Injects the release version (e.g., `v1.0.0`) into the footer. |
