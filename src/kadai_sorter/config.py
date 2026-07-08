from pathlib import Path
import tomllib

from kadai_sorter.models import AppConfig, CourseRule


class ConfigError(ValueError):
    """設定ファイルを読み込めない、または内容が無効です。"""


def is_safe_path_component(value: str) -> bool:
    return (
        value not in {".", ".."}
        and not Path(value).is_absolute()
        and "/" not in value
        and "\\" not in value
    )


def _nonblank_strings(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list) or not value:
        return None

    strings: list[str] = []
    for item in value:
        if not isinstance(item, str):
            return None
        stripped = item.strip()
        if not stripped:
            return None
        strings.append(stripped)
    return tuple(strings)


def load_config(path: Path) -> AppConfig:
    try:
        content = path.read_text(encoding="utf-8")
        data = tomllib.loads(content)
    except UnicodeDecodeError as error:
        raise ConfigError(f"設定ファイルをUTF-8として読み込めません: {path}") from error
    except OSError as error:
        raise ConfigError(f"設定ファイルを読み込めません: {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"設定ファイルのTOML形式が不正です: {path}") from error

    student_id = data.get("student_id")
    if not isinstance(student_id, str) or not student_id.strip():
        raise ConfigError("student_id に空でない文字列を指定してください")
    student_id = student_id.strip()
    if not is_safe_path_component(student_id):
        raise ConfigError("student_id に安全なファイル名要素を指定してください")

    raw_courses = data.get("courses")
    if not isinstance(raw_courses, list) or not raw_courses:
        raise ConfigError("courses を1件以上指定してください")

    courses: list[CourseRule] = []
    for raw_course in raw_courses:
        if not isinstance(raw_course, dict):
            raise ConfigError("course はテーブル形式で指定してください")

        name = raw_course.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError("course name に空でない文字列を指定してください")
        name = name.strip()
        if not is_safe_path_component(name):
            raise ConfigError("course name に安全なファイル名要素を指定してください")

        aliases = _nonblank_strings(raw_course.get("aliases"))
        if aliases is None:
            raise ConfigError(f"{name}: aliases に空でない文字列を1件以上指定してください")

        extensions = _nonblank_strings(raw_course.get("extensions"))
        if extensions is None:
            raise ConfigError(f"{name}: extensions に空でない文字列を1件以上指定してください")

        normalized_extensions = tuple(
            extension.lower() if extension.startswith(".") else f".{extension.lower()}"
            for extension in extensions
        )
        courses.append(CourseRule(name=name, aliases=aliases, extensions=normalized_extensions))

    return AppConfig(student_id=student_id, courses=tuple(courses))
