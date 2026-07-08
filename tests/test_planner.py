from pathlib import Path

import pytest

from kadai_sorter.models import AppConfig, CourseRule, PlanStatus
from kadai_sorter.planner import build_plan


def test_plan_is_recursive_and_detects_duplicate_destinations(tmp_path: Path) -> None:
    config = AppConfig(
        student_id="262e140e",
        courses=(CourseRule("経済学", ("economics",), (".pdf",)),),
    )
    source = tmp_path / "in"
    output = tmp_path / "out"
    (source / "a").mkdir(parents=True)
    (source / "b").mkdir()
    (source / "a" / "economics_assignment1_262e140e.pdf").write_bytes(b"a")
    (source / "b" / "economics_report1_262e140e.pdf").write_bytes(b"b")

    plan = build_plan(source, output, config)

    assert [item.status for item in plan].count(PlanStatus.CONFLICT) == 2
    assert not output.exists()


def test_plan_returns_absolute_destination_for_ready_files(tmp_path: Path) -> None:
    config = AppConfig(
        student_id="262e140e",
        courses=(CourseRule("経済学", ("economics",), (".pdf",)),),
    )
    source = tmp_path / "in"
    output = tmp_path / "out"
    source.mkdir()
    (source / "economics_assignment2_262e140e.pdf").write_bytes(b"pdf")

    plan = build_plan(source, output, config)

    assert len(plan) == 1
    assert plan[0].status is PlanStatus.READY
    assert plan[0].destination == output.resolve() / "経済学/課題2/経済学_課題2_262e140e.pdf"
    assert not output.exists()


def test_plan_preserves_skipped_items(tmp_path: Path) -> None:
    config = AppConfig(
        student_id="262e140e",
        courses=(CourseRule("経済学", ("economics",), (".pdf",)),),
    )
    source = tmp_path / "in"
    output = tmp_path / "out"
    source.mkdir()
    (source / "history_assignment2_262e140e.pdf").write_bytes(b"pdf")

    plan = build_plan(source, output, config)

    assert len(plan) == 1
    assert plan[0].status is PlanStatus.SKIPPED
    assert plan[0].destination is None
    assert "科目" in plan[0].reason


def test_plan_detects_existing_destination_conflict(tmp_path: Path) -> None:
    config = AppConfig(
        student_id="262e140e",
        courses=(CourseRule("経済学", ("economics",), (".pdf",)),),
    )
    source = tmp_path / "in"
    output = tmp_path / "out"
    source.mkdir()
    (source / "economics_assignment2_262e140e.pdf").write_bytes(b"new")
    existing = output / "経済学/課題2/経済学_課題2_262e140e.pdf"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"old")

    plan = build_plan(source, output, config)

    assert len(plan) == 1
    assert plan[0].status is PlanStatus.CONFLICT
    assert "既に存在" in plan[0].reason
    assert existing.read_bytes() == b"old"


def test_plan_rejects_same_source_and_output(tmp_path: Path) -> None:
    config = AppConfig(
        student_id="262e140e",
        courses=(CourseRule("経済学", ("economics",), (".pdf",)),),
    )
    source = tmp_path / "same"
    source.mkdir()

    with pytest.raises(ValueError, match="別"):
        build_plan(source, source, config)


def test_plan_rejects_missing_source(tmp_path: Path) -> None:
    config = AppConfig(
        student_id="262e140e",
        courses=(CourseRule("経済学", ("economics",), (".pdf",)),),
    )

    with pytest.raises(FileNotFoundError):
        build_plan(tmp_path / "missing", tmp_path / "out", config)
