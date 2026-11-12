import { get } from 'svelte/store';
import { toast } from 'svelte-sonner';
import { settings } from '$lib/stores';
import { readNzilaSettings } from '$lib/utils/nzila/defaults';
import { nzilaTouchActivity } from '$lib/apis/nzila';

const loadStartedAt = new Map<string, number>();
const loadingToastIds = new Map<string, string | number>();
const sawFirstToken = new Set<string>();

export const nzilaLastLoadSeconds = new Map<string, number>();

const toastsOn = () => readNzilaSettings(get(settings)).showModelToasts !== false;

export const nzilaOnModelSwitch = (modelId: string, label: string) => {
	if (!toastsOn()) return;
	toast.message(`Switched to ${label}`);
	void modelId;
};

export const nzilaOnLoadStart = (modelId: string, label: string) => {
	if (!toastsOn()) return;
	loadStartedAt.set(modelId, performance.now());
	sawFirstToken.delete(modelId);
	const id = toast.loading(`Loading ${label}…`);
	loadingToastIds.set(modelId, id);
};

export const nzilaOnFirstToken = (modelId: string, label: string) => {
	if (!toastsOn()) return;
	if (sawFirstToken.has(modelId)) return;
	sawFirstToken.add(modelId);
	const started = loadStartedAt.get(modelId);
	if (started === undefined) return;
	const elapsed = (performance.now() - started) / 1000;
	nzilaLastLoadSeconds.set(modelId, elapsed);
	const toastId = loadingToastIds.get(modelId);
	const message = `Loaded ${label} in ${elapsed.toFixed(1)}s`;
	if (toastId !== undefined) toast.success(message, { id: toastId });
	else toast.success(message);
	loadingToastIds.delete(modelId);
	void nzilaTouchActivity(localStorage.token, modelId).catch(() => {});
};

export const nzilaOnInferenceDone = (modelId: string) => {
	void nzilaTouchActivity(localStorage.token, modelId).catch(() => {});
};

export const nzilaOnUnload = (modelId: string, label: string, freedMb: number | null) => {
	if (!toastsOn()) return;
	const suffix = freedMb !== null && freedMb > 0 ? `, GPU freed (${Math.round(freedMb)} MB)` : ', GPU freed';
	toast.success(`Unloaded ${label}${suffix}`);
	void modelId;
};
