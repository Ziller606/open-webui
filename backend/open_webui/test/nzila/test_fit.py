from conftest import load_module

fit = load_module('nzila_fit', 'nzila/fit.py')
compute_fit_limits = fit.compute_fit_limits
fit_zone = fit.fit_zone
kv_gb_for_context = fit.kv_gb_for_context
parse_parameter_billions = fit.parse_parameter_billions


def test_parse_parameter_billions():
    assert parse_parameter_billions('1.7B') == 1.7


def test_kv_grows():
    assert kv_gb_for_context(8192, 7) > kv_gb_for_context(4096, 7)


def test_fit_zone():
    limits = {'safe_max': 8192, 'tight_max': 16384, 'hard_max': 32768}
    assert fit_zone(4096, limits) == 'safe'
    assert fit_zone(12000, limits) == 'tight'
    assert fit_zone(40000, limits) == 'over'


def test_compute_with_gpu():
    limits = compute_fit_limits(
        model_size_bytes=int(1.2e9),
        parameter_size='1.7B',
        gpu_stats={'vram_used_gb': 2, 'vram_total_gb': 6},
    )
    assert limits['safe_max'] >= 2048
    assert limits['tight_max'] >= limits['safe_max']


def test_compute_with_mib_gpu():
    limits = compute_fit_limits(
        model_size_bytes=int(1.2e9),
        parameter_size='1.7B',
        gpu_stats={'memory_used_mib': 2048, 'memory_total_mib': 6144},
    )
    assert limits['safe_max'] >= 2048
