import { describe, expect, it } from 'vitest';
import { NZILA_SETTINGS_DEFAULTS, mergeNzilaSettings, readNzilaSettings } from './defaults';

describe('mergeNzilaSettings', () => {
	it('uses defaults', () => {
		expect(mergeNzilaSettings().pollIntervalMs).toBe(2000);
		expect(mergeNzilaSettings().showContextSlider).toBe(true);
	});

	it('merges defaults per model', () => {
		const merged = mergeNzilaSettings({
			defaultContextByModel: { 'lfm:latest': 65536 }
		});
		expect(merged.defaultContextByModel['lfm:latest']).toBe(65536);
	});
});

describe('readNzilaSettings', () => {
	it('reads from settings.nzila', () => {
		expect(readNzilaSettings({ nzila: { showGpuMeter: false } }).showGpuMeter).toBe(false);
		expect(readNzilaSettings(null).showGpuTopBar).toBe(NZILA_SETTINGS_DEFAULTS.showGpuTopBar);
	});
});
