from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_role = None

    def test_func(self):
        if self.required_role is None:
            return True
        return getattr(self.request.user, self.required_role, False)