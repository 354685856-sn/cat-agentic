# v0.15.0 Composer Draft Recovery Quality Run

Date: 2026-07-03

## Scope

- Persist bounded composer text by project and session.
- Restore after refresh/session return.
- Clear after successful send.
- Prevent rapid new-session id collisions.
- Keep attachment bodies out of persistent draft storage.

## Commands

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/x_agentic_workflow
.venv/bin/xaw --version
.venv/bin/xaw desktop --help
.venv/bin/xaw smoke-openai-compatible --allow-skip
.venv/bin/python -m build
.venv/bin/python -m twine check dist/x_agentic_workflow-0.15.0*
```

## Results

- Targeted desktop tests: passed, 21 tests.
- Full pytest suite: passed, 36 tests.
- Ruff: passed.
- Mypy: passed.
- Browser smoke:
  - draft restored after refresh.
  - immediate new session received a distinct id and empty draft.
  - reopening original session restored its draft.
  - successful intercepted send cleared draft across refresh.
- `.venv/bin/xaw --version`: `0.15.0`.
- `.venv/bin/xaw desktop --help`: passed.
- `.venv/bin/xaw smoke-openai-compatible --allow-skip`: skipped safely because
  `OPENAI_API_KEY` is not set.
- Build: passed, generated `x_agentic_workflow-0.15.0.tar.gz` and
  `x_agentic_workflow-0.15.0-py3-none-any.whl`.
- Twine check: passed for both v0.15.0 artifacts.

## Evidence Notes

- Draft key includes encoded workdir and session id.
- Draft content is capped at 64 KiB.
- localStorage errors are isolated from normal composer behavior.
- Attachment arrays and file bodies are never serialized into draft storage.

## Confidence

Medium-high.

## Scope Risk

Low-to-moderate. Change is limited to browser-side text drafts and session-id
generation precision.
