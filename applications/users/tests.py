from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.views import View
from django.core.exceptions import PermissionDenied

from applications.users.mixins import RoleRequiredMixin
from applications.users.models import User


class _EmployeeOnlyView(RoleRequiredMixin, View):
    required_role = 'is_employee'

    def get(self, request, *args, **kwargs):
        return HttpResponse('ok')


class _ResponsibleOnlyView(RoleRequiredMixin, View):
    required_role = 'is_responsible'

    def get(self, request, *args, **kwargs):
        return HttpResponse('ok')


class RoleRequiredMixinTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_user_with_matching_role_can_access(self):
        user = User.objects.create_user(
            username='empleado1', password='pass',
            is_employee=True, is_responsible=False,
        )
        request = self.factory.get('/dummy/')
        request.user = user

        response = _EmployeeOnlyView.as_view()(request)

        self.assertEqual(response.status_code, 200)

    def test_user_without_matching_role_gets_forbidden(self):
        user = User.objects.create_user(
            username='responsable1', password='pass',
            is_employee=False, is_responsible=True,
        )
        request = self.factory.get('/dummy/')
        request.user = user

        with self.assertRaises(PermissionDenied):
            _EmployeeOnlyView.as_view()(request)

    def test_anonymous_user_is_redirected_to_login(self):
        request = self.factory.get('/dummy/')
        request.user = AnonymousUser()

        response = _EmployeeOnlyView.as_view()(request)

        self.assertEqual(response.status_code, 302)

    def test_responsible_only_view_rejects_pure_employee(self):
        user = User.objects.create_user(
            username='empleado2', password='pass',
            is_employee=True, is_responsible=False,
        )
        request = self.factory.get('/dummy/')
        request.user = user

        with self.assertRaises(PermissionDenied):
            _ResponsibleOnlyView.as_view()(request)

    def test_user_with_both_roles_can_access_both_views(self):
        user = User.objects.create_user(
            username='ambos', password='pass',
            is_employee=True, is_responsible=True,
        )
        request = self.factory.get('/dummy/')
        request.user = user

        employee_response = _EmployeeOnlyView.as_view()(request)
        responsible_response = _ResponsibleOnlyView.as_view()(request)

        self.assertEqual(employee_response.status_code, 200)
        self.assertEqual(responsible_response.status_code, 200)