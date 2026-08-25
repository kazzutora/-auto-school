"""core.tasks.db_backup, tech.md sections 6 and 19.

Idempotency key is the dated filename: a second run on the same day must not
produce a second dump.
"""

import gzip
from datetime import date, timedelta
from pathlib import Path

import pytest

from apps.core.tasks import _rotate, db_backup

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def backup_dir(tmp_path: Path, settings) -> Path:
    directory = tmp_path / "backups"
    settings.BACKUP_DIR = directory
    return directory


def test_first_run_writes_one_dump(backup_dir: Path) -> None:
    result = db_backup.apply().get()

    dumps = sorted(backup_dir.glob("*.sql.gz"))
    assert len(dumps) == 1
    assert result["created"] == dumps[0].name


def test_second_run_on_the_same_day_does_nothing(backup_dir: Path) -> None:
    first = db_backup.apply().get()
    before = (backup_dir / first["created"]).read_bytes()

    second = db_backup.apply().get()

    assert second["created"] is None
    assert len(list(backup_dir.glob("*.sql.gz"))) == 1
    assert (backup_dir / first["created"]).read_bytes() == before


def test_the_dump_is_real_gzipped_sql(backup_dir: Path) -> None:
    """A backup nobody can restore is not a backup."""
    result = db_backup.apply().get()

    with gzip.open(backup_dir / result["created"], "rb") as archive:
        sql = archive.read().decode("utf-8", "replace")

    assert "CREATE TABLE public.core_page" in sql
    assert "CREATE TABLE public.gallery_galleryimage" in sql


def test_no_half_written_dump_survives_a_failure(backup_dir: Path, monkeypatch) -> None:
    """A truncated file would look finished to the next run and never be retried."""
    import apps.core.tasks as tasks

    def explode(*args: object, **kwargs: object) -> None:
        raise OSError("pg_dump vanished")

    monkeypatch.setattr(tasks.subprocess, "Popen", explode)

    with pytest.raises(OSError):
        db_backup.apply().get()

    assert list(backup_dir.glob("*.sql.gz")) == []
    assert list(backup_dir.glob("*.part")) == []


def test_rotation_keeps_the_retention_window(backup_dir: Path) -> None:
    """tech.md section 19: fourteen days."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    today = date(2026, 8, 25)
    for age in (0, 1, 13, 14, 15, 60):
        (backup_dir / f"osk-{today - timedelta(days=age):%Y%m%d}.sql.gz").write_bytes(b"x")
    (backup_dir / "notes.txt").write_bytes(b"keep me")

    removed = _rotate(backup_dir, keep_days=14, today=today)

    kept = {path.name for path in backup_dir.glob("*.sql.gz")}
    assert len(kept) == 4  # ages 0, 1, 13 and 14
    assert len(removed) == 2  # ages 15 and 60
    assert (backup_dir / "notes.txt").exists()


def test_rotation_ignores_files_it_did_not_write(backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "osk-not-a-date.sql.gz").write_bytes(b"x")

    assert _rotate(backup_dir, keep_days=14, today=date(2026, 8, 25)) == []
    assert (backup_dir / "osk-not-a-date.sql.gz").exists()
