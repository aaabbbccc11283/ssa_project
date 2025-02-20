from django.urls import path
from two_factor.urls import urlpatterns as tf_urls
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('mfa/', include(tf_urls)),  # Add the two-factor authentication URLs
]