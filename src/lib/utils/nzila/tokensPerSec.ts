export type TokUsage = {
	eval_count?: number;
	eval_duration?: number;
	completion_tokens?: number;
	output_tokens?: number;
	predicted_n?: number;
	predicted_ms?: number;
	prompt_ms?: number;
	total_tokens?: number;
};

/** Tokens per second from Ollama or llama.cpp usage on a finished message. */
export const tokensPerSecond = (usage: TokUsage | null | undefined): number | null => {
	if (!usage) return null;
	const count =
		usage.eval_count ?? usage.completion_tokens ?? usage.output_tokens ?? usage.predicted_n;
	let durationNs = usage.eval_duration;
	if (durationNs && durationNs > 0 && durationNs < 1_000_000) {
		durationNs *= 1_000_000;
	}
	if ((!count || !durationNs) && usage.predicted_ms && usage.predicted_ms > 0 && count) {
		return count / (usage.predicted_ms / 1000);
	}
	if (!count || !durationNs || durationNs <= 0) return null;
	return count / (durationNs / 1e9);
};
