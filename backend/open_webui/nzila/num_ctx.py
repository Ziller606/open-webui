from __future__ import annotations

from open_webui.nzila.model_meta import parse_num_ctx_from_show, params_num_ctx


async def resolve_model_num_ctx(request, user, model_id: str, db_model=None) -> int | None:
    from_params = params_num_ctx(db_model)
    if from_params is not None:
        return from_params

    ollama_models = getattr(request.app.state, 'OLLAMA_MODELS', {}) or {}
    if model_id not in ollama_models:
        return None

    from open_webui.models.config import Config
    from open_webui.routers.ollama import get_ollama_connection, send_request
    from open_webui.utils.json_codec import JSONCodec
    from open_webui.utils.model_ids import strip_provider_model_prefix

    entry = ollama_models[model_id]
    url_indices = entry.get('urls') or [0]
    if not url_indices:
        return None
    idx = url_indices[0]
    url, api_config, key = await get_ollama_connection(idx)
    prefix_id = api_config.get('prefix_id')
    actual = strip_provider_model_prefix(model_id, prefix_id)
    payload = JSONCodec.dumps({'model': actual, 'name': actual})
    try:
        show = await send_request(
            f'{url}/api/show',
            payload=payload,
            key=key,
            user=user,
            api_config=api_config,
            request=request,
        )
    except Exception:
        return None
    if isinstance(show, dict):
        return parse_num_ctx_from_show(show)
    return None
