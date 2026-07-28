"""Recording + querying audit events. Only safe metadata is stored."""

import logging

from reports.models import AuditEvent
from reports.shared.correlation import get_correlation_id

logger = logging.getLogger("reports.audit")


def _client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record(action, *, actor=None, request=None, target=None, outcome="success", metadata=None):
    target_type, target_id = "", ""
    if target is not None:
        target_type = target.__class__.__name__
        target_id = str(getattr(target, "pk", "") or "")
    try:
        return AuditEvent.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            outcome=outcome,
            request_id=get_correlation_id() or "",
            ip_address=_client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT", "")[:400] if request else ""),
            metadata=metadata or {},
        )
    except Exception:  # audit must never break the request
        logger.exception("failed to record audit event %s", action)
        return None
