from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.is_responsible:
            return reverse_lazy('r-dash')
        return reverse_lazy('e-dash')
    
    