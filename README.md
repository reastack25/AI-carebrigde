# CareBridge AI

CareBridge AI is a healthcare companion designed to make health information easier to understand and help connect patients with appropriate care. It is built as a full-stack application with React, Flask, PostgreSQL, JWT authentication, and Gemini AI.

## Phase 1

- React + Vite frontend foundation
- Flask REST API
- PostgreSQL-ready SQLAlchemy models
- JWT authentication
- Role-based users: patient, doctor, admin
- Protected frontend routes
- Health-check endpoint
- Environment-based configuration

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
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       └── health.py
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

CareBridge AI is an educational and care-navigation tool. It does not replace a qualified healthcare professional or emergency services.

## Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```
