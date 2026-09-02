from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Expense(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        APPROVED = 'APPROVED', 'Aprobado'
        REJECTED = 'REJECTED', 'Rechazado'

    class Category(models.TextChoices):
        TRAVEL = 'TRAVEL', 'Viáticos'
        SUPPLIES = 'SUPPLIES', 'Insumos'
        SOFTWARE = 'SOFTWARE', 'Software'
        OTHER = 'OTHER', 'Otro'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expenses',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),   # ← nombre nuevo
                name='expense_amount_positive',
            ),
        ]

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    def can_be_edited(self):
        return self.is_pending

    def can_be_decided_by(self, user):
        return self.is_pending and self.owner_id != user.id


class Decision(models.Model):
    class Result(models.TextChoices):
        APPROVED = 'APPROVED', 'Aprobado'
        REJECTED = 'REJECTED', 'Rechazado'

    expense = models.OneToOneField(
        Expense,
        on_delete=models.CASCADE,
        related_name='decision',
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='decisions_made',
    )
    result = models.CharField(max_length=20, choices=Result.choices)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.expense} → {self.get_result_display()} por {self.responsible}'