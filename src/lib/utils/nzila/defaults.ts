export type NzilaUserSettings = {
	showGpuTopBar: boolean;
	showGpuMeter: boolean;
	showContextSlider: boolean;
	pollIntervalMs: number;
	applyContextLive: boolean;
	showToksPerSec: boolean;
	defaultContextByModel: Record<string, number>;
};

export const NZILA_SETTINGS_DEFAULTS: NzilaUserSettings = {
	showGpuTopBar: true,
	showGpuMeter: true,
	showContextSlider: true,
	pollIntervalMs: 2000,
	applyContextLive: true,
	showToksPerSec: false,
	defaultContextByModel: {}
};

export const mergeNzilaSettings = (partial?: Partial<NzilaUserSettings> | null): NzilaUserSettings => ({
	...NZILA_SETTINGS_DEFAULTS,
	...(partial ?? {}),
	defaultContextByModel: {
		...NZILA_SETTINGS_DEFAULTS.defaultContextByModel,
		...(partial?.defaultContextByModel ?? {})
	}
});

export const readNzilaSettings = (settings: { nzila?: Partial<NzilaUserSettings> } | null | undefined) =>
	mergeNzilaSettings(settings?.nzila);
