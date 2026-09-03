from django.test import TestCase
from django.urls import reverse

from applications.expenses.models import Expense
from applications.users.models import User
from .models import Decision

# ==========================================
# ----- Employee
# ==========================================

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
    
    
    
    
class ExpenseListViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='empleado1', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.other = User.objects.create_user(
            username='empleado2', password='pass123',
            is_employee=True, is_responsible=False,
        )
        Expense.objects.create(
            owner=self.owner, title='Mío', category=Expense.Category.OTHER,
            amount='10.00', date='2026-09-01',
        )
        Expense.objects.create(
            owner=self.other, title='Ajeno', category=Expense.Category.OTHER,
            amount='20.00', date='2026-09-01',
        )
        self.client.login(username='empleado1', password='pass123')

    def test_employee_only_sees_own_expenses(self):
        response = self.client.get(reverse('expense-list'))

        titles = [e.title for e in response.context['expenses']]
        self.assertIn('Mío', titles)
        self.assertNotIn('Ajeno', titles)

    def test_employee_list_shows_empty_state_message(self):
        Expense.objects.all().delete()

        response = self.client.get(reverse('expense-list'))

        self.assertContains(response, 'No tenés gastos registrados')
        
        
        
class ExpenseDetailViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='empleado1', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.other = User.objects.create_user(
            username='empleado2', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.expense = Expense.objects.create(
            owner=self.owner, title='Mío', category=Expense.Category.OTHER,
            amount='10.00', date='2026-09-01',
        )

    def test_owner_can_view_own_expense_detail(self):
        self.client.login(username='empleado1', password='pass123')

        response = self.client.get(
            reverse('expense-detail', args=[self.expense.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['expense'], self.expense)

    def test_employee_cannot_view_others_expense_detail(self):
        self.client.login(username='empleado2', password='pass123')

        response = self.client.get(
            reverse('expense-detail', args=[self.expense.pk])
        )

        self.assertEqual(response.status_code, 404)
        
        
class ExpenseUpdateViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='empleado1', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.other = User.objects.create_user(
            username='empleado2', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.pending_expense = Expense.objects.create(
            owner=self.owner, title='Original', category=Expense.Category.OTHER,
            amount='10.00', date='2026-09-01',
        )
        self.approved_expense = Expense.objects.create(
            owner=self.owner, title='Ya aprobado', category=Expense.Category.OTHER,
            amount='20.00', date='2026-09-01', status=Expense.Status.APPROVED,
        )

    def test_owner_can_edit_pending_expense(self):
        self.client.login(username='empleado1', password='pass123')

        response = self.client.post(
            reverse('expense-update', args=[self.pending_expense.pk]),
            {
                'title': 'Editado',
                'category': Expense.Category.OTHER,
                'amount': '15.00',
                'date': '2026-09-01',
                'description': '',
            }
        )

        self.pending_expense.refresh_from_db()
        self.assertEqual(self.pending_expense.title, 'Editado')
        self.assertEqual(response.status_code, 302)

    def test_cannot_edit_approved_expense(self):
        self.client.login(username='empleado1', password='pass123')

        response = self.client.post(
            reverse('expense-update', args=[self.approved_expense.pk]),
            {
                'title': 'Intento de edición',
                'category': Expense.Category.OTHER,
                'amount': '99.00',
                'date': '2026-09-01',
                'description': '',
            }
        )

        self.approved_expense.refresh_from_db()
        self.assertEqual(self.approved_expense.title, 'Ya aprobado')
        self.assertEqual(response.status_code, 404)

    def test_employee_cannot_edit_others_expense(self):
        self.client.login(username='empleado2', password='pass123')

        response = self.client.post(
            reverse('expense-update', args=[self.pending_expense.pk]),
            {
                'title': 'Intento ajeno',
                'category': Expense.Category.OTHER,
                'amount': '99.00',
                'date': '2026-09-01',
                'description': '',
            }
        )

        self.pending_expense.refresh_from_db()
        self.assertEqual(self.pending_expense.title, 'Original')
        self.assertEqual(response.status_code, 404)
        
# ==========================================
# ----- Responsible
# ==========================================

class PendingExpenseListViewTests(TestCase):
    def setUp(self):
        self.responsible = User.objects.create_user(
            username='responsable1', password='pass123',
            is_employee=False, is_responsible=True,
        )
        self.employee1 = User.objects.create_user(
            username='empleado1', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.employee2 = User.objects.create_user(
            username='empleado2', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.pending1 = Expense.objects.create(
            owner=self.employee1, title='Pendiente de emp1',
            category=Expense.Category.OTHER, amount='10.00', date='2026-09-01',
        )
        self.pending2 = Expense.objects.create(
            owner=self.employee2, title='Pendiente de emp2',
            category=Expense.Category.OTHER, amount='20.00', date='2026-09-01',
        )
        self.approved = Expense.objects.create(
            owner=self.employee1, title='Ya decidido',
            category=Expense.Category.OTHER, amount='30.00', date='2026-09-01',
            status=Expense.Status.APPROVED,
        )
        self.client.login(username='responsable1', password='pass123')

    def test_lists_only_pending_expenses(self):
        response = self.client.get(reverse('pending-expenses'))

        titles = [e.title for e in response.context['expenses']]
        self.assertIn('Pendiente de emp1', titles)
        self.assertIn('Pendiente de emp2', titles)
        self.assertNotIn('Ya decidido', titles)

    def test_filters_by_owner(self):
        response = self.client.get(
            reverse('pending-expenses'), {'owner': self.employee1.id}
        )

        titles = [e.title for e in response.context['expenses']]
        self.assertIn('Pendiente de emp1', titles)
        self.assertNotIn('Pendiente de emp2', titles)

    def test_employee_cannot_access_pending_list(self):
        self.client.logout()
        self.client.login(username='empleado1', password='pass123')

        response = self.client.get(reverse('pending-expenses'))

        self.assertEqual(response.status_code, 403)
        
        
class ExpenseDecisionViewTests(TestCase):
    def setUp(self):
        self.responsible = User.objects.create_user(
            username='responsable1', password='pass123',
            is_employee=False, is_responsible=True,
        )
        self.employee = User.objects.create_user(
            username='empleado1', password='pass123',
            is_employee=True, is_responsible=False,
        )
        self.dual_role = User.objects.create_user(
            username='dual1', password='pass123',
            is_employee=True, is_responsible=True,
        )
        self.expense = Expense.objects.create(
            owner=self.employee, title='Gasto', category=Expense.Category.OTHER,
            amount='10.00', date='2026-09-01',
        )
        self.own_expense = Expense.objects.create(
            owner=self.dual_role, title='Gasto propio', category=Expense.Category.OTHER,
            amount='10.00', date='2026-09-01',
        )

    def test_responsible_can_approve_pending_expense(self):
        self.client.login(username='responsable1', password='pass123')

        response = self.client.post(
            reverse('expense-decide', args=[self.expense.pk]),
            {'result': Decision.Result.APPROVED, 'comment': 'Todo en orden'},
        )

        self.expense.refresh_from_db()
        self.assertEqual(self.expense.status, Expense.Status.APPROVED)
        self.assertEqual(self.expense.decision.result, Decision.Result.APPROVED)
        self.assertEqual(self.expense.decision.responsible, self.responsible)
        self.assertEqual(response.status_code, 302)

    def test_responsible_can_reject_pending_expense(self):
        self.client.login(username='responsable1', password='pass123')

        response = self.client.post(
            reverse('expense-decide', args=[self.expense.pk]),
            {'result': Decision.Result.REJECTED, 'comment': 'Falta comprobante'},
        )

        self.expense.refresh_from_db()
        self.assertEqual(self.expense.status, Expense.Status.REJECTED)
        self.assertEqual(response.status_code, 302)

    def test_cannot_decide_own_expense_even_as_responsible(self):
        self.client.login(username='dual1', password='pass123')

        response = self.client.post(
            reverse('expense-decide', args=[self.own_expense.pk]),
            {'result': Decision.Result.APPROVED, 'comment': 'Autoaprobado'},
        )

        self.own_expense.refresh_from_db()
        self.assertEqual(self.own_expense.status, Expense.Status.PENDING)
        self.assertFalse(Decision.objects.filter(expense=self.own_expense).exists())
        self.assertEqual(response.status_code, 403)

    def test_cannot_decide_already_decided_expense(self):
        self.client.login(username='responsable1', password='pass123')
        self.client.post(
            reverse('expense-decide', args=[self.expense.pk]),
            {'result': Decision.Result.APPROVED, 'comment': 'Primera decisión'},
        )

        response = self.client.post(
            reverse('expense-decide', args=[self.expense.pk]),
            {'result': Decision.Result.REJECTED, 'comment': 'Segundo intento'},
        )

        self.assertEqual(Decision.objects.filter(expense=self.expense).count(), 1)
        self.assertEqual(response.status_code, 404)

    def test_employee_cannot_access_decision_view(self):
        self.client.login(username='empleado1', password='pass123')

        response = self.client.post(
            reverse('expense-decide', args=[self.expense.pk]),
            {'result': Decision.Result.APPROVED, 'comment': 'No debería poder'},
        )

        self.assertEqual(response.status_code, 403)
        
