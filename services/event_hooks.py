"""
Event hooks for external service integration.

Emits structured events (market resolved, submission created, etc.) to
configured webhook endpoints. Designed for future integration with
Pro (SNAG training data) and SNAG-Bench (predictive scoring).

Configure via environment variables:
    PROTEUS_WEBHOOK_URL      - Primary webhook endpoint (POST JSON)
    PROTEUS_WEBHOOK_SECRET   - HMAC-SHA256 signing secret (optional)

Events are fire-and-forget: failures are logged but never block the
caller. No retries -- downstream consumers should be idempotent.
"""

import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

import requests

from utils.logging_config import get_logger

logger = get_logger(__name__)

_WEBHOOK_URL: Optional[str] = os.environ.get('PROTEUS_WEBHOOK_URL')
_WEBHOOK_SECRET: Optional[str] = os.environ.get('PROTEUS_WEBHOOK_SECRET')
_TIMEOUT_SECONDS = 5


def _sign_payload(payload_bytes: bytes) -> str:
    """HMAC-SHA256 signature for webhook verification."""
    if not _WEBHOOK_SECRET:
        return ''
    return hmac.new(
        _WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()


def emit_event(event_type: str, data: Dict[str, Any]) -> None:
    """Fire a webhook event. Non-blocking, best-effort delivery.

    Args:
        event_type: e.g. "market.resolved", "market.created", "submission.created"
        data: Arbitrary JSON-serializable payload.
    """
    if not _WEBHOOK_URL:
        return  # No webhook configured -- silent no-op

    payload = {
        'event': event_type,
        'timestamp': int(time.time()),
        'data': data,
    }

    try:
        body = json.dumps(payload, separators=(',', ':'))
        headers = {
            'Content-Type': 'application/json',
            'X-Proteus-Event': event_type,
        }
        sig = _sign_payload(body.encode())
        if sig:
            headers['X-Proteus-Signature'] = f'sha256={sig}'

        resp = requests.post(
            _WEBHOOK_URL,
            data=body,
            headers=headers,
            timeout=_TIMEOUT_SECONDS,
        )
        logger.info(f"Webhook {event_type} -> {resp.status_code}")
    except Exception as e:
        logger.warning(f"Webhook {event_type} failed: {e}")
