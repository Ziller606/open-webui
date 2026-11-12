from __future__ import annotations

from open_webui.nzila.bonsai_router import BonsaiRouterError, apply_bonsai_context

# Back-compat alias used by nzila router tests and callers
RouterCtxError = BonsaiRouterError

__all__ = ['RouterCtxError', 'apply_bonsai_context', 'BonsaiRouterError']
