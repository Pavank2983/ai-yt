from types import SimpleNamespace
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from app.models.video_platform_status import PlatformUploadStatus, VideoPlatformStatus
from app.services.ai_video_service import _claim_upload_status


class _Query:
    def __init__(self, session):
        self.session = session

    def filter(self, *args, **kwargs):
        return self

    def with_for_update(self):
        self.session.lock_count += 1
        return self

    def first(self):
        return self.session.existing

    def one(self):
        return self.session.existing


class _Session:
    def __init__(self, existing=None, duplicate_on_flush=False):
        self.existing = existing
        self.duplicate_on_flush = duplicate_on_flush
        self.added = []
        self.lock_count = 0
        self.rollback_count = 0
        self.flush_count = 0

    def query(self, model):
        return _Query(self)

    def add(self, value):
        self.added.append(value)

    def flush(self):
        self.flush_count += 1
        if self.duplicate_on_flush:
            self.existing = SimpleNamespace(
                status=PlatformUploadStatus.success,
                uploaded_url="https://www.youtube.com/watch?v=existing",
            )
            raise IntegrityError("INSERT", {}, RuntimeError("duplicate key"))

    def rollback(self):
        self.rollback_count += 1


def test_existing_success_is_reused_without_inserting_or_downgrading_status():
    existing = SimpleNamespace(
        status=PlatformUploadStatus.success,
        uploaded_url="https://www.youtube.com/watch?v=existing",
    )
    session = _Session(existing=existing)

    result = _claim_upload_status(session, video_id=21, platform_id=1)

    assert result is existing
    assert result.status == PlatformUploadStatus.success
    assert session.added == []
    assert session.flush_count == 0
    assert session.lock_count == 1


def test_existing_pending_status_is_reused_under_row_lock():
    existing = SimpleNamespace(status=PlatformUploadStatus.pending, uploaded_url=None)
    session = _Session(existing=existing)

    result = _claim_upload_status(session, video_id=21, platform_id=1)

    assert result is existing
    assert session.added == []
    assert session.lock_count == 1


def test_unique_conflict_reloads_the_committed_existing_row():
    session = _Session(duplicate_on_flush=True)

    result = _claim_upload_status(session, video_id=21, platform_id=1)

    assert result.status == PlatformUploadStatus.success
    assert result.uploaded_url.endswith("existing")
    assert session.rollback_count == 1
    assert session.lock_count == 2


def test_missing_status_is_inserted_once():
    session = _Session()

    result = _claim_upload_status(session, video_id=21, platform_id=1)

    assert result in session.added
    assert result.status == PlatformUploadStatus.pending
    assert session.flush_count == 1


def test_model_declares_video_platform_unique_constraint():
    constraints = VideoPlatformStatus.__table__.constraints
    matching = [
        constraint
        for constraint in constraints
        if constraint.name == "uq_video_platform_status_video_platform"
    ]

    assert len(matching) == 1
    assert [column.name for column in matching[0].columns] == [
        "video_id",
        "platform_id",
    ]


def test_unique_constraint_migration_is_non_destructive_and_chained():
    migration = Path(__file__).parents[1] / "migrations" / "versions" / (
        "d4f7c2e19a11_add_unique_video_platform_status.py"
    )
    source = migration.read_text(encoding="utf-8")

    assert 'down_revision: Union[str, Sequence[str], None] = "ab3aaf5f7a43"' in source
    assert "op.create_unique_constraint" in source
    assert "op.drop_constraint" in source
    assert "video_platform_status" in source
    assert "video_id" in source and "platform_id" in source
    assert "duplicate_pairs" in source
    assert "reconcile them before applying" in source
    assert "DELETE FROM" not in source.upper()
