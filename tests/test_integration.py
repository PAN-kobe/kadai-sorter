from pathlib import Path

from typer.testing import CliRunner

from kadai_sorter.cli import app


def write_test_config(tmp_path: Path) -> Path:
    config = tmp_path / "rules.toml"
    config.write_text(
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        'name = "プログラミング"\n'
        'aliases = ["programming", "プログラミング"]\n'
        'extensions = [".pdf", ".py"]\n',
        encoding="utf-8",
    )
    return config


def test_organize_command_copies_and_reports(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    (source / "programming_assignment3_262e140e.pdf").write_bytes(b"pdf")
    (source / "programming_assignment3.pdf").write_bytes(b"missing id")
    config = write_test_config(tmp_path)

    result = CliRunner().invoke(
        app,
        ["organize", str(source), str(output), "--config", str(config)],
    )

    assert result.exit_code == 0
    assert "コピー: 1" in result.stdout
    assert "スキップ: 1" in result.stdout
    assert (output / "プログラミング/課題3/プログラミング_課題3_262e140e.pdf").exists()
    assert (output / "kadai-sort-audit.csv").exists()


def test_scan_command_does_not_create_output(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    (source / "programming_assignment3_262e140e.pdf").write_bytes(b"pdf")
    config = write_test_config(tmp_path)

    result = CliRunner().invoke(app, ["scan", str(source), str(output), "--config", str(config)])

    assert result.exit_code == 0
    assert "ready" in result.stdout
    assert not output.exists()


def test_report_command_creates_chart(tmp_path: Path) -> None:
    audit = tmp_path / "audit.csv"
    chart = tmp_path / "status.pdf"
    audit.write_text(
        "source,destination,course,assignment,status,reason\na,b,プログラミング,課題1,copied,\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["report", str(audit), str(chart)])

    assert result.exit_code == 0
    assert "グラフ" in result.stdout
    assert chart.exists()


def test_benchmark_command_writes_outputs(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["benchmark", "--output", str(tmp_path)])

    assert result.exit_code == 0
    assert "ベンチマーク" in result.stdout
    assert (tmp_path / "benchmark.csv").exists()
    assert (tmp_path / "benchmark.pdf").exists()
