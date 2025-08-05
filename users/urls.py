from django.urls import path, include
from . import views

urlpatterns = [    
    path("", views.user, name="user"),
    path('accounts/', include('allauth.urls')),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('register/', views.register, name='register'),
    path('delete/', views.delete_account, name='delete'),
    path('top_up/', views.top_up, name='top_up'),
    path("portal/", views.user_portal, name="user_portal"),
    path('change_password/', views.change_password, name='change_password'),
    ]