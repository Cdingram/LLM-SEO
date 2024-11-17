from django.urls import path
from . import views

urlpatterns = [
    path("", views.Home.as_view(), name="Home"),
    path('test-progress/<str:test_run_id>/', views.check_test_progress, name='test_progress'),
]