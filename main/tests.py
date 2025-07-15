import hashlib
import secrets

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

CustomUser = get_user_model()


def hash_string(input_string):
    """Hash a string using SHA-256."""
    return hashlib.sha256(input_string.encode()).hexdigest()


def generate_secure_token():
    """Generate a secure random token."""
    return secrets.token_hex(16)


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password=hash_string("testpass123"),  # Hashed password
            role="Client",
        )
        self.user.save()

    def test_custom_login(self):
        url = reverse("login")
        data = {"username": "testuser", "password": hash_string("testpass123")}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("reset_url", response.data)

    def test_custom_double_factor_auth(self):
        self.user.code_connexion = hash_string("123456")  # Hashed connection code
        self.user.reset_token = generate_secure_token()  # Secure token
        self.user.save()

        url = reverse("double-factor-auth")
        data = {"code_connexion": hash_string("123456"), "token": self.user.reset_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("redirect_url", response.data)

    def test_custom_forgot_password(self):
        url = reverse("forgot-password")
        data = {"email": "test@example.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reset_url", response.data)

    def test_custom_reset_password(self):
        self.user.code_secret = hash_string("123456")  # Hashed secret code
        self.user.reset_token = generate_secure_token()  # Secure token
        self.user.save()

        url = reverse("reset-password")
        data = {
            "code_secret": hash_string("123456"),
            "new_password": hash_string("newpass123"),
            "token": self.user.reset_token,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_custom_logout(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("api-logout")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_token_refresh(self):
        url = reverse("token_refresh")
        refresh = RefreshToken.for_user(self.user)
        data = {"refresh": str(refresh)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
