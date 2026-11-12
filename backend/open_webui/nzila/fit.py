"""VRAM / context fit estimation (mirrors src/lib/utils/nzila/fit.ts)."""

from __future__ import annotations

import re
from typing import Any

DEFAULT_SLIDER_MAX = 131072
DEFAULT_SLIDER_MIN = 2048


def parse_parameter_billions(parameter_size: str | None) -> float:
    if not parameter_size:
        return 3.0
    match = re.search(r'([\d.]+)\s*([bmk])?', parameter_size.strip(), re.I)
    if not match:
        return 3.0
    value = float(match.group(1))
    suffix = (match.group(2) or 'b').lower()
    if suffix == 'm':
        return value / 1000.0
    if suffix == 'k':
        return value / 1_000_000.0
    return value


def kv_gb_for_context(ctx_tokens: int, param_b: float) -> float:
    """Rough KV cache footprint (GB) for q8-style KV at ctx_tokens."""
    if ctx_tokens <= 0:
        return 0.0
    gb_per_1k = max(0.004, param_b * 0.0016)
    return (ctx_tokens / 1024.0) * gb_per_1k


def weights_gb(model_size_bytes: int | float | None, param_b: float) -> float:
    if model_size_bytes and model_size_bytes > 0:
        return float(model_size_bytes) / (1024**3)
    return max(0.8, param_b * 0.55)


def gpu_vram_free_gb(gpu_stats: dict[str, Any] | None) -> float | None:
    if not gpu_stats:
        return None

    def _num(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    used = _num(gpu_stats.get('vram_used_gb')) or _num(gpu_stats.get('memory_used_gb'))
    total = _num(gpu_stats.get('vram_total_gb')) or _num(gpu_stats.get('memory_total_gb'))
    used_b = _num(gpu_stats.get('vram_used')) or _num(gpu_stats.get('memory_used'))
    total_b = _num(gpu_stats.get('vram_total')) or _num(gpu_stats.get('memory_total'))
    if used is None and used_b is not None:
        used = used_b / (1024**3)
    if total is None and total_b is not None:
        total = total_b / (1024**3)
    if used is not None and total is not None:
        return max(0.0, total - used)
    free = _num(gpu_stats.get('vram_free_gb')) or _num(gpu_stats.get('memory_free_gb'))
    return free


def ctx_for_budget_gb(budget_gb: float, param_b: float, model_weights_gb: float) -> int:
    k = max(1e-9, (param_b * 0.0016) / 1024.0)
    remaining = budget_gb - model_weights_gb
    if remaining <= 0:
        return DEFAULT_SLIDER_MIN
    ctx = int(remaining / k * 1024)
    ctx = max(DEFAULT_SLIDER_MIN, min(DEFAULT_SLIDER_MAX, ctx))
    return (ctx // 1024) * 1024


def compute_fit_limits(
    *,
    model_size_bytes: int | float | None = None,
    parameter_size: str | None = None,
    gpu_stats: dict[str, Any] | None = None,
    override: dict[str, Any] | None = None,
) -> dict[str, int | bool]:
    override = override or {}
    param_b = parse_parameter_billions(parameter_size)
    w_gb = weights_gb(model_size_bytes, param_b)
    free_gb = gpu_vram_free_gb(gpu_stats)

    if free_gb is not None:
        safe_max = ctx_for_budget_gb(free_gb * 0.82 - w_gb, param_b, w_gb)
        tight_max = ctx_for_budget_gb(free_gb * 0.98 - w_gb, param_b, w_gb)
        hard_max = min(DEFAULT_SLIDER_MAX, max(tight_max, safe_max * 2, 32768))
    else:
        safe_max = min(65536, max(8192, int(param_b * 8192)))
        tight_max = min(DEFAULT_SLIDER_MAX, max(safe_max, safe_max + 16384))
        hard_max = min(DEFAULT_SLIDER_MAX, max(tight_max, tight_max + 32768))

    if isinstance(override.get('safe_max'), (int, float)) and override['safe_max'] > 0:
        safe_max = int(override['safe_max'])
    if isinstance(override.get('tight_max'), (int, float)) and override['tight_max'] > 0:
        tight_max = int(override['tight_max'])
    if isinstance(override.get('hard_max'), (int, float)) and override['hard_max'] > 0:
        hard_max = int(override['hard_max'])
    safe_max = max(DEFAULT_SLIDER_MIN, safe_max)
    tight_max = max(safe_max, tight_max)
    hard_max = max(tight_max, hard_max)

    return {
        'safe_max': safe_max,
        'tight_max': tight_max,
        'hard_max': hard_max,
        'fixed': bool(override.get('fixed', False)),
        'bonsai': bool(override.get('bonsai', False)),
    }


def fit_zone(ctx: int, limits: dict[str, int]) -> str:
    if ctx <= limits['safe_max']:
        return 'safe'
    if ctx <= limits['tight_max']:
        return 'tight'
    return 'over'
