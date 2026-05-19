# Wexa AI — SaaS Analytics Platform

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)

Wexa AI is a production-ready SaaS analytics platform built for high-performance event ingestion, real-time data visualization, and threshold-based alerting. Serving as a lightweight alternative to Mixpanel or Metabase, it provides multi-tenant organizations with drag-and-drop custom dashboards and instantaneous insights.

Demo Link - https://athera-production.up.railway.app/

---

## 📑 Table of Contents

1. [Core Features](#-core-features)
2. [Tech Stack](#-tech-stack)
3. [Architecture & Project Structure](#-architecture--project-structure)
4. [Database Schema](#-database-schema)
5. [Getting Started (Local Development)](#-getting-started)
6. [API Ingestion Reference](#-api-ingestion-reference)
7. [Testing & Verification](#-testing--verification)
8. [Phased Delivery Plan](#-phased-delivery-plan)

---

## ✨ Core Features

### 🔐 Authentication & Multi-Tenancy

* **Robust Auth:** JWT-based access tokens (15-minute expiry) and HTTP-only refresh cookies (7-day expiry).
* **Role-Based Access Control (RBAC):** Hierarchical permissions (Owner → Admin → Analyst → Viewer) enforced via FastAPI dependencies.
* **Organization Isolation:** Strict tenant data isolation across all database queries.
* **Team Onboarding:** Invite-based team management via secure email tokens.

### 📊 High-Throughput Data Ingestion

* **Flexible Endpoints:** Single event, batch events, and direct CSV upload capabilities.
* **Asynchronous Processing:** Celery workers handle event storage, ensuring the ingestion API remains lightning-fast.
* **Security & Limits:** Organization-specific API keys with rotation/revocation, protected by Redis-backed rate limiting (SlowAPI).

### 📈 Custom Dashboards & Widgets

* **Drag-and-Drop Builder:** Create personalized views with Line Charts, Bar Charts, Pie Charts, KPI Cards, and Data Tables.
* **Dynamic Queries:** Link widgets to saved analytics queries with configurable time ranges.
* **Sharing:** Secure public links or internal team-only access.
* **Auto-Refresh:** Configurable polling intervals (30s, 1m, 5m).

### 🚨 Alerts & Notifications

* **Rule Engine:** Define threshold-based conditions (e.g., `error_rate > 5%`).
* **Scheduled Evaluation:** Celery Beat periodically evaluates alert conditions against live data.
* **Multi-Channel Delivery:** In-app notifications, SMTP Emails, and Slack Webhooks.

### ⚡ Real-Time Infrastructure

* **Live Dashboards:** Native WebSockets push metric updates directly to the frontend.
* **Event Stream Viewer:** Watch raw events arrive in real-time.
* **Resilience:** Auto-reconnect strategies with exponential backoff on the frontend client.

---

## 🛠 Tech Stack

### Frontend Architecture

* **Framework:** Next.js 14+ (App Router)
* **Language:** TypeScript
* **UI/Styling:** Shadcn/UI + Tailwind CSS
* **Data Visualization:** Recharts
* **State Management:** Zustand
* **Data Fetching:** TanStack Query (React Query)
* **Real-Time:** Native WebSocket API

### Backend Architecture

* **Framework:** FastAPI (Python 3.11+)
* **ORM:** SQLAlchemy 2.0 (Async) + Alembic (Migrations)
* **Database:** PostgreSQL
* **Task Queue:** Celery + Redis (with Celery Beat for cron tasks)
* **Validation:** Pydantic v2
* **Security:** passlib/bcrypt + JWT (python-jose)
* **Logging:** structlog

---

## 📂 Architecture & Project Structure

The repository is organized into cleanly separated frontend and backend services, designed for modularity and scalability.

```text
wexa-analytics/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # API Routers (v1)
│   │   ├── core/             # Configuration, Security, Dependencies
│   │   ├── db/               # SQLAlchemy Models & Sessions
│   │   ├── schemas/          # Pydantic v2 Models
│   │   ├── services/         # Core Business Logic
│   │   ├── repositories/     # DB Query Abstraction Layer
│   │   └── tasks/            # Async Celery Tasks & Beat Schedules
│   ├── alembic/              # Database Migrations
│   └── tests/                # Pytest Suite
├── frontend/                 # Next.js Application
│   ├── src/
│   │   ├── app/              # App Router (Auth & Protected Routes)
│   │   ├── components/       # Shadcn UI, Charts, Dashboard Builder
│   │   ├── lib/              # API Client & WebSocket Manager
│   │   └── stores/           # Zustand State
└── docker-compose.yml        # Orchestrates Postgres, Redis, API, and Frontend

```

---

## 🗄 Database Schema

The core relational model emphasizes strict organizational isolation.

| **Table** | **Key Fields** | **Description** |
| --- | --- | --- |
| `organizations` | `id`, `name`, `slug`, `created_at` | Top-level tenant container. |
| `users` | `id`, `org_id`, `email`, `hashed_password`, `role` | Platform users linked to an org. |
| `invitations` | `id`, `org_id`, `email`, `token`, `expires_at` | Pending team invites. |
| `api_keys` | `id`, `org_id`, `key_hash`, `name`, `revoked_at` | Ingestion keys for client apps. |
| `events` | `id`, `org_id`, `event_name`, `properties` (JSONB), `timestamp` | Raw ingested analytics events. |
| `dashboards` | `id`, `org_id`, `name`, `config` (JSONB), `share_token` | Saved dashboard configurations. |
| `widgets` | `id`, `dashboard_id`, `type`, `query_config` (JSONB), `position` | Visual components on dashboards. |
| `alert_rules` | `id`, `org_id`, `name`, `condition`, `channels`, `status` | Configured thresholds. |
| `alert_history` | `id`, `rule_id`, `triggered_at`, `value` | Audit log of triggered alerts. |

---

## 🚀 Getting Started

### Prerequisites

* Docker & Docker Compose
* Node.js (v18+)
* Python 3.11+

### 1. Clone & Configure

```bash
git clone [https://github.com/your-org/wexa-analytics.git](https://github.com/your-org/wexa-analytics.git)
cd wexa-analytics

```

Copy the example environment files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

```

### 2. Launch Infrastructure (Docker)

Start the PostgreSQL database, Redis instance, and Celery workers:

```bash
docker-compose up -d db redis celery_worker celery_beat

```

### 3. Setup Backend

Navigate to the backend, install dependencies, and run migrations:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000

```

### 4. Setup Frontend

```bash
cd frontend
npm install
npm run dev

```

Platform will be available at `http://localhost:3000`. Backend Swagger docs at `http://localhost:8000/docs`.

---

## 📡 API Ingestion Reference

Send data to Wexa AI from your applications using your Organization's API Key.

**Single Event**

```http
POST /api/v1/events/
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "event_name": "user_signup",
  "timestamp": "2023-10-25T14:30:00Z",
  "properties": {
    "plan": "pro",
    "source": "google_ads"
  }
}

```

**Batch Ingestion**

```http
POST /api/v1/events/batch
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "events": [
    { "event_name": "page_view", "properties": { "path": "/pricing" } },
    { "event_name": "button_click", "properties": { "button_id": "buy_now" } }
  ]
}

```

---

## 🧪 Testing & Verification

### Backend Tests

Written in `pytest` utilizing `httpx` for async testing.

```bash
cd backend
pytest tests/ -v --asyncio-mode=auto

```

### Frontend E2E

Playwright ensures core user flows (Auth, Dashboard Creation) function correctly.

```bash
cd frontend
npx playwright test

```

---

## 📅 Phased Delivery Plan

| **Phase** | **Description** | **Status** |
| --- | --- | --- |
| **Phase 1** | Project scaffold, Docker Compose, DB models, Alembic setup | Done |
| **Phase 2** | Auth & Multi-tenancy (JWT, RBAC, org isolation logic) | Done |
| **Phase 3** | Data ingestion pipeline (API, CSV parsing, Celery queue) | Done |
| **Phase 4** | Dashboards & Widget System (Drag/Drop UI + Query execution) | Done |
| **Phase 5** | Alerts engine, Celery Beat rules, and WebSockets integration | Done |
| **Phase 6** | E2E Testing, performance tuning, and deployment manifests | Done |

---


```

```
