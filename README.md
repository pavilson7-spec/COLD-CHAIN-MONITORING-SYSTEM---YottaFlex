# Cold Chain Monitoring System

An enterprise-grade, regulatory-compliant Cold Chain Monitoring, Excursion Detection, and Corrective Action platform developed for the YottaFlex AI 72-Hour Coding Challenge.

---

## 1. System Architecture

- **Backend:** Python 3.10+, FastAPI, SQLAlchemy 2.0 (with connection pooling), Alembic 1.13, Pydantic v2
- **Database:** PostgreSQL 17 (`cold_chain_monitoring_db` on port 5432)
- **Frontend:** React 19, Vite, Tailwind CSS, Lucide Icons, Recharts
- **Simulation:** Pandas, NumPy (reproducible seed `20261022`)
- **Security:** OAuth2 JWT, Argon2/Bcrypt password hashing, Role-Based Access Control (RBAC), HTTP security headers

---

## 2. Default Enterprise User Accounts

| Username | Password | Role | Description |
|---|---|---|---|
| `admin` | `AdminSecure2026!` | **OT/IT Administrator** | Full system administration & audit permissions |
| `quality` | `Quality2026!` | **Quality Engineer** | Excursion evaluation, threshold policies, CAPA actions |
| `operator` | `Operator2026!` | **Plant Operator** | Telemetry oversight, alert acknowledgements |
| `planner` | `Planner2026!` | **Production Planner** | Shipment dispatching, container assignment |

---

## 3. Quick Start Guide (Windows PowerShell)

### Step 1: Clone & Configure Environment
```powershell
cd "c:\Users\97150\Desktop\Cold Chain Monitoring"
Copy-Item .env.example .env
```
*(Ensure PostgreSQL is running locally on port 5432 and `cold_chain_monitoring_db` is created).*

### Step 2: Set Up Python Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### Step 3: Run Alembic Database Migrations
```powershell
cd backend
..\venv\Scripts\alembic upgrade head
cd ..
```

### Step 4: Generate Synthetic Telemetry & Mandatory Scenarios
```powershell
.\venv\Scripts\python -m generator.generate_data --shipments 100 --containers 30 --seed 20261022
```

### Step 5: Start FastAPI Backend Server
```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*API Swagger Documentation will be accessible at: `http://localhost:8000/docs`*

### Step 6: Start React Frontend Application
Open a new terminal window:
```powershell
cd "c:\Users\97150\Desktop\Cold Chain Monitoring\frontend"
npm install
npm run dev
```
*Frontend UI will be live at: `http://localhost:5173`*

---

## 4. Automated Testing & Validation

### Run Full Pytest Suite
```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\pytest backend\tests -v
```

### Run Mandatory Negative Scenarios Integrity Audit
```powershell
.\venv\Scripts\python -m generator.validate_data
```

### Verify Dataset Reproducibility (SHA-256 Checksum)
```powershell
.\venv\Scripts\python -m generator.test_reproducibility
```

---

## 5. Mandatory Negative Scenarios Handled

1. **Reading outside physical range:** Telemetry values exceeding `[-80, 70]°C` are flagged as critical hardware anomalies.
2. **Missing interval safe assumption prevention:** Telemetry gaps (>10 min) are flagged as critical telemetry failures rather than assumed safe.
3. **Shipment delivered before departure:** Rejected by both backend validator and shipment lifecycle transition logic.
4. **Wrong product threshold applied:** Foreign key integrity and calibration status checks prevent mismatched or expired policies.
5. **Excursion duration undercounting:** Calculations preserve unbroken continuous durations across consecutive violation readings.

---

## 6. Project Structure

```
Cold Chain Monitoring/
├── backend/
│   ├── alembic/              # Alembic migration revisions
│   ├── app/
│   │   ├── core/             # Database connection pool, security, configs
│   │   ├── models/           # 10 core SQLAlchemy models + Users & Alerts
│   │   ├── routes/           # REST endpoints (/auth, /dashboard, /entities, etc.)
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── services/         # Deterministic Excursion Rule Engine
│   │   └── validators/       # Automated data integrity & audit validator
│   ├── tests/                # Automated pytest test cases
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── layouts/          # Responsive enterprise dashboard layout
│   │   ├── pages/            # 16 complete functional application pages
│   │   └── services/         # Axios API client
│   └── package.json
├── generator/
│   ├── generate_data.py      # Synthetic dataset generator (seed: 20261022)
│   ├── inject_anomalies.py   # Mandatory negative scenario injector
│   ├── ground_truth.py       # Isolated ground truth tracker
│   └── validate_data.py      # Automated integrity verification
├── data/
│   ├── generated/            # ground_truth.csv, ground_truth.json, manifests
│   └── exports/              # CSV/JSON exports
├── docs/                     # Data dictionary, schema, architecture, reports
├── .env.example
├── .gitignore
└── README.md
```
