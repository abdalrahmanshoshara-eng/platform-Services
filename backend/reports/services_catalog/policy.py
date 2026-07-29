from dataclasses import dataclass

from django.db.models import Q
from django.utils import timezone

from reports.models import Service, UserCategoryRestriction, UserServiceRestriction


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str = ""
    code: str = ""


# Stable, UI/language-independent reason codes.
CODE_ALLOWED = "ALLOWED"
CODE_AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
CODE_ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
CODE_SERVICE_DISABLED = "SERVICE_DISABLED"
CODE_STAFF_ONLY = "STAFF_ONLY"
CODE_SERVICE_RESTRICTION = "SERVICE_RESTRICTION"
CODE_CATEGORY_RESTRICTION = "CATEGORY_RESTRICTION"


def _decide(service, user, service_restriction, category_restriction) -> AccessDecision:
    """Single source of truth for a service-access decision.

    Precedence: account disabled → service/category disabled → staff-only →
    direct service restriction → category restriction → allowed.
    """
    if not service.is_active or not service.category.is_active:
        return AccessDecision(False, "الخدمة غير متاحة حالياً.", CODE_SERVICE_DISABLED)
    if service.requires_staff and not user.is_staff:
        return AccessDecision(False, "هذه الخدمة مخصصة للمشرفين.", CODE_STAFF_ONLY)
    if service_restriction is not None:
        return AccessDecision(
            False,
            service_restriction.reason or "لا تملك صلاحية الوصول إلى هذه الخدمة.",
            CODE_SERVICE_RESTRICTION,
        )
    if category_restriction is not None:
        return AccessDecision(
            False,
            category_restriction.reason or "لا تملك صلاحية الوصول إلى هذه الفئة من الخدمات.",
            CODE_CATEGORY_RESTRICTION,
        )
    return AccessDecision(True, "", CODE_ALLOWED)


def access_decisions_for(user, services) -> dict:
    """Decide access for many services with a constant number of queries.

    Restrictions are fetched in two user-scoped queries (service-level and
    category-level), so callers that iterate a service list avoid an N+1.
    Expired restrictions are simply excluded by the active-window filter and
    are never deleted here.
    """
    services = list(services)
    if not getattr(user, "is_authenticated", False):
        reason = "سجّل الدخول لاستخدام هذه الخدمة."
        return {s.pk: AccessDecision(False, reason, CODE_AUTHENTICATION_REQUIRED) for s in services}
    if not user.is_active:
        reason = "حسابك معطّل حالياً."
        return {s.pk: AccessDecision(False, reason, CODE_ACCOUNT_DISABLED) for s in services}
    if not services:
        return {}

    now = timezone.now()
    service_ids = [s.pk for s in services]
    category_ids = {s.category_id for s in services}

    service_window = (Q(starts_at__isnull=True) | Q(starts_at__lte=now)) & (
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )
    service_restrictions = {
        r.service_id: r
        for r in UserServiceRestriction.objects.filter(service_window, user=user, service_id__in=service_ids)
    }

    category_window = Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    category_restrictions = {
        r.category_id: r
        for r in UserCategoryRestriction.objects.filter(category_window, user=user, category_id__in=category_ids)
    }

    return {
        service.pk: _decide(
            service,
            user,
            service_restrictions.get(service.pk),
            category_restrictions.get(service.category_id),
        )
        for service in services
    }


def service_access_for(user, service: Service) -> AccessDecision:
    """Centralized single-service access decision (accounts for account state,
    service/category status, and both direct and category restrictions)."""
    return access_decisions_for(user, [service])[service.pk]
