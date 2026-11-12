"""Load and normalize per-model safe context limits from JSON.

Canonical file shape (``safe-ctx.json``)::

    {
      "<model-id>": {
        "safe_max": 131072,
        "tight_max": 196608,
        "hard_max": 262144,
        "fixed": false,
        "fixed_ctx": null
      }
    }

Accepted variants per model entry:

- Bare integer ``131072`` → ``safe_max``
- ``{"safe": N}`` / ``{"safe_max": N}`` / ``{"max": N}``
- ``{"tight": N}`` / ``{"tight_max": N}``
- ``{"hard": N}`` / ``{"hard_max": N}`` / ``{"slider_max": N}``
- ``{"fixed": true}`` or ``{"fixed_context": N}`` (implies read-only at ``fixed_ctx`` or ``safe_max``)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from open_webui.utils.json_codec import JSONCodec

log = logging.getLogger(__name__)

SCHEMA_DOC = {
    'description': 'Per-model VRAM fit limits for the context slider (tokens).',
    'canonical_entry': {
        'safe_max': 'int — fully fits on GPU (green zone end)',
        'tight_max': 'int — tight / partial CPU offload (amber zone end)',
        'hard_max': 'int — slider maximum / red zone end (defaults to 1.5× tight_max or 2× safe_max)',
        'fixed': 'bool — backend ignores num_ctx when true',
        'fixed_ctx': 'int|null — displayed context when fixed (defaults to safe_max)',
    },
    'accepted_variants': [
        'integer safe_max shorthand',
        'safe / safe_max / max keys',
        'tight / tight_max keys',
        'hard / hard_max / slider_max keys',
        'fixed_context as integer sets fixed=true',
    ],
}


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _normalize_entry(raw: Any) -> dict[str, Any] | None:
    if raw is None:
        return None

    if isinstance(raw, (int, float, str)):
        safe = _as_int(raw)
        if safe is None or safe <= 0:
            return None
        tight = max(safe, int(safe * 1.25))
        hard = max(tight, int(safe * 2))
        return {
            'safe_max': safe,
            'tight_max': tight,
            'hard_max': hard,
            'fixed': False,
            'fixed_ctx': None,
        }

    if not isinstance(raw, dict):
        return None

    safe = _as_int(
        raw.get('safe_max', raw.get('safe', raw.get('max', raw.get('safe_context'))))
    )
    tight = _as_int(raw.get('tight_max', raw.get('tight', raw.get('tight_context'))))
    hard = _as_int(
        raw.get('hard_max', raw.get('hard', raw.get('slider_max', raw.get('max_ctx'))))
    )

    fixed_ctx = _as_int(raw.get('fixed_ctx', raw.get('fixed_context', raw.get('context'))))
    fixed = bool(raw.get('fixed', raw.get('is_fixed', False)))
    if fixed_ctx is not None and not fixed:
        fixed = True

    if safe is None and fixed_ctx is not None:
        safe = fixed_ctx

    if safe is None or safe <= 0:
        return None

    if tight is None or tight < safe:
        tight = max(safe, int(safe * 1.25))
    if hard is None or hard < tight:
        hard = max(tight, int(tight * 1.5))

    if fixed and fixed_ctx is None:
        fixed_ctx = safe

    bonsai = bool(raw.get('bonsai', raw.get('router', False)))

    return {
        'safe_max': safe,
        'tight_max': tight,
        'hard_max': hard,
        'fixed': fixed,
        'fixed_ctx': fixed_ctx if fixed else None,
        'bonsai': bonsai,
    }


def normalize_safe_ctx_document(data: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict):
        return {}

    models: dict[str, dict[str, Any]] = {}
    for model_id, entry in data.items():
        if not isinstance(model_id, str):
            continue
        normalized = _normalize_entry(entry)
        if normalized:
            models[model_id] = normalized
    return models


def load_safe_ctx_file(path: str | Path) -> dict[str, dict[str, Any]]:
    file_path = Path(path)
    if not file_path.is_file():
        log.warning('NZILA safe context file not found: %s', file_path)
        return {}

    try:
        raw = JSONCodec.loads(file_path.read_text(encoding='utf-8'))
    except OSError as exc:
        log.warning('NZILA safe context file unreadable: %s (%s)', file_path, exc)
        return {}
    except JSONCodec.JSONDecodeError as exc:
        log.warning('NZILA safe context file invalid JSON: %s (%s)', file_path, exc)
        return {}

    if isinstance(raw, dict) and 'models' in raw and isinstance(raw['models'], dict):
        raw = raw['models']

    return normalize_safe_ctx_document(raw)
