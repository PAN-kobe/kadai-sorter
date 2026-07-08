# Kadai Sorter Design

## Purpose

Kadai Sorter is a Python command-line application that helps a student safely
organize coursework files. It scans an input directory, validates filenames,
classifies files by course and assignment, proposes normalized destination
paths, and copies approved files into an organized output directory.

The software is an independent utility rather than a description of the course
assignment. Its primary user is a university student who manages assignments
from multiple courses and wants to reduce naming mistakes and filing time.

## Success Criteria

- A user can preview every proposed file operation before any file is copied.
- Supported files are classified and renamed consistently from configurable
  course rules.
- Missing student IDs, unsupported extensions, duplicate destinations, and
  unrecognized filenames are reported without changing the source files.
- The tool writes a CSV audit report and a Matplotlib summary chart.
- The package is installable with `uv`, documented in Japanese, tested with
  `pytest`, type-checked, and verified by GitHub Actions.
- The accompanying Japanese LaTeX report is no more than two pages and includes
  the student's name, student ID, repository URL, verification results, a
  vector-format chart, and an AI-use disclosure.

## User Experience

The package exposes the `kadai-sort` command.

1. `kadai-sort scan SOURCE --config rules.toml` reads files recursively and
   prints a table of recognized files, warnings, and proposed destinations.
2. `kadai-sort organize SOURCE OUTPUT --config rules.toml` repeats validation
   and copies only valid, conflict-free files. Source files are never modified.
3. `kadai-sort report OUTPUT` reads the audit CSV and creates a summary PNG for
   normal use plus a PDF chart for the LaTeX report.

`organize` is safe by default:

- It copies rather than moves.
- It never overwrites an existing destination.
- It rejects source and output directories that resolve to the same location.
- It prints a final count of copied, skipped, warning, and error records.

## Configuration And Naming

Configuration uses TOML so Python 3.12 can read it with `tomllib`. Each course
entry defines:

- A canonical course name.
- A list of filename aliases.
- Allowed extensions.
- A destination template.

The initial normalized filename is:

`{course}_{assignment}_{student_id}{extension}`

The parser accepts Japanese, Chinese, and ASCII course aliases. It extracts an
assignment token such as `課題3`, `assignment-3`, or `report_03`, and recognizes
the configured student ID `262e140e`. Files that cannot be classified remain
untouched and appear in the audit report with a reason.

## Architecture

The application is divided into small modules:

- `models.py`: immutable records and status enums shared by the package.
- `config.py`: TOML loading and validation.
- `parser.py`: filename tokenization, course matching, assignment extraction,
  and normalized filename generation.
- `planner.py`: recursive scanning, validation, collision detection, and
  creation of a list of proposed operations.
- `executor.py`: safe copy operations and CSV audit writing.
- `charts.py`: aggregation and Matplotlib chart generation.
- `cli.py`: Typer commands and Rich terminal presentation.

The parser and planner contain no terminal or filesystem mutation logic. The
executor receives an already validated plan, which keeps destructive concerns
isolated and makes behavior straightforward to test.

## Data Flow

1. Load and validate `rules.toml`.
2. Discover regular files under the source directory.
3. Parse each filename into course, assignment, student ID, and extension.
4. Produce a proposed destination or a structured skip/error reason.
5. Detect duplicate destinations across both the plan and existing output.
6. Display the plan.
7. For `organize`, copy valid entries and write `kadai-sort-audit.csv`.
8. Aggregate the audit CSV and generate status/course charts.

## Error Handling

- Invalid TOML or missing required fields returns a concise configuration error.
- Missing source directories and unreadable files return non-zero exit codes.
- Unsupported files and unrecognized names are skipped, not treated as fatal.
- Copy failures are recorded per file, and remaining independent files continue.
- Existing destination files are reported as conflicts and are never replaced.
- Unexpected exceptions are not hidden; the CLI presents a short message while
  tests retain the original exception context.

## Dependencies And Tooling

- Python 3.12 or newer.
- `typer` for the command interface.
- `rich` for readable preview and result tables.
- `matplotlib` for charts.
- `pytest` for unit and integration tests.
- `ruff` for linting and formatting checks.
- `mypy` for static type checking.
- `uv` for dependency and environment management.

Project metadata, command entry points, dependency groups, and tool settings are
defined in `pyproject.toml`. The project uses the MIT license.

## Testing Strategy

Unit tests cover:

- Valid and invalid configuration.
- Alias and assignment matching.
- Student ID and extension validation.
- Unicode filenames.
- Destination generation.
- Duplicate detection.
- Existing destination protection.
- CSV aggregation.

Integration tests create temporary source/output directories and verify that:

- `scan` changes no files.
- `organize` copies valid files with expected names.
- Invalid files remain untouched.
- Re-running never overwrites output.
- The CSV audit and chart are generated.

GitHub Actions runs `ruff check`, `mypy`, and `pytest` on Python 3.12. The README
shows the CI badge and includes purpose, installation, user usage, examples,
developer setup, test commands, and chart output without becoming a long report.

## Verification And Report

A reproducible benchmark fixture contains at least 100 synthetic coursework
filenames split among valid, invalid, unsupported, and duplicate cases. A
benchmark command records:

- Number of files processed.
- Classification accuracy against fixture labels.
- Number of unsafe conflicts correctly blocked.
- Total processing time.

The LaTeX report uses these measured results rather than invented values. A
Matplotlib PDF chart compares processing time for increasing file counts and is
embedded as vector data. The report explains the software purpose,
implementation choices, verification outcome, and AI use. The repository URL is
inserted only after the remote repository exists.

## Repository And Delivery

The repository is public unless the user explicitly chooses private access.
Commits are divided by meaningful milestones: project setup, parsing, planning,
safe execution, reporting, documentation, and final report. No API keys,
environment files, personal documents, or real coursework submissions are
committed.

Final deliverables are:

- A GitHub repository URL submitted through the course form.
- A Japanese LaTeX-generated PDF of no more than two pages.

