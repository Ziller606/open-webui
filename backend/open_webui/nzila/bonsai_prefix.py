from __future__ import annotations

from open_webui.env import NZILA_BONSAI_ROUTER_URL


def _root_url(url: str) -> str:
    return url.rstrip('/').removesuffix('/v1')


async def resolve_bonsai_prefix_id() -> str | None:
    """prefix_id for the OpenAI connection that points at the Bonsai router."""
    if not NZILA_BONSAI_ROUTER_URL:
        return None
    from open_webui.models.config import Config

    router_root = _root_url(NZILA_BONSAI_ROUTER_URL)
    config = await Config.get_many('openai.api_configs', 'openai.api_base_urls')
    base_urls = config.get('openai.api_base_urls') or []
    api_configs = config.get('openai.api_configs') or {}
    for idx, base_url in enumerate(base_urls):
        api_config = api_configs.get(str(idx), api_configs.get(base_url, {})) or {}
        if _root_url(base_url) != router_root:
            continue
        prefix = api_config.get('prefix_id')
        if prefix:
            return str(prefix)
    return None


def strip_bonsai_router_id(model_id: str, prefix_id: str | None) -> str:
    if prefix_id and model_id.startswith(f'{prefix_id}.'):
        return model_id[len(prefix_id) + 1 :]
    return model_id


def with_bonsai_prefix(router_id: str, prefix_id: str | None) -> str:
    if prefix_id and not router_id.startswith(f'{prefix_id}.'):
        return f'{prefix_id}.{router_id}'
    return router_id

