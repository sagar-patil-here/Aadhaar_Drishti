"""
Entry-point shim for platforms (Vercel, gunicorn, uvicorn CLI) that
auto-detect `main:app` at the service root. The actual FastAPI app is
defined in `app/main.py` — this file just re-exports it so the existing
package layout keeps working with every deployment target.
"""

from app.main import app  # re-export for ASGI servers / Vercel autodetect

__all__ = ["app"]
