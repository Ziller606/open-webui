import { describe, expect, it } from 'vitest';
import { resolveModelNumCtx } from './modelCtx';

describe('resolveModelNumCtx', () => {
	it('prefers fit num_ctx', () => {
		expect(
			resolveModelNumCtx({ id: 'm', name: 'm', owned_by: 'ollama' } as any, { num_ctx: 65536, safe_max: 8192, tight_max: 16384, hard_max: 32768 })
		).toBe(65536);
	});

	it('reads workspace params', () => {
		expect(
			resolveModelNumCtx({
				id: 'm',
				name: 'm',
				owned_by: 'ollama',
				info: { params: { num_ctx: 32768 } }
			} as any)
		).toBe(32768);
	});
});
