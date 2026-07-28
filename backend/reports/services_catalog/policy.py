from dataclasses import dataclass

from django.db.models import Q
from django.utils import timezone

from reports.models import Service


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str = ""


def service_access_for(user, service: Service) -> AccessDecision:
    if not service.is_active or not service.category.is_active:
        return AccessDecision(False, "الخدمة غير متاحة حالياً.")
    if service.requires_staff and not user.is_staff:
        return AccessDecision(False, "هذه الخدمة مخصصة للمشرفين.")

    now = timezone.now()
    active = (Q(starts_at__isnull=True) | Q(starts_at__lte=now)) & (
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )
    service_restriction = service.user_restrictions.filter(active, user=user).first()
    if service_restriction:
        return AccessDecision(False, service_restriction.reason or "لا تملك صلاحية الوصول إلى هذه الخدمة.")

    return AccessDecision(True)
