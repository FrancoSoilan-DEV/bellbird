from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from applications.users.mixins import EmployeeRequiredMixin

from .forms import *

# ----- Employee

class EmployeeDashboardView(EmployeeRequiredMixin, TemplateView):
    template_name = 'employee/dashboard.html'
    
    
class ExpenseCreateView(EmployeeRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expense_form.html'
    success_url = reverse_lazy('e-dash')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)