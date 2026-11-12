import { WEBUI_API_BASE_URL } from '$lib/constants';

export type NzilaSafeCtxEntry = {
	safe_max: number;
	tight_max: number;
	hard_max: number;
	fixed: boolean;
	fixed_ctx: number | null;
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
