from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("email")
        if not identifier or not password:
            return None

        User = get_user_model()
        user = User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier)).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
