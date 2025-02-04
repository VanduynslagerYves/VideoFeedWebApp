from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Use Django's built-in login view at /accounts/login/
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),  # Default login URL
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),  # Default logout URL (optional)
    
    # Your home page, which is protected by login
    path('', views.index, name='index'),
]
