# Aadhaar DRISHTI — Backend

Proactive fraud detection for Aadhaar enrollment data using Isolation Forest + Tri-Shield rule modules.

## Validated Results (500k real records)
- Input: 983,132 merged rows across 3 CSVs
- Flagged: 3,909 records (0.40%)
- HIGH severity: 931 | MEDIUM: 2,357 | LOW: 621
- Laundering Detector triggers: 750 | Ghost Scanner: 1,385 | Migration Radar: 93

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the model
```bash
python scripts/train.py \
  --enrol data/api_data_aadhar_enrolment_0_500000.csv \
  --bio   data/api_data_aadhar_biometric_0_500000.csv \
  --demo  data/api_data_aadhar_demographic_0_500000.csv
```

### 3. Start with Docker Compose
```bash
docker-compose up --build
```

### 4. Run API only (local dev)
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Run tests
```bash
pytest tests/ -v
```

### 6. Start Celery worker (for large batch uploads)
```bash
celery -A app.workers.batch_processor worker --loglevel=info
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | /health | Model + DB status |
| POST | /api/v1/ingest | Upload 3 CSVs, get results |
| GET  | /api/v1/dashboard/summary | KPI counts |
| GET  | /api/v1/dashboard/flags | Paginated red flags |
| PATCH| /api/v1/dashboard/flags/{id}/status | Update flag status |
| GET  | /api/v1/dashboard/heatmap | State-level counts for map |
| POST | /api/v1/reports/generate/{id} | Generate PDF report |
| GET  | /api/v1/reports/download/{id} | Download PDF |
| GET  | /api/v1/batches/{batch_id} | Poll batch progress |

## Architecture
```
3 CSV feeds → Preprocessor → Tri-Shield modules → Isolation Forest → Decision Logic
                                                                           ↓
                                                              Secure DB  |  Red Flag Queue
                                                                                ↓
                                                                       PDF Report + Dashboard
```
