from conftest import load_module

prefix = load_module('open_webui.nzila.bonsai_prefix', 'nzila/bonsai_prefix.py')


def test_strip_and_with_prefix():
    assert prefix.strip_bonsai_router_id('bonsai.foo', 'bonsai') == 'foo'
    assert prefix.with_bonsai_prefix('foo', 'bonsai') == 'bonsai.foo'
