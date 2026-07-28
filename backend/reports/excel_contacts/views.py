import base64

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .application import ProcessExcelContactsUseCase
from .serializers import ExcelContactsInputSerializer


class ExcelContactsProcessView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "excel_contacts"

    def post(self, request):
        serializer = ExcelContactsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ProcessExcelContactsUseCase().execute(
            user=request.user,
            uploaded_file=serializer.validated_data["file"],
            country_code=serializer.validated_data["countryCode"],
            request=request,
        )
        response = Response(
            {
                "fileName": result.file_name,
                "zipBase64": base64.b64encode(result.zip_buffer).decode("ascii"),
                "summary": result.summary,
                "sourceSheetName": result.source_sheet_name,
                "previews": result.previews,
            }
        )
        response["Cache-Control"] = "no-store"
        return response
