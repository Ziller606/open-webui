from __future__ import annotations

import logging

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from open_webui.env import NZILA_CONTEXT_SLIDER_ENABLED, NZILA_GPU_METER_ENABLED, NZILA_GPU_STATS_URL
from open_webui.env import NZILA_SAFE_CTX_PATH
from open_webui.nzila.safe_ctx import SCHEMA_DOC, load_safe_ctx_file
from open_webui.utils.auth import get_verified_user

log = logging.getLogger(__name__)

router = APIRouter()

_GPU_TIMEOUT = aiohttp.ClientTimeout(total=2.5)


@router.get('/safe-ctx/schema')
async def get_safe_ctx_schema(user=Depends(get_verified_user)):
    if not NZILA_CONTEXT_SLIDER_ENABLED:
        raise HTTPException(status_code=404, detail='Not found')
    return SCHEMA_DOC


@router.get('/safe-ctx')
async def get_safe_ctx(user=Depends(get_verified_user)):
    if not NZILA_CONTEXT_SLIDER_ENABLED or not NZILA_SAFE_CTX_PATH:
        raise HTTPException(status_code=404, detail='Not found')

    models = load_safe_ctx_file(NZILA_SAFE_CTX_PATH)
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
