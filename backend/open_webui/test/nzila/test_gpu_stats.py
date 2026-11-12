from conftest import load_module

gpu = load_module('open_webui.nzila.gpu_stats', 'nzila/gpu_stats.py')
normalize_gpu_stats = gpu.normalize_gpu_stats


def test_normalizes_mib_fields():
    raw = {'memory_used_mib': 2048, 'memory_total_mib': 6144, 'utilization_gpu': 42}
    out = normalize_gpu_stats(raw)
    assert abs(out['vram_used_gb'] - 2.0) < 0.01
    assert abs(out['vram_total_gb'] - 6.0) < 0.01
    assert out['gpu_utilization'] == 42
