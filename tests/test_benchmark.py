import csv
from pathlib import Path

from kadai_sorter.benchmark import run_benchmark, write_benchmark
from kadai_sorter.models import AppConfig, CourseRule, PlanStatus
from kadai_sorter.planner import build_plan


def test_benchmark_is_reproducible(tmp_path: Path) -> None:
    first = run_benchmark(tmp_path / "a", sizes=(25, 50))
    second = run_benchmark(tmp_path / "b", sizes=(25, 50))

    assert [row["accuracy"] for row in first] == [1.0, 1.0]
    assert [row["files"] for row in first] == [row["files"] for row in second]


def test_duplicate_fixture_is_blocked(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / "programming_assignment1_262e140e.pdf").write_bytes(b"a")
    (source / "programming_report1_262e140e.pdf").write_bytes(b"b")
    config = AppConfig(
        student_id="262e140e",
        courses=(CourseRule("プログラミング", ("programming",), (".pdf",)),),
    )

    plan = build_plan(source, tmp_path / "output", config)

    assert [item.status for item in plan] == [PlanStatus.CONFLICT, PlanStatus.CONFLICT]


def test_write_benchmark_outputs_csv_and_vector_chart(tmp_path: Path) -> None:
    rows = write_benchmark(tmp_path)

    assert rows
    assert (tmp_path / "benchmark.pdf").exists()
    with (tmp_path / "benchmark.csv").open(encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert [int(row["files"]) for row in csv_rows] == [row["files"] for row in rows]
    assert all(float(row["accuracy"]) == 1.0 for row in csv_rows)


def test_write_benchmark_can_be_recreated(tmp_path: Path) -> None:
    write_benchmark(tmp_path)

    rows = write_benchmark(tmp_path)

    assert [row["files"] for row in rows] == [25, 100, 500]
