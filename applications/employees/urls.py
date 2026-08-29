from django.urls import path

from .views import LandingView

app_name = 'employees'

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
]