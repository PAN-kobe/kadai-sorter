import re
import unicodedata
from pathlib import Path

from kadai_sorter.config import is_safe_path_component
from kadai_sorter.models import AppConfig, CourseRule, PlanItem, PlanStatus


ASSIGNMENT_PATTERN = re.compile(r"(?:課題|assignment|report)[-_ ]*(\d+)")


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _find_course(stem: str, config: AppConfig) -> CourseRule | None:
    matched_rule: CourseRule | None = None
    matched_length = -1
    for rule in config.courses:
        for alias in rule.aliases:
            normalized_alias = _normalize(alias)
            if normalized_alias in stem and len(normalized_alias) > matched_length:
                matched_rule = rule
                matched_length = len(normalized_alias)
    return matched_rule


def _find_assignment(stem: str) -> str | None:
    match = ASSIGNMENT_PATTERN.search(stem)
    if match is None:
        return None
    return f"課題{int(match.group(1))}"


def _contains_token(value: str, token: str) -> bool:
    start = value.find(token)
    while start >= 0:
        end = start + len(token)
        starts_at_boundary = start == 0 or not value[start - 1].isalnum()
        ends_at_boundary = end == len(value) or not value[end].isalnum()
        if starts_at_boundary and ends_at_boundary:
            return True
        start = value.find(token, start + 1)
    return False


def _normalize_suffix(suffix: str) -> str:
    return unicodedata.normalize("NFKC", suffix).lower()


def _skipped(
    source: Path,
    reason: str,
    course: str | None,
    assignment: str | None,
) -> PlanItem:
    return PlanItem(
        source=source,
        destination=None,
        course=course,
        assignment=assignment,
        status=PlanStatus.SKIPPED,
        reason=reason,
    )


def parse_file(path: Path, config: AppConfig) -> PlanItem:
    normalized_stem = _normalize(path.stem)
    rule = _find_course(normalized_stem, config)
    assignment = _find_assignment(normalized_stem)
    course = rule.name if rule is not None else None

    if rule is None:
        return _skipped(path, "科目を特定できません", course, assignment)

    if not is_safe_path_component(rule.name) or not is_safe_path_component(config.student_id):
        return _skipped(path, "安全な出力先を作成できません", course, assignment)

    suffix = _normalize_suffix(path.suffix)
    normalized_extensions = {_normalize_suffix(extension) for extension in rule.extensions}
    if suffix not in normalized_extensions:
        return _skipped(path, "対応していない拡張子です", course, assignment)

    if assignment is None:
        return _skipped(path, "課題番号を特定できません", course, assignment)

    if not _contains_token(normalized_stem, _normalize(config.student_id)):
        return _skipped(path, "学生番号が見つかりません", course, assignment)

    destination = (
        Path(rule.name) / assignment / f"{rule.name}_{assignment}_{config.student_id}{suffix}"
    )
    return PlanItem(
        source=path,
        destination=destination,
        course=course,
        assignment=assignment,
        status=PlanStatus.READY,
        reason="",
    )
