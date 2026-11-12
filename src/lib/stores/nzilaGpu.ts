import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { getNzilaGpuStats } from '$lib/apis/nzila';

export type NzilaGpuSnapshot = {
	stats: Record<string, unknown> | null;
	utilPercent: number | null;
	vramUsedGb: number | null;
	vramTotalGb: number | null;
};

const empty: NzilaGpuSnapshot = {
	stats: null,
	utilPercent: null,
	vramUsedGb: null,
	vramTotalGb: null
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

const parseSnapshot = (payload: Record<string, unknown> | null): NzilaGpuSnapshot => {
	if (!payload) return { ...empty };
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
	try {
		const payload = await getNzilaGpuStats(localStorage.token);
		nzilaGpu.set(parseSnapshot(payload));
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
