from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend


class EmailOrUsernameBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            # Try authenticating with username (user_id) first
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                # If username doesn't exist, try using email
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

        # Check the password
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
