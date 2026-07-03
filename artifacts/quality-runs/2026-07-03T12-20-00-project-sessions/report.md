# Quality Run: v0.9.0 Project Sessions

Date: 2026-07-03

Scope: desktop project-scoped session storage, active-project session list
filtering, session store rebuild after project switch, and release packaging
checks.

## Commands Run

```bash
.venv/bin/python -m pytest tests/test_desktop.py -q
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/x_agentic_workflow
.venv/bin/xaw --version
.venv/bin/xaw desktop --help
.venv/bin/xaw smoke-openai-compatible --allow-skip
.venv/bin/python -m build
.venv/bin/python -m twine check dist/x_agentic_workflow-0.9.0*
```

## Results

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_desktop.py -q` | PASS, 13 tests |
| `.venv/bin/python -m pytest` | PASS, 28 tests |
| `.venv/bin/python -m ruff check src tests` | PASS |
| `.venv/bin/python -m mypy src/x_agentic_workflow` | PASS |
| `.venv/bin/xaw --version` | PASS, `0.9.0` |
| `.venv/bin/xaw desktop --help` | PASS |
| `.venv/bin/xaw smoke-openai-compatible --allow-skip` | PASS, skipped because `OPENAI_API_KEY` is absent |
| `.venv/bin/python -m build` | PASS, built `x_agentic_workflow-0.9.0.tar.gz` and `x_agentic_workflow-0.9.0-py3-none-any.whl` |
| `.venv/bin/python -m twine check dist/x_agentic_workflow-0.9.0*` | PASS |

## Session Isolation Evidence

The desktop tests create two temporary projects and write a session into the
first project. After switching to the second project, the first session is not
listed. After switching back, the first session is listed again and the second
project's session remains hidden.

The namespace helper is also tested for stability and path specificity: two
folders with the same basename under different parents map to different session
directories.

## Confidence

Medium-high for this scoped feature.

## Scope Risk

Low-to-moderate. Existing unscoped session files are not deleted or migrated,
but the desktop UI now reads and writes project-scoped session directories.
