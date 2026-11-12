import { describe, expect, it } from 'vitest';
import { formatCountdownMmSs, parseExpiresAtMs, secondsRemaining, soonestExpiryMs } from './countdown';

describe('countdown', () => {
	it('parses ISO expires_at', () => {
		const ms = parseExpiresAtMs('2026-01-01T00:01:00.000Z');
		expect(ms).not.toBeNull();
	});

	it('formats mm:ss', () => {
		expect(formatCountdownMmSs(125)).toBe('2:05');
		expect(formatCountdownMmSs(0)).toBe('0:00');
	});

	it('counts down seconds', () => {
		const now = 1_000_000;
		expect(secondsRemaining(1_010_000, now)).toBe(10);
	});

	it('picks soonest expiry', () => {
		const soon = soonestExpiryMs(['2026-01-01T00:10:00Z', '2026-01-01T00:05:00Z']);
		expect(soon).toBe(Date.parse('2026-01-01T00:05:00Z'));
	});
});
