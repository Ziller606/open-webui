export const parseExpiresAtMs = (value: string | null | undefined): number | null => {
	if (!value) return null;
	const parsed = Date.parse(value);
	return Number.isFinite(parsed) ? parsed : null;
};

export const secondsRemaining = (expiresAtMs: number, nowMs = Date.now()): number => {
	return Math.max(0, (expiresAtMs - nowMs) / 1000);
};

export const formatCountdownMmSs = (seconds: number): string => {
	const total = Math.ceil(Math.max(0, seconds));
	const minutes = Math.floor(total / 60);
	const remainder = total % 60;
	return `${minutes}:${String(remainder).padStart(2, '0')}`;
};

/** Soonest expiry across loaded models (ms), or null if none. */
export const soonestExpiryMs = (expires: Array<string | null | undefined>): number | null => {
	let best: number | null = null;
	for (const raw of expires) {
		const ms = parseExpiresAtMs(raw ?? null);
		if (ms === null) continue;
		if (best === null || ms < best) best = ms;
	}
	return best;
};
