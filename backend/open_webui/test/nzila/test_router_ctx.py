import json
from unittest.mock import patch

import pytest

from conftest import load_module

router_ctx = load_module('nzila_router_ctx', 'nzila/router_ctx.py')
RouterCtxError = router_ctx.RouterCtxError
apply_bonsai_context = router_ctx.apply_bonsai_context


class _Resp:
    def __init__(self, status: int, body):
        self.status = status
        self._body = body

    async def json(self, content_type=None):
        return self._body

    async def text(self):
        return json.dumps(self._body)


class _Ctx:
    def __init__(self, resp):
        self._resp = resp

    async def __aenter__(self):
        return self._resp

    async def __aexit__(self, *args):
        return False


class _Session:
    def post(self, url, json=None):
        self.url = url
        self.json = json
        return _Ctx(_Resp(200, {'status': 'ok', **(json or {})}))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.mark.asyncio
async def test_apply_bonsai_context_success():
    with patch('aiohttp.ClientSession', return_value=_Session()):
        result = await apply_bonsai_context('http://127.0.0.1:8096', 'bonsai-32k', 32768)
    assert result['ctx'] == 32768
    assert result['model'] == 'bonsai-32k'


@pytest.mark.asyncio
async def test_apply_bonsai_context_error():
    class BadSession:
        def post(self, url, json=None):
            return _Ctx(_Resp(500, {'detail': 'reload failed'}))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    with patch('aiohttp.ClientSession', return_value=BadSession()):
        with pytest.raises(RouterCtxError):
            await apply_bonsai_context('http://127.0.0.1:8096', 'm', 8192)
