from django.views.generic import TemplateView, CreateView, ListView
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