<script lang="ts">
	import { nzilaGpu } from '$lib/stores/nzilaGpu';
	import { settings } from '$lib/stores';
	import { readNzilaSettings } from '$lib/utils/nzila/defaults';
	import { utilBarFillClass, vramBarFillClass, vramPercent } from '$lib/utils/nzila/redzone';

	export let enabled = false;

	$: snap = $nzilaGpu;
	$: nzila = readNzilaSettings($settings);
	$: threshold = nzila.vramRedZonePercent ?? 90;
	$: visible =
		enabled && snap.vramTotalGb !== null && snap.vramUsedGb !== null && snap.vramTotalGb > 0;
	$: vramPct = visible ? vramPercent(snap.vramUsedGb, snap.vramTotalGb) : null;
	$: utilPct = snap.utilPercent ?? 0;
	$: fillClass = vramBarFillClass(vramPct, threshold);
	$: utilClass = utilBarFillClass(utilPct);

	const fmt = (v: number | null) => (v === null ? '—' : v >= 10 ? v.toFixed(1) : v.toFixed(2));
</script>

{#if visible && vramPct !== null}
	<div
		class="pointer-events-auto relative z-20 h-1 w-full shrink-0 overflow-hidden bg-gray-200 dark:bg-gray-800"
		aria-label="VRAM {fmt(snap.vramUsedGb)}/{fmt(snap.vramTotalGb)} GB"
	>
		<div
			class="absolute inset-y-0 left-0 transition-[width] duration-500 ease-out {fillClass}"
			style:width="{vramPct}%"
		></div>
		<div
			class="absolute inset-y-0 left-0 transition-[width] duration-500 {utilClass}"
			style:width="{utilPct}%"
		></div>
		<span class="sr-only"
			>VRAM {fmt(snap.vramUsedGb)}/{fmt(snap.vramTotalGb)} GB, {utilPct}% utilisation</span
		>
	</div>
{/if}
