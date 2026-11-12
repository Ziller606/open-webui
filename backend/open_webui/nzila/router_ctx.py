from __future__ import annotations

import logging

import aiohttp

log = logging.getLogger(__name__)

_ROUTER_TIMEOUT = aiohttp.ClientTimeout(total=120)


async def apply_bonsai_context(router_base_url: str, model_id: str, ctx: int) -> dict:
    url = router_base_url.rstrip('/') + '/admin/ctx'
    payload = {'model': model_id, 'ctx': int(ctx)}
    async with aiohttp.ClientSession(timeout=_ROUTER_TIMEOUT, trust_env=True) as session:
        async with session.post(url, json=payload) as response:
            body = None
            try:
                body = await response.json(content_type=None)
            except Exception:
                body = {'status': response.status, 'detail': await response.text()}
            if response.status >= 400:
                detail = body if isinstance(body, dict) else {'detail': str(body)}
                raise RouterCtxError(response.status, detail)
            return body if isinstance(body, dict) else {'ok': True, 'raw': body}


class RouterCtxError(Exception):
    def __init__(self, status: int, detail: dict | str):
        self.status = status
        self.detail = detail
        super().__init__(str(detail))
