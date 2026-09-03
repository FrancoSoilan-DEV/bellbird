from django.views import View
from django.views.generic import (
    TemplateView, 
    CreateView, 
    ListView,
    DetailView,
    UpdateView,
)
from django.urls import reverse_lazy
from applications.users.mixins import EmployeeRequiredMixin, ResponsibleRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.core.exceptions import PermissionDenied

from .forms import *
from .models import Expense, Decision
# ==========================================
# ----- Employee
# ==========================================

class EmployeeDashboardView(EmployeeRequiredMixin, TemplateView):
    template_name = 'employee/dashboard.html'
    
    
class ExpenseCreateView(EmployeeRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'employee/expense_form.html'
    success_url = reverse_lazy('e-dash')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
    
class ExpenseListView(EmployeeRequiredMixin, ListView):
    model = Expense
    template_name = 'employee/expense_list.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        return Expense.objects.filter(owner=self.request.user)
    
    
class ExpenseDetailView(EmployeeRequiredMixin, DetailView):
    model = Expense
    template_name = 'employee/expense_detail.html'
    context_object_name = 'expense'

    def get_queryset(self):
        return Expense.objects.filter(owner=self.request.user)
      
class ExpenseUpdateView(EmployeeRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'employee/expense_form.html'
    success_url = reverse_lazy('e-dash')

    def get_queryset(self):
        return Expense.objects.filter(
            owner=self.request.user,
            status=Expense.Status.PENDING,
        )      


# ==========================================
# ----- Responsible
# ==========================================

class PendingExpenseListView(ResponsibleRequiredMixin, ListView):
    model = Expense
    template_name = 'responsible/pending_list.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        queryset = Expense.objects.filter(status=Expense.Status.PENDING)

        owner_id = self.request.GET.get('owner')
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        return queryset
    


class ExpenseDecisionView(ResponsibleRequiredMixin, View):

    def post(self, request, pk):
        expense = get_object_or_404(
            Expense, pk=pk, status=Expense.Status.PENDING
        )

        if not expense.can_be_decided_by(request.user):
            raise PermissionDenied

        result = request.POST.get('result')
        comment = request.POST.get('comment', '')

        with transaction.atomic():
            Decision.objects.create(
                expense=expense,
                responsible=request.user,
                result=result,
                comment=comment,
            )
            expense.status = result
            expense.save(update_fields=['status', 'updated_at'])

        return redirect('pending-expenses')
