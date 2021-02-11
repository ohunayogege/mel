from django.contrib.auth.models import (
	AbstractBaseUser, BaseUserManager, PermissionsMixin, AbstractUser
)
from django.db import models
from django.utils import timezone
import datetime
from datetime import timedelta
from datetime import datetime as dt
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.conf import settings

today = datetime.date.today()
current_time = datetime.datetime.now()


class UserManager(BaseUserManager):
	"""
	Custom user model manager where email is the unique identifiers
	for authentication instead of username.
	"""
	def create_user(self, email, password, **extra_fields):
		"""
		Create and save a User with the given email and password.
		"""
		if not email:
			raise ValueError(_('The Email must be set'))
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save()
		return user

	def create_superuser(self, email, password, **extra_fields):
		"""
		Create and save a SuperUser with the given email and password.
		"""
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		extra_fields.setdefault('is_active', True)

		if extra_fields.get('is_staff') is not True:
			raise ValueError(_('Superuser must have is_staff=True.'))
		if extra_fields.get('is_superuser') is not True:
			raise ValueError(_('Superuser must have is_superuser=True.'))
		return self.create_user(email, password, **extra_fields)


#### This is User Profile
class User(AbstractUser):
	user_gender = (
		('Male', 'Male'),
		('Female', 'Female')
	)
	username = models.CharField(_('Username'), max_length=100, default='', blank=True)
	email = models.EmailField(_('email address'), unique=True, default='')
	first_name = models.CharField(max_length=200, null=True)
	last_name = models.CharField(max_length=200, null=True)
	gender = models.CharField(max_length=10, default='', choices=user_gender)
	mobile = models.CharField(max_length=200, default='', unique=True)
	address = models.TextField(default="", blank=True)
	activate = models.BooleanField(default=False)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['first_name', 'last_name']

	objects = UserManager()

	def __str__(self):
		return self.first_name + ' ' + self.last_name


class UserVerify(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, default=None)
	email_code = models.CharField(_('Email Verification Code'), max_length=10, default='')
	email_verified = models.BooleanField(default=False)
	expires_in = models.DateTimeField(default=current_time + timedelta(minutes=30))
	expired = models.BooleanField(default=False)

	def __str__(self):
		return self.user.email

@receiver(pre_save, sender=UserVerify)
def update_expired(sender, instance, *args, **kwargs):
	if instance.expires_in < current_time:
		instance.expired = True
	else:
		instance.expired = False


class UserPassToken(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
	token = models.CharField(max_length=100, default='', blank=True)
	expires_in = models.DateTimeField(default=current_time + timedelta(minutes=5))
	expired = models.BooleanField(default=False)
	sent = models.BooleanField(default=False)

	def __str__(self):
		return self.user.first_name + ' - ' + self.user.last_name

@receiver(pre_save, sender=UserPassToken)
def update_expired(sender, instance, *args, **kwargs):
	if instance.expires_in < current_time:
		instance.expired = True
	else:
		instance.expired = False
