# Kadai Sorter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a safe Python CLI that validates, classifies, copies, audits, and visualizes university coursework files, then deliver a public-ready repository and a two-page Japanese LaTeX report.

**Architecture:** Pure parsing and planning modules produce immutable records without mutating the filesystem. A separate executor copies only validated plans and writes an audit CSV; reporting code reads that CSV to create charts. Typer and Rich provide a thin CLI over these testable modules.

**Tech Stack:** Python 3.12, uv, Typer, Rich, Matplotlib, pytest, mypy, Ruff, GitHub Actions, LaTeX.

---

## File Structure

- `pyproject.toml`: package metadata, dependencies, command entry point, and tool configuration.
- `src/kadai_sorter/models.py`: status enum and immutable configuration/plan records.
- `src/kadai_sorter/config.py`: TOML loading and validation.
- `src/kadai_sorter/parser.py`: course, assignment, student ID, and extension parsing.
- `src/kadai_sorter/planner.py`: scanning and collision detection.
- `src/kadai_sorter/executor.py`: safe copying and CSV audit writing.
- `src/kadai_sorter/charts.py`: audit aggregation and Matplotlib output.
- `src/kadai_sorter/benchmark.py`: reproducible synthetic benchmark.
- `src/kadai_sorter/cli.py`: `scan`, `organize`, `report`, and `benchmark` commands.
- `tests/`: unit and integration tests matching each module.
- `.github/workflows/ci.yml`: Ruff, mypy, and pytest checks.
- `examples/rules.toml`: student-ready configuration example.
- `README.md`: concise Japanese user and developer documentation.
- `LICENSE`: MIT license.
- `report/report.tex`: Japanese two-page final report.
- `report/benchmark.pdf`: vector chart generated from measured data.

### Task 1: Package Skeleton And Quality Gates

**Files:**
- Create: `pyproject.toml`
- Create: `src/kadai_sorter/__init__.py`
- Create: `src/kadai_sorter/cli.py`
- Create: `tests/test_cli.py`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the failing CLI smoke test**

```python
from typer.testing import CliRunner

from kadai_sorter.cli import app


def test_cli_help_lists_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.stdout
    assert "organize" in result.stdout
    assert "report" in result.stdout
```

- [ ] **Step 2: Add package metadata and test dependencies**

```toml
[project]
name = "kadai-sorter"
version = "0.1.0"
description = "Safely organize university coursework files"
requires-python = ">=3.12"
dependencies = ["matplotlib>=3.9", "rich>=13.9", "typer>=0.15"]

[project.scripts]
kadai-sort = "kadai_sorter.cli:app"

[dependency-groups]
dev = ["mypy>=1.13", "pytest>=8.3", "ruff>=0.8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/kadai_sorter"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.mypy]
python_version = "3.12"
strict = true
packages = ["kadai_sorter"]

[tool.ruff]
target-version = "py312"
line-length = 100
```

- [ ] **Step 3: Run the test and verify the missing app failure**

Run: `uv run pytest tests/test_cli.py -v`

Expected: FAIL because `kadai_sorter.cli` or `app` does not exist.

- [ ] **Step 4: Add the minimal Typer app**

```python
import typer

app = typer.Typer(help="大学の課題ファイルを安全に整理します。")


@app.command()
def scan() -> None:
    """整理計画を表示します。"""


@app.command()
def organize() -> None:
    """検証済みファイルをコピーします。"""


@app.command()
def report() -> None:
    """監査CSVからグラフを作成します。"""
```

- [ ] **Step 5: Add GitHub Actions**

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.12"
      - run: uv sync --all-groups
      - run: uv run ruff check .
      - run: uv run mypy src
      - run: uv run pytest
```

- [ ] **Step 6: Verify and commit**

Run: `uv run pytest tests/test_cli.py -v`

Expected: PASS.

Run: `uv run ruff check . && uv run mypy src`

Expected: both commands exit with code 0.

Commit:

```bash
git add pyproject.toml src tests .github/workflows/ci.yml
git commit -m "build: initialize typed Python CLI"
```

### Task 2: Configuration And Domain Models

**Files:**
- Create: `src/kadai_sorter/models.py`
- Create: `src/kadai_sorter/config.py`
- Create: `tests/test_config.py`
- Create: `examples/rules.toml`

- [ ] **Step 1: Write configuration tests**

```python
from pathlib import Path

import pytest

from kadai_sorter.config import ConfigError, load_config


def test_load_config_reads_student_and_course(tmp_path: Path) -> None:
    path = tmp_path / "rules.toml"
    path.write_text(
        'student_id = "262e140e"\n'
        '[[courses]]\nname = "プログラミング"\n'
        'aliases = ["programming", "プログラミング"]\n'
        'extensions = [".pdf", ".py"]\n',
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.student_id == "262e140e"
    assert config.courses[0].name == "プログラミング"


def test_load_config_rejects_empty_aliases(tmp_path: Path) -> None:
    path = tmp_path / "rules.toml"
    path.write_text(
        'student_id = "262e140e"\n'
        '[[courses]]\nname = "経済学"\naliases = []\nextensions = [".pdf"]\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="aliases"):
        load_config(path)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_config.py -v`

Expected: FAIL because model and loader modules are missing.

- [ ] **Step 3: Implement immutable models**

```python
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class PlanStatus(StrEnum):
    READY = "ready"
    SKIPPED = "skipped"
    CONFLICT = "conflict"
    COPIED = "copied"
    ERROR = "error"


@dataclass(frozen=True)
class CourseRule:
    name: str
    aliases: tuple[str, ...]
    extensions: tuple[str, ...]


@dataclass(frozen=True)
class AppConfig:
    student_id: str
    courses: tuple[CourseRule, ...]


@dataclass(frozen=True)
class PlanItem:
    source: Path
    destination: Path | None
    course: str | None
    assignment: str | None
    status: PlanStatus
    reason: str
```

- [ ] **Step 4: Implement strict TOML loading**

```python
import tomllib
from pathlib import Path

from kadai_sorter.models import AppConfig, CourseRule


class ConfigError(ValueError):
    pass


def load_config(path: Path) -> AppConfig:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"設定ファイルを読み込めません: {exc}") from exc
    student_id = data.get("student_id")
    raw_courses = data.get("courses")
    if not isinstance(student_id, str) or not student_id.strip():
        raise ConfigError("student_id を指定してください")
    if not isinstance(raw_courses, list) or not raw_courses:
        raise ConfigError("courses を1件以上指定してください")
    courses: list[CourseRule] = []
    for raw in raw_courses:
        name = raw.get("name")
        aliases = raw.get("aliases")
        extensions = raw.get("extensions")
        if not isinstance(name, str) or not name:
            raise ConfigError("course name が必要です")
        if not isinstance(aliases, list) or not aliases or not all(isinstance(x, str) for x in aliases):
            raise ConfigError(f"{name}: aliases を1件以上指定してください")
        if not isinstance(extensions, list) or not extensions:
            raise ConfigError(f"{name}: extensions を1件以上指定してください")
        normalized = tuple(x.lower() if x.startswith(".") else f".{x.lower()}" for x in extensions)
        courses.append(CourseRule(name, tuple(aliases), normalized))
    return AppConfig(student_id.strip(), tuple(courses))
```

- [ ] **Step 5: Add a Japanese example configuration**

```toml
student_id = "262e140e"

[[courses]]
name = "プログラミング"
aliases = ["programming", "プログラミング", "プログラム"]
extensions = [".py", ".pdf", ".tex", ".zip"]

[[courses]]
name = "応用国際経済学"
aliases = ["international-economics", "応用国際経済学", "国際経済学"]
extensions = [".pdf", ".docx", ".tex"]
```

- [ ] **Step 6: Verify and commit**

Run: `uv run pytest tests/test_config.py -v`

Expected: PASS.

Commit:

```bash
git add src/kadai_sorter/models.py src/kadai_sorter/config.py tests/test_config.py examples
git commit -m "feat: load coursework organization rules"
```

### Task 3: Filename Parser

**Files:**
- Create: `src/kadai_sorter/parser.py`
- Create: `tests/test_parser.py`

- [ ] **Step 1: Write parser tests**

```python
from pathlib import Path

from kadai_sorter.models import AppConfig, CourseRule, PlanStatus
from kadai_sorter.parser import parse_file

CONFIG = AppConfig(
    "262e140e",
    (CourseRule("プログラミング", ("programming", "プログラミング"), (".pdf", ".py")),),
)


def test_parse_japanese_filename() -> None:
    item = parse_file(Path("プログラミング_課題3_262e140e.pdf"), CONFIG)
    assert item.status is PlanStatus.READY
    assert item.course == "プログラミング"
    assert item.assignment == "課題3"


def test_parse_reports_missing_student_id() -> None:
    item = parse_file(Path("programming-assignment-3.pdf"), CONFIG)
    assert item.status is PlanStatus.SKIPPED
    assert "学籍番号" in item.reason


def test_parse_rejects_unsupported_extension() -> None:
    item = parse_file(Path("programming_assignment3_262e140e.exe"), CONFIG)
    assert item.status is PlanStatus.SKIPPED
    assert "拡張子" in item.reason
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_parser.py -v`

Expected: FAIL because `parse_file` is missing.

- [ ] **Step 3: Implement normalized parsing**

```python
import re
import unicodedata
from pathlib import Path

from kadai_sorter.models import AppConfig, PlanItem, PlanStatus

ASSIGNMENT_RE = re.compile(r"(?:課題|assignment|report)[-_ ]*0*(\d+)", re.IGNORECASE)


def _normalized(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def parse_file(path: Path, config: AppConfig) -> PlanItem:
    stem = _normalized(path.stem)
    rule = next(
        (course for course in config.courses if any(_normalized(alias) in stem for alias in course.aliases)),
        None,
    )
    if rule is None:
        return PlanItem(path, None, None, None, PlanStatus.SKIPPED, "科目を判定できません")
    if path.suffix.lower() not in rule.extensions:
        return PlanItem(path, None, rule.name, None, PlanStatus.SKIPPED, "未対応の拡張子です")
    match = ASSIGNMENT_RE.search(stem)
    if match is None:
        return PlanItem(path, None, rule.name, None, PlanStatus.SKIPPED, "課題番号がありません")
    assignment = f"課題{int(match.group(1))}"
    if _normalized(config.student_id) not in stem:
        return PlanItem(path, None, rule.name, assignment, PlanStatus.SKIPPED, "学籍番号がありません")
    filename = f"{rule.name}_{assignment}_{config.student_id}{path.suffix.lower()}"
    return PlanItem(path, Path(rule.name) / assignment / filename, rule.name, assignment, PlanStatus.READY, "")
```

- [ ] **Step 4: Verify edge cases and commit**

Run: `uv run pytest tests/test_parser.py -v`

Expected: PASS for Japanese, ASCII, missing ID, missing assignment, and extension cases.

Commit:

```bash
git add src/kadai_sorter/parser.py tests/test_parser.py
git commit -m "feat: classify and normalize coursework filenames"
```

### Task 4: Safe Planning And Collision Detection

**Files:**
- Create: `src/kadai_sorter/planner.py`
- Create: `tests/test_planner.py`

- [ ] **Step 1: Write planner tests**

```python
from pathlib import Path

from kadai_sorter.models import AppConfig, CourseRule, PlanStatus
from kadai_sorter.planner import build_plan


def test_plan_is_recursive_and_detects_duplicate_destinations(tmp_path: Path) -> None:
    config = AppConfig(
        "262e140e",
        (CourseRule("経済学", ("economics",), (".pdf",)),),
    )
    source = tmp_path / "in"
    output = tmp_path / "out"
    (source / "a").mkdir(parents=True)
    (source / "b").mkdir()
    (source / "a/economics_assignment1_262e140e.pdf").write_bytes(b"a")
    (source / "b/economics_report1_262e140e.pdf").write_bytes(b"b")
    plan = build_plan(source, output, config)
    assert [item.status for item in plan].count(PlanStatus.CONFLICT) == 2
    assert not output.exists()
```

- [ ] **Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_planner.py -v`

Expected: FAIL because `build_plan` is missing.

- [ ] **Step 3: Implement a mutation-free planner**

```python
from collections import Counter
from dataclasses import replace
from pathlib import Path

from kadai_sorter.models import AppConfig, PlanItem, PlanStatus
from kadai_sorter.parser import parse_file


def build_plan(source: Path, output: Path, config: AppConfig) -> list[PlanItem]:
    source_resolved = source.resolve()
    output_resolved = output.resolve()
    if source_resolved == output_resolved:
        raise ValueError("入力と出力には別のフォルダを指定してください")
    if not source_resolved.is_dir():
        raise FileNotFoundError(f"入力フォルダがありません: {source}")
    items = [parse_file(path, config) for path in sorted(source_resolved.rglob("*")) if path.is_file()]
    ready_destinations = [
        output_resolved / item.destination
        for item in items
        if item.status is PlanStatus.READY and item.destination is not None
    ]
    counts = Counter(ready_destinations)
    result: list[PlanItem] = []
    for item in items:
        if item.status is not PlanStatus.READY or item.destination is None:
            result.append(item)
            continue
        destination = output_resolved / item.destination
        if counts[destination] > 1:
            result.append(replace(item, destination=destination, status=PlanStatus.CONFLICT, reason="出力先が重複しています"))
        elif destination.exists():
            result.append(replace(item, destination=destination, status=PlanStatus.CONFLICT, reason="出力先が既に存在します"))
        else:
            result.append(replace(item, destination=destination))
    return result
```

- [ ] **Step 4: Verify planner safety and commit**

Run: `uv run pytest tests/test_planner.py -v`

Expected: PASS and no output directory is created by planning.

Commit:

```bash
git add src/kadai_sorter/planner.py tests/test_planner.py
git commit -m "feat: plan safe coursework file operations"
```

### Task 5: Copy Executor And Audit CSV

**Files:**
- Create: `src/kadai_sorter/executor.py`
- Create: `tests/test_executor.py`

- [ ] **Step 1: Write integration tests**

```python
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
        assert list(csv.DictReader(handle))[0]["status"] == "copied"
```

- [ ] **Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_executor.py -v`

Expected: FAIL because `execute_plan` is missing.

- [ ] **Step 3: Implement safe copies and complete audit rows**

```python
import csv
import shutil
from dataclasses import replace
from pathlib import Path

from kadai_sorter.models import PlanItem, PlanStatus

FIELDNAMES = ["source", "destination", "course", "assignment", "status", "reason"]


def execute_plan(plan: list[PlanItem], audit_path: Path) -> list[PlanItem]:
    results: list[PlanItem] = []
    for item in plan:
        if item.status is not PlanStatus.READY or item.destination is None:
            results.append(item)
            continue
        try:
            item.destination.parent.mkdir(parents=True, exist_ok=True)
            if item.destination.exists():
                results.append(replace(item, status=PlanStatus.CONFLICT, reason="出力先が既に存在します"))
                continue
            shutil.copy2(item.source, item.destination)
            results.append(replace(item, status=PlanStatus.COPIED))
        except OSError as exc:
            results.append(replace(item, status=PlanStatus.ERROR, reason=str(exc)))
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for item in results:
            writer.writerow(
                {
                    "source": item.source,
                    "destination": item.destination or "",
                    "course": item.course or "",
                    "assignment": item.assignment or "",
                    "status": item.status,
                    "reason": item.reason,
                }
            )
    return results
```

- [ ] **Step 4: Add tests for skipped files, reruns, and copy errors**

```python
def test_execute_does_not_touch_skipped_file(tmp_path: Path) -> None:
    source = tmp_path / "unknown.txt"
    source.write_text("keep", encoding="utf-8")
    plan = [PlanItem(source, None, None, None, PlanStatus.SKIPPED, "科目不明")]
    results = execute_plan(plan, tmp_path / "audit.csv")
    assert source.read_text(encoding="utf-8") == "keep"
    assert results[0].status is PlanStatus.SKIPPED


def test_execute_never_overwrites_existing_file(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    destination = tmp_path / "out.pdf"
    source.write_bytes(b"new")
    destination.write_bytes(b"original")
    plan = [PlanItem(source, destination, "course", "課題1", PlanStatus.READY, "")]
    results = execute_plan(plan, tmp_path / "audit.csv")
    assert destination.read_bytes() == b"original"
    assert results[0].status is PlanStatus.CONFLICT
```

- [ ] **Step 5: Verify and commit**

Run: `uv run pytest tests/test_executor.py -v`

Expected: PASS.

Commit:

```bash
git add src/kadai_sorter/executor.py tests/test_executor.py
git commit -m "feat: copy validated files and write audit CSV"
```

### Task 6: Charts And Reproducible Benchmark

**Files:**
- Create: `src/kadai_sorter/charts.py`
- Create: `src/kadai_sorter/benchmark.py`
- Create: `tests/test_charts.py`
- Create: `tests/test_benchmark.py`

- [ ] **Step 1: Write aggregation and benchmark tests**

```python
from pathlib import Path

from kadai_sorter.benchmark import run_benchmark
from kadai_sorter.charts import summarize_audit


def test_summarize_audit_counts_statuses(tmp_path: Path) -> None:
    csv_path = tmp_path / "audit.csv"
    csv_path.write_text(
        "source,destination,course,assignment,status,reason\n"
        "a,b,経済学,課題1,copied,\n"
        "c,,経済学,,skipped,課題番号がありません\n",
        encoding="utf-8",
    )
    assert summarize_audit(csv_path)["copied"] == 1
    assert summarize_audit(csv_path)["skipped"] == 1


def test_benchmark_is_reproducible(tmp_path: Path) -> None:
    first = run_benchmark(tmp_path / "a", sizes=(25, 50))
    second = run_benchmark(tmp_path / "b", sizes=(25, 50))
    assert [row["accuracy"] for row in first] == [1.0, 1.0]
    assert [row["files"] for row in first] == [row["files"] for row in second]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_charts.py tests/test_benchmark.py -v`

Expected: FAIL because chart and benchmark functions are missing.

- [ ] **Step 3: Implement CSV aggregation and chart output**

```python
import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


def summarize_audit(path: Path) -> Counter[str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return Counter(row["status"] for row in csv.DictReader(handle))


def create_status_chart(audit_path: Path, output_path: Path) -> None:
    counts = summarize_audit(audit_path)
    labels = ["copied", "skipped", "conflict", "error"]
    values = [counts[label] for label in labels]
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.bar(labels, values, color=["#2f6f4e", "#d9a441", "#b54a4a", "#555555"])
    axis.set_title("Kadai Sorter results")
    axis.set_ylabel("Files")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
```

- [ ] **Step 4: Implement synthetic labeled fixtures and timing**

```python
from pathlib import Path
from time import perf_counter_ns
from typing import TypedDict

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
        "262e140e",
        (CourseRule("プログラミング", ("programming",), (".pdf",)),),
    )
    results: list[BenchmarkRow] = []
    for size in sizes:
        source = root / f"input-{size}"
        output = root / f"output-{size}"
        source.mkdir(parents=True)
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
```

```python
def test_duplicate_fixture_is_blocked(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / "programming_assignment1_262e140e.pdf").write_bytes(b"a")
    (source / "programming_report1_262e140e.pdf").write_bytes(b"b")
    config = AppConfig(
        "262e140e",
        (CourseRule("プログラミング", ("programming",), (".pdf",)),),
    )
    plan = build_plan(source, tmp_path / "output", config)
    assert [item.status for item in plan] == [PlanStatus.CONFLICT, PlanStatus.CONFLICT]
```

- [ ] **Step 5: Create benchmark CSV and vector chart**

Add the public writer used by the CLI:

```python
import csv

import matplotlib.pyplot as plt


def write_benchmark(output: Path) -> list[BenchmarkRow]:
    output.mkdir(parents=True, exist_ok=True)
    rows = run_benchmark(output / "fixtures")
    with (output / "benchmark.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(BenchmarkRow.__annotations__))
        writer.writeheader()
        writer.writerows(rows)
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.plot([row["files"] for row in rows], [row["milliseconds"] for row in rows], marker="o")
    axis.set_xlabel("Files")
    axis.set_ylabel("Processing time (ms)")
    axis.set_title("Kadai Sorter benchmark")
    figure.tight_layout()
    figure.savefig(output / "benchmark.pdf")
    plt.close(figure)
    return rows
```

Run:

```bash
uv run kadai-sort benchmark --output report
```

Expected files:

- `report/benchmark.csv`
- `report/benchmark.pdf`

Expected result: accuracy is `1.0` for every fixture size and processing time is
measured rather than hard-coded.

- [ ] **Step 6: Verify and commit**

Run: `uv run pytest tests/test_charts.py tests/test_benchmark.py -v`

Expected: PASS.

Commit:

```bash
git add src/kadai_sorter/charts.py src/kadai_sorter/benchmark.py tests report/benchmark.csv report/benchmark.pdf
git commit -m "feat: measure and visualize organizer performance"
```

### Task 7: Complete CLI, README, License, And End-To-End Tests

**Files:**
- Modify: `src/kadai_sorter/cli.py`
- Modify: `tests/test_cli.py`
- Create: `tests/test_integration.py`
- Create: `README.md`
- Create: `LICENSE`

- [ ] **Step 1: Write end-to-end CLI tests**

```python
def test_organize_command_copies_and_reports(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    (source / "programming_assignment3_262e140e.pdf").write_bytes(b"pdf")
    config = write_test_config(tmp_path)
    result = CliRunner().invoke(
        app,
        ["organize", str(source), str(output), "--config", str(config)],
    )
    assert result.exit_code == 0
    assert "コピー: 1" in result.stdout
    assert (output / "プログラミング/課題3/プログラミング_課題3_262e140e.pdf").exists()
    assert (output / "kadai-sort-audit.csv").exists()
```

- [ ] **Step 2: Run the end-to-end test and verify failure**

Run: `uv run pytest tests/test_integration.py -v`

Expected: FAIL because CLI command parameters are not wired.

- [ ] **Step 3: Wire commands to config, planner, executor, charts, and benchmark**

```python
from collections import Counter
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from kadai_sorter.benchmark import write_benchmark
from kadai_sorter.charts import create_status_chart
from kadai_sorter.config import ConfigError, load_config
from kadai_sorter.executor import execute_plan
from kadai_sorter.models import PlanItem
from kadai_sorter.planner import build_plan

app = typer.Typer(help="大学の課題ファイルを安全に整理します。")
console = Console()


def _show(items: list[PlanItem]) -> None:
    table = Table("入力", "出力", "状態", "理由")
    for item in items:
        table.add_row(str(item.source), str(item.destination or "-"), item.status, item.reason)
    console.print(table)


def _plan(source: Path, output: Path, config: Path) -> list[PlanItem]:
    try:
        return build_plan(source, output, load_config(config))
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc


@app.command()
def scan(source: Path, output: Path, config: Path = typer.Option(...)) -> None:
    _show(_plan(source, output, config))


@app.command()
def organize(source: Path, output: Path, config: Path = typer.Option(...)) -> None:
    results = execute_plan(_plan(source, output, config), output / "kadai-sort-audit.csv")
    _show(results)
    counts = Counter(item.status for item in results)
    console.print(f"コピー: {counts['copied']} / スキップ: {counts['skipped']}")


@app.command()
def report(audit: Path, output: Path) -> None:
    create_status_chart(audit, output)
    console.print(f"グラフを作成しました: {output}")


@app.command()
def benchmark(output: Path = typer.Option(Path("report"))) -> None:
    write_benchmark(output)
    console.print(f"ベンチマークを保存しました: {output}")
```

- [ ] **Step 4: Write concise Japanese README sections**

Use this structure and replace only command output with verified output:

```markdown
# Kadai Sorter

[![CI](https://github.com/OWNER/kadai-sorter/actions/workflows/ci.yml/badge.svg)](...)

大学の課題ファイルを科目・課題番号・学籍番号で検証し、安全にコピーして整理するCLIです。

## インストール
`uv tool install .`

## 使い方
`kadai-sort scan INPUT OUTPUT --config examples/rules.toml`
`kadai-sort organize INPUT OUTPUT --config examples/rules.toml`
`kadai-sort report OUTPUT/kadai-sort-audit.csv OUTPUT/status.png`

## 安全性
元ファイルを変更せず、既存の出力ファイルを上書きしません。

## 開発
`uv sync --all-groups`
`uv run pytest`
`uv run ruff check .`
`uv run mypy src`

## ライセンス
MIT
```

Add the `examples/rules.toml` contents directly under a `設定` heading and one
terminal transcript under an `実行例` heading showing copied, skipped, and
conflict counts from the integration fixture. Keep the README focused on users
rather than reproducing the final report.

- [ ] **Step 5: Add MIT license and full verification**

Run:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

Expected: all commands exit with code 0 and pytest reports no failures.

- [ ] **Step 6: Commit**

```bash
git add src tests README.md LICENSE
git commit -m "docs: complete user workflow and repository guidance"
```

### Task 8: Japanese LaTeX Report And Final Repository Audit

**Files:**
- Create: `report/report.tex`
- Create: `report/report.pdf`
- Create: `report/README.md`
- Modify: `README.md`

- [ ] **Step 1: Generate fresh benchmark evidence**

Run:

```bash
uv run kadai-sort benchmark --output report
```

Expected: benchmark CSV and PDF chart are recreated from the current software.

- [ ] **Step 2: Write the two-page Japanese LaTeX report**

Start from this file and replace `MEASURED_*` and `REPOSITORY_URL` only with
values read from the generated benchmark CSV and the created repository:

```latex
\documentclass[a4paper,10pt]{bxjsarticle}
\usepackage[margin=17mm]{geometry}
\usepackage{graphicx}
\title{Kadai Sorter: 課題ファイル整理支援ソフトウェア}
\author{潘東キン（学籍番号：262e140e）}
\date{}
\begin{document}
\maketitle
\vspace{-8mm}
\section{目的}
複数科目の課題ファイルについて、命名ミスと保存場所の混乱を減らすことを目的とした。
リポジトリ：\texttt{REPOSITORY_URL}
\section{実装}
ファイル名を正規化して科目・課題番号・学籍番号・拡張子を検証し、操作計画を作成する。
元ファイルは変更せず、既存ファイルも上書きしない。Typer、Rich、Matplotlibを利用し、
pytest、mypy、Ruff、GitHub Actionsで品質を確認した。
\section{検証}
合成データMEASURED_FILES件に対する分類精度はMEASURED_ACCURACY\%、
処理時間はMEASURED_TIMEミリ秒であった。重複出力MEASURED_CONFLICTS件をすべて停止した。
\begin{figure}[h]
\centering
\includegraphics[width=.72\linewidth]{benchmark.pdf}
\caption{ファイル数と処理時間}
\end{figure}
\section{AIの使用}
OpenAI Codexを設計整理、実装支援、テスト案、文書作成、最終確認に使用した。
生成内容はテストと実行結果で検証し、測定値を推測で記載しないようにした。
\end{document}
```

Keep the compiled result within two A4 pages and do not use invented values.

- [ ] **Step 3: Compile and visually inspect**

Run:

```bash
latexmk -pdf -interaction=nonstopmode report.tex
pdfinfo report.pdf
pdftoppm -png -r 150 report.pdf preview/page
```

Expected: LaTeX exits with code 0, `pdfinfo` reports exactly 2 pages or fewer,
and rendered pages contain no clipping, missing glyphs, or overlapping content.

- [ ] **Step 4: Audit every course checkpoint**

Run:

```bash
git log --oneline --decorate -10
git status --short
uv run ruff check .
uv run mypy src
uv run pytest
```

Confirm:

- README includes purpose, examples, installation, usage, developer setup,
  tests, and CI badge.
- CI workflow exists.
- Unit and integration tests pass.
- Commit history has meaningful milestones.
- License exists.
- No `.env`, API keys, real coursework, or personal files are tracked.
- Report includes required identity, URL, sections, measured verification,
  Matplotlib chart, and AI disclosure.

- [ ] **Step 5: Commit final deliverables**

```bash
git add README.md report
git commit -m "docs: add verified Japanese final report"
```
