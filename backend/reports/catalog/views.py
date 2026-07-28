from rest_framework import viewsets

from reports.shared.permissions import IsAdminOrReadOnly

from .selectors import visible_report_types
from .serializers import ReportTypeSerializer


class ReportTypeViewSet(viewsets.ModelViewSet):
    serializer_class = ReportTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        return visible_report_types(self.request.user)
