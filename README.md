# CareBridge AI

**Your AI-powered healthcare companion for underserved communities.**

CareBridge AI is a healthcare information and decision-support application designed to help patients understand health information, symptoms, medicines, and medical documents. It is educational support and does not replace qualified healthcare professionals or emergency services.

## Current capabilities

- JWT authentication with patient, doctor, and admin roles
- AI health chat powered by Gemini
- Conversation memory with recent context
- Symptom checker with cautious urgency guidance and red flags
- Multimodal medicine/report/prescription analysis for supported images and PDFs
- Structured medication extraction from uploaded prescriptions and medicine documents
- Multilingual responses: English, Kiswahili, Dholuo, Kikuyu, and Kalenjin
- Structured patient health timeline for chat, symptom checks, document analyses, and medication extraction
- User-isolated conversations and timeline records
- React + Vite + Tailwind patient dashboard
- Flask + PostgreSQL-ready backend with automated tests
- Versioned PostgreSQL schema migrations with Flask-Migrate/Alembic

## AI request rate limiting

AI-generating POST endpoints are protected by a database-backed per-user rate limit:

- `POST /api/ai/chat`
- `POST /api/ai/symptom-check`
- `POST /api/ai/analyze-image`

The default limit is **20 requests per user per 3,600-second window**. When the limit is exceeded, the API returns HTTP `429`, a `Retry-After` header, and a JSON response containing `retry_after_seconds`.

Configure the limit in `backend/.env`:

```dotenv
AI_RATE_LIMIT=20
AI_RATE_WINDOW_SECONDS=3600
```

Both values must be positive integers. The limiter counts persisted user messages, so malformed requests and provider failures are not counted as successful AI requests. Rate-limit violations are logged with the authenticated user ID, endpoint, current count, and window duration. For high-concurrency production deployments, a shared counter such as Redis or a dedicated request-event table can provide stronger atomicity and cross-instance coordination.

## Production configuration

Set `APP_ENV=production` and provide production-only secrets and service endpoints. The backend validates these settings before initializing Flask extensions and refuses unsafe defaults.

Required production settings:

```dotenv
APP_ENV=production
SECRET_KEY=<32+ character secret>
JWT_SECRET_KEY=<32+ character secret>
DATABASE_URL=postgresql+psycopg://<user>:<password>@<managed-db-host>:5432/<database>
CORS_ORIGINS=https://your-frontend.example.com
GEMINI_API_KEY=<production Gemini API key>
JWT_ACCESS_TOKEN_EXPIRES=3600
AI_RATE_LIMIT=20
AI_RATE_WINDOW_SECONDS=3600
```

Production validation rejects development secrets, wildcard or local CORS origins, SQLite/non-PostgreSQL database URLs, the development database default, and local database hosts. Keep credentials and API keys in the deployment platform's secret manager rather than committing them to Git.

## Local development configuration

The Vite development server commonly runs on port `5173`, but it may select `5174` when `5173` is busy. Configure the backend to allow the actual frontend origin in `backend/.env`:

```dotenv
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

If the frontend uses `127.0.0.1`, add that origin as well. Restart Flask after changing `.env`; configuration is loaded at application startup. Avoid using `*` for an authenticated application.

## Database migrations

The backend uses Flask-Migrate/Alembic for schema management. Always apply the complete migration chain to the database used by the running backend:

```bash
cd backend
source .venv/bin/activate
flask --app run.py db current
flask --app run.py db upgrade
```

After changing SQLAlchemy models:

```bash
flask --app run.py db migrate -m "describe the schema change"
flask --app run.py db upgrade
```

If a development database already contains tables created outside Alembic, inspect the schema and migration state before stamping or upgrading it. Do not recreate an existing database casually, because that can remove users and clinical records.

## Medication extraction API

All medication endpoints require a valid JWT bearer token.

### List saved medications

```http
GET /api/ai/medications
Authorization: Bearer <access-token>
```

Returns the authenticated user's medication records, newest first, limited to 50 records.

### Extract medications from an upload

```http
POST /api/ai/extract-medications
Authorization: Bearer <access-token>
Content-Type: multipart/form-data
```

Multipart fields:

- `image` — required image or PDF upload; supported types include JPEG, PNG, WEBP, HEIC, HEIF, and PDF
- `instruction` — optional extraction guidance, maximum 1,000 characters
- `language` — optional supported language code: `en`, `sw`, `luo`, `kik`, or `kal`
- `conversation_id` — optional conversation to associate with the extraction

The endpoint returns the extracted medication details, persisted records, and the related conversation. The system does not intentionally guess text that is unreadable or absent from the uploaded document.

## Health timeline

CareBridge records structured AI activity separately from raw chat messages. Timeline events contain an event type, title, summary, optional conversation reference, safe metadata, and creation timestamp. The API endpoint `GET /api/ai/timeline` returns only the authenticated user's events and supports filtering with `?type=health_chat`, `?type=symptom_check`, or `?type=document_analysis`.

Raw uploaded document bytes are not stored in the timeline. The current implementation keeps analysis metadata and the generated educational summary; persistent file storage can be added later with explicit retention controls.

## Repository structure

```text
carebridge-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models.py
│   │   └── routes/
│   ├── migrations/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── services/
    │   ├── App.jsx
    │   └── main.jsx
    ├── .env.example
    └── package.json
```

## Safety

CareBridge AI is an educational and care-navigation tool. AI output can be incomplete or incorrect. Important medical information should be verified with a qualified healthcare professional. Emergency symptoms should be handled through appropriate emergency services rather than relying on the application.

## Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app run.py db upgrade
python run.py
```

Run tests:

```bash
cd backend
python -m pytest -q
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```
