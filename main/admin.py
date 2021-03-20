from main.models import Category, Comment, Payment, User, UserVideo, Video
from django.contrib import admin

# Register your models here.
admin.site.register(Category)
admin.site.register(Video)
admin.site.register(User)
admin.site.register(UserVideo)
admin.site.register(Payment)
admin.site.register(Comment)
