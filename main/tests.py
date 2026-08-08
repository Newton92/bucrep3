import hashlib
import secrets

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def hash_string(input_string):
    """Hash a string using SHA-256."""
    return hashlib.sha256(input_string.encode()).hexdigest()


def generate_secure_token():
    """Generate a secure random token."""
    return secrets.token_hex(16)


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
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


class ReportCommentsTests(APITestCase):
    """Ensure comment fields are included in generated report data."""

    def setUp(self):
        # create minimal user/acheteur for authentication
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="reportuser",
            email="report@example.com",
            password=hash_string("reportpass"),
            role="Client",
        )
        self.client.force_authenticate(user=self.user)
        # create acheteur and related objects
        from main.models import Acheteur, RegistreCommerce, ProduitService, Marque, Certification, InnovationDeveloppement, ProcedureCollective
        self.acheteur = Acheteur.objects.create(nom="TestAcheteur")
        # add one record of each type with commentaire
        RegistreCommerce.objects.create(
            acheteur=self.acheteur,
            numero="R123",
            date_inscription="2023-01-01",
            est_actif=True,
            commentaire="reg comment"
        )
        ProduitService.objects.create(
            acheteur=self.acheteur,
            produits="P",
            services="S",
            commentaire="prod comment"
        )
        Marque.objects.create(
            acheteur=self.acheteur,
            marques="M",
            commentaire="marque comment"
        )
        Certification.objects.create(
            acheteur=self.acheteur,
            type_certification="autre",
            nom_certification="Cert",
            commentaire="cert comment"
        )
        InnovationDeveloppement.objects.create(
            acheteur=self.acheteur,
            type_innovation="innovation_produit",
            titre="Innov",
            commentaire="innov comment",
        )
        ProcedureCollective.objects.create(
            acheteur=self.acheteur,
            type_procedure="proc",
            commentaire="proc comment",
        )

    def test_report_includes_comments(self):
        url = reverse("generer_rapport_solvabilite")
        payload = {
            "annee_n": 2025,
            "annee_n1": 2024,
            "annee_n2": 2023,
            "inclure_commande": "non",
            "langue": "fr",
            "acheteur_id": self.acheteur.id,
            "format_rapport": "json",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        # check reg comment appears
        self.assertIn("registres", data)
        self.assertTrue(data["registres"])
        self.assertEqual(data["registres"][0].get("commentaires"), "reg comment")
        # check one other comment for good measure
        self.assertIn("procedures", data)
