# Updating Nzila custom Open WebUI

This fork layers **context slider + GPU meter** on upstream Open WebUI. Custom code is isolated under:

- `backend/open_webui/nzila/` and `backend/open_webui/routers/nzila.py`
- `src/lib/components/nzila/`, `src/lib/apis/nzila/`
- Small hooks in `main.py`, `env.py`, `Chat.svelte`, `Placeholder.svelte`, `(app)/+layout.svelte`

## Environment variables

| Variable | When set | Purpose |
|----------|----------|---------|
| `NZILA_SAFE_CTX_PATH` | Path to JSON file on the **host** (mount into the container) | Enables context slider + `GET /api/v1/nzila/safe-ctx` |
| `NZILA_GPU_STATS_URL` | Any value; empty string uses `http://127.0.0.1:8197` | Enables GPU meter + `GET /api/v1/nzila/gpu-stats` proxy |

Unset variables = upstream behaviour (no routes, no UI).

### `safe-ctx.json` schema (canonical)

```json
{
  "lfm-64k": {
    "safe_max": 131072,
    "tight_max": 196608,
    "hard_max": 262144,
    "fixed": false,
    "fixed_ctx": null
  },
  "bonsai-ternary-2-27b": {
    "safe_max": 8192,
    "tight_max": 8192,
    "hard_max": 8192,
    "fixed": true,
    "fixed_ctx": 8192
  }
}
```

**Accepted variants** (per model key): bare integer; `safe` / `max`; `tight` / `tight_max`; `hard` / `slider_max`; `fixed_context` (number) sets `fixed: true`. Optional wrapper `{"models": { ... }}`. See `GET /api/v1/nzila/safe-ctx/schema` when the feature is enabled.

## Rebase or cherry-pick onto a new upstream tag

```bash
git fetch origin --tags
git checkout v0.13.3   # or your current custom base
git pull

# Option A: rebase the custom branch onto a newer tag
git checkout nzila/custom-v0.13.3
git rebase v0.14.0   # replace with the target tag

# Option B: cherry-pick only the Nzila commits onto a fresh branch
git checkout -b nzila/custom-v0.14.0 v0.14.0
git cherry-pick <first-custom-commit>^..<last-custom-commit>
```

Resolve conflicts preferring upstream in unrelated files; keep `nzila/*` and the small integration hunks.

## Rebuild the image

```bash
chmod +x scripts/nzila-build.sh
./scripts/nzila-build.sh
# Produces open-webui:nzila-custom by default
```

Override: `NZILA_IMAGE_NAME=my-registry/open-webui:custom ./scripts/nzila-build.sh`

## Swap the running container (keep data volume)

Assume existing container `open-webui`, host networking, data at `open-webui` volume or bind mount.

```bash
docker stop open-webui
docker rm open-webui

docker run -d --name open-webui \
  --network host \
  --restart unless-stopped \
  -v open-webui:/app/backend/data \
  -v /path/on/host/safe-ctx.json:/config/safe-ctx.json:ro \
  -e NZILA_SAFE_CTX_PATH=/config/safe-ctx.json \
  -e NZILA_GPU_STATS_URL= \
  open-webui:nzila-custom
```

- Keep your existing `-v` / env vars (Ollama URLs, auth, etc.).
- `NZILA_GPU_STATS_URL=` (empty) uses default `http://127.0.0.1:8197` (works with `--network host` on the laptop).
- Remove the two `-e` / mount lines to return to stock behaviour while still running this image build.

```bash
docker start open-webui   # after first create, or to restart
docker logs -f open-webui
```
