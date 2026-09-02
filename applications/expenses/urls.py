
from django.urls import path

from .views import EmployeeDashboardView

urlpatterns = [
    path('employee/dashboard/', EmployeeDashboardView.as_view(), name='e-dash'),
]