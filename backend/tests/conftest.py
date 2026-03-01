"""Shared test fixtures and configuration for PilaMatch backend tests.

Sets up environment variables required by app.core.config.Settings before
any application module is imported.
"""

import os

# Must be set BEFORE importing any app modules, because Settings reads
# environment variables at import time (module-level `settings = Settings()`).
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///./test.db")
