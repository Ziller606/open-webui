from __future__ import annotations

import logging
from typing import Any

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from open_webui.env import (
    NZILA_BONSAI_ROUTER_ENABLED,
    NZILA_BONSAI_ROUTER_URL,
    NZILA_CONTEXT_SLIDER_ENABLED,
    NZILA_EXTENSIONS_ENABLED,
    NZILA_GPU_METER_ENABLED,
    NZILA_GPU_STATS_URL,
    NZILA_SAFE_CTX_PATH,
)
from open_webui.models.models import Models
from open_webui.nzila.fit import compute_fit_limits
from open_webui.nzila.loaded import list_loaded_models
from open_webui.nzila.router_ctx import RouterCtxError, apply_bonsai_context
from open_webui.nzila.bonsai_router import touch_bonsai_model
from open_webui.nzila.unload import UnloadError, unload_all_models, unload_model
from open_webui.nzila.safe_ctx import SCHEMA_DOC, load_safe_ctx_file
from open_webui.utils.auth import get_verified_user

log = logging.getLogger(__name__)

router = APIRouter()

_GPU_TIMEOUT = aiohttp.ClientTimeout(total=2.5)


def _require_extensions():
    if not NZILA_EXTENSIONS_ENABLED:
        raise HTTPException(status_code=404, detail='Not found')


async def _fetch_gpu_stats() -> dict[str, Any] | None:
    if not NZILA_GPU_METER_ENABLED or not NZILA_GPU_STATS_URL:
        return None
    try:
        async with aiohttp.ClientSession(timeout=_GPU_TIMEOUT, trust_env=True) as session:
            async with session.get(NZILA_GPU_STATS_URL) as response:
                if response.status >= 400:
                    return None
                payload = await response.json(content_type=None)
                return payload if isinstance(payload, dict) else None
    except Exception as exc:
        log.debug('NZILA gpu stats read failed: %s', exc)
        return None


def _resolve_safe_entry(model_id: str, models: dict[str, dict]) -> dict | None:
    if model_id in models:
        return models[model_id]
    tail = model_id.split(':')[-1] if ':' in model_id else model_id
    for key, entry in models.items():
        if key == tail or model_id.endswith(key):
            return entry
    return None


def _model_hints(model: dict | None) -> tuple[int | None, str | None, bool]:
    if not model:
        return None, None, False
    size = model.get('size')
    details = model.get('details') or {}
    param = details.get('parameter_size')
    meta = (model.get('info') or {}).get('meta') or {}
    bonsai = bool(meta.get('nzila_bonsai', False))
    return size, param, bonsai


@router.get('/safe-ctx/schema')
async def get_safe_ctx_schema(user=Depends(get_verified_user)):
    _require_extensions()
    return SCHEMA_DOC


@router.get('/safe-ctx')
async def get_safe_ctx(user=Depends(get_verified_user)):
    _require_extensions()
    models = load_safe_ctx_file(NZILA_SAFE_CTX_PATH) if NZILA_SAFE_CTX_PATH else {}
    return {'models': models, 'schema': SCHEMA_DOC}


@router.get('/gpu-stats')
async def get_gpu_stats(user=Depends(get_verified_user)):
    if not NZILA_GPU_METER_ENABLED or not NZILA_GPU_STATS_URL:
        raise HTTPException(status_code=404, detail='Not found')

    try:
        async with aiohttp.ClientSession(timeout=_GPU_TIMEOUT, trust_env=True) as session:
            async with session.get(NZILA_GPU_STATS_URL) as response:
                if response.status >= 400:
                    raise HTTPException(status_code=502, detail='GPU stats upstream error')
                payload = await response.json(content_type=None)
                if not isinstance(payload, dict):
                    raise HTTPException(status_code=502, detail='GPU stats upstream invalid payload')
                return JSONResponse(content=payload)
    except HTTPException:
        raise
    except aiohttp.ClientError as exc:
        log.debug('NZILA GPU stats upstream unavailable: %s', exc)
        raise HTTPException(status_code=503, detail='GPU stats upstream unavailable') from exc
    except Exception as exc:
        log.debug('NZILA GPU stats proxy failed: %s', exc)
        raise HTTPException(status_code=503, detail='GPU stats upstream unavailable') from exc


@router.get('/fit/{model_id}')
async def get_model_fit(model_id: str, request: Request, user=Depends(get_verified_user)):
    _require_extensions()
    safe_models = load_safe_ctx_file(NZILA_SAFE_CTX_PATH) if NZILA_SAFE_CTX_PATH else {}
    override = _resolve_safe_entry(model_id, safe_models) or {}

    ollama_models = getattr(request.app.state, 'OLLAMA_MODELS', {}) or {}
    ollama_model = ollama_models.get(model_id)
    size, param, meta_bonsai = _model_hints(ollama_model)

    db_model = await Models.get_model_by_id(model_id)
    if db_model and db_model.info:
        meta = (db_model.info or {}).get('meta') or {}
        meta_bonsai = meta_bonsai or bool(meta.get('nzila_bonsai', False))

    bonsai = bool(override.get('bonsai', False) or meta_bonsai)
    if NZILA_BONSAI_ROUTER_ENABLED and bonsai:
        override = {**override, 'bonsai': True, 'fixed': False}

    gpu_stats = await _fetch_gpu_stats()
    limits = compute_fit_limits(
        model_size_bytes=size,
        parameter_size=param,
        gpu_stats=gpu_stats,
        override=override,
    )
    limits['bonsai'] = bonsai and NZILA_BONSAI_ROUTER_ENABLED
    return limits


class CtxForm(BaseModel):
    ctx: int = Field(..., ge=512, le=2_000_000)


@router.post('/ctx/{model_id}')
async def set_model_context(
    model_id: str,
    form_data: CtxForm,
    user=Depends(get_verified_user),
):
    if not NZILA_BONSAI_ROUTER_ENABLED or not NZILA_BONSAI_ROUTER_URL:
        raise HTTPException(status_code=404, detail='Bonsai router not configured')

    try:
        result = await apply_bonsai_context(NZILA_BONSAI_ROUTER_URL, model_id, form_data.ctx)
        return {'model': model_id, 'ctx': form_data.ctx, 'router': result}
    except RouterCtxError as exc:
        raise HTTPException(status_code=exc.status if 400 <= exc.status < 600 else 502, detail=exc.detail) from exc
    except aiohttp.ClientError as exc:
        raise HTTPException(status_code=503, detail='Bonsai router unavailable') from exc


@router.get('/loaded')
async def get_loaded_models(request: Request, user=Depends(get_verified_user)):
    _require_extensions()
    models = await list_loaded_models(request, user)
    return {'models': models}


@router.post('/unload-all')
async def post_unload_all(request: Request, user=Depends(get_verified_user)):
    _require_extensions()
    try:
        return await unload_all_models(request, user)
    except UnloadError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc


@router.post('/activity/{model_id}')
async def post_bonsai_activity(model_id: str, user=Depends(get_verified_user)):
    """Record last inference time for Bonsai idle countdown (llama-server sleep-idle-seconds)."""
    _require_extensions()
    touch_bonsai_model(model_id)
    return {'model': model_id, 'ok': True}


@router.post('/unload/{model_id}')
async def post_unload_model(model_id: str, request: Request, user=Depends(get_verified_user)):
    _require_extensions()
    try:
        return await unload_model(request, user, model_id)
    except UnloadError as exc:
        status = 404 if exc.code == 'not_found' else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc


@router.get('/config')
async def get_nzila_config(user=Depends(get_verified_user)):
    _require_extensions()
    return {
        'gpu_meter': NZILA_GPU_METER_ENABLED,
        'safe_ctx_path': bool(NZILA_SAFE_CTX_PATH),
        'bonsai_router': NZILA_BONSAI_ROUTER_ENABLED,
        'bonsai_router_url': NZILA_BONSAI_ROUTER_URL if NZILA_BONSAI_ROUTER_ENABLED else None,
    }
