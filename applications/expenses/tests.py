from django.test import TestCase
from django.urls import reverse

from applications.expenses.models import Expense
from applications.users.models import User

# ----- Employee

class ExpenseCreateViewTests(TestCase):
    def test_employee_can_create_expense_with_valid_data(self):
        User.objects.create_user(
            username='empleado1', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.client.login(username='empleado1', password='pass123')

        response = self.client.post(reverse('expense-create'), {
            'title': 'Almuerzo con cliente',
            'category': Expense.Category.OTHER,
            'amount': '150.50',
            'date': '2026-09-01',
            'description': '',
        })

        expense = Expense.objects.get(title='Almuerzo con cliente')
        self.assertEqual(expense.status, Expense.Status.PENDING)
        self.assertEqual(expense.owner.username, 'empleado1')
        self.assertEqual(response.status_code, 302)
        
class ExpenseCreateValidationTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            username='empleado1', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.client.login(username='empleado1', password='pass123')

    def test_amount_zero_is_rejected(self):
        response = self.client.post(reverse('expense-create'), {
            'title': 'Gasto inválido',
            'category': Expense.Category.OTHER,
            'amount': '0',
            'date': '2026-09-01',
            'description': '',
        })

        self.assertEqual(Expense.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get('amount'))

    def test_negative_amount_is_rejected(self):
        response = self.client.post(reverse('expense-create'), {
            'title': 'Gasto inválido',
            'category': Expense.Category.OTHER,
            'amount': '-50',
            'date': '2026-09-01',
            'description': '',
        })

        self.assertEqual(Expense.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
    