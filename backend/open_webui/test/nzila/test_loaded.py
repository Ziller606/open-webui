from conftest import load_module

loaded = load_module('open_webui.nzila.loaded', 'nzila/loaded.py')


def test_normalize_ollama_entry():
    entry = loaded.normalize_loaded_entry(
        {'model': 'gemma:2b', 'size_vram': 1_000_000, 'expires_at': '2026-01-01T00:00:00Z'},
        source='ollama',
    )
    assert entry['model'] == 'gemma:2b'
    assert entry['size_vram_bytes'] == 1_000_000
    assert entry['source'] == 'ollama'


def test_normalize_with_prefix():
    entry = loaded.normalize_loaded_entry({'model': 'm1', 'size_vram': 10}, source='ollama', prefix_id='pfx')
    assert entry['model'] == 'pfx.m1'


def test_bonsai_loaded_skips_sleeping():
    import asyncio
    from unittest.mock import AsyncMock

    bonsai = load_module('open_webui.nzila.bonsai_router', 'nzila/bonsai_router.py')
    bonsai.fetch_router_models_raw = AsyncMock(
        return_value=[
            {'id': 'a', 'status': {'value': 'sleeping'}},
            {'id': 'b', 'status': {'value': 'loaded'}, 'memory': {'effective': {'devices': [{'model': 1_000_000}]}}},
        ]
    )
    bonsai.resolve_router_idle_seconds = AsyncMock(return_value=300)

    rows = asyncio.run(bonsai.fetch_bonsai_loaded_models('http://127.0.0.1:8096', prefix_id='bonsai'))
    assert len(rows) == 1
    assert rows[0]['model'] == 'bonsai.b'
