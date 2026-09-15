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

## Database migrations

The backend uses Flask-Migrate/Alembic for production schema management. The migration chain is:

```text
0001_baseline
    ↓
0002_structured_medical_records
    ↓
0003_medications
```

From the `backend/` directory:

```bash
flask --app run.py db upgrade
```

After changing SQLAlchemy models:

```bash
flask --app run.py db migrate -m "describe the schema change"
flask --app run.py db upgrade
```

If a development database already contains the baseline schema and was created outside Alembic, stamp it instead of recreating the tables:

```bash
flask --app run.py db stamp 0001_baseline
```

Never run `db upgrade` against an existing database until you have confirmed whether its schema is already represented by the migration history.

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
│   │   │   ├── 0001_baseline.py
│   │   │   ├── 0002_structured_medical_records.py
│   │   │   └── 0003_medications.py
│   │   ├── env.py
│   │   ├── alembic.ini
│   │   └── script.py.mako
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
