import csv
from pathlib import Path

from kadai_sorter.executor import execute_plan
from kadai_sorter.models import PlanItem, PlanStatus


def test_execute_copies_ready_file_and_writes_audit(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    destination = tmp_path / "out" / "course" / "source.pdf"
    source.write_bytes(b"coursework")
    plan = [PlanItem(source, destination, "course", "課題1", PlanStatus.READY, "")]

    results = execute_plan(plan, tmp_path / "audit.csv")

    assert destination.read_bytes() == b"coursework"
    assert results[0].status is PlanStatus.COPIED
    with (tmp_path / "audit.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["source"] == str(source)
    assert rows[0]["destination"] == str(destination)
    assert rows[0]["course"] == "course"
    assert rows[0]["assignment"] == "課題1"
    assert rows[0]["status"] == "copied"
    assert rows[0]["reason"] == ""


def test_execute_does_not_touch_skipped_file(tmp_path: Path) -> None:
    source = tmp_path / "unknown.txt"
    source.write_text("keep", encoding="utf-8")
    plan = [PlanItem(source, None, None, None, PlanStatus.SKIPPED, "科目不明")]

    results = execute_plan(plan, tmp_path / "audit.csv")

    assert source.read_text(encoding="utf-8") == "keep"
    assert results[0].status is PlanStatus.SKIPPED
    with (tmp_path / "audit.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["destination"] == ""
    assert rows[0]["status"] == "skipped"
    assert rows[0]["reason"] == "科目不明"


def test_execute_never_overwrites_existing_file(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    destination = tmp_path / "out.pdf"
    source.write_bytes(b"new")
    destination.write_bytes(b"original")
    plan = [PlanItem(source, destination, "course", "課題1", PlanStatus.READY, "")]

    results = execute_plan(plan, tmp_path / "audit.csv")

    assert destination.read_bytes() == b"original"
    assert results[0].status is PlanStatus.CONFLICT
    assert "既に存在" in results[0].reason


def test_execute_records_copy_errors(tmp_path: Path) -> None:
    source = tmp_path / "missing.pdf"
    destination = tmp_path / "out" / "missing.pdf"
    plan = [PlanItem(source, destination, "course", "課題1", PlanStatus.READY, "")]

    results = execute_plan(plan, tmp_path / "audit.csv")

    assert results[0].status is PlanStatus.ERROR
    assert results[0].reason
    assert not destination.exists()
