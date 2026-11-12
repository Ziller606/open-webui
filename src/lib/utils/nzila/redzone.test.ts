import { describe, expect, it } from 'vitest';
import { isVramRedZone, vramBarFillClass, vramPercent } from './redzone';

describe('redzone', () => {
	it('computes vram percent', () => {
		expect(vramPercent(9, 10)).toBeCloseTo(90);
		expect(vramPercent(null, 10)).toBeNull();
	});

	it('detects red zone at threshold', () => {
		expect(isVramRedZone(89.9, 90)).toBe(false);
		expect(isVramRedZone(90, 90)).toBe(true);
	});

	it('uses red class only in red zone', () => {
		expect(vramBarFillClass(50, 90)).toContain('gray');
		expect(vramBarFillClass(95, 90)).toContain('red');
	});
});
