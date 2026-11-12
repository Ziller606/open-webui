from conftest import load_module
from types import SimpleNamespace

meta = load_module('open_webui.nzila.model_meta', 'nzila/model_meta.py')


def test_db_model_bonsai_from_meta():
    model = SimpleNamespace(meta={'nzila_bonsai': True}, params={})
    assert meta.db_model_bonsai(model) is True


def test_parse_num_ctx_from_show():
    payload = {'modelfile': 'PARAMETER num_ctx 65536\n'}
    assert meta.parse_num_ctx_from_show(payload) == 65536
