# verify_email_tests/test_verify_email.py
import time

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from verify_email.email_handler import ActivationMailManager
from verify_email.token_manager import TokenManager, SafeURL, ActivationLinkManager
from django.core import mail
from django.conf import settings
from verify_email.app_configurations import GetFieldFromSettings


User = get_user_model()


class VerifyEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.user.is_active = False
        self.user.save()

    def test_send_verification_email(self):
        """Test that verification email is sent."""
        response = ActivationMailManager.send_verification_link(self.user)
        self.assertIsNotNone(response)
        self.assertEquals(len(mail.outbox), 1)

    def test_verification_view_by_token_and_email(self):
        """Test the email verification view."""
        user_token = TokenManager().generate_token_for_user(self.user)
        user_email = SafeURL.perform_encoding(self.user.email)
        response = self.client.get(reverse('verify-email', args=[user_email, user_token]))
        self.assertEqual(response.status_code, 200)

    def test_verification_link(self):
        user_token = TokenManager().generate_token_for_user(self.user)
        user_email = self.user.email
        link = ActivationLinkManager.generate_link(user_token, user_email)

        full_url = f"http://testserver{link}"

        resp = self.client.get(full_url)

        self.assertEquals(resp.status_code, 200)

    def test_process(self):
        user_token = TokenManager().generate_token_for_user(self.user)
        time.sleep(1)

        link = ActivationLinkManager.generate_link(user_token, self.user.email)
        full_url = f"http://testserver{link}"
        resp = self.client.get(full_url)
        self.assertEquals(resp.status_code, 200)

    def test_timestamp_invalid_link(self):
        user_token = TokenManager().generate_token_for_user(self.user)
        time.sleep(3)

        link = ActivationLinkManager().generate_link(user_token, self.user.email)
        full_url = f"http://testserver{link}"
        resp = self.client.get(full_url)
        self.assertEquals(resp.status_code, 401)

    def test_timestamp_valid_link(self):
        user_token = TokenManager().generate_token_for_user(self.user)
        time.sleep(3)

        link = ActivationLinkManager.generate_link(user_token, self.user.email)
        full_url = f"http://testserver{link}"
        resp = self.client.get(full_url)
        self.assertEquals(resp.status_code, 200)
