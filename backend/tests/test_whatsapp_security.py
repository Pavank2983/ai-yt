import hashlib
import hmac
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.api.webhooks.whatsapp_webhook import (
    _is_authorized_sender,
    _verify_signature,
    receive_webhook,
)
from app.models.approval_token import ApprovalAction, ApprovalToken
from app.models.video import ApprovalStatus, Video
from app.services.approval.approval_service import ApprovalError, process_approval_token


def _signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_webhook_signature_accepts_valid_raw_body_and_rejects_tampering():
    body = b'{"entry": []}'
    signature = _signature(body, "test-meta-secret")

    assert _verify_signature(body, signature, "test-meta-secret")
    assert not _verify_signature(body + b" ", signature, "test-meta-secret")
    assert not _verify_signature(body, None, "test-meta-secret")
    assert not _verify_signature(body, "sha256=not-hex", "test-meta-secret")
    assert not _verify_signature(body, signature, None)


def test_webhook_sender_must_match_configured_administrator():
    assert _is_authorized_sender("+91 98765-43210", "+919876543210")
    assert not _is_authorized_sender("+919876543211", "+919876543210")
    assert not _is_authorized_sender("+919876543210", None)
    assert not _is_authorized_sender(None, "+919876543210")


class _Request:
    def __init__(self, body: bytes, signature: str | None):
        self._body = body
        self.headers = {"X-Hub-Signature-256": signature} if signature else {}

    async def body(self):
        return self._body


def test_webhook_route_rejects_missing_or_invalid_signature():
    body = b'{"entry": []}'

    missing = asyncio.run(receive_webhook(_Request(body, None)))
    invalid = asyncio.run(receive_webhook(_Request(body, "sha256=bad")))

    assert missing.status_code == 403
    assert invalid.status_code == 403


def test_webhook_route_rejects_unauthorized_signed_sender(monkeypatch):
    import app.api.webhooks.whatsapp_webhook as webhook

    monkeypatch.setattr(webhook, "ADMIN_PHONE", "+919876543210")
    body = json.dumps(
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+919876543211",
                                        "type": "button",
                                        "button": {"payload": "redacted-test-token"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    ).encode()

    response = asyncio.run(
        receive_webhook(
            _Request(body, _signature(body, "test-meta-secret"))
        )
    )

    assert response.status_code == 403


class _FakeQuery:
    def __init__(self, db, model):
        self.db = db
        self.model = model

    def filter(self, *args, **kwargs):
        return self

    def with_for_update(self):
        self.db.locked_models.append(self.model)
        return self

    def one_or_none(self):
        if self.model is ApprovalToken:
            return self.db.token
        if self.model is Video:
            return self.db.video
        return None


class _FakeSession:
    def __init__(self, token, video):
        self.token = token
        self.video = video
        self.locked_models = []
        self.flush_count = 0
        self.commit_count = 0

    def query(self, model):
        return _FakeQuery(self, model)

    def flush(self):
        self.flush_count += 1

    def commit(self):
        self.commit_count += 1


def _approval_token(**overrides):
    values = {
        "id": 1,
        "video_id": 10,
        "used_at": None,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "action": ApprovalAction.approve,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _video(**overrides):
    values = {
        "id": 10,
        "approval_status": ApprovalStatus.pending_review,
        "approved_at": None,
        "rejected_at": None,
        "approved_by": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_approval_transition_locks_rows_and_commits_once():
    token = _approval_token()
    video = _video()
    db = _FakeSession(token, video)

    result = process_approval_token(db, token)

    assert result is video
    assert video.approval_status == ApprovalStatus.approved
    assert token.used_at is not None
    assert db.locked_models == [ApprovalToken, Video]
    assert db.flush_count == 1
    assert db.commit_count == 1


def test_duplicate_delivery_cannot_reuse_the_consumed_token():
    token = _approval_token()
    video = _video()
    db = _FakeSession(token, video)

    process_approval_token(db, token)

    with pytest.raises(ApprovalError, match="Token already used"):
        process_approval_token(db, token)


def test_competing_approval_and_rejection_cannot_both_transition_video():
    approve_token = _approval_token(action=ApprovalAction.approve)
    reject_token = _approval_token(id=2, action=ApprovalAction.reject)
    video = _video()

    process_approval_token(_FakeSession(approve_token, video), approve_token)

    with pytest.raises(ApprovalError, match="Video already processed"):
        process_approval_token(_FakeSession(reject_token, video), reject_token)


def test_replayed_or_expired_tokens_and_processed_videos_are_rejected():
    used_token = _approval_token(used_at=datetime.now(timezone.utc))
    with pytest.raises(ApprovalError, match="Token already used"):
        process_approval_token(_FakeSession(used_token, _video()), used_token)

    expired_token = _approval_token(
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)
    )
    with pytest.raises(ApprovalError, match="Token expired"):
        process_approval_token(_FakeSession(expired_token, _video()), expired_token)

    active_token = _approval_token()
    rejected_video = _video(approval_status=ApprovalStatus.rejected)
    with pytest.raises(ApprovalError, match="Video already processed"):
        process_approval_token(_FakeSession(active_token, rejected_video), active_token)


def test_migration_status_enum_preserves_processing_and_publishing_values():
    migration = Path(__file__).parents[1] / "migrations" / "versions" / (
        "ab3aaf5f7a43_add_publishing_to_video_status.py"
    )
    source = migration.read_text(encoding="utf-8")

    # Both directions retain all statuses that can exist in the database;
    # notably, processing must not be dropped by the upgrade.
    for value in (
        "draft",
        "processing",
        "rendering",
        "ready_for_review",
        "uploaded",
        "publishing",
        "published",
        "failed",
    ):
        assert source.count(f"'{value}'") >= 2
