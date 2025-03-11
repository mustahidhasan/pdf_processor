from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend

class EmailOrUsernameBackend(BaseBackend):
    @staticmethod
    def authenticate(self=None, request=None, username=None, password=None):
        try:
            # Try using email to find the user
            user = User.objects.get(email=username)
            return user
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user(user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
