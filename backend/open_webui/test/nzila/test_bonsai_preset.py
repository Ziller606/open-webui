from conftest import load_module

preset_mod = load_module('open_webui.nzila.bonsai_preset', 'nzila/bonsai_preset.py')


def test_update_preset_ctx_size(tmp_path):
    ini = tmp_path / 'webui-models.ini'
    ini.write_text(
        '[bonsai-32k]\nmodel=/data/model.gguf\nn-gpu-layers=99\nctx-size=8192\n',
        encoding='utf-8',
    )
    section = preset_mod.update_preset_ctx_size(ini, 'bonsai-32k', 32768)
    assert section == 'bonsai-32k'
    text = ini.read_text(encoding='utf-8')
    assert 'ctx-size=32768' in text
    assert (tmp_path / 'webui-models.ini.bak').is_file()
