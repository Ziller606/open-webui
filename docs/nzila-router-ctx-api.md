# Nzila Bonsai — llama-server router mode

`NZILA_BONSAI_ROUTER_URL` points at **llama.cpp `llama-server` in router mode**, for example:

```bash
llama-server \
  --models-preset ~/.config/bonsai/webui-models.ini \
  --models-max 1 \
  --sleep-idle-seconds 300 \
  --metrics
```

Default base URL when the env var is set but empty: `http://127.0.0.1:8096` (no `/v1` suffix).

There is **no separate Bonsai router service**. Open WebUI calls the native HTTP API documented in the [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).

## Preset INI (`NZILA_BONSAI_PRESET_PATH`)

Mount `webui-models.ini` **read-write** when you want live context changes from the slider. Open WebUI writes `ctx-size=` for the model section and keeps `webui-models.ini.bak` beside it.

Example section:

```ini
[bonsai-32k]
model=/path/to/model.gguf
n-gpu-layers=99
ctx-size=32768
```

Match is by section name or `model=` / `alias=` within the section.

| Env | Purpose |
|-----|---------|
| `NZILA_BONSAI_ROUTER_URL` | Router `llama-server` base URL |
| `NZILA_BONSAI_PRESET_PATH` | Host path to `webui-models.ini` (required for slider ctx reload) |
| `NZILA_BONSAI_IDLE_SECONDS` | Fallback idle countdown if `/props` has no sleep value (default **300**) |

## Upstream endpoints

### `GET /models`

Lists models and status. Loaded VRAM entries use `memory.effective` (bytes) when present.

Statuses treated as loaded: `loaded`, `sleeping`; also `loading` for the UI list.

### `POST /models/unload`

```json
{ "model": "<model-id>" }
```

Open WebUI proxy: `POST /api/v1/nzila/unload/{model_id}` for Bonsai models.

### `POST /models/load`

```json
{ "model": "<model-id>" }
```

Native load does **not** accept a per-request `ctx-size` override; context comes from the preset.

### `GET /props`

Optional: read `sleep-idle-seconds` for countdown accuracy. Per-model: `GET /props?model=<id>`.

## Open WebUI proxies

| Proxy | Behaviour |
|-------|-----------|
| `GET /api/v1/nzila/loaded` | Ollama `GET /api/ps` + router `GET /models` (merged) |
| `POST /api/v1/nzila/unload/{id}` | Ollama `keep_alive: 0` or `POST /models/unload` |
| `POST /api/v1/nzila/unload-all` | Unloads everything reported loaded |
| `POST /api/v1/nzila/ctx/{id}` | Patch preset `ctx-size`, `POST /models/unload` if running, `POST /models/load` |
| `POST /api/v1/nzila/activity/{id}` | Resets Bonsai idle countdown after chat (pairs with `sleep-idle-seconds`) |

## Countdown UX

- **Ollama**: `expires_at` from `/api/ps` (keep_alive).
- **Bonsai**: `expires_at ≈ last_activity + sleep_idle_seconds`. Activity is updated when the user gets a first token or completes a reply (`/activity`), and when the model is newly seen as loaded or reloaded after a ctx change.

Polling `/loaded` re-syncs the countdown; GET `/models` and GET `/props` do not reset the idle timer on the server.
