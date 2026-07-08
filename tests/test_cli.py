from typer.testing import CliRunner

from kadai_sorter.cli import app


def test_cli_help_lists_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.stdout
    assert "organize" in result.stdout
    assert "report" in result.stdout
