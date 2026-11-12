# Nzila Bonsai router — live context API

Open WebUI calls this when the user releases the context slider on a **Bonsai** model (`NZILA_BONSAI_ROUTER_URL` set, model marked `bonsai: true` in `safe-ctx.json` or `meta.nzila_bonsai` on the model).

## Endpoint

`POST {NZILA_BONSAI_ROUTER_URL}/admin/ctx`

Default router base: `http://127.0.0.1:8096` (no `/v1` suffix).

### Request body

```json
{
  "model": "<model-id>",
  "ctx": 32768
}
```

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Router model id (same as Open WebUI model id, or alias your router expects) |
| `ctx` | integer | New context size in **tokens** |

### Expected behaviour

1. Unload/reload the named llama-server instance with the new `--ctx-size` (or equivalent).
2. Return JSON when done, e.g. `{"status": "ok", "model": "...", "ctx": 32768}`.
3. On failure, non-2xx HTTP with a JSON `detail` or plain-text body (proxied to the UI).

### Open WebUI proxy

`POST /api/v1/nzila/ctx/{model_id}` with body `{"ctx": n}` forwards to the router as above, with `model` set to `{model_id}`.

Requires env `NZILA_BONSAI_ROUTER_URL` (empty value → default `http://127.0.0.1:8096`).

## Client UX

- Slider updates a local value while dragging; **apply on release** only.
- While the proxy request is in flight the row shows **Reloading model…**
- Ollama models skip this endpoint; they use chat `num_ctx` on the next completion instead.
