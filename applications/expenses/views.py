from django.views.generic import TemplateView

from applications.users.mixins import EmployeeRequiredMixin


class EmployeeDashboardView(EmployeeRequiredMixin, TemplateView):
    template_name = 'employee/dashboard.html'