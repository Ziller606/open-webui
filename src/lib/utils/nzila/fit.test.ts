import { describe, expect, it } from 'vitest';
import {
	computeFitLimits,
	ctxForBudgetGb,
	fitZone,
	gpuVramFreeGb,
	kvGbForContext,
	parseParameterBillions
} from './fit';

describe('parseParameterBillions', () => {
	it('parses B suffix', () => {
		expect(parseParameterBillions('1.7B')).toBeCloseTo(1.7, 5);
	});
	it('defaults when missing', () => {
		expect(parseParameterBillions(undefined)).toBe(3);
	});
});

describe('kvGbForContext', () => {
	it('grows with context', () => {
		expect(kvGbForContext(8192, 7)).toBeGreaterThan(kvGbForContext(4096, 7));
	});
});

describe('gpuVramFreeGb', () => {
	it('subtracts used from total', () => {
		expect(gpuVramFreeGb({ vram_used_gb: 4, vram_total_gb: 6 })).toBeCloseTo(2);
	});
});

describe('computeFitLimits', () => {
	it('derives safe/tight from GPU headroom', () => {
		const limits = computeFitLimits(
			{ sizeBytes: 1.2e9, parameterSize: '1.7B' },
			{ vram_used_gb: 2, vram_total_gb: 6 }
		);
		expect(limits.safe_max).toBeGreaterThanOrEqual(2048);
		expect(limits.tight_max).toBeGreaterThanOrEqual(limits.safe_max);
		expect(limits.hard_max).toBeGreaterThanOrEqual(limits.tight_max);
	});

	it('respects overrides', () => {
		const limits = computeFitLimits({ parameterSize: '7B' }, null, {
			safe_max: 32768,
			tight_max: 65536,
			hard_max: 131072
		});
		expect(limits.safe_max).toBe(32768);
	});
});

describe('fitZone', () => {
	it('classifies token counts', () => {
		const limits = { safe_max: 8192, tight_max: 16384 };
		expect(fitZone(4096, limits)).toBe('safe');
		expect(fitZone(12000, limits)).toBe('tight');
		expect(fitZone(32000, limits)).toBe('over');
	});
});

describe('ctxForBudgetGb', () => {
	it('returns slider min when budget empty', () => {
		expect(ctxForBudgetGb(0.1, 3, 2)).toBe(2048);
	});
});
