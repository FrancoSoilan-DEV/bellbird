
from django.urls import path

from .views import *

urlpatterns = [
    path('employee/dashboard/', EmployeeDashboardView.as_view(), name='e-dash'),
    # employee
    path('expenses/new/', ExpenseCreateView.as_view(), name='expense-create'),
    path('expenses/', ExpenseListView.as_view(), name='expense-list'),
    path('expenses/<int:pk>/', ExpenseDetailView.as_view(), name='expense-detail'),
    path('expenses/<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense-update'),
    # responsible
    path('responsible/pending/', PendingExpenseListView.as_view(), name='pending-expenses'),
]