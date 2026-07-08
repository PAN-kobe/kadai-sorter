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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.bar(labels, values, color=["#2f6f4e", "#d9a441", "#b54a4a", "#555555"])
    axis.set_title("Kadai Sorter results")
    axis.set_ylabel("Files")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
