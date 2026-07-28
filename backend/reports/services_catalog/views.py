from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from reports.audit.service import record
from reports.models import Service

from .policy import service_access_for
from .serializers import ServiceSerializer


class ServiceViewSet(ReadOnlyModelViewSet):
    serializer_class = ServiceSerializer
    pagination_class = None
    lookup_field = "slug"

    def get_queryset(self):
        # Access decisions are computed in a constant number of user-scoped
        # queries by the policy layer, so no per-service restriction prefetch is
        # needed here (category is select_related for the disabled-category check).
        return Service.objects.filter(is_active=True, category__is_active=True).select_related("category")

    @action(detail=True, methods=["post"])
    def launch(self, request, slug=None):
        service = self.get_object()
        decision = service_access_for(request.user, service)
        if not decision.allowed:
            record(
                "service.launch",
                actor=request.user,
                request=request,
                target=service,
                outcome="denied",
                metadata={"service": service.slug},
            )
            return Response(
                {"message": decision.reason, "code": "SERVICE_ACCESS_DENIED"},
                status=status.HTTP_403_FORBIDDEN,
            )

        record(
            "service.launch",
            actor=request.user,
            request=request,
            target=service,
            metadata={"service": service.slug, "kind": service.kind},
        )
        return Response({"target": service.launch_target, "kind": service.kind})
