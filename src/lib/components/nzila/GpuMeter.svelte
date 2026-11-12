<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { getNzilaGpuStats } from '$lib/apis/nzila';

	export let enabled = false;

	let visible = false;
	let gpuPct: number | null = null;
	let vramUsedGb: number | null = null;
	let vramTotalGb: number | null = null;

	let timer: ReturnType<typeof setInterval> | null = null;
	let controller: AbortController | null = null;

	const asNumber = (value: unknown): number | null => {
		if (typeof value === 'number' && Number.isFinite(value)) return value;
		if (typeof value === 'string' && value.trim() !== '' && !Number.isNaN(Number(value))) {
			return Number(value);
		}
		return null;
	};

	const bytesToGb = (bytes: number) => bytes / 1024 ** 3;

	const parseStats = (payload: Record<string, unknown>) => {
		const util =
			asNumber(payload.gpu_utilization) ??
			asNumber(payload.utilization_gpu) ??
			asNumber(payload.gpu_util) ??
			asNumber(payload.utilization) ??
			asNumber(payload.gpu);

		let used =
			asNumber(payload.vram_used_gb) ??
			asNumber(payload.memory_used_gb) ??
			asNumber(payload.used_gb);
		let total =
			asNumber(payload.vram_total_gb) ??
			asNumber(payload.memory_total_gb) ??
			asNumber(payload.total_gb);

		const usedBytes =
			asNumber(payload.vram_used) ??
			asNumber(payload.memory_used) ??
			asNumber(payload.used_memory) ??
			asNumber(payload.used);
		const totalBytes =
			asNumber(payload.vram_total) ??
			asNumber(payload.memory_total) ??
			asNumber(payload.total_memory) ??
			asNumber(payload.total);

		if (used === null && usedBytes !== null) used = bytesToGb(usedBytes);
		if (total === null && totalBytes !== null) total = bytesToGb(totalBytes);

		const gpus = payload.gpus;
		if (Array.isArray(gpus) && gpus.length > 0 && typeof gpus[0] === 'object' && gpus[0]) {
			const first = gpus[0] as Record<string, unknown>;
			return parseStats({ ...payload, ...first });
		}

		return { util, used, total };
	};

	const poll = async () => {
		if (!enabled) return;
		controller?.abort();
		controller = new AbortController();
		try {
			const token = localStorage.token;
			const payload = await getNzilaGpuStats(token);
			if (!payload) {
				visible = false;
				return;
			}
			const { util, used, total } = parseStats(payload);
			if (util === null && used === null && total === null) {
				visible = false;
				return;
			}
			gpuPct = util !== null ? Math.round(Math.max(0, Math.min(100, util))) : null;
			vramUsedGb = used;
			vramTotalGb = total;
			visible = true;
		} catch {
			visible = false;
		}
	};

	const fmtGb = (value: number | null) => {
		if (value === null) return '—';
		if (value >= 10) return value.toFixed(1);
		return value.toFixed(2);
	};

	const start = () => {
		if (timer) return;
		void poll();
		timer = setInterval(poll, 1500);
	};

	const stop = () => {
		visible = false;
		if (timer) {
			clearInterval(timer);
			timer = null;
		}
		controller?.abort();
	};

	onMount(() => {
		if (enabled) start();
	});

	onDestroy(() => {
		stop();
	});

	$: if (enabled) start();
	else stop();
</script>

{#if enabled && visible}
	<div
		class="hidden sm:flex items-center gap-2 rounded-md border border-gray-200/80 bg-white/80 px-2 py-0.5 text-[0.6875rem] tabular-nums tracking-tight text-gray-600 backdrop-blur-sm dark:border-gray-800 dark:bg-gray-900/80 dark:text-gray-300"
		aria-live="polite"
		aria-label="GPU status"
	>
		{#if gpuPct !== null}
			<span>{gpuPct}%</span>
		{/if}
		{#if vramUsedGb !== null || vramTotalGb !== null}
			<span class="text-gray-400 dark:text-gray-500">·</span>
			<span>
				{fmtGb(vramUsedGb)}{#if vramTotalGb !== null}<span class="text-gray-400 dark:text-gray-500"
						>/{fmtGb(vramTotalGb)}</span
					> GB{/if}
			</span>
		{/if}
	</div>
{/if}
