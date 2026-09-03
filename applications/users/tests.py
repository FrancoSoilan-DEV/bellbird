from django.test import TestCase
from django.urls import reverse

from applications.users.models import User


class CustomLoginViewTests(TestCase):
    def test_responsible_login_redirects_to_responsible_dashboard(self):
        User.objects.create_user(
            username='responsable1', password='pass123',
            is_employee=False, is_responsible=True,
        )

        response = self.client.post(reverse('login'), {
            'username': 'responsable1',
            'password': 'pass123',
        })

        self.assertRedirects(response, reverse('r-dash'))
    
    def test_employee_login_redirects_to_employee_dashboard(self):
        User.objects.create_user(
            username='empleado1', password='pass123',
            is_employee=True, is_responsible=False,
        )

        response = self.client.post(reverse('login'), {
            'username': 'empleado1',
            'password': 'pass123',
        })

        self.assertRedirects(response, reverse('e-dash'))


class DashboardProtectionTests(TestCase):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse('e-dash'))

        self.assertEqual(response.status_code, 302)