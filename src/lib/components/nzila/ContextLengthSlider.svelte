<script lang="ts">
	import { createEventDispatcher, onDestroy, onMount } from 'svelte';
	import type { Model } from '$lib/stores';
	import { models } from '$lib/stores';
	import { nzilaGpu } from '$lib/stores/nzilaGpu';
	import {
		getNzilaModelFit,
		getNzilaSafeCtx,
		setNzilaBonsaiContext,
		type NzilaSafeCtxEntry
	} from '$lib/apis/nzila';
	import {
		computeFitLimits,
		formatCtx,
		type FitLimits,
		type ModelFitHints
	} from '$lib/utils/nzila/fit';

	type ReleasedDetail = { modelId: string; ctx: number; bonsai: boolean };

	const dispatch = createEventDispatcher<{ release: ReleasedDetail }>();

	export let selectedModels: string[] = [];
	export let modelContexts: Record<string, number> = {};
	export let disabled = false;
	const MIN_CTX = 2048;
	const STEP = 1024;
	const DEFAULT_MAX = 131072;

	let safeLimits: Record<string, NzilaSafeCtxEntry> = {};
	let fitCache: Record<string, FitLimits> = {};
	let draft: Record<string, number> = {};
	let reloading: Record<string, boolean> = {};
	let refreshTimer: ReturnType<typeof setInterval> | null = null;

	$: modelIds = selectedModels.map((id) => id?.trim()).filter(Boolean);
	$: gpuStats = $nzilaGpu.stats;

	const resolveSafeEntry = (modelId: string) => {
		if (safeLimits[modelId]) return safeLimits[modelId];
		const model = $models.find((m: Model) => m.id === modelId);
		const aliases = [model?.name, model?.id, (model as { model?: string })?.model].filter(Boolean) as string[];
		for (const key of aliases) {
			if (safeLimits[key]) return safeLimits[key];
		}
		const tail = modelId.includes(':') ? modelId.split(':').pop()! : modelId;
		const match = Object.entries(safeLimits).find(([key]) => key === tail || modelId.endsWith(key));
		return match?.[1];
	};

	const hintsForModel = (modelId: string): ModelFitHints => {
		const model = $models.find((m: Model) => m.id === modelId) as Model & { size?: number; details?: { parameter_size?: string } };
		return {
			sizeBytes: model?.size ?? null,
			parameterSize: model?.details?.parameter_size ?? model?.info?.meta?.params?.parameter_size ?? null
		};
	};

	const limitsFor = (modelId: string): FitLimits => {
		if (fitCache[modelId]) return fitCache[modelId];
		const override = resolveSafeEntry(modelId);
		const metaBonsai = !!$models.find((m) => m.id === modelId)?.info?.meta?.nzila_bonsai;
		const merged = computeFitLimits(hintsForModel(modelId), gpuStats, {
			...(override ?? {}),
			bonsai: override?.bonsai ?? metaBonsai
		});
		return merged;
	};

	const refreshFit = async () => {
		for (const modelId of modelIds) {
			const remote = await getNzilaModelFit(localStorage.token, modelId).catch(() => null);
			if (remote) fitCache = { ...fitCache, [modelId]: remote };
			else fitCache = { ...fitCache, [modelId]: limitsFor(modelId) };
		}
		fitCache = { ...fitCache };
	};

	const loadSafeLimits = async () => {
		const res = await getNzilaSafeCtx(localStorage.token).catch(() => null);
		if (res?.models) safeLimits = res.models;
	};

	onMount(() => {
		void loadSafeLimits();
		void refreshFit();
		refreshTimer = setInterval(() => {
			void loadSafeLimits();
			void refreshFit();
		}, 8000);
	});

	onDestroy(() => {
		if (refreshTimer) clearInterval(refreshTimer);
	});

	$: if (modelIds.length && gpuStats) {
		fitCache = Object.fromEntries(modelIds.map((id) => [id, limitsFor(id)]));
	}

	const displayValue = (modelId: string) =>
		draft[modelId] ??
		modelContexts[modelId] ??
		fitCache[modelId]?.safe_max ??
		8192;

	const trackStyle = (limits: FitLimits) => {
		const sliderMax = limits.hard_max || DEFAULT_MAX;
		const safeEnd = (limits.safe_max / sliderMax) * 100;
		const tightEnd = (limits.tight_max / sliderMax) * 100;
		return `linear-gradient(to right,
			rgb(134 239 172) 0%,
			rgb(134 239 172) ${safeEnd}%,
			rgb(252 211 77) ${safeEnd}%,
			rgb(252 211 77) ${tightEnd}%,
			rgb(248 113 113) ${tightEnd}%,
			rgb(248 113 113) 100%)`;
	};

	const onInput = (modelId: string, event: Event) => {
		const value = Number((event.currentTarget as HTMLInputElement).value);
		draft = { ...draft, [modelId]: value };
	};

	const onRelease = async (modelId: string, limits: FitLimits) => {
		const value = Math.min(limits.hard_max, Math.max(MIN_CTX, displayValue(modelId)));
		draft = { ...draft, [modelId]: value };
		const bonsai = !!limits.bonsai;
		if (bonsai) {
			reloading = { ...reloading, [modelId]: true };
			try {
				await setNzilaBonsaiContext(localStorage.token, modelId, value);
			} catch (err) {
				console.error(err);
			} finally {
				reloading = { ...reloading, [modelId]: false };
			}
		}
		dispatch('release', { modelId, ctx: value, bonsai });
		delete draft[modelId];
	};
</script>

{#if modelIds.length > 0}
	<div class="mx-auto mb-1 w-full max-w-3xl space-y-1 px-3 sm:px-4" data-nzila-context-slider>
		{#each modelIds as modelId (modelId)}
			{@const limits = fitCache[modelId] ?? limitsFor(modelId)}
			{@const sliderMax = limits.hard_max ?? DEFAULT_MAX}
			{@const current = displayValue(modelId)}
			{@const fillPct = ((current - MIN_CTX) / Math.max(1, sliderMax - MIN_CTX)) * 100}
			{@const model = $models.find((m) => m.id === modelId)}
			<div
				class="flex items-center gap-3 rounded-xl border border-gray-100/80 bg-gray-50/50 px-3 py-2 dark:border-gray-800/80 dark:bg-gray-900/40"
			>
				<div class="min-w-0 max-w-[28%] shrink-0 truncate text-[0.6875rem] text-gray-500 dark:text-gray-400">
					{model?.name ?? modelId}
				</div>

				{#if reloading[modelId]}
					<div class="flex-1 text-[0.75rem] text-gray-500 dark:text-gray-400">Reloading model…</div>
				{:else}
					<div class="relative flex min-w-0 flex-1 items-center gap-2">
						<input
							type="range"
							min={MIN_CTX}
							max={sliderMax}
							step={STEP}
							value={current}
							{disabled}
							class="nzila-ctx-slider h-4 w-full cursor-pointer appearance-none rounded bg-gray-200/90 dark:bg-gray-800"
							style:background-image={`${trackStyle(limits)}, linear-gradient(to right, rgba(0,0,0,0.12) ${fillPct}%, transparent ${fillPct}%)`}
							aria-label="Context length for {modelId}"
							on:input={(e) => onInput(modelId, e)}
							on:change={() => onRelease(modelId, limits)}
						/>
						<span
							class="w-12 shrink-0 text-right text-[0.75rem] tabular-nums text-gray-700 dark:text-gray-200"
						>
							{formatCtx(current)}
						</span>
					</div>
				{/if}
			</div>
		{/each}
	</div>
{/if}

<style>
	.nzila-ctx-slider::-webkit-slider-thumb {
		appearance: none;
		width: 0.875rem;
		height: 0.875rem;
		border-radius: 9999px;
		background: white;
		box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.12);
	}
	.nzila-ctx-slider::-moz-range-thumb {
		width: 0.875rem;
		height: 0.875rem;
		border: 0;
		border-radius: 9999px;
		background: white;
		box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.12);
	}
</style>
