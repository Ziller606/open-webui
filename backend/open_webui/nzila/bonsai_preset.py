from __future__ import annotations

import logging
import re
import shutil
from configparser import ConfigParser
from pathlib import Path

log = logging.getLogger(__name__)

_CTX_KEYS = ('ctx-size', 'ctx_size', 'c', 'ctx')


def _section_matches(parser: ConfigParser, section: str, model_id: str) -> bool:
    if section == model_id or section.lower() == model_id.lower():
        return True
    if section == '*':
        return False
    try:
        model_path = parser.get(section, 'model', fallback='').strip()
        if model_path and (model_path == model_id or model_path.endswith(model_id)):
            return True
        alias = parser.get(section, 'alias', fallback='').strip()
        if alias and alias == model_id:
            return True
    except Exception:
        pass
    tail = model_id.split(':')[-1] if ':' in model_id else model_id
    return section == tail or section.endswith(tail)


def find_model_section(parser: ConfigParser, model_id: str) -> str | None:
    for section in parser.sections():
        if _section_matches(parser, section, model_id):
            return section
    return None


def _split_ini_preamble(text: str) -> tuple[str, str]:
    preamble: list[str] = []
    body: list[str] = []
    seen_section = False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if not seen_section:
            if stripped.startswith('[') and stripped.endswith(']'):
                seen_section = True
                body.append(line)
            else:
                preamble.append(line)
        else:
            body.append(line)
    return ''.join(preamble), ''.join(body)


def update_preset_ctx_size(preset_path: str | Path, model_id: str, ctx: int) -> str:
    """Rewrite ctx-size for one model section. Keeps a ``.bak`` alongside the preset."""
    path = Path(preset_path)
    if not path.is_file():
        raise FileNotFoundError(f'Preset not found: {path}')

    text = path.read_text(encoding='utf-8')
    preamble, body = _split_ini_preamble(text)
    parser = ConfigParser()
    parser.optionxform = str  # preserve key casing
    parser.read_string(body or '\n')

    section = find_model_section(parser, model_id)
    if not section:
        raise KeyError(f'No preset section for model {model_id!r}')

    updated = False
    for key in _CTX_KEYS:
        if parser.has_option(section, key):
            parser.set(section, key, str(int(ctx)))
            updated = True
            break
    if not updated:
        parser.set(section, 'ctx-size', str(int(ctx)))

    bak = path.with_suffix(path.suffix + '.bak')
    shutil.copy2(path, bak)

    _lines: list[str] = []
    in_section = False
    replaced = False
    ctx_line = re.compile(rf'^\s*(?:{"|".join(_CTX_KEYS)})\s*=\s*\d+\s*$', re.IGNORECASE)
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            in_section = stripped[1:-1].strip() == section
            _lines.append(line)
            continue
        if in_section and not replaced and ctx_line.match(stripped):
            key = stripped.split('=', 1)[0].strip()
            _lines.append(f'{key}={int(ctx)}\n')
            replaced = True
            continue
        _lines.append(line)
    if not replaced:
        # append ctx-size inside section (before next section or EOF)
        out: list[str] = []
        inserted = False
        for line in _lines:
            out.append(line)
            if not inserted and line.strip() == f'[{section}]':
                out.append(f'ctx-size={int(ctx)}\n')
                inserted = True
        _lines = out
    path.write_text(''.join(_lines), encoding='utf-8')

    log.info('Updated preset %s section [%s] ctx-size=%s (backup %s)', path, section, ctx, bak)
    return section
