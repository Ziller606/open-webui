<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { nzilaGpu } from '$lib/stores/nzilaGpu';

	export let enabled = false;

	$: snap = $nzilaGpu;
	$: visible =
		enabled &&
		(snap.utilPercent !== null || snap.vramUsedGb !== null || snap.vramTotalGb !== null);

	const fmtGb = (value: number | null) => {
		if (value === null) return '—';
		if (value >= 10) return value.toFixed(1);
		return value.toFixed(2);
	};

	onMount(() => {});
	onDestroy(() => {});
</script>

{#if enabled && visible}
	<div
		class="hidden sm:flex items-center gap-2 rounded-md border border-gray-200/80 bg-white/80 px-2 py-0.5 text-[0.6875rem] tabular-nums tracking-tight text-gray-600 backdrop-blur-sm dark:border-gray-800 dark:bg-gray-900/80 dark:text-gray-300"
		aria-live="polite"
		aria-label="GPU status"
	>
		{#if snap.utilPercent !== null}
			<span>{snap.utilPercent}%</span>
		{/if}
		{#if snap.vramUsedGb !== null || snap.vramTotalGb !== null}
			<span class="text-gray-400 dark:text-gray-500">·</span>
			<span>
				{fmtGb(snap.vramUsedGb)}{#if snap.vramTotalGb !== null}<span
						class="text-gray-400 dark:text-gray-500">/{fmtGb(snap.vramTotalGb)}</span
					> GB{/if}
			</span>
		{/if}
	</div>
{/if}
