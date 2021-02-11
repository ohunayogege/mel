from django.conf.urls import url
from .views import Login, SignUp, home
from . import views

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^login/$', views.login, name='login'),
    url(r'^Login/$', Login.as_view(), name='login_rest'),
    url(r'^register/$', views.register, name='register'),
    url(r'^signup/$', SignUp.as_view(), name='register_rest'),
    url(r'^register/confirm_registration/$', views.verify_register, name='verify_reg'),
    url(r'^confirm_registration/$', SignUp.as_view(), name='register_verify'),
    url(r'^resetPassword/', views.reset_password, name='reset_pass'),
]
