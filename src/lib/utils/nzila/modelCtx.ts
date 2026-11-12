import type { Model } from '$lib/stores';
import type { FitLimits } from '$lib/utils/nzila/fit';

export const resolveModelNumCtx = (
	model: Model | undefined,
	fit?: FitLimits | null
): number | undefined => {
	if (fit?.num_ctx && fit.num_ctx > 0) return fit.num_ctx;
	const fromInfo = model?.info?.params?.num_ctx;
	if (typeof fromInfo === 'number' && fromInfo > 0) return fromInfo;
	if (typeof fromInfo === 'string' && fromInfo.trim()) {
		const n = Number(fromInfo);
		if (Number.isFinite(n) && n > 0) return n;
	}
	return undefined;
};
