<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { nzilaGpu, refreshNzilaGpu } from '$lib/stores/nzilaGpu';
	import { settings } from '$lib/stores';
	import { readNzilaSettings } from '$lib/utils/nzila/defaults';
	import { nzilaUnloadAll, nzilaUnloadModel } from '$lib/apis/nzila';
	import { nzilaLastLoadSeconds, nzilaOnUnload } from '$lib/utils/nzila/lifecycle';
	import {
		formatCountdownMmSs,
		parseExpiresAtMs,
		secondsRemaining,
		soonestExpiryMs
	} from '$lib/utils/nzila/countdown';
	import { isVramRedZone, vramPercent } from '$lib/utils/nzila/redzone';
	import { toast } from 'svelte-sonner';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	export let enabled = false;

	let show = false;
	let now = Date.now();
	let tickTimer: ReturnType<typeof setInterval> | null = null;
	let unloading: Record<string, boolean> = {};
	let freeingAll = false;

	$: snap = $nzilaGpu;
	$: nzila = readNzilaSettings($settings);
	$: threshold = nzila.vramRedZonePercent ?? 90;
	$: visible =
		enabled &&
		(snap.utilPercent !== null || snap.vramUsedGb !== null || snap.vramTotalGb !== null);
	$: vramPct = vramPercent(snap.vramUsedGb, snap.vramTotalGb);
	$: inRed = isVramRedZone(vramPct, threshold);
	$: soonestMs =
		snap.loadedModels.length > 0 && nzila.showGpuCountdown
			? soonestExpiryMs(
					snap.loadedModels.map((m) => m.expiresAt),
					now
				)
			: null;
	$: countdownSec =
		nzila.showGpuCountdown && soonestMs !== null ? secondsRemaining(soonestMs, now) : null;
	$: countdownLabel =
		countdownSec !== null && countdownSec > 0 ? formatCountdownMmSs(countdownSec) : null;

	const fmtGb = (value: number | null) => {
		if (value === null) return '—';
		if (value >= 10) return value.toFixed(1);
		return value.toFixed(2);
	};

	const shortModel = (id: string) => (id.length > 28 ? `${id.slice(0, 26)}…` : id);

	const vramMb = (bytes: number | null) => (bytes === null ? null : bytes / (1024 * 1024));

	const unloadOne = async (modelId: string) => {
		const entry = snap.loadedModels.find((m) => m.model === modelId);
		const freedMb = vramMb(entry?.sizeVramBytes ?? null);
		unloading = { ...unloading, [modelId]: true };
		try {
			await nzilaUnloadModel(localStorage.token, modelId);
			nzilaOnUnload(modelId, shortModel(modelId), freedMb);
			refreshNzilaGpu();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to unload model');
		} finally {
			unloading = { ...unloading, [modelId]: false };
		}
	};

	const freeGpu = async () => {
		freeingAll = true;
		try {
			await nzilaUnloadAll(localStorage.token);
			nzilaOnUnload('all', 'all models', null);
			refreshNzilaGpu();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to free GPU');
		} finally {
			freeingAll = false;
		}
	};

	const modelCountdown = (expiresAt: string | null) => {
		if (!nzila.showGpuCountdown || !expiresAt) return null;
		const ms = parseExpiresAtMs(expiresAt);
		if (ms === null) return null;
		const sec = secondsRemaining(ms, now);
		return sec > 0 ? formatCountdownMmSs(sec) : null;
	};

	onMount(() => {
		tickTimer = setInterval(() => {
			now = Date.now();
		}, 1000);
	});

	onDestroy(() => {
		if (tickTimer) clearInterval(tickTimer);
	});
</script>

{#if enabled && visible}
	<Dropdown bind:show side="bottom" align="end">
		<Tooltip content="GPU memory and loaded models">
			<button
				type="button"
				class="flex items-center gap-2 rounded-lg border px-2 py-0.5 text-[0.6875rem] tabular-nums tracking-tight transition-colors
					{inRed
					? 'border-red-300/70 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200'
					: 'border-gray-200/80 bg-white/90 text-gray-700 dark:border-gray-800 dark:bg-gray-900/90 dark:text-gray-200'}"
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
				{#if countdownLabel}
					<span class="text-gray-500 dark:text-gray-400">· frees {countdownLabel}</span>
				{/if}
			</button>
		</Tooltip>

		<div
			slot="content"
			class="w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-gray-200 bg-white p-2 text-xs text-gray-800 shadow-lg dark:border-gray-800 dark:bg-gray-850 dark:text-gray-100"
		>
			<div class="mb-2 flex items-center justify-between gap-2 px-1">
				<span class="font-medium text-gray-700 dark:text-gray-200">GPU</span>
				{#if countdownLabel}
					<span class="tabular-nums text-gray-500 dark:text-gray-400">Frees in {countdownLabel}</span>
				{/if}
			</div>

			{#if snap.loadedModels.length === 0}
				<p class="px-1 py-2 text-gray-500 dark:text-gray-400">No models loaded in VRAM.</p>
			{:else}
				<ul class="max-h-56 overflow-y-auto">
					{#each snap.loadedModels as row (row.model)}
						<li class="flex items-start gap-2 border-t border-gray-100 py-2 first:border-0 dark:border-gray-800">
							<div class="min-w-0 flex-1">
								<p class="truncate font-medium">{shortModel(row.model)}</p>
								<p class="text-[0.6875rem] text-gray-500 dark:text-gray-400">
									{#if row.sizeVramBytes !== null}{Math.round(row.sizeVramBytes / (1024 * 1024))} MB VRAM · {/if}
									{row.source}
									{#if modelCountdown(row.expiresAt)}
										· GPU frees in {modelCountdown(row.expiresAt)}
									{/if}
									{#if nzilaLastLoadSeconds.has(row.model)}
										· last load {nzilaLastLoadSeconds.get(row.model)?.toFixed(1)}s
									{/if}
								</p>
							</div>
							<button
								type="button"
								class="shrink-0 rounded-lg border border-gray-200 px-2 py-0.5 text-[0.6875rem] hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:hover:bg-gray-800"
								disabled={!!unloading[row.model]}
								on:click|stopPropagation={() => unloadOne(row.model)}
							>
								{unloading[row.model] ? '…' : 'Unload'}
							</button>
						</li>
					{/each}
				</ul>
			{/if}

			<div class="mt-2 border-t border-gray-100 pt-2 dark:border-gray-800">
				<button
					type="button"
					class="w-full rounded-lg border border-gray-200 px-2 py-1.5 text-xs font-medium hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:hover:bg-gray-800"
					disabled={freeingAll || snap.loadedModels.length === 0}
					on:click|stopPropagation={freeGpu}
				>
					{freeingAll ? 'Freeing GPU…' : 'Free GPU'}
				</button>
			</div>
		</div>
	</Dropdown>
{/if}
