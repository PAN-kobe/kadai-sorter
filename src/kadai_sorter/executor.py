import csv
import shutil
from dataclasses import replace
from pathlib import Path

from kadai_sorter.models import PlanItem, PlanStatus


FIELDNAMES = ["source", "destination", "course", "assignment", "status", "reason"]


def _audit_row(item: PlanItem) -> dict[str, str]:
    return {
        "source": str(item.source),
        "destination": str(item.destination) if item.destination is not None else "",
        "course": item.course or "",
        "assignment": item.assignment or "",
        "status": item.status.value,
        "reason": item.reason,
    }


def execute_plan(plan: list[PlanItem], audit_path: Path) -> list[PlanItem]:
    results: list[PlanItem] = []
    for item in plan:
        if item.status is not PlanStatus.READY or item.destination is None:
            results.append(item)
            continue

        try:
            item.destination.parent.mkdir(parents=True, exist_ok=True)
            if item.destination.exists():
                results.append(
                    replace(
                        item,
                        status=PlanStatus.CONFLICT,
                        reason="出力先が既に存在します",
                    )
                )
                continue

            shutil.copy2(item.source, item.destination)
            results.append(replace(item, status=PlanStatus.COPIED))
        except OSError as error:
            results.append(replace(item, status=PlanStatus.ERROR, reason=str(error)))

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(_audit_row(item) for item in results)
    return results
