import json
from unittest.mock import patch

import pytest

from conftest import load_module

bonsai = load_module('open_webui.nzila.bonsai_router', 'nzila/bonsai_router.py')
router_admin = load_module('open_webui.nzila.router_admin', 'nzila/router_admin.py')
RouterAdminError = router_admin.RouterAdminError
apply_bonsai_unload = router_admin.apply_bonsai_unload


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
    def __init__(self):
        self.last_url = None
        self.last_json = None

    def request(self, method, url, json=None):
        self.last_url = url
        self.last_json = json
        return _Ctx(_Resp(200, {'success': True, **(json or {})}))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.mark.asyncio
async def test_apply_bonsai_unload_uses_native_endpoint():
    session = _Session()
    with patch('aiohttp.ClientSession', return_value=session):
        result = await apply_bonsai_unload('http://127.0.0.1:8096', 'bonsai-32k')
    assert result['model'] == 'bonsai-32k'
    assert session.last_url.endswith('/models/unload')
