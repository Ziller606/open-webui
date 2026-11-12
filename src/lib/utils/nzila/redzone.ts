export const vramPercent = (usedGb: number | null, totalGb: number | null): number | null => {
	if (usedGb === null || totalGb === null || totalGb <= 0) return null;
	return Math.min(100, Math.max(0, (usedGb / totalGb) * 100));
};

export const isVramRedZone = (percent: number | null, thresholdPercent = 90): boolean => {
	if (percent === null) return false;
	return percent >= thresholdPercent;
};

/** Tailwind class for VRAM fill segments (monochrome until red zone). */
export const vramBarFillClass = (percent: number | null, thresholdPercent = 90): string => {
	if (isVramRedZone(percent, thresholdPercent)) {
		return 'bg-red-500/85 dark:bg-red-500/80';
	}
	return 'bg-gray-900/80 dark:bg-gray-100/85';
};

export const utilBarFillClass = (utilPercent: number | null): string => {
	return 'bg-gray-500/35 dark:bg-gray-400/30 mix-blend-multiply dark:mix-blend-screen';
};
