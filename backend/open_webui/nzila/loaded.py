from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from open_webui.env import NZILA_BONSAI_ROUTER_ENABLED, NZILA_BONSAI_ROUTER_URL

log = logging.getLogger(__name__)

_ROUTER_TIMEOUT = aiohttp.ClientTimeout(total=5)


def normalize_loaded_entry(
    raw: dict[str, Any],
    *,
    source: str,
    prefix_id: str | None = None,
) -> dict[str, Any] | None:
    model = raw.get('model') or raw.get('name') or raw.get('id')
    if not model:
        return None
    model_id = str(model)
    if prefix_id and source == 'ollama' and not model_id.startswith(f'{prefix_id}.'):
        model_id = f'{prefix_id}.{model_id}'
    vram = raw.get('size_vram') or raw.get('size_vram_bytes') or raw.get('vram_bytes') or raw.get('size')
    vram_int = None
    if vram is not None:
        try:
            vram_int = int(vram)
        except (TypeError, ValueError):
            vram_int = None
    return {
        'model': model_id,
        'source': source,
        'size_vram_bytes': vram_int,
        'loaded_at': raw.get('loaded_at'),
        'expires_at': raw.get('expires_at'),
    }


async def fetch_ollama_loaded(request, user) -> list[dict[str, Any]]:
    from open_webui.models.config import Config
    from open_webui.routers.ollama import merge_models_lists, resolve_api_config, send_get_request

    if not await Config.get('ollama.enable'):
        return []

    base_urls = await Config.get('ollama.base_urls', [])
    api_configs = await Config.get('ollama.api_configs', {})
    tasks = []
    for idx, url in enumerate(base_urls):
        api_config = resolve_api_config(api_configs, idx, url)
        if not api_config:
            tasks.append(send_get_request(request, f'{url}/api/ps', user=user))
        elif api_config.get('enable', True):
            tasks.append(
                send_get_request(request, f'{url}/api/ps', api_config.get('key'), user=user, config=api_config)
            )
        else:
            tasks.append(asyncio.ensure_future(asyncio.sleep(0, None)))

    responses = await asyncio.gather(*tasks)

    for idx, response in enumerate(responses):
        if not response:
            continue
        api_config = resolve_api_config(api_configs, idx, base_urls[idx])
        prefix_id = api_config.get('prefix_id')
        if prefix_id:
            for m in response.get('models', []):
                m['model'] = f'{prefix_id}.{m["model"]}'

    merged_raw = merge_models_lists(r.get('models', []) if r else None for r in responses)

    out: list[dict[str, Any]] = []
    for raw in merged_raw:
        entry = normalize_loaded_entry(raw, source='ollama')
        if entry:
            out.append(entry)
    return out


async def fetch_bonsai_loaded(router_base_url: str, *, prefix_id: str | None = None) -> list[dict[str, Any]]:
    from open_webui.nzila.bonsai_router import fetch_bonsai_loaded_models

    try:
        return await fetch_bonsai_loaded_models(router_base_url, prefix_id=prefix_id)
    except Exception as exc:
        log.debug('Bonsai GET /models failed: %s', exc)
        return []


async def list_loaded_models(request, user) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    try:
        models.extend(await fetch_ollama_loaded(request, user))
    except Exception as exc:
        log.debug('Ollama loaded list failed: %s', exc)
    if NZILA_BONSAI_ROUTER_ENABLED and NZILA_BONSAI_ROUTER_URL:
        from open_webui.nzila.bonsai_prefix import resolve_bonsai_prefix_id

        prefix_id = await resolve_bonsai_prefix_id()
        models.extend(await fetch_bonsai_loaded(NZILA_BONSAI_ROUTER_URL, prefix_id=prefix_id))
    return models
