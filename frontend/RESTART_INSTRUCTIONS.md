# Restart instructions

This project no longer includes a backend. Only the React app needs to be restarted.

## Stop the dev server

Press `Ctrl+C` in the terminal where `npm start` is running.

## Start again

```bash
cd frontend
npm start
```

Open **http://localhost:3000**.



backend :

cd /Users/sagarpatil/Work/Projects/Web/Aadhaar_DRISHTI/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000