from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Customizer JWT serializer to add user roles/permissions to the token."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["username"] = user.username
        token["email"] = user.email
        token["is_superuser"] = user.is_superuser
        token["is_staff"] = user.is_staff
        
        # Add RBAC Role
        try:
            token["role"] = user.profile.role
        except Exception:
            token["role"] = "PATIENT"
        
        # Add groups
        token["roles"] = list(user.groups.values_list("name", flat=True))

        return token
