
from django.urls import path

from .views import *

urlpatterns = [
    path('employee/dashboard/', EmployeeDashboardView.as_view(), name='e-dash'),
    path('expenses/new/', ExpenseCreateView.as_view(), name='expense-create'),
]