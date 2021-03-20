from django.conf.urls import url
from . import dashboard
from . import views

urlpatterns = [
    url(r'^$', dashboard.home, name='home'),
    url(r'^../$', views.home, name='website'),
    url(r'^categories/$', dashboard.category, name='cats'),
    url(r'^categories/new/$', dashboard.addCategory, name='add-cat'),
    url(r'^categories/new_ajax/$', dashboard.cat_ajax, name='cats_ajax'),
    url(r'^category/edit/(?P<slug>[\w.@+-/]+)/$', dashboard.cat_edit, name='edit-cats'),
    url(r'^category/update_ajax/$', dashboard.updateCat, name='edit-cat_ajax'),
    url(r'^category/remove/(?P<slug>[\w.@+-/]+)/$', dashboard.cat_delete, name='del_cat'),
    url(r'^videos/$', dashboard.video, name='videos'),
    url(r'^videos/new/$', dashboard.add_video, name='add_video'),
    url(r'^videos/new_ajax/$', dashboard.add_video_ajax, name='add_video_ajax'),
    url(r'^users/$', dashboard.user, name='users'),
    url(r'^comments/$', dashboard.comment, name='comments'),
]
