from __future__ import annotations

import re

_NUM_CTX_RE = re.compile(r'num_ctx\s+(\d+)', re.M)


def db_model_meta_dict(db_model) -> dict:
    if not db_model or db_model.meta is None:
        return {}
    meta = db_model.meta
    if hasattr(meta, 'model_dump'):
        return meta.model_dump()
    return meta if isinstance(meta, dict) else {}


def db_model_bonsai(db_model) -> bool:
    return bool(db_model_meta_dict(db_model).get('nzila_bonsai'))


def params_num_ctx(db_model) -> int | None:
    if not db_model or db_model.params is None:
        return None
    params = db_model.params
    raw = params.model_dump() if hasattr(params, 'model_dump') else (params if isinstance(params, dict) else {})
    value = raw.get('num_ctx')
    if isinstance(value, (int, float)) and value > 0:
        return int(value)
    return None


def parse_num_ctx_from_show(payload: dict) -> int | None:
    for field in ('modelfile', 'parameters'):
        text = payload.get(field)
        if isinstance(text, str):
            match = _NUM_CTX_RE.search(text)
            if match:
                return int(match.group(1))
    return None
