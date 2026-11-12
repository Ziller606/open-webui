<script lang="ts">
	import { config, models, settings, user } from '$lib/stores';
	import { mergeNzilaSettings, readNzilaSettings, type NzilaUserSettings } from '$lib/utils/nzila/defaults';
	import { computeFitLimits, fitZone } from '$lib/utils/nzila/fit';
	import { nzilaGpu } from '$lib/stores/nzilaGpu';
	import UserSettingRow from './UserSettingRow.svelte';
	import UserSettingSection from './UserSettingSection.svelte';

	export let saveSettings: (updated: Record<string, unknown>) => Promise<void>;

	let nzila: NzilaUserSettings = mergeNzilaSettings();

	$: nzila = readNzilaSettings($settings);
	$: gpuSnap = $nzilaGpu;

	const persist = async (patch: Partial<NzilaUserSettings>) => {
		const merged = mergeNzilaSettings({ ...nzila, ...patch });
		nzila = merged;
		await saveSettings({ nzila: merged });
	};

	const setDefaultCtx = async (modelId: string, value: number) => {
		const next = {
			...nzila.defaultContextByModel,
			[modelId]: value
		};
		await persist({ defaultContextByModel: next });
	};

	const zoneLabel = (modelId: string, ctx: number) => {
		const model = $models.find((m) => m.id === modelId);
		const limits = computeFitLimits(
			{
				sizeBytes: (model as { size?: number })?.size,
				parameterSize: (model as { details?: { parameter_size?: string } })?.details?.parameter_size
			},
			gpuSnap.stats
		);
		const zone = fitZone(ctx, limits);
		if (zone === 'safe') return 'Fits';
		if (zone === 'tight') return 'Tight';
		return "Won't fit";
	};

	$: ollamaModels = ($models ?? []).filter((m) => m.id);
</script>

<UserSettingSection title="Local GPU">
	{#if !$config?.features?.nzila_local_gpu}
		<p class="px-1 text-xs text-gray-500 dark:text-gray-400">
			Enable server env vars (`NZILA_GPU_STATS_URL`, `NZILA_SAFE_CTX_PATH`, and/or
			`NZILA_BONSAI_ROUTER_URL`) and rebuild to use these controls.
		</p>
	{:else}
		<UserSettingRow label="GPU top bar" description="Thin VRAM bar across the top of chat">
			<input
				type="checkbox"
				class="size-4 rounded border-gray-300"
				checked={nzila.showGpuTopBar}
				on:change={(e) => persist({ showGpuTopBar: e.currentTarget.checked })}
			/>
		</UserSettingRow>
		<UserSettingRow label="GPU meter" description="Percent and VRAM chip in the header">
			<input
				type="checkbox"
				class="size-4 rounded border-gray-300"
				checked={nzila.showGpuMeter}
				on:change={(e) => persist({ showGpuMeter: e.currentTarget.checked })}
			/>
		</UserSettingRow>
		<UserSettingRow label="Context slider" description="Per-model context controls in chat">
			<input
				type="checkbox"
				class="size-4 rounded border-gray-300"
				checked={nzila.showContextSlider}
				on:change={(e) => persist({ showContextSlider: e.currentTarget.checked })}
			/>
		</UserSettingRow>
		<UserSettingRow label="Polling interval (ms)">
			<input
				type="number"
				min="1000"
				max="10000"
				step="500"
				class="w-24 rounded-lg border border-gray-200 bg-white px-2 py-1 text-xs dark:border-gray-700 dark:bg-gray-900"
				value={nzila.pollIntervalMs}
				on:change={(e) => persist({ pollIntervalMs: Number(e.currentTarget.value) || 2000 })}
			/>
		</UserSettingRow>
		<UserSettingRow
			label="Apply context live"
			description="Save context to the chat when you release the slider"
		>
			<input
				type="checkbox"
				class="size-4 rounded border-gray-300"
				checked={nzila.applyContextLive}
				on:change={(e) => persist({ applyContextLive: e.currentTarget.checked })}
			/>
		</UserSettingRow>
		<UserSettingRow
			label="Show tok/s under replies"
			description="Uses Ollama eval_count and eval_duration on each assistant message (no extra metadata yet)"
		>
			<input
				type="checkbox"
				class="size-4 rounded border-gray-300"
				checked={nzila.showToksPerSec}
				on:change={(e) => persist({ showToksPerSec: e.currentTarget.checked })}
			/>
		</UserSettingRow>

		<div class="mt-4">
			<h3 class="mb-2 px-1 text-xs font-medium text-gray-700 dark:text-gray-200">Default context</h3>
			<div class="max-h-64 overflow-y-auto rounded-lg border border-gray-100 dark:border-gray-800">
				<table class="w-full text-left text-[0.6875rem]">
					<thead class="sticky top-0 bg-gray-50 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
						<tr>
							<th class="px-2 py-1 font-normal">Model</th>
							<th class="px-2 py-1 font-normal">Context</th>
							<th class="px-2 py-1 font-normal">Fit</th>
						</tr>
					</thead>
					<tbody>
						{#each ollamaModels as model (model.id)}
							{@const ctx = nzila.defaultContextByModel[model.id] ?? 8192}
							<tr class="border-t border-gray-100 dark:border-gray-800">
								<td class="max-w-[10rem] truncate px-2 py-1">{model.name ?? model.id}</td>
								<td class="px-2 py-1">
									<input
										type="number"
										min="2048"
										step="1024"
										class="w-20 rounded border border-gray-200 bg-white px-1 py-0.5 dark:border-gray-700 dark:bg-gray-900"
										value={ctx}
										on:change={(e) => setDefaultCtx(model.id, Number(e.currentTarget.value))}
									/>
								</td>
								<td class="px-2 py-1 text-gray-500">{zoneLabel(model.id, ctx)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		{#if $user?.role === 'admin'}
			<div class="mt-4 px-1 text-[0.6875rem] text-gray-500 dark:text-gray-400">
				<p class="font-medium text-gray-600 dark:text-gray-300">Server paths (read-only)</p>
				<p>Safe ctx: {($config as { nzila?: { safe_ctx?: boolean } }).nzila?.safe_ctx ? 'mounted' : 'not set'}</p>
				<p>
					Bonsai router: {$config?.features?.nzila_bonsai_router ? 'enabled' : 'not set'}
				</p>
			</div>
		{/if}
	{/if}
</UserSettingSection>
