"""
human_review.py — Human-in-the-loop verification queue for the retrieval pipeline.

Two responsibilities:
  1. Enqueue items that automated methods couldn't resolve confidently, writing
     them to Firebase under /human_review/<push-id>.
  2. Expose a FastAPI router (/review/...) so auditors can list pending items,
     submit corrections, and mark items resolved.

Mount the router in main.py with one line:
    from human_review import router as review_router
    app.include_router(review_router)
"""

import re
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from firebase_admin import db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_key(k: str) -> str:
    """Firebase keys cannot contain . # $ [ ] / — replace with _."""
    return re.sub(r'[.#$\[\]/]', '_', str(k))


def _now() -> str:
    return str(datetime.now())


# ---------------------------------------------------------------------------
# Queue write — called by pipeline.py
# ---------------------------------------------------------------------------

def enqueue_for_review(
    image_path: str,
    image_type: str,
    partial_data: dict,
    reason: str = "low_confidence",
) -> str:
    """
    Push an unresolved extraction to Firebase /human_review and return the
    generated node key so the pipeline can surface it to the caller.

    Args:
        image_path:   Path (or GCS URL) of the image that failed automated extraction.
        image_type:   "receipt" or "shelf".
        partial_data: Whatever the pipeline managed to extract before giving up
                      (may be empty or incomplete).
        reason:       Short tag explaining why it ended up here
                      e.g. "low_confidence", "no_items_parsed", "all_methods_failed".

    Returns:
        The Firebase push key (string) for the new review node.
    """
    node = {
        "status":       "pending",
        "reason":       reason,
        "image_type":   image_type,
        "image_path":   image_path,
        "partial_data": partial_data,
        "created_at":   _now(),
        "resolved_at":  None,
        "correction":   None,
        "auditor_note": None,
    }
    # Sanitise keys in partial_data in case they contain Firebase-illegal chars
    node = json.loads(json.dumps(node, default=str))

    ref  = db.reference("human_review").push(node)
    key  = ref.key
    print(f"[human_review] Queued for review: /human_review/{key}  reason={reason}")
    return key


# ---------------------------------------------------------------------------
# FastAPI router — consumed by auditors / internal dashboard
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/review", tags=["human_review"])


class CorrectionPayload(BaseModel):
    """Body expected when an auditor submits a correction."""
    correction:   dict[str, Any]   # The corrected/completed data
    auditor_note: str = ""


@router.get("/pending")
def list_pending():
    """
    Return all items whose status is still 'pending'.
    Auditors poll this to see what needs attention.
    """
    all_items = db.reference("human_review").get() or {}
    pending = {
        key: val
        for key, val in all_items.items()
        if isinstance(val, dict) and val.get("status") == "pending"
    }
    return {"count": len(pending), "items": pending}


@router.get("/{review_id}")
def get_review_item(review_id: str):
    """Fetch a single review item by its Firebase push key."""
    node = db.reference(f"human_review/{review_id}").get()
    if node is None:
        return {"error": "not found"}, 404
    return node


@router.post("/{review_id}/resolve")
def resolve_review_item(review_id: str, payload: CorrectionPayload):
    """
    Mark a review item as resolved and store the auditor's correction.
    The corrected data is written back under /human_review/<id>/correction
    so downstream jobs can pick it up and write it to the main database.
    """
    ref  = db.reference(f"human_review/{review_id}")
    node = ref.get()
    if node is None:
        return {"error": "not found"}, 404
    if node.get("status") == "resolved":
        return {"error": "already resolved"}

    # Sanitise correction keys before writing to Firebase
    safe_correction = {
        _safe_key(k): v for k, v in payload.correction.items()
    }
    safe_correction = json.loads(json.dumps(safe_correction, default=str))

    ref.update({
        "status":       "resolved",
        "correction":   safe_correction,
        "auditor_note": payload.auditor_note,
        "resolved_at":  _now(),
    })
    return {"status": "resolved", "review_id": review_id}


@router.delete("/{review_id}")
def discard_review_item(review_id: str):
    """
    Mark an item as discarded (e.g. blurry image, not a real product).
    Does not delete the Firebase node — keeps an audit trail.
    """
    ref  = db.reference(f"human_review/{review_id}")
    node = ref.get()
    if node is None:
        return {"error": "not found"}, 404

    ref.update({"status": "discarded", "resolved_at": _now()})
    return {"status": "discarded", "review_id": review_id}
