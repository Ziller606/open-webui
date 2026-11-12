import { describe, expect, it } from 'vitest';
import { tokensPerSecond } from './tokensPerSec';

describe('tokensPerSecond', () => {
	it('uses Ollama eval fields', () => {
		const tps = tokensPerSecond({ eval_count: 100, eval_duration: 2e9 });
		expect(tps).toBeCloseTo(50, 1);
	});

	it('uses completion_tokens', () => {
		const tps = tokensPerSecond({ completion_tokens: 10, eval_duration: 1e9 });
		expect(tps).toBe(10);
	});
});
