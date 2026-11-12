<script lang="ts">
	import { nzilaGpu } from '$lib/stores/nzilaGpu';

	export let enabled = false;

	$: snap = $nzilaGpu;
	$: visible =
		enabled && snap.vramTotalGb !== null && snap.vramUsedGb !== null && snap.vramTotalGb > 0;
	$: vramPct = visible ? Math.min(100, (snap.vramUsedGb! / snap.vramTotalGb!) * 100) : 0;
	$: utilPct = snap.utilPercent ?? 0;
	$: barClass =
		vramPct < 72 ? 'bg-emerald-500/90' : vramPct < 88 ? 'bg-amber-400/90' : 'bg-red-500/85';
	$: utilClass =
		utilPct < 55 ? 'bg-emerald-400/50' : utilPct < 82 ? 'bg-amber-300/55' : 'bg-red-400/55';

	const fmt = (v: number | null) => (v === null ? '—' : v >= 10 ? v.toFixed(1) : v.toFixed(2));
</script>

{#if visible}
	<div
		class="pointer-events-auto relative z-20 h-1 w-full shrink-0 overflow-hidden bg-gray-200/80 dark:bg-gray-800/80"
		title={utilPct >= 55 ? 'GPU busy' : 'GPU free'}
		aria-label={utilPct >= 55 ? 'GPU busy' : 'GPU free'}
	>
		<div
			class="absolute inset-y-0 left-0 transition-[width] duration-500 ease-out {barClass}"
			style:width="{vramPct}%"
		></div>
		<div
			class="absolute inset-y-0 left-0 mix-blend-multiply dark:mix-blend-screen transition-[width] duration-500 {utilClass}"
			style:width="{utilPct}%"
		></div>
		<span class="sr-only"
			>VRAM {fmt(snap.vramUsedGb)}/{fmt(snap.vramTotalGb)} GB, {utilPct}% utilisation</span
		>
	</div>
{/if}
