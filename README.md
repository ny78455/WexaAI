Wexa AI — SaaS Analytics PlatformWexa AI is a production-ready SaaS analytics platform built for high-performance event ingestion, real-time data visualization, and threshold-based alerting. Serving as a lightweight alternative to Mixpanel or Metabase, it provides multi-tenant organizations with drag-and-drop custom dashboards and instantaneous insights.📑 Table of ContentsCore FeaturesTech StackArchitecture & Project StructureDatabase SchemaGetting Started (Local Development)API Ingestion ReferenceTesting & VerificationPhased Delivery Plan✨ Core Features🔐 Authentication & Multi-TenancyRobust Auth: JWT-based access tokens (15-minute expiry) and HTTP-only refresh cookies (7-day expiry).Role-Based Access Control (RBAC): Hierarchical permissions (Owner → Admin → Analyst → Viewer) enforced via FastAPI dependencies.Organization Isolation: Strict tenant data isolation across all database queries.Team Onboarding: Invite-based team management via secure email tokens.📊 High-Throughput Data IngestionFlexible Endpoints: Single event, batch events, and direct CSV upload capabilities.Asynchronous Processing: Celery workers handle event storage, ensuring the ingestion API remains lightning-fast.Security & Limits: Organization-specific API keys with rotation/revocation, protected by Redis-backed rate limiting (SlowAPI).📈 Custom Dashboards & WidgetsDrag-and-Drop Builder: Create personalized views with Line Charts, Bar Charts, Pie Charts, KPI Cards, and Data Tables.Dynamic Queries: Link widgets to saved analytics queries with configurable time ranges.Sharing: Secure public links or internal team-only access.Auto-Refresh: Configurable polling intervals (30s, 1m, 5m).🚨 Alerts & NotificationsRule Engine: Define threshold-based conditions (e.g., error_rate > 5%).Scheduled Evaluation: Celery Beat periodically evaluates alert conditions against live data.Multi-Channel Delivery: In-app notifications, SMTP Emails, and Slack Webhooks.⚡ Real-Time InfrastructureLive Dashboards: Native WebSockets push metric updates directly to the frontend.Event Stream Viewer: Watch raw events arrive in real-time.Resilience: Auto-reconnect strategies with exponential backoff on the frontend client.🛠 Tech StackFrontend ArchitectureFramework: Next.js 14+ (App Router)Language: TypeScriptUI/Styling: Shadcn/UI + Tailwind CSSData Visualization: RechartsState Management: ZustandData Fetching: TanStack Query (React Query)Real-Time: Native WebSocket APIBackend ArchitectureFramework: FastAPI (Python 3.11+)ORM: SQLAlchemy 2.0 (Async) + Alembic (Migrations)Database: PostgreSQLTask Queue: Celery + Redis (with Celery Beat for cron tasks)Validation: Pydantic v2Security: passlib/bcrypt + JWT (python-jose)Logging: structlog📂 Architecture & Project StructureThe repository is organized into cleanly separated frontend and backend services, designed for modularity and scalability.wexa-analytics/
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
🗄 Database SchemaThe core relational model emphasizes strict organizational isolation.TableKey FieldsDescriptionorganizationsid, name, slug, created_atTop-level tenant container.usersid, org_id, email, hashed_password, rolePlatform users linked to an org.invitationsid, org_id, email, token, expires_atPending team invites.api_keysid, org_id, key_hash, name, revoked_atIngestion keys for client apps.eventsid, org_id, event_name, properties (JSONB), timestampRaw ingested analytics events.dashboardsid, org_id, name, config (JSONB), share_tokenSaved dashboard configurations.widgetsid, dashboard_id, type, query_config (JSONB), positionVisual components on dashboards.alert_rulesid, org_id, name, condition, channels, statusConfigured thresholds.alert_historyid, rule_id, triggered_at, valueAudit log of triggered alerts.🚀 Getting StartedPrerequisitesDocker & Docker ComposeNode.js (v18+)Python 3.11+1. Clone & Configuregit clone [https://github.com/your-org/wexa-analytics.git](https://github.com/your-org/wexa-analytics.git)
cd wexa-analytics
Copy the example environment files:cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
2. Launch Infrastructure (Docker)Start the PostgreSQL database, Redis instance, and Celery workers:docker-compose up -d db redis celery_worker celery_beat
3. Setup BackendNavigate to the backend, install dependencies, and run migrations:cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
4. Setup Frontendcd frontend
npm install
npm run dev
Platform will be available at http://localhost:3000. Backend Swagger docs at http://localhost:8000/docs.📡 API Ingestion ReferenceSend data to Wexa AI from your applications using your Organization's API Key.Single EventPOST /api/v1/events/
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
Batch IngestionPOST /api/v1/events/batch
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "events": [
    { "event_name": "page_view", "properties": { "path": "/pricing" } },
    { "event_name": "button_click", "properties": { "button_id": "buy_now" } }
  ]
}
🧪 Testing & VerificationBackend TestsWritten in pytest utilizing httpx for async testing.cd backend
pytest tests/ -v --asyncio-mode=auto
Frontend E2EPlaywright ensures core user flows (Auth, Dashboard Creation) function correctly.cd frontend
npx playwright test
📅 Phased Delivery PlanPhaseDescriptionStatusPhase 1Project scaffold, Docker Compose, DB models, Alembic setup⏳ DonePhase 2Auth & Multi-tenancy (JWT, RBAC, org isolation logic) DonePhase 3Data ingestion pipeline (API, CSV parsing, Celery queue) DonePhase 4Dashboards & Widget System (Drag/Drop UI + Query execution) DonePhase 5Alerts engine, Celery Beat rules, and WebSockets integration DonePhase 6E2E Testing, performance tuning, and deployment manifests DoneMaintained by the Wexa AI Engineering Team.
