from rest_framework import serializers


class ExcelContactsInputSerializer(serializers.Serializer):
    file = serializers.FileField(allow_empty_file=True)
    countryCode = serializers.CharField(default="963", max_length=4, required=False)
