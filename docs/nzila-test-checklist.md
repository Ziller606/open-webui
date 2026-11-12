# Nzila local GPU — manual UI checklist

Run on your machine with `NZILA_*` env vars set and after `./scripts/nzila-smoke.sh` passes.

## Visual

- [ ] GPU top bar is grey/black (light/dark) until VRAM red zone; turns red only above **VRAM red zone %** in Settings → Local GPU.
- [ ] Context slider track is monochrome (no green/amber); red segment only in overflow / VRAM red zone.
- [ ] GPU header chip matches Open WebUI borders, typography, and dark mode.

## GPU chip popover

- [ ] Lists models from Ollama and/or Bonsai (router `GET /models`) with VRAM MB when available.
- [ ] **Unload** removes one model; **Free GPU** clears all.
- [ ] Countdown **Frees in m:ss** matches Ollama `expires_at` and resets after you send a reply (keep_alive refresh).
- [ ] After each poll, countdown stays aligned (no drift without resync).

## Toasts (Settings → Local GPU → Model load toasts)

- [ ] Send a prompt: **Loading &lt;model&gt;…** then **Loaded in X.Xs** on first token.
- [ ] Change selected model: **Switched to &lt;model&gt;**.
- [ ] Unload from popover: **Unloaded &lt;model&gt;, GPU freed (N MB)** when VRAM known.

## Settings

- [ ] Toggles use the standard **Switch** control (not raw checkboxes).
- [ ] Red zone %, toasts, and countdown toggles persist after reload.

## Scripts

```bash
export NZILA_SMOKE_BASE_URL="https://your-open-webui"
export NZILA_SMOKE_TOKEN="your-jwt"
chmod +x scripts/nzila-smoke.sh
./scripts/nzila-smoke.sh
```

Optional unload smoke (will evict models):

```bash
curl -X POST -H "Authorization: Bearer $NZILA_SMOKE_TOKEN" \
  "$NZILA_SMOKE_BASE_URL/api/v1/nzila/unload-all"
```
