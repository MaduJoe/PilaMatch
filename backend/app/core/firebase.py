"""Firebase Admin SDK initialization."""

import json
import logging
import os

logger = logging.getLogger(__name__)


def init_firebase() -> None:
    """Initialize Firebase Admin SDK from service account or env var.

    Looks for credentials in this order:
    1. GOOGLE_APPLICATION_CREDENTIALS env var (path to service account JSON)
    2. FIREBASE_SERVICE_ACCOUNT_JSON env var (inline JSON string)
    3. Skip initialization (mock mode)
    """
    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            return  # Already initialized

        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        cred_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("[Firebase] Initialized from service account file")
        elif cred_json:
            cred = credentials.Certificate(json.loads(cred_json))
            firebase_admin.initialize_app(cred)
            logger.info("[Firebase] Initialized from env JSON")
        else:
            logger.warning(
                "[Firebase] No credentials found. Push notifications will be mocked. "
                "Set GOOGLE_APPLICATION_CREDENTIALS or FIREBASE_SERVICE_ACCOUNT_JSON"
            )
    except ImportError:
        logger.warning("[Firebase] firebase-admin not installed, push disabled")
    except Exception as e:
        logger.error(f"[Firebase] Init failed: {e}")
