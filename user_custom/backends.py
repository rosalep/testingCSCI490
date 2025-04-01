from django.contrib.auth.backends import BaseBackend
from users.models import CustomUser
from django.contrib.auth.hashers import check_password
import bcrypt
class CustomAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = CustomUser.objects.get(username=username) # or email
        except CustomUser.DoesNotExist:
            return None

        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return user
        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None