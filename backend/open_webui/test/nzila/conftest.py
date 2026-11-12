import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _ensure_stubs():
    if 'open_webui.utils.json_codec' in sys.modules:
        return

    codec = types.SimpleNamespace()

    class JSONCodec:
        @staticmethod
        def loads(value):
            return json.loads(value)

        JSONDecodeError = json.JSONDecodeError

    codec.JSONCodec = JSONCodec
    pkg = types.ModuleType('open_webui')
    utils = types.ModuleType('open_webui.utils')
    sys.modules.setdefault('open_webui', pkg)
    sys.modules.setdefault('open_webui.utils', utils)
    sys.modules['open_webui.utils.json_codec'] = codec


def load_module(name: str, relative: str):
    _ensure_stubs()
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
