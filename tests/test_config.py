from dataclasses import FrozenInstanceError
from pathlib import Path
from tomllib import TOMLDecodeError

import pytest

from kadai_sorter.config import ConfigError, load_config
from kadai_sorter.models import PlanStatus


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "rules.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_config_reads_student_and_course(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        'name = "プログラミング"\n'
        'aliases = ["programming", "プログラミング"]\n'
        'extensions = [".pdf", ".py"]\n',
    )

    config = load_config(path)

    assert config.student_id == "262e140e"
    assert len(config.courses) == 1
    assert config.courses[0].name == "プログラミング"
    assert config.courses[0].aliases == ("programming", "プログラミング")
    assert config.courses[0].extensions == (".pdf", ".py")


def test_loaded_config_is_immutable(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        'name = "経済学"\n'
        'aliases = ["economics"]\n'
        'extensions = [".pdf"]\n',
    )

    config = load_config(path)

    with pytest.raises(FrozenInstanceError):
        config.student_id = "different"  # type: ignore[misc]


def test_plan_status_values_match_the_data_contract() -> None:
    assert [status.value for status in PlanStatus] == [
        "ready",
        "skipped",
        "conflict",
        "copied",
        "error",
    ]


@pytest.mark.parametrize("student_line", ["", 'student_id = ""\n', 'student_id = "   "\n'])
def test_load_config_rejects_missing_or_blank_student_id(tmp_path: Path, student_line: str) -> None:
    path = write_config(
        tmp_path,
        student_line
        + "[[courses]]\n"
        + 'name = "経済学"\n'
        + 'aliases = ["economics"]\n'
        + 'extensions = [".pdf"]\n',
    )

    with pytest.raises(ConfigError, match="student_id"):
        load_config(path)


@pytest.mark.parametrize("courses_line", ["", "courses = []\n"])
def test_load_config_rejects_no_courses(tmp_path: Path, courses_line: str) -> None:
    path = write_config(tmp_path, 'student_id = "262e140e"\n' + courses_line)

    with pytest.raises(ConfigError, match="courses"):
        load_config(path)


@pytest.mark.parametrize("name_line", ["", 'name = ""\n', 'name = "   "\n', "name = 42\n"])
def test_load_config_rejects_invalid_course_name(tmp_path: Path, name_line: str) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        + "[[courses]]\n"
        + name_line
        + 'aliases = ["economics"]\n'
        + 'extensions = [".pdf"]\n',
    )

    with pytest.raises(ConfigError, match="name"):
        load_config(path)


def test_load_config_rejects_non_mapping_course(tmp_path: Path) -> None:
    path = write_config(tmp_path, 'student_id = "262e140e"\ncourses = ["経済学"]\n')

    with pytest.raises(ConfigError, match="course"):
        load_config(path)


@pytest.mark.parametrize(
    "aliases",
    ["[]", '[""]', '["   "]', '["economics", 42]'],
)
def test_load_config_rejects_invalid_aliases(tmp_path: Path, aliases: str) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        'name = "経済学"\n'
        f"aliases = {aliases}\n"
        'extensions = [".pdf"]\n',
    )

    with pytest.raises(ConfigError, match="aliases"):
        load_config(path)


@pytest.mark.parametrize(
    "extensions",
    ["[]", '[""]', '["   "]', '["pdf", 42]'],
)
def test_load_config_rejects_invalid_extensions(tmp_path: Path, extensions: str) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        'name = "経済学"\n'
        'aliases = ["economics"]\n'
        f"extensions = {extensions}\n",
    )

    with pytest.raises(ConfigError, match="extensions"):
        load_config(path)


def test_load_config_normalizes_extensions(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        'name = "経済学"\n'
        'aliases = ["economics"]\n'
        'extensions = ["PDF", ".DoCx"]\n',
    )

    config = load_config(path)

    assert config.courses[0].extensions == (".pdf", ".docx")


def test_load_config_trims_course_name(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        'name = "  経済学  "\n'
        'aliases = ["economics"]\n'
        'extensions = [".pdf"]\n',
    )

    config = load_config(path)

    assert config.courses[0].name == "経済学"


def test_load_config_trims_aliases(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        'name = "経済学"\n'
        'aliases = ["  economics  ", " 経済学 "]\n'
        'extensions = [".pdf"]\n',
    )

    config = load_config(path)

    assert config.courses[0].aliases == ("economics", "経済学")


def test_load_config_trims_and_normalizes_extensions(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        'name = "経済学"\n'
        'aliases = ["economics"]\n'
        'extensions = [" pdf ", " .DoCx "]\n',
    )

    config = load_config(path)

    assert config.courses[0].extensions == (".pdf", ".docx")


@pytest.mark.parametrize("student_id", ["/absolute", ".", "..", "path/id", r"path\id"])
def test_load_config_rejects_unsafe_student_id(tmp_path: Path, student_id: str) -> None:
    path = write_config(
        tmp_path,
        f"student_id = {student_id!r}\n"
        "[[courses]]\n"
        'name = "経済学"\n'
        'aliases = ["economics"]\n'
        'extensions = [".pdf"]\n',
    )

    with pytest.raises(ConfigError, match="student_id.*安全"):
        load_config(path)


@pytest.mark.parametrize("name", ["/absolute", ".", "..", "path/name", r"path\name"])
def test_load_config_rejects_unsafe_course_name(tmp_path: Path, name: str) -> None:
    path = write_config(
        tmp_path,
        'student_id = "262e140e"\n'
        "[[courses]]\n"
        f"name = {name!r}\n"
        'aliases = ["economics"]\n'
        'extensions = [".pdf"]\n',
    )

    with pytest.raises(ConfigError, match="course name.*安全"):
        load_config(path)


def test_load_config_wraps_malformed_toml(tmp_path: Path) -> None:
    path = write_config(tmp_path, 'student_id = "262e140e"\ninvalid = [\n')

    with pytest.raises(ConfigError, match="TOML") as error:
        load_config(path)

    assert isinstance(error.value.__cause__, TOMLDecodeError)


def test_load_config_wraps_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "rules.toml"
    path.write_bytes(b"\xff")

    with pytest.raises(ConfigError, match="UTF-8") as error:
        load_config(path)

    assert isinstance(error.value.__cause__, UnicodeDecodeError)


def test_load_config_wraps_file_errors(tmp_path: Path) -> None:
    path = tmp_path / "missing.toml"

    with pytest.raises(ConfigError, match="読み込") as error:
        load_config(path)

    assert isinstance(error.value.__cause__, OSError)
