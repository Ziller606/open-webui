import { WEBUI_API_BASE_URL } from '$lib/constants';
import type { FitLimits } from '$lib/utils/nzila/fit';

export type NzilaSafeCtxEntry = FitLimits & {
	fixed_ctx?: number | null;
};

export type NzilaSafeCtxResponse = {
	models: Record<string, NzilaSafeCtxEntry>;
	schema?: unknown;
};

export const getNzilaSafeCtx = async (token: string): Promise<NzilaSafeCtxResponse | null> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/nzila/safe-ctx`, {
		headers: {
			...(token && { authorization: `Bearer ${token}` })
		}
	});
	if (res.status === 404) return null;
	if (!res.ok) throw new Error(await res.text());
	return res.json();
};

export const getNzilaGpuStats = async (token: string): Promise<Record<string, unknown> | null> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/nzila/gpu-stats`, {
		headers: {
			...(token && { authorization: `Bearer ${token}` })
		}
	});
	if (res.status === 404 || res.status === 503) return null;
	if (!res.ok) return null;
	const data = await res.json();
	return typeof data === 'object' && data !== null ? data : null;
};

export const getNzilaModelFit = async (token: string, modelId: string): Promise<FitLimits | null> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/nzila/fit/${encodeURIComponent(modelId)}`, {
		headers: {
			...(token && { authorization: `Bearer ${token}` })
		}
	});
	if (res.status === 404) return null;
	if (!res.ok) return null;
	return res.json();
};

export const setNzilaBonsaiContext = async (token: string, modelId: string, ctx: number) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/nzila/ctx/${encodeURIComponent(modelId)}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({ ctx })
	});
	if (!res.ok) {
		const text = await res.text();
		throw new Error(text || 'Failed to set router context');
	}
	return res.json();
};
