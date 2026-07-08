from pathlib import Path

import pytest

from kadai_sorter.models import AppConfig, CourseRule, PlanStatus
from kadai_sorter.parser import parse_file


@pytest.fixture
def config() -> AppConfig:
    return AppConfig(
        student_id="262E140E",
        courses=(
            CourseRule(
                name="プログラミング",
                aliases=("プログラミング", "Programming"),
                extensions=(".pdf", ".py"),
            ),
            CourseRule(
                name="経済学",
                aliases=("経済学", "Economics"),
                extensions=(".pdf",),
            ),
        ),
    )


def test_parse_japanese_ready_file_builds_relative_destination(config: AppConfig) -> None:
    source = Path("/incoming/プログラミング_課題3_262E140E.pdf")

    item = parse_file(source, config)

    assert item.source == source
    assert item.destination == Path("プログラミング/課題3/プログラミング_課題3_262E140E.pdf")
    assert not item.destination.is_absolute()
    assert item.course == "プログラミング"
    assert item.assignment == "課題3"
    assert item.status is PlanStatus.READY
    assert item.reason == ""


def test_parse_matches_english_alias_case_insensitively(config: AppConfig) -> None:
    item = parse_file(Path("PROGRAMMING_assignment-3_262e140e.py"), config)

    assert item.destination == Path("プログラミング/課題3/プログラミング_課題3_262E140E.py")
    assert item.course == "プログラミング"
    assert item.assignment == "課題3"
    assert item.status is PlanStatus.READY


def test_parse_normalizes_fullwidth_digits_and_uppercase_extension(config: AppConfig) -> None:
    item = parse_file(Path("経済学_課題３_２６２Ｅ１４０Ｅ.PDF"), config)

    assert item.destination == Path("経済学/課題3/経済学_課題3_262E140E.pdf")
    assert item.assignment == "課題3"
    assert item.status is PlanStatus.READY


@pytest.mark.parametrize(
    ("filename", "assignment"),
    [
        ("economics_assignment-3_262e140e.pdf", "課題3"),
        ("economics_assignment_03_262e140e.pdf", "課題3"),
        ("economics_assignment 3_262e140e.pdf", "課題3"),
        ("economics_assignment3_262e140e.pdf", "課題3"),
        ("economics_課題-3_262e140e.pdf", "課題3"),
        ("economics_課題_3_262e140e.pdf", "課題3"),
        ("economics_report03_262e140e.pdf", "課題3"),
        ("economics_report_03_262e140e.pdf", "課題3"),
        ("economics_report-3_262e140e.pdf", "課題3"),
        ("economics_report 3_262e140e.pdf", "課題3"),
    ],
)
def test_parse_extracts_assignment_forms(config: AppConfig, filename: str, assignment: str) -> None:
    item = parse_file(Path(filename), config)

    assert item.assignment == assignment
    assert item.status is PlanStatus.READY


def test_parse_skips_missing_student_id_and_preserves_metadata(config: AppConfig) -> None:
    item = parse_file(Path("economics_report03.pdf"), config)

    assert item.destination is None
    assert item.course == "経済学"
    assert item.assignment == "課題3"
    assert item.status is PlanStatus.SKIPPED
    assert "学生番号" in item.reason


def test_parse_skips_unsupported_extension_and_preserves_metadata(config: AppConfig) -> None:
    item = parse_file(Path("economics_report03_262e140e.txt"), config)

    assert item.destination is None
    assert item.course == "経済学"
    assert item.assignment == "課題3"
    assert item.status is PlanStatus.SKIPPED
    assert "拡張子" in item.reason


def test_parse_skips_unknown_course_but_preserves_assignment(config: AppConfig) -> None:
    item = parse_file(Path("history_assignment-03_262e140e.pdf"), config)

    assert item.destination is None
    assert item.course is None
    assert item.assignment == "課題3"
    assert item.status is PlanStatus.SKIPPED
    assert "科目" in item.reason


def test_parse_skips_missing_assignment_and_preserves_course(config: AppConfig) -> None:
    item = parse_file(Path("economics_262e140e.pdf"), config)

    assert item.destination is None
    assert item.course == "経済学"
    assert item.assignment is None
    assert item.status is PlanStatus.SKIPPED
    assert "課題番号" in item.reason


def test_parse_prefers_longest_overlapping_alias() -> None:
    config = AppConfig(
        student_id="s123",
        courses=(
            CourseRule(name="先の科目", aliases=("data",), extensions=(".pdf",)),
            CourseRule(name="後の科目", aliases=("database",), extensions=(".pdf",)),
        ),
    )

    item = parse_file(Path("database_assignment-1_s123.pdf"), config)

    assert item.course == "後の科目"
    assert item.destination == Path("後の科目/課題1/後の科目_課題1_s123.pdf")


def test_parse_uses_configuration_order_to_break_equal_alias_ties() -> None:
    config = AppConfig(
        student_id="s123",
        courses=(
            CourseRule(name="先の科目", aliases=("shared",), extensions=(".pdf",)),
            CourseRule(name="後の科目", aliases=("shared",), extensions=(".pdf",)),
        ),
    )

    item = parse_file(Path("shared_assignment-1_s123.pdf"), config)

    assert item.course == "先の科目"


def test_parse_requires_student_id_as_filename_token() -> None:
    config = AppConfig(
        student_id="s123",
        courses=(CourseRule(name="経済学", aliases=("economics",), extensions=(".pdf",)),),
    )

    item = parse_file(Path("economics_assignment-1_xs1234.pdf"), config)

    assert item.destination is None
    assert item.course == "経済学"
    assert item.assignment == "課題1"
    assert item.status is PlanStatus.SKIPPED
    assert "学生番号" in item.reason


def test_parse_normalizes_fullwidth_suffix_for_matching_and_output(config: AppConfig) -> None:
    source = Path("economics_assignment-3_262e140e.ＰＤＦ")
    assert source.suffix == ".ＰＤＦ"

    item = parse_file(source, config)

    assert item.destination == Path("経済学/課題3/経済学_課題3_262E140E.pdf")
    assert item.status is PlanStatus.READY


@pytest.mark.parametrize(
    ("student_id", "course_name"),
    [
        ("s123", "../escape"),
        ("../s123", "経済学"),
    ],
)
def test_parse_rejects_unsafe_destination_components(student_id: str, course_name: str) -> None:
    config = AppConfig(
        student_id=student_id,
        courses=(CourseRule(name=course_name, aliases=("economics",), extensions=(".pdf",)),),
    )

    item = parse_file(Path("economics_assignment-1_s123.pdf"), config)

    assert item.destination is None
    assert item.status is PlanStatus.SKIPPED
    assert "安全" in item.reason
