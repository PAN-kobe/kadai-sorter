import csv
from pathlib import Path
from time import perf_counter_ns
from typing import TypedDict

import matplotlib.pyplot as plt

from kadai_sorter.models import AppConfig, CourseRule, PlanStatus
from kadai_sorter.planner import build_plan


class BenchmarkRow(TypedDict):
    files: int
    milliseconds: float
    accuracy: float
    blocked_conflicts: int


def _fixture_names(size: int) -> list[tuple[str, PlanStatus]]:
    rows: list[tuple[str, PlanStatus]] = []
    for index in range(size):
        kind = index % 4
        if kind == 0:
            rows.append((f"programming_assignment{index}_262e140e.pdf", PlanStatus.READY))
        elif kind == 1:
            rows.append((f"programming_assignment{index}.pdf", PlanStatus.SKIPPED))
        elif kind == 2:
            rows.append((f"programming_assignment{index}_262e140e.exe", PlanStatus.SKIPPED))
        else:
            rows.append((f"unknown_assignment{index}_262e140e.pdf", PlanStatus.SKIPPED))
    return rows


def run_benchmark(root: Path, sizes: tuple[int, ...] = (25, 100, 500)) -> list[BenchmarkRow]:
    config = AppConfig(
        student_id="262e140e",
        courses=(CourseRule("プログラミング", ("programming",), (".pdf",)),),
    )
    results: list[BenchmarkRow] = []
    for size in sizes:
        source = root / f"input-{size}"
        output = root / f"output-{size}"
        source.mkdir(parents=True, exist_ok=True)
        expected: dict[str, PlanStatus] = {}
        for filename, status in _fixture_names(size):
            (source / filename).write_bytes(b"sample")
            expected[filename] = status

        started = perf_counter_ns()
        plan = build_plan(source, output, config)
        elapsed_ms = (perf_counter_ns() - started) / 1_000_000
        correct = sum(item.status is expected[item.source.name] for item in plan)
        results.append(
            {
                "files": size,
                "milliseconds": elapsed_ms,
                "accuracy": correct / size,
                "blocked_conflicts": sum(item.status is PlanStatus.CONFLICT for item in plan),
            }
        )
    return results


def write_benchmark(output: Path) -> list[BenchmarkRow]:
    output.mkdir(parents=True, exist_ok=True)
    rows = run_benchmark(output / "fixtures")

    with (output / "benchmark.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(BenchmarkRow.__annotations__))
        writer.writeheader()
        writer.writerows(rows)

    figure, axis = plt.subplots(figsize=(7, 4))
    axis.plot(
        [row["files"] for row in rows],
        [row["milliseconds"] for row in rows],
        marker="o",
    )
    axis.set_xlabel("Files")
    axis.set_ylabel("Processing time (ms)")
    axis.set_title("Kadai Sorter benchmark")
    figure.tight_layout()
    figure.savefig(output / "benchmark.pdf")
    plt.close(figure)
    return rows
