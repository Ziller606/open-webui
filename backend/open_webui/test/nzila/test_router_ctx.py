import json
from unittest.mock import AsyncMock, patch

import pytest

from conftest import load_module

load_module('open_webui.nzila.bonsai_preset', 'nzila/bonsai_preset.py')
bonsai = load_module('open_webui.nzila.bonsai_router', 'nzila/bonsai_router.py')
router_ctx = load_module('open_webui.nzila.router_ctx', 'nzila/router_ctx.py')
RouterCtxError = router_ctx.RouterCtxError
apply_bonsai_context = router_ctx.apply_bonsai_context


@pytest.mark.asyncio
async def test_apply_bonsai_context_requires_preset(tmp_path, monkeypatch):
    preset = tmp_path / 'models.ini'
    preset.write_text('[m]\nmodel=test\nctx-size=8192\n', encoding='utf-8')
    monkeypatch.setattr(bonsai, 'NZILA_BONSAI_PRESET_PATH', None)
    with pytest.raises(RouterCtxError) as exc:
        await apply_bonsai_context('http://127.0.0.1:8096', 'm', 32768)
    assert exc.value.status == 503


@pytest.mark.asyncio
async def test_apply_bonsai_context_reload(tmp_path, monkeypatch):
    preset = tmp_path / 'models.ini'
    preset.write_text('[m]\nmodel=test\nctx-size=8192\n', encoding='utf-8')
    monkeypatch.setattr(bonsai, 'NZILA_BONSAI_PRESET_PATH', str(preset))
    monkeypatch.setattr(
        bonsai,
        'fetch_router_models_raw',
        AsyncMock(return_value=[{'id': 'm', 'status': {'value': 'loaded'}}]),
    )
    monkeypatch.setattr(bonsai, 'unload_router_model', AsyncMock(return_value={'success': True}))
    monkeypatch.setattr(bonsai, 'load_router_model', AsyncMock(return_value={'success': True}))
    result = await apply_bonsai_context('http://127.0.0.1:8096', 'm', 32768)
    assert result['ctx'] == 32768
    bonsai.unload_router_model.assert_awaited_once()
    bonsai.load_router_model.assert_awaited_once()
