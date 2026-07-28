from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.generation.serializers import GeneratedReportSerializer

from .selectors import dashboard_statistics


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = dashboard_statistics(request.user)
        stats["latest_reports"] = GeneratedReportSerializer(
            stats["latest_reports"], many=True, context={"request": request}
        ).data
        return Response(stats)
