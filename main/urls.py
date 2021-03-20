from django.conf.urls import url
from .views import Login, SignUp, Verify_Payment
from . import views

urlpatterns = [
    url(r'^$', views.home, name='index'),
    url(r'^home/$', views.home, name='home'),
    url(r'^login/$', views.login, name='login'),
    url(r'^Login/$', Login.as_view(), name='login_rest'),
    url(r'^register/$', views.register, name='register'),
    url(r'^signup/$', SignUp.as_view(), name='register_rest'),
    url(r'^register/confirm_registration/$', views.verify_register, name='verify_reg'),
    url(r'^confirm_registration/$', SignUp.as_view(), name='register_verify'),
    url(r'^resetPassword/$', views.reset_password, name='reset_pass'),
    url(r'^profile/(?P<username>[\w.@+-]+)/$', views.profile, name='profile'),
    url(r'^profile/(?P<username>[\w.@+-]+)/edit/$', views.editprofile, name='edit_profile'),
    url(r'^edit_profile/$', views.profile_ajax, name='edit_profile_ajax'),

    url(r'^categories/$', views.category, name='category'),
    url(r'^cat/(?P<slug>[\w.@+-]+)/$', views.category_view, name='cat'),
    url(r'^video/(?P<slug>[\w.@+-]+)/$', views.video_page, name='single-video'),
    url(r'^comment/video/new/$', views.comment_ajax, name='make_comment'),
    url(r'^videos/search/$', views.search_page, name='search'),

    url(r'^verify_transaction', Verify_Payment.as_view(), name='verify_transaction'),
]
