from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class EmployeeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    # permission_denied_message = "No tenés permitido acceder a esta vista." django usa esto por defecto

    def test_func(self):
        return self.request.user.is_employee


class ResponsibleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_responsible