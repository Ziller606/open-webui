export type GpuStats = Record<string, unknown>;

export type FitLimits = {
	safe_max: number;
	tight_max: number;
	hard_max: number;
	fixed?: boolean;
	bonsai?: boolean;
	num_ctx?: number;
};

export type ModelFitHints = {
	sizeBytes?: number | null;
	parameterSize?: string | null;
};

const DEFAULT_SLIDER_MAX = 131072;
const DEFAULT_SLIDER_MIN = 2048;

export const parseParameterBillions = (parameterSize?: string | null): number => {
	if (!parameterSize) return 3;
	const match = parameterSize.trim().match(/([\d.]+)\s*([bmk])?/i);
	if (!match) return 3;
	const value = parseFloat(match[1]);
	const suffix = (match[2] ?? 'b').toLowerCase();
	if (suffix === 'm') return value / 1000;
	if (suffix === 'k') return value / 1_000_000;
	return value;
};

export const kvGbForContext = (ctxTokens: number, paramB: number): number => {
	if (ctxTokens <= 0) return 0;
	const gbPer1k = Math.max(0.004, paramB * 0.0016);
	return (ctxTokens / 1024) * gbPer1k;
};

export const weightsGb = (sizeBytes: number | null | undefined, paramB: number): number => {
	if (sizeBytes && sizeBytes > 0) return sizeBytes / 1024 ** 3;
	return Math.max(0.8, paramB * 0.55);
};

const asNumber = (value: unknown): number | null => {
	if (typeof value === 'number' && Number.isFinite(value)) return value;
	if (typeof value === 'string' && value.trim() && !Number.isNaN(Number(value))) return Number(value);
	return null;
};

export const gpuVramFreeGb = (gpuStats?: GpuStats | null): number | null => {
	if (!gpuStats) return null;
	const usedMib = asNumber(gpuStats.memory_used_mib);
	const totalMib = asNumber(gpuStats.memory_total_mib);
	let used =
		asNumber(gpuStats.vram_used_gb) ??
		asNumber(gpuStats.memory_used_gb) ??
		asNumber(gpuStats.used_gb);
	let total =
		asNumber(gpuStats.vram_total_gb) ??
		asNumber(gpuStats.memory_total_gb) ??
		asNumber(gpuStats.total_gb);
	if (used === null && usedMib !== null) used = usedMib / 1024;
	if (total === null && totalMib !== null) total = totalMib / 1024;
	const usedBytes =
		asNumber(gpuStats.vram_used) ?? asNumber(gpuStats.memory_used) ?? asNumber(gpuStats.used);
	const totalBytes =
		asNumber(gpuStats.vram_total) ?? asNumber(gpuStats.memory_total) ?? asNumber(gpuStats.total);
	if (used === null && usedBytes !== null) used = usedBytes / 1024 ** 3;
	if (total === null && totalBytes !== null) total = totalBytes / 1024 ** 3;
	if (used !== null && total !== null) return Math.max(0, total - used);
	return asNumber(gpuStats.vram_free_gb) ?? asNumber(gpuStats.memory_free_gb);
};

export const ctxForBudgetGb = (budgetGb: number, paramB: number, modelWeightsGb: number): number => {
	const k = Math.max(1e-9, (paramB * 0.0016) / 1024);
	const remaining = budgetGb - modelWeightsGb;
	if (remaining <= 0) return DEFAULT_SLIDER_MIN;
	let ctx = Math.floor((remaining / k) * 1024);
	ctx = Math.max(DEFAULT_SLIDER_MIN, Math.min(DEFAULT_SLIDER_MAX, ctx));
	return Math.floor(ctx / 1024) * 1024;
};

export const computeFitLimits = (
	hints: ModelFitHints,
	gpuStats?: GpuStats | null,
	override?: Partial<FitLimits> | null
): FitLimits => {
	const paramB = parseParameterBillions(hints.parameterSize);
	const wGb = weightsGb(hints.sizeBytes, paramB);
	const freeGb = gpuVramFreeGb(gpuStats);

	let safeMax: number;
	let tightMax: number;
	let hardMax: number;

	if (freeGb !== null) {
		safeMax = ctxForBudgetGb(freeGb * 0.82 - wGb, paramB, wGb);
		tightMax = ctxForBudgetGb(freeGb * 0.98 - wGb, paramB, wGb);
		hardMax = Math.min(DEFAULT_SLIDER_MAX, Math.max(tightMax, safeMax * 2, 32768));
	} else {
		safeMax = Math.min(65536, Math.max(8192, Math.floor(paramB * 8192)));
		tightMax = Math.min(DEFAULT_SLIDER_MAX, Math.max(safeMax, safeMax + 16384));
		hardMax = Math.min(DEFAULT_SLIDER_MAX, Math.max(tightMax, tightMax + 32768));
	}

	if (override?.safe_max && override.safe_max > 0) safeMax = override.safe_max;
	if (override?.tight_max && override.tight_max > 0) tightMax = override.tight_max;
	if (override?.hard_max && override.hard_max > 0) hardMax = override.hard_max;

	safeMax = Math.max(DEFAULT_SLIDER_MIN, safeMax);
	tightMax = Math.max(safeMax, tightMax);
	hardMax = Math.max(tightMax, hardMax);

	return {
		safe_max: safeMax,
		tight_max: tightMax,
		hard_max: hardMax,
		fixed: override?.fixed,
		bonsai: override?.bonsai
	};
};

export const fitZone = (ctx: number, limits: Pick<FitLimits, 'safe_max' | 'tight_max'>): 'safe' | 'tight' | 'over' => {
	if (ctx <= limits.safe_max) return 'safe';
	if (ctx <= limits.tight_max) return 'tight';
	return 'over';
};

export const formatCtx = (value: number) => {
	if (value >= 1024 && value % 1024 === 0) return `${value / 1024}k`;
	return String(value);
};
