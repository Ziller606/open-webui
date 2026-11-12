from __future__ import annotations

import logging
from typing import Any

import aiohttp

from open_webui.env import (
    AIOHTTP_CLIENT_SESSION_SSL,
    NZILA_BONSAI_ROUTER_ENABLED,
    NZILA_BONSAI_ROUTER_URL,
)
from open_webui.env import NZILA_SAFE_CTX_PATH
from open_webui.nzila.safe_ctx import load_safe_ctx_file
from open_webui.nzila.router_admin import RouterAdminError, apply_bonsai_unload

log = logging.getLogger(__name__)

_OLLAMA_TIMEOUT = aiohttp.ClientTimeout(total=30)


class UnloadError(Exception):
    def __init__(self, code: str, detail: str | None = None):
        self.code = code
        self.detail = detail or code
        super().__init__(self.detail)


def _resolve_safe_bonsai(model_id: str) -> bool:
    if not NZILA_SAFE_CTX_PATH:
        return False
    models = load_safe_ctx_file(NZILA_SAFE_CTX_PATH)
    if model_id in models and models[model_id].get('bonsai'):
        return True
    tail = model_id.split(':')[-1] if ':' in model_id else model_id
    for key, entry in models.items():
        if (key == tail or model_id.endswith(key)) and entry.get('bonsai'):
            return True
    return False


async def model_is_bonsai(model_id: str, request) -> bool:
    from open_webui.models.models import Models

    if _resolve_safe_bonsai(model_id):
        return True
    from open_webui.nzila.bonsai_prefix import resolve_bonsai_prefix_id
    from open_webui.nzila.model_meta import db_model_bonsai

    prefix_id = await resolve_bonsai_prefix_id()
    if prefix_id and model_id.startswith(f'{prefix_id}.'):
        return True
    db_model = await Models.get_model_by_id(model_id)
    if db_model_bonsai(db_model):
        return True
    ollama_models = getattr(request.app.state, 'OLLAMA_MODELS', {}) or {}
    meta = (ollama_models.get(model_id) or {}).get('info', {}) or {}
    if isinstance(meta, dict):
        inner = meta.get('meta') or {}
        if inner.get('nzila_bonsai'):
            return True
    return False


async def unload_ollama_model(request, user, model_id: str) -> dict[str, Any]:
    from open_webui.models.config import Config
    from open_webui.utils.headers import get_headers_and_cookies
    from open_webui.utils.json_codec import JSONCodec
    from open_webui.utils.model_ids import strip_provider_model_prefix
    from open_webui.routers.ollama import clear_models_cache, get_all_models

    if not await Config.get('ollama.enable'):
        raise UnloadError('ollama_disabled')

    await get_all_models(request, user=user)
    ollama_models = getattr(request.app.state, 'OLLAMA_MODELS', {}) or {}
    if model_id not in ollama_models:
        raise UnloadError('not_found', f'Model not found: {model_id}')

    ollama_base_urls = await Config.get('ollama.base_urls', [])
    ollama_api_configs = await Config.get('ollama.api_configs', {})
    url_indices = ollama_models[model_id].get('urls', [])
    errors: list[dict] = []
    for idx in url_indices:
        if idx >= len(ollama_base_urls):
            continue
        url = ollama_base_urls[idx]
        api_config = ollama_api_configs.get(str(idx), ollama_api_configs.get(url, {}))
        key = api_config.get('key', None)
        prefix_id = api_config.get('prefix_id', None)
        actual_model = strip_provider_model_prefix(model_id, prefix_id)
        payload = JSONCodec.dumps({'model': actual_model, 'keep_alive': 0, 'prompt': ''})
        try:
            async with aiohttp.ClientSession(timeout=_OLLAMA_TIMEOUT, trust_env=True) as session:
                headers, cookies = await get_headers_and_cookies(request, url, key, api_config, user=user)
                async with session.post(
                    f'{url}/api/generate',
                    data=payload,
                    headers=headers,
                    cookies=cookies,
                    ssl=AIOHTTP_CLIENT_SESSION_SSL,
                ) as response:
                    if not response.ok:
                        errors.append({'url_idx': idx, 'error': await response.text()})
        except Exception as exc:
            log.exception('Nzila unload failed on node %s: %s', idx, exc)
            errors.append({'url_idx': idx, 'error': str(exc)})

    await clear_models_cache(request)
    if errors:
        raise UnloadError('upstream_error', f'Failed on {len(errors)} node(s)')
    return {'model': model_id, 'source': 'ollama', 'status': 'ok'}


async def unload_model(request, user, model_id: str) -> dict[str, Any]:
    bonsai = NZILA_BONSAI_ROUTER_ENABLED and NZILA_BONSAI_ROUTER_URL and await model_is_bonsai(model_id, request)
    if bonsai:
        try:
            from open_webui.nzila.bonsai_prefix import resolve_bonsai_prefix_id, strip_bonsai_router_id

            prefix_id = await resolve_bonsai_prefix_id()
            router_id = strip_bonsai_router_id(model_id, prefix_id)
            result = await apply_bonsai_unload(NZILA_BONSAI_ROUTER_URL, router_id)
            return {'model': model_id, 'source': 'bonsai', 'status': 'ok', 'router': result}
        except RouterAdminError as exc:
            raise UnloadError('router_error', str(exc.detail)) from exc
    return await unload_ollama_model(request, user, model_id)


async def unload_all_models(request, user) -> dict[str, Any]:
    from open_webui.nzila.loaded import list_loaded_models

    loaded = await list_loaded_models(request, user)
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for entry in loaded:
        mid = entry['model']
        if mid in seen:
            continue
        seen.add(mid)
        try:
            results.append(await unload_model(request, user, mid))
        except UnloadError as exc:
            errors.append({'model': mid, 'error': exc.detail})
    return {'unloaded': results, 'errors': errors, 'status': 'ok' if not errors else 'partial'}
