from collections import Counter
from dataclasses import replace
from pathlib import Path

from kadai_sorter.models import AppConfig, PlanItem, PlanStatus
from kadai_sorter.parser import parse_file


def _under_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def build_plan(source: Path, output: Path, config: AppConfig) -> list[PlanItem]:
    source_resolved = source.resolve()
    output_resolved = output.resolve()
    if source_resolved == output_resolved:
        raise ValueError("入力と出力には別のフォルダを指定してください")
    if not source_resolved.is_dir():
        raise FileNotFoundError(f"入力フォルダがありません: {source}")

    items = [
        parse_file(path, config) for path in sorted(source_resolved.rglob("*")) if path.is_file()
    ]
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
        if not _under_root(destination.resolve(strict=False), output_resolved):
            result.append(
                replace(
                    item,
                    destination=None,
                    status=PlanStatus.CONFLICT,
                    reason="安全な出力先を作成できません",
                )
            )
        elif counts[destination] > 1:
            result.append(
                replace(
                    item,
                    destination=destination,
                    status=PlanStatus.CONFLICT,
                    reason="出力先が重複しています",
                )
            )
        elif destination.exists():
            result.append(
                replace(
                    item,
                    destination=destination,
                    status=PlanStatus.CONFLICT,
                    reason="出力先が既に存在します",
                )
            )
        else:
            result.append(replace(item, destination=destination))
    return result
