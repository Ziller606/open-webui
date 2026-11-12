from conftest import load_module


def test_resolve_safe_bonsai(tmp_path):
    safe = tmp_path / 'safe-ctx.json'
    safe.write_text('{"my-model": {"safe_max": 8192, "bonsai": true}}', encoding='utf-8')
    load_module('open_webui.nzila.safe_ctx', 'nzila/safe_ctx.py')
    load_module('open_webui.nzila.router_admin', 'nzila/router_admin.py')
    import open_webui.env as env_mod

    env_mod.NZILA_SAFE_CTX_PATH = str(safe)
    unload_mod = load_module('open_webui.nzila.unload', 'nzila/unload.py')
    assert unload_mod._resolve_safe_bonsai('my-model') is True
    assert unload_mod._resolve_safe_bonsai('other') is False
