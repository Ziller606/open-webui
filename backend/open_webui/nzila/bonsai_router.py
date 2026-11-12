from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp

from open_webui.env import NZILA_BONSAI_IDLE_SECONDS, NZILA_BONSAI_PRESET_PATH

log = logging.getLogger(__name__)

_LOAD_TIMEOUT = aiohttp.ClientTimeout(total=120)
_QUICK_TIMEOUT = aiohttp.ClientTimeout(total=8)

LOADED_STATES = frozenset({'loaded', 'sleeping'})
_LOADING_STATES = frozenset({'loading'})

_prev_bonsai_loaded: set[str] = set()
_bonsai_last_activity: dict[str, float] = {}
_idle_seconds_cache: tuple[float, int] | None = None


class BonsaiRouterError(Exception):
    def __init__(self, status: int, detail: dict | str):
        self.status = status
        self.detail = detail
        super().__init__(str(detail))


def touch_bonsai_model(model_id: str, when: float | None = None) -> None:
    _bonsai_last_activity[model_id] = when if when is not None else time.time()


def _status_value(entry: dict[str, Any]) -> str | None:
    status = entry.get('status')
    if isinstance(status, dict):
        return status.get('value')
    if isinstance(status, str):
        return status
    return None


def _model_id(entry: dict[str, Any]) -> str | None:
    mid = entry.get('id') or entry.get('model') or entry.get('name')
    return str(mid) if mid else None


def _vram_bytes(entry: dict[str, Any]) -> int | None:
    mem = entry.get('memory')
    if not isinstance(mem, dict):
        return None
    effective = mem.get('effective')
    if not isinstance(effective, dict):
        return None
    devices = effective.get('devices')
    if not isinstance(devices, list):
        return None
    total = 0
    for dev in devices:
        if not isinstance(dev, dict):
            continue
        for key in ('model', 'context', 'compute'):
            val = dev.get(key)
            if isinstance(val, (int, float)) and val > 0:
                total += int(val)
    return total if total > 0 else None


def _expires_at_iso(model_id: str, idle_seconds: int) -> str | None:
    last = _bonsai_last_activity.get(model_id)
    if last is None:
        return None
    expiry = datetime.fromtimestamp(last + idle_seconds, tz=timezone.utc)
    return expiry.isoformat().replace('+00:00', 'Z')


async def _fetch_json(url: str, *, method: str = 'GET', json_body: dict | None = None, timeout=_QUICK_TIMEOUT):
    async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
        async with session.request(method, url, json=json_body) as response:
            body: Any = None
            try:
                body = await response.json(content_type=None)
            except Exception:
                body = {'detail': await response.text()}
            if response.status >= 400:
                detail = body if isinstance(body, dict) else {'detail': str(body)}
                raise BonsaiRouterError(response.status, detail)
            return body if isinstance(body, dict) else {'ok': True, 'raw': body}


async def resolve_router_idle_seconds(router_base_url: str) -> int:
    global _idle_seconds_cache
    now = time.time()
    if _idle_seconds_cache and now - _idle_seconds_cache[0] < 60:
        return _idle_seconds_cache[1]

    idle = NZILA_BONSAI_IDLE_SECONDS
    url = router_base_url.rstrip('/') + '/props'
    try:
        props = await _fetch_json(url)
        for key in (
            'sleep_idle_seconds',
            'sleep-idle-seconds',
            'sleep_idle',
            'idle_seconds',
        ):
            val = props.get(key)
            if isinstance(val, (int, float)) and val > 0:
                idle = int(val)
                break
        default = props.get('default_generation_settings')
        if isinstance(default, dict):
            for key in ('sleep_idle_seconds', 'sleep-idle-seconds'):
                val = default.get(key)
                if isinstance(val, (int, float)) and val > 0:
                    idle = int(val)
                    break
    except Exception as exc:
        log.debug('Could not read router /props for idle seconds: %s', exc)

    _idle_seconds_cache = (now, idle)
    return idle


async def fetch_router_models_raw(router_base_url: str) -> list[dict[str, Any]]:
    url = router_base_url.rstrip('/') + '/models'
    payload = await _fetch_json(url)
    data = payload.get('data')
    if isinstance(data, list):
        return [m for m in data if isinstance(m, dict)]
    return []


async def fetch_bonsai_loaded_models(router_base_url: str) -> list[dict[str, Any]]:
    global _prev_bonsai_loaded
    idle_seconds = await resolve_router_idle_seconds(router_base_url)
    raw = await fetch_router_models_raw(router_base_url)
    loaded: list[dict[str, Any]] = []
    current_ids: set[str] = set()

    for entry in raw:
        mid = _model_id(entry)
        if not mid:
            continue
        state = _status_value(entry)
        if state not in LOADED_STATES and state not in _LOADING_STATES:
            continue
        current_ids.add(mid)
        if mid not in _prev_bonsai_loaded:
            touch_bonsai_model(mid)
        loaded_at = None
        last = _bonsai_last_activity.get(mid)
        if last is not None:
            loaded_at = datetime.fromtimestamp(last, tz=timezone.utc).isoformat().replace('+00:00', 'Z')
        loaded.append(
            {
                'model': mid,
                'source': 'bonsai',
                'size_vram_bytes': _vram_bytes(entry),
                'loaded_at': loaded_at,
                'expires_at': _expires_at_iso(mid, idle_seconds),
                'status': state,
                'idle_seconds': idle_seconds,
            }
        )

    _prev_bonsai_loaded = current_ids
    return loaded


async def unload_router_model(router_base_url: str, model_id: str) -> dict[str, Any]:
    url = router_base_url.rstrip('/') + '/models/unload'
    try:
        result = await _fetch_json(url, method='POST', json_body={'model': model_id}, timeout=_LOAD_TIMEOUT)
    except BonsaiRouterError as exc:
        if exc.status == 400:
            detail = exc.detail if isinstance(exc.detail, dict) else {'detail': exc.detail}
            message = str(detail.get('error', detail.get('detail', detail)))
            if 'not running' in message.lower():
                return {'success': True, 'model': model_id, 'already_unloaded': True}
        raise
    _bonsai_last_activity.pop(model_id, None)
    _prev_bonsai_loaded.discard(model_id)
    return result


async def load_router_model(router_base_url: str, model_id: str) -> dict[str, Any]:
    url = router_base_url.rstrip('/') + '/models/load'
    result = await _fetch_json(url, method='POST', json_body={'model': model_id}, timeout=_LOAD_TIMEOUT)
    touch_bonsai_model(model_id)
    return result


async def apply_bonsai_context(router_base_url: str, model_id: str, ctx: int) -> dict[str, Any]:
    """Change ctx for a router-preset model: patch INI, unload, reload."""
    if not NZILA_BONSAI_PRESET_PATH:
        raise BonsaiRouterError(
            503,
            'Set NZILA_BONSAI_PRESET_PATH to the webui-models.ini mounted read-write for live ctx changes.',
        )

    from open_webui.nzila.bonsai_preset import update_preset_ctx_size

    section = update_preset_ctx_size(NZILA_BONSAI_PRESET_PATH, model_id, int(ctx))

    raw = await fetch_router_models_raw(router_base_url)
    state = None
    for entry in raw:
        if _model_id(entry) == model_id:
            state = _status_value(entry)
            break

    steps: list[dict[str, Any]] = [{'preset_section': section, 'ctx': int(ctx)}]
    if state in LOADED_STATES or state in _LOADING_STATES:
        steps.append(await unload_router_model(router_base_url, model_id))
    steps.append(await load_router_model(router_base_url, model_id))
    touch_bonsai_model(model_id)
    return {'model': model_id, 'ctx': int(ctx), 'steps': steps}
