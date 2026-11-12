from __future__ import annotations

from open_webui.nzila.bonsai_router import BonsaiRouterError, unload_router_model

RouterAdminError = BonsaiRouterError


async def apply_bonsai_unload(router_base_url: str, model_id: str) -> dict:
    return await unload_router_model(router_base_url, model_id)
