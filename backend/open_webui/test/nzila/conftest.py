import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _ensure_stubs():
    pkg = types.ModuleType('open_webui')
    sys.modules.setdefault('open_webui', pkg)

    if 'open_webui.utils.json_codec' not in sys.modules:
        codec = types.SimpleNamespace()

        class JSONCodec:
            @staticmethod
            def loads(value):
                return json.loads(value)

            JSONDecodeError = json.JSONDecodeError

        codec.JSONCodec = JSONCodec
        utils = types.ModuleType('open_webui.utils')
        sys.modules.setdefault('open_webui.utils', utils)
        sys.modules['open_webui.utils.json_codec'] = codec

    if 'open_webui.env' not in sys.modules:
        env = types.ModuleType('open_webui.env')
        env.NZILA_BONSAI_ROUTER_ENABLED = False
        env.NZILA_BONSAI_ROUTER_URL = None
        env.NZILA_SAFE_CTX_PATH = None
        env.AIOHTTP_CLIENT_SESSION_SSL = None
        env.NZILA_BONSAI_PRESET_PATH = None
        env.NZILA_BONSAI_IDLE_SECONDS = 300
        sys.modules['open_webui.env'] = env

    if 'open_webui.nzila' not in sys.modules:
        sys.modules['open_webui.nzila'] = types.ModuleType('open_webui.nzila')


def load_module(name: str, relative: str):
    _ensure_stubs()
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    if name.startswith('open_webui.'):
        pass
    elif relative.startswith('nzila/'):
        fq = 'open_webui.' + relative.replace('/', '.').replace('.py', '')
        sys.modules[fq] = module
    spec.loader.exec_module(module)
    return module
