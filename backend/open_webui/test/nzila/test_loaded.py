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
