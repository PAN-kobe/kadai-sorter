from collections import Counter
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from kadai_sorter.benchmark import write_benchmark
from kadai_sorter.charts import create_status_chart
from kadai_sorter.config import ConfigError, load_config
from kadai_sorter.executor import execute_plan
from kadai_sorter.models import PlanItem, PlanStatus
from kadai_sorter.planner import build_plan

app = typer.Typer(help="大学の課題ファイルを安全に整理します。")
console = Console(color_system=None)


def _show(items: list[PlanItem]) -> None:
    table = Table("入力", "出力", "状態", "理由")
    for item in items:
        table.add_row(
            str(item.source),
            str(item.destination or "-"),
            item.status.value,
            item.reason,
        )
    console.print(table)


def _plan(source: Path, output: Path, config: Path) -> list[PlanItem]:
    try:
        return build_plan(source, output, load_config(config))
    except (ConfigError, FileNotFoundError, ValueError) as error:
        console.print(str(error))
        raise typer.Exit(code=2) from error


@app.command()
def scan(
    source: Path,
    output: Path,
    config: Path = typer.Option(..., "--config", "-c", help="整理ルールのTOMLファイル"),
) -> None:
    """整理計画を表示します。"""
    _show(_plan(source, output, config))


@app.command()
def organize(
    source: Path,
    output: Path,
    config: Path = typer.Option(..., "--config", "-c", help="整理ルールのTOMLファイル"),
) -> None:
    """検証済みファイルをコピーします。"""
    audit_path = output / "kadai-sort-audit.csv"
    results = execute_plan(_plan(source, output, config), audit_path)
    _show(results)
    counts = Counter(item.status for item in results)
    console.print(
        f"コピー: {counts[PlanStatus.COPIED]} / "
        f"スキップ: {counts[PlanStatus.SKIPPED]} / "
        f"競合: {counts[PlanStatus.CONFLICT]} / "
        f"エラー: {counts[PlanStatus.ERROR]}"
    )
    console.print(f"監査CSV: {audit_path}")


@app.command()
def report(audit: Path, output: Path) -> None:
    """監査CSVからグラフを作成します。"""
    create_status_chart(audit, output)
    console.print(f"グラフを作成しました: {output}")


@app.command()
def benchmark(output: Path = typer.Option(Path("report"), "--output", "-o")) -> None:
    """合成データで処理時間と分類精度を測定します。"""
    write_benchmark(output)
    console.print(f"ベンチマークを保存しました: {output}")
