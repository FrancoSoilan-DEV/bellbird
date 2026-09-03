from django.views.generic import (
    TemplateView, 
    CreateView, 
    ListView,
    DetailView,
    UpdateView,
)
from django.urls import reverse_lazy
from applications.users.mixins import EmployeeRequiredMixin

from .forms import *

# ----- Employee

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
