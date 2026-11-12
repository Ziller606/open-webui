# Updating Nzila custom Open WebUI

Custom code lives under:

- `backend/open_webui/nzila/` and `backend/open_webui/routers/nzila.py`
- `src/lib/components/nzila/`, `src/lib/apis/nzila/`, `src/lib/utils/nzila/`
- Small hooks in `main.py`, `env.py`, `Chat.svelte`, `Placeholder.svelte`, `(app)/+layout.svelte`, `SettingsModal.svelte`

## Environment variables

| Variable | When set | Purpose |
|----------|----------|---------|
| `NZILA_SAFE_CTX_PATH` | Path to JSON on the host (mount read-only into the container) | Per-model overrides + fit hints; optional if you rely on live GPU estimates only |
| `NZILA_GPU_STATS_URL` | Present in env (`=` alone → `http://127.0.0.1:8197`) | GPU meter, top bar, dynamic fit colouring |
| `NZILA_BONSAI_ROUTER_URL` | Present in env (`=` alone → `http://127.0.0.1:8096`) | llama-server **router mode** (`GET/POST /models`, `POST /models/load`, `POST /models/unload`) |
| `NZILA_BONSAI_PRESET_PATH` | Path to `webui-models.ini` (read-write mount) | Live context: rewrite `ctx-size`, then unload/load via router |
| `NZILA_BONSAI_IDLE_SECONDS` | Optional (default `300`) | Bonsai GPU countdown when `/props` does not expose sleep idle |

Unset **all three** → stock Open WebUI (no `/api/v1/nzila/*`, no Local GPU UI).

Recommended host file: `~/.config/open-webui/safe-ctx.nzila.json` mounted at `/config/safe-ctx.nzila.json`.

### `safe-ctx.json` (canonical entry)

```json
{
  "lfm-1.7b": {
    "safe_max": 65536,
    "tight_max": 98304,
    "hard_max": 131072,
    "bonsai": false
  },
  "bonsai-32k": {
    "safe_max": 32768,
    "tight_max": 32768,
    "hard_max": 32768,
    "bonsai": true
  }
}
```

See also `docs/nzila-safe-ctx.example.json` and `docs/nzila-router-ctx-api.md`.

## Rebase or cherry-pick onto a new upstream tag

```bash
git fetch origin --tags
git checkout nzila/custom-v0.13.3

# Rebase onto newer tag
git rebase v0.14.0

# Or cherry-pick onto a fresh branch
git checkout -b nzila/custom-v0.14.0 v0.14.0
git cherry-pick <first-custom-commit>^..<last-custom-commit>
```

## Rebuild

```bash
chmod +x scripts/nzila-build.sh
./scripts/nzila-build.sh
```

## Swap container (keep data + secret key)

```bash
# Preserve auth/session signing key from the running container
docker cp open-webui:/app/backend/.webui_secret_key /tmp/.webui_secret_key

docker stop open-webui
docker rm open-webui

docker run -d --name open-webui \
  --network host \
  --restart unless-stopped \
  -v open-webui:/app/backend/data \
  -v /tmp/.webui_secret_key:/app/backend/.webui_secret_key:ro \
  -v "$HOME/.config/open-webui/safe-ctx.nzila.json:/config/safe-ctx.nzila.json:ro" \
  -e NZILA_SAFE_CTX_PATH=/config/safe-ctx.nzila.json \
  -e NZILA_GPU_STATS_URL= \
  -e NZILA_BONSAI_ROUTER_URL= \
  open-webui:nzila-custom
```

- Keep your existing Ollama URL, auth, and volume mounts.
- `NZILA_GPU_STATS_URL=` and `NZILA_BONSAI_ROUTER_URL=` use defaults on host networking (`127.0.0.1:8197`, `127.0.0.1:8096`).
- Remove the Nzila `-e` / mount lines to disable features without changing image.

```bash
docker logs -f open-webui
```

## User settings

**Settings → Local GPU** stores per-user preferences under `settings.nzila` (GPU bar, meter, slider, polling, default context per model, tok/s display). Requires `nzila_local_gpu` from the server config (any Nzila env var above).
