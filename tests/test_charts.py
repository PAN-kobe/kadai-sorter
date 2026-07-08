from pathlib import Path

from kadai_sorter.charts import create_status_chart, summarize_audit


def test_summarize_audit_counts_statuses(tmp_path: Path) -> None:
    csv_path = tmp_path / "audit.csv"
    csv_path.write_text(
        "source,destination,course,assignment,status,reason\n"
        "a,b,経済学,課題1,copied,\n"
        "c,,経済学,,skipped,課題番号がありません\n",
        encoding="utf-8",
    )

    counts = summarize_audit(csv_path)

    assert counts["copied"] == 1
    assert counts["skipped"] == 1


def test_create_status_chart_writes_output_file(tmp_path: Path) -> None:
    csv_path = tmp_path / "audit.csv"
    output_path = tmp_path / "status.pdf"
    csv_path.write_text(
        "source,destination,course,assignment,status,reason\n"
        "a,b,経済学,課題1,copied,\n"
        "c,,経済学,,skipped,課題番号がありません\n",
        encoding="utf-8",
    )

    create_status_chart(csv_path, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0
