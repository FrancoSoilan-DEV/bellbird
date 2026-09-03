from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from applications.users.models import User
from applications.expenses.models import Expense, Decision


class Command(BaseCommand):
    help = 'Carga datos demo reproducibles: usuarios, gastos y decisiones de ejemplo.'

    def handle(self, *args, **options):
        employee = self._get_or_create_user(
            'empleado1', is_employee=True, is_responsible=False,
            first_name='Empleado', last_name='Uno',
        )
        responsible = self._get_or_create_user(
            'responsable1', is_employee=False, is_responsible=True,
            first_name='Responsable', last_name='Uno',
        )
        self._get_or_create_user(
            'dual1', is_employee=True, is_responsible=True,
            first_name='Doble', last_name='Rol',
        )

        today = timezone.now().date()

        self._get_or_create_expense(
            owner=employee, title='Almuerzo con cliente',
            category=Expense.Category.OTHER, amount='85.00',
            date=today - timedelta(days=1),
            description='Reunión comercial',
        )

        approved = self._get_or_create_expense(
            owner=employee, title='Pasaje en bus',
            category=Expense.Category.TRAVEL, amount='40.00',
            date=today - timedelta(days=5),
            status=Expense.Status.APPROVED,
        )
        if approved:
            Decision.objects.get_or_create(
                expense=approved,
                defaults={
                    'responsible': responsible,
                    'result': Decision.Result.APPROVED,
                    'comment': 'Todo en orden.',
                },
            )

        rejected = self._get_or_create_expense(
            owner=employee, title='Suscripción software personal',
            category=Expense.Category.SOFTWARE, amount='15.00',
            date=today - timedelta(days=10),
            status=Expense.Status.REJECTED,
        )
        if rejected:
            Decision.objects.get_or_create(
                expense=rejected,
                defaults={
                    'responsible': responsible,
                    'result': Decision.Result.REJECTED,
                    'comment': 'Gasto no relacionado con la empresa.',
                },
            )

        self.stdout.write(self.style.SUCCESS('Datos demo listos.'))
        self.stdout.write('')
        self.stdout.write('Credenciales demo:')
        self.stdout.write('  Empleado:    empleado1 / demo1234')
        self.stdout.write('  Responsable: responsable1 / demo1234')
        self.stdout.write('  Doble rol:   dual1 / demo1234')

    def _get_or_create_user(self, username, **fields):
        user, created = User.objects.get_or_create(
            username=username, defaults=fields,
        )
        if created:
            user.set_password('demo1234')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Usuario {username} creado'))
        else:
            self.stdout.write(f'Usuario {username} ya existía')
        return user

    def _get_or_create_expense(self, owner, title, **fields):
        expense, created = Expense.objects.get_or_create(
            owner=owner, title=title, defaults=fields,
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Gasto "{title}" creado'))
        return expense