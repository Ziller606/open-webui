"""Normalize gpu-meter payloads to legacy GB field names."""

from __future__ import annotations

from typing import Any


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_gpu_stats(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    used_mib = _num(payload.get('memory_used_mib'))
    total_mib = _num(payload.get('memory_total_mib'))
    free_mib = _num(payload.get('memory_free_mib'))
    if used_mib is not None and out.get('vram_used_gb') is None and out.get('memory_used_gb') is None:
        out['vram_used_gb'] = used_mib / 1024.0
        out['memory_used_gb'] = out['vram_used_gb']
    if total_mib is not None and out.get('vram_total_gb') is None and out.get('memory_total_gb') is None:
        out['vram_total_gb'] = total_mib / 1024.0
        out['memory_total_gb'] = out['vram_total_gb']
    if free_mib is not None and out.get('vram_free_gb') is None and out.get('memory_free_gb') is None:
        out['vram_free_gb'] = free_mib / 1024.0
        out['memory_free_gb'] = out['vram_free_gb']
    if out.get('gpu_utilization') is None and out.get('utilization_gpu') is not None:
        out['gpu_utilization'] = out['utilization_gpu']
    return out
