from rest_framework import serializers

from reports.models import Service, ServiceCategory

from .policy import access_decisions_for, service_access_for


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["id", "name", "slug", "description", "icon", "sort_order"]


class ServiceSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    is_available = serializers.SerializerMethodField()
    restriction_reason = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "kind",
            "icon",
            "accent",
            "category",
            "is_available",
            "restriction_reason",
        ]

    def _decision(self, obj):
        cache = self.context.get("_access_decisions")
        if cache is None:
            instance = getattr(self.root, "instance", None)
            if instance is None:
                services = []
            elif isinstance(instance, Service):
                services = [instance]
            else:
                services = list(instance)
            cache = access_decisions_for(self.context["request"].user, services)
            self.context["_access_decisions"] = cache
        if obj.pk not in cache:
            cache[obj.pk] = service_access_for(self.context["request"].user, obj)
        return cache[obj.pk]

    def get_is_available(self, obj):
        return self._decision(obj).allowed

    def get_restriction_reason(self, obj):
        return self._decision(obj).reason
