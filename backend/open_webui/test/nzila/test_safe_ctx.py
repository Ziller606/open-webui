from open_webui.nzila.safe_ctx import load_safe_ctx_file, normalize_safe_ctx_document


def test_normalize_canonical():
    raw = {
        'm1': {'safe_max': 131072, 'tight_max': 196608, 'hard_max': 262144, 'fixed': False},
        'm2': 32768,
        'm3': {'fixed_context': 8192},
    }
    out = normalize_safe_ctx_document(raw)
    assert out['m1']['safe_max'] == 131072
    assert out['m2']['safe_max'] == 32768
    assert out['m3']['fixed'] is True
    assert out['m3']['fixed_ctx'] == 8192


def test_normalize_models_wrapper(tmp_path):
    path = tmp_path / 'safe-ctx.json'
    path.write_text('{"models": {"a": 4096}}', encoding='utf-8')
    out = load_safe_ctx_file(path)
    assert out['a']['safe_max'] == 4096
