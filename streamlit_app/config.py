from __future__ import annotations
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env once (no‑op if file missing)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

# Expose the few vars the app needs.
API_BASE: str            = os.environ["API_BASE"]          # raises KeyError if unset
SUPABASE_URL: str        = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str        = os.environ["SUPABASE_KEY"]  # *public* anon key only