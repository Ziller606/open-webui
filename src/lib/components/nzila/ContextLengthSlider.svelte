<script lang="ts">
	import { createEventDispatcher, onDestroy, onMount } from 'svelte';
	import type { Model } from '$lib/stores';
	import { models } from '$lib/stores';
	import {
		getNzilaSafeCtx,
		type NzilaSafeCtxEntry,
		type NzilaSafeCtxResponse
	} from '$lib/apis/nzila';

	const dispatch = createEventDispatcher<{ change: number }>();

	export let selectedModels: string[] = [];
	export let numCtx: number | null = null;
	export let disabled = false;

	const MIN_CTX = 2048;
	const STEP = 1024;
	const DEFAULT_MAX = 131072;

	let limits: Record<string, NzilaSafeCtxEntry> = {};
	let refreshTimer: ReturnType<typeof setInterval> | null = null;

	$: primaryId = selectedModels.find((id) => id && id.trim()) ?? '';
	$: model = $models.find((m: Model) => m.id === primaryId) ?? null;

	const resolveLimits = (modelId: string, all: Record<string, NzilaSafeCtxEntry>) => {
		if (all[modelId]) return all[modelId];
		const modelEntry = $models.find((m: Model) => m.id === modelId);
		const aliases = [
			modelEntry?.name,
			modelEntry?.id,
			(modelEntry as { model?: string })?.model
		].filter((v): v is string => !!v);
		for (const key of aliases) {
			if (all[key]) return all[key];
		}
		const tail = modelId.includes(':') ? modelId.split(':').pop() : modelId;
		const match = Object.entries(all).find(([key]) => key === tail || modelId.endsWith(key));
		return match?.[1] ?? null;
	};

	$: entry = primaryId ? resolveLimits(primaryId, limits) : null;
	$: sliderMax = entry?.hard_max ?? DEFAULT_MAX;
	$: sliderMin = MIN_CTX;
	$: safeEnd = entry ? (entry.safe_max / sliderMax) * 100 : 0;
	$: tightEnd = entry ? (entry.tight_max / sliderMax) * 100 : 0;
	$: isFixed = entry?.fixed === true;
	$: fixedValue = entry?.fixed_ctx ?? entry?.safe_max ?? numCtx ?? MIN_CTX;
	$: currentValue =
		numCtx !== null && numCtx > 0
			? Math.min(sliderMax, Math.max(sliderMin, numCtx))
			: entry?.safe_max ?? 8192;
	$: trackStyle = entry
		? `linear-gradient(to right,
			rgb(134 239 172) 0%,
			rgb(134 239 172) ${safeEnd}%,
			rgb(252 211 77) ${safeEnd}%,
			rgb(252 211 77) ${tightEnd}%,
			rgb(248 113 113) ${tightEnd}%,
			rgb(248 113 113) 100%)`
		: undefined;
	$: fillPct = ((currentValue - sliderMin) / Math.max(1, sliderMax - sliderMin)) * 100;

	const loadLimits = async () => {
		try {
			const res: NzilaSafeCtxResponse | null = await getNzilaSafeCtx(localStorage.token);
			if (res?.models) limits = res.models;
		} catch {
			/* keep last known limits */
		}
	};

	onMount(() => {
		void loadLimits();
		refreshTimer = setInterval(loadLimits, 5000);
	});

	onDestroy(() => {
		if (refreshTimer) clearInterval(refreshTimer);
	});

	const onInput = (event: Event) => {
		if (isFixed) return;
		const value = Number((event.currentTarget as HTMLInputElement).value);
		dispatch('change', value);
	};

	const formatCtx = (value: number) => {
		if (value >= 1024 && value % 1024 === 0) return `${value / 1024}k`;
		return String(value);
	};
</script>

{#if primaryId && model}
	<div
		class="mx-auto mb-1 w-full max-w-3xl px-3 sm:px-4"
		data-nzila-context-slider
	>
		<div class="flex items-center gap-3 rounded-xl border border-gray-100/80 bg-gray-50/50 px-3 py-2 dark:border-gray-800/80 dark:bg-gray-900/40">
			<div class="min-w-0 shrink-0 text-[0.6875rem] text-gray-500 dark:text-gray-400">
				Context
			</div>

			{#if isFixed}
				<div class="flex min-w-0 flex-1 items-center gap-2 text-[0.75rem] tabular-nums text-gray-700 dark:text-gray-200">
					<span>{formatCtx(fixedValue)}</span>
					<span class="truncate text-[0.6875rem] text-gray-400 dark:text-gray-500"
						>Fixed backend context (num_ctx ignored)</span
					>
				</div>
			{:else}
				<div class="relative flex min-w-0 flex-1 items-center gap-2">
					<input
						type="range"
						min={sliderMin}
						max={sliderMax}
						step={STEP}
						value={currentValue}
						{disabled}
						class="nzila-ctx-slider h-4 w-full cursor-pointer appearance-none rounded bg-gray-200/90 dark:bg-gray-800"
						style:background-image={trackStyle
							? `${trackStyle}, linear-gradient(to right, rgba(0,0,0,0.15) ${fillPct}%, transparent ${fillPct}%)`
							: `linear-gradient(to right, var(--color-gray-500) ${fillPct}%, transparent ${fillPct}%)`}
						aria-label="Context length"
						aria-valuemin={sliderMin}
						aria-valuemax={sliderMax}
						aria-valuenow={currentValue}
						on:input={onInput}
					/>
					<span class="w-12 shrink-0 text-right text-[0.75rem] tabular-nums text-gray-700 dark:text-gray-200">
						{formatCtx(currentValue)}
					</span>
				</div>
			{/if}
		</div>
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
