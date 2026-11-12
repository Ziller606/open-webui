import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { getNzilaGpuStats, getNzilaLoaded, type NzilaLoadedModel } from '$lib/apis/nzila';

export type NzilaLoadedSnapshot = {
	model: string;
	source: string;
	sizeVramBytes: number | null;
	loadedAt: string | null;
	expiresAt: string | null;
};

export type NzilaGpuSnapshot = {
	stats: Record<string, unknown> | null;
	utilPercent: number | null;
	vramUsedGb: number | null;
	vramTotalGb: number | null;
	loadedModels: NzilaLoadedSnapshot[];
	loadedFetchedAt: number | null;
};

const empty: NzilaGpuSnapshot = {
	stats: null,
	utilPercent: null,
	vramUsedGb: null,
	vramTotalGb: null,
	loadedModels: [],
	loadedFetchedAt: null
};

export const nzilaGpu = writable<NzilaGpuSnapshot>(empty);

let timer: ReturnType<typeof setInterval> | null = null;
let active = false;
let intervalMs = 2000;
let tabVisible = true;

const asNumber = (value: unknown): number | null => {
	if (typeof value === 'number' && Number.isFinite(value)) return value;
	if (typeof value === 'string' && value.trim() && !Number.isNaN(Number(value))) return Number(value);
	return null;
};

const parseLoaded = (models: NzilaLoadedModel[] | undefined): NzilaLoadedSnapshot[] => {
	if (!models?.length) return [];
	return models.map((m) => ({
		model: m.model,
		source: m.source,
		sizeVramBytes: m.size_vram_bytes ?? null,
		loadedAt: m.loaded_at ?? null,
		expiresAt: m.expires_at ?? null
	}));
};

const parseSnapshot = (payload: Record<string, unknown> | null): Omit<NzilaGpuSnapshot, 'loadedModels' | 'loadedFetchedAt'> => {
	if (!payload) {
		return {
			stats: null,
			utilPercent: null,
			vramUsedGb: null,
			vramTotalGb: null
		};
	}
	const util =
		asNumber(payload.gpu_utilization) ??
		asNumber(payload.utilization_gpu) ??
		asNumber(payload.gpu_util) ??
		asNumber(payload.utilization) ??
		asNumber(payload.gpu);
	let used =
		asNumber(payload.vram_used_gb) ?? asNumber(payload.memory_used_gb) ?? asNumber(payload.used_gb);
	let total =
		asNumber(payload.vram_total_gb) ?? asNumber(payload.memory_total_gb) ?? asNumber(payload.total_gb);
	const usedBytes = asNumber(payload.vram_used) ?? asNumber(payload.memory_used) ?? asNumber(payload.used);
	const totalBytes =
		asNumber(payload.vram_total) ?? asNumber(payload.memory_total) ?? asNumber(payload.total);
	if (used === null && usedBytes !== null) used = usedBytes / 1024 ** 3;
	if (total === null && totalBytes !== null) total = totalBytes / 1024 ** 3;
	return {
		stats: payload,
		utilPercent: util !== null ? Math.round(Math.min(100, Math.max(0, util))) : null,
		vramUsedGb: used,
		vramTotalGb: total
	};
};

const poll = async () => {
	if (!active || !tabVisible || !browser) return;
	const token = localStorage.token;
	try {
		const [gpuPayload, loadedPayload] = await Promise.all([
			getNzilaGpuStats(token),
			getNzilaLoaded(token)
		]);
		const base = parseSnapshot(gpuPayload);
		nzilaGpu.set({
			...base,
			loadedModels: parseLoaded(loadedPayload?.models),
			loadedFetchedAt: Date.now()
		});
	} catch {
		nzilaGpu.set({ ...empty });
	}
};

const onVisibility = () => {
	tabVisible = !document.hidden;
	if (tabVisible && active) void poll();
};

export const startNzilaGpuPolling = (enabled: boolean, ms = 2000) => {
	intervalMs = Math.max(1000, ms);
	if (!browser) return;
	if (timer) {
		clearInterval(timer);
		timer = null;
	}
	active = enabled;
	if (!enabled) {
		nzilaGpu.set({ ...empty });
		return;
	}
	document.removeEventListener('visibilitychange', onVisibility);
	document.addEventListener('visibilitychange', onVisibility);
	void poll();
	timer = setInterval(poll, intervalMs);
};

export const stopNzilaGpuPolling = () => startNzilaGpuPolling(false);

export const refreshNzilaGpu = () => {
	if (active) void poll();
};
