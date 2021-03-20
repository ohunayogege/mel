from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category, Comment, Payment, User, UserVerify, UserPassToken, UserVideo, Video
from django.contrib.auth.hashers import make_password
from django.contrib import auth
import secrets
import requests
import random
import os
import datetime
from datetime import timedelta
from datetime import datetime as dt
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string, get_template
from django.contrib.auth import login, authenticate, logout


def gen_token(length=64, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@$%-_"):
	return "".join([secrets.choice(charset) for _ in range(0, length)])

def gen_email_code(length, charset="0123456789"):
	return "".join([secrets.choice(charset) for _ in range(0, length)])

def home(request):
	videos = Video.objects.all().order_by("id").reverse()
	context = {
		'videos': videos
	}
	return render(request, 'index.html', context)

def video_page(request, slug):
	video = Video.objects.get(slug=slug)
	comments = Comment.objects.filter(video=video).order_by("id").reverse()
	if video.tags:
		video_tags = video.tags.split(',')
	else:
		video_tags = None
	user_video_check = UserVideo.objects.filter(video=video).exists()
	if user_video_check:
		user_video = UserVideo.objects.get(video=video)
	else:
		user_video = None
	if request.user.is_authenticated:
		user_videos = UserVideo.objects.filter(user=request.user).exclude(video=video)
	else:
		user_videos = None
	object_list = list(Video.objects.filter(Q(title__contains=video.title) | Q(cat__name__contains=video.cat.name) | Q(tags__contains=video.tags)))
	random.shuffle(object_list)
	rand_videos = object_list[:10]
	context = {
		'video': video,
		'comments': comments,
		'comm_count': len(comments),
		'paystack_key': settings.PAYSTACK_PUBLIC_KEY,
		'user_video': user_video,
		'video_tags': video_tags,
		'user_videos': user_videos,
		'random_videos': rand_videos
	}
	return render(request, 'single-video.html', context)

class Verify_Payment(APIView):
	def get(self, request):
		user = request.user
		reference = request.GET.get("reference")
		video = request.GET.get("video")
		vid = Video.objects.get(title=video)
		url = 'https://api.paystack.co/transaction/verify/'+reference
		headers = {
			"Authorization": "Bearer " +settings.PAYSTACK_SECRET_KEY
		}
		x = requests.get(url, headers=headers)
		if x.json()['status'] == False:
			return False
		results = x.json()
		Payment.objects.create(user=user, charge_ref=results["data"]["reference"], amount=results["data"]["amount"], video=vid)
		UserVideo.objects.create(user=user, video=vid)

		return Response(results)


def login(request):
	return render(request, "login.html")

def register(request):
	return render(request, "register.html")

def verify_register(request):
	token = request.GET.get("signature")
	check_token = UserVerify.objects.filter(email_code=token).exists()
	if check_token == False:
		message = 'Invalid Link or link has expired. Request for another link.'
		messageHead = 'Error Verifying Account'
		link = ""
	else:
		get_user = UserVerify.objects.get(email_code=token)
		if get_user.expired:
			message = 'Verification link expired. Request another one.'
			messageHead = 'Error Verifying Account'
			link = ""
		else:
			instance = UserVerify.objects.filter(id=get_user.id).update(email_verified=True, expires_in=dt.now() + timedelta(minutes=1))
			User.objects.filter(email=get_user.user.email).update(activate=True)
			message = 'Thank you for verifying your account.'
			messageHead = 'Account Verified Successful'
			link = ""
	context = {
		'messageHead': messageHead,
		'message': message,
		'link': link
	}
	return render(request, "verify_register.html", context)

def reset_password(request):
	return render(request, "reset_password.html")


class SignUp(APIView):
	def post(self, request):
		full_name = request.data.get("name")
		email = request.data.get("email")
		password = request.data.get("password")
		password2 = request.data.get("password2")

		first, *last = full_name.split()
		first_name = first
		last_name = " ".join(str(x) for x in last)
		first_name = first_name.title()
		last_name = last_name.title()

		upper_case = sum(1 for c in password if c.isupper())
		digits = sum(1 for c in password if c.isdigit())
		chars = sum(1 for c in password if not c.isalnum())
		length = len(password)

		# We throw error if the above are passed
		# 
		if password2 != password:
			return Response({'error': 'Password mismatch. Try again.'}, status=status.HTTP_200_OK)
		elif length < 6:
			return Response({'error': 'Password is too short. Try another'}, status=status.HTTP_200_OK)
		# elif not upper_case:
		# 	return Response({'error': 'Password must contain at least one Uppercase.'}, status=status.HTTP_200_OK)
		elif not digits:
			return Response({'error': 'Password must contain at least one number.'}, status=status.HTTP_200_OK)
		# elif not chars:
		# 	return Response({'error': 'Password must contain at least one character.'}, status=status.HTTP_200_OK)

		password = make_password(password)
		code = gen_email_code(10)
		code = int(code)+1 # This is added to avoid generating same number randomly

		check_user_exist = User.objects.filter(email=email).exists()
		if check_user_exist:
			return Response({'error': 'User with this email already exist. Try loggin in if this is your account.'}, status=status.HTTP_200_OK)
		
		# Let's setup variable's to add to our template
		from_email = settings.DEFAULT_MAIL_SENDER
		site_name = settings.SITE_NAME
		to_email = [email]
		subject_file = os.path.join(settings.BASE_DIR, "mail/register/subject.txt")
		subject = render_to_string(subject_file, {'name': first_name, 'site_name': site_name})
		confirm_registration_link = settings.SITE_URL+'user/confirm_registration/?signature='+str(code)+'&non_affli='+str(gen_token())

		register_message_file = os.path.join(settings.BASE_DIR, "mail/register/body.txt")
		register_message = render_to_string(register_message_file, {
													'first_name': first_name, 'site_name': site_name,
													'confirm_registration_link': confirm_registration_link,
												})

		message = EmailMultiAlternatives(subject=subject, body=register_message, from_email=from_email, to=to_email)

		html_template = os.path.join(settings.BASE_DIR, "mail/register/body.html")
		template = render_to_string(html_template, {
													'first_name': first_name, 'site_name': site_name,
													'confirm_registration_link': confirm_registration_link,
													})

		message.attach_alternative(template, "text/html")

		message.send()
		instance = User.objects.create(email=email, password=password, first_name=first_name, last_name=last_name)
		UserVerify.objects.create(user=instance, email_code=code)

		return Response({'success': 'Verification link has been sent to '+email}, status=status.HTTP_200_OK)

	def get(self, request):
		token = request.GET.get("signature")
		get_user = UserVerify.objects.get(email_code=token)
		if get_user.expired:
			return Response({'error': 'Verification link expired. Request another one.'}, status=status.HTTP_200_OK)
		# instance = UserVerify.objects.filter(id=get_user.id).update(email_verified=True, expires_in=dt.now() + timedelta(days=30))
		return Response({'success': "Account verified successfully."}, status=status.HTTP_200_OK)


class ResetPasswordSend(APIView):
	def post(self, request):
		email = request.data.get('email')
		# Check if email exists
		check_user = User.objects.filter(email=email).exists()
		if check_user == False:
			return Response({'error': 'User with the email not found'})
		else:
			user = User.objects.get(email=email)
			# Let's call the generate function to generate our token
			token = gen_token()
			first_name = user.first_name
			last_name = user.last_name
			password_link = 'http://localhost/forgot-password/reset_password/?signature='+token

			# Let's setup variable's to add to our template
			subject_file = os.path.join(settings.BASE_DIR, "mail/reset_password/subject.txt")
			subject = render_to_string(subject_file, {'name': first_name})
			from_email = settings.DEFAULT_MAIL_SENDER
			to_email = [email]

			password_message_file = os.path.join(settings.BASE_DIR, "mail/reset_password/body.txt")
			password_message = render_to_string(password_message_file, {
														'first_name': first_name, 'last_name': last_name,
														'password_link': password_link,
													})

			message = EmailMultiAlternatives(subject=subject, body=password_message, from_email=from_email, to=to_email)

			html_template = os.path.join(settings.BASE_DIR, "mail/reset_password/body.html")
			template = render_to_string(html_template, {
														'first_name': first_name, 'last_name': last_name,
														'password_link': password_link,
														})

			message.attach_alternative(template, "text/html")

			message.send()
			UserPassToken.objects.create(user=user, token=token, sent=True)


		return Response({'success': 'Password Reset Link has been sent to'+ ' ' + email}, status=status.HTTP_200_OK)

class ResetPassChange(APIView):
	def post(self, request):
		signature = request.data.get('token')
		password = request.data.get('new_password')
		password2 = request.data.get('confirm_password')

		# We declare some password verifications

		upper_case = sum(1 for c in password if c.isupper())
		digits = sum(1 for c in password if c.isdigit())
		chars = sum(1 for c in password if not c.isalnum())
		length = len(password)

		# We throw error if the above are passed

		if password2 != password:
			return Response({'error': 'Password mismatch. Try again.'})
		elif length < 6:
			return Response({'error': 'Password is too short. Try another'})
		elif not upper_case:
			return Response({'error': 'Password must contain at least one Uppercase.'})
		elif not digits:
			return Response({'error': 'Password must contain at least one number.'})
		elif not chars:
			return Response({'error': 'Password must contain at least one character.'})

		new_password = make_password(password)

		# Check if token exists
		check_token = UserPassToken.objects.filter(token=signature).exists()
		# Check if token has expired
		if check_token == False:
			return Response({'error': 'Code is invalid. Try again'}, status=status.HTTP_404_NOT_FOUND)
		else:
			get_token = UserPassToken.objects.get(token=signature)
		if get_token.expired:
			return Response({'error': 'Sorry, Code has already been expired.'})

		# get user from UserPassToken
		token = UserPassToken.objects.get(token=signature)
		user = User.objects.get(id=token.user.id)
		user.password = new_password
		user.save()
		UserPassToken.objects.filter(token=signature).update(expired=True)
		return Response({'success': "Password Changed Successfully."}, status=status.HTTP_200_OK)


class Login(APIView):
	def post(self, request):
		email = request.data.get('email', None)
		password = request.data.get('password', None)

		check_email = User.objects.filter(email=email).exists()
		if check_email == False:
			return Response({'error': 'Account with the email does not exists.'}, status=status.HTTP_200_OK)
		
		
		d_user = User.objects.get(email=email)
		if d_user.check_password(password):
			if d_user.activate == False:
					return Response({'error': 'You have not activate your account yet. Check your email to activate.'}, status=status.HTTP_200_OK)

		user = auth.authenticate(email=email, password=password)
		if user is not None:
			auth.login(request, user)
			return Response({'success': 'Login successful.'}, status=status.HTTP_200_OK)
		else:
			return Response({'error': 'Error Email/Password. Try again.'})


class ChangePassword(APIView):
	def post(self, request, *args, **kwargs):
		user = request.user
		old_password = request.data.get('old_password')
		new_password = request.data.get('new_password')
		new_password2 = request.data.get('new_password2')
		user = request.user
		if user.check_password(old_password):
			# We declare some password verifications

			upper_case = sum(1 for c in new_password if c.isupper())
			digits = sum(1 for c in new_password if c.isdigit())
			chars = sum(1 for c in new_password if not c.isalnum())
			length = len(new_password)

			# We throw error if the above are passed

			if new_password2 != new_password:
				return Response({'error': 'Password mismatch. Try again.'})
			elif length < 6:
				return Response({'error': 'New Password is too short. Try another'})
			elif not upper_case:
				return Response({'error': 'New Password must contain at least one Uppercase.'})
			elif not digits:
				return Response({'error': 'New Password must contain at least one number.'})
			elif not chars:
				return Response({'error': 'New Password must contain at least one character.'})

			# password = make_password(new_password)
			user.set_password(new_password)
			user.save()


		return Response({'success': 'Password updated successfully'}, status=status.HTTP_200_OK)


def category(request):
	cats = Category.objects.all()
	context = {
		'cats': cats
	}
	return render(request, "category.html", context)


def category_view(request, slug):
	cat = Category.objects.get(slug=slug)
	videos = Video.objects.filter(cat=cat)
	context = {
		'videos': videos,
		'cat': cat
	}
	return render(request, 'category_view.html', context)


def profile(request, username):
	user = User.objects.get(username=username)
	user_videos = UserVideo.objects.filter(user=user)
	context = {
		'user': user,
		'user_videos': user_videos,
	}
	return render(request, 'profile.html', context)

def editprofile(request, username):
	user = User.objects.get(username=username)
	context = {
		'user': user
	}
	return render(request, 'edit_profile.html', context)

def search_page(request):
	search_text = request.GET.get("q")
	videos = Video.objects.filter(Q(title__contains=search_text) | Q(cat__name__startswith=search_text) | Q(tags__contains=search_text))
	context = {
		'videos': videos,
		'search_text': search_text.capitalize()
	}
	return render(request, 'search.html', context)


def search_tags(request):
	search_text = request.GET.get("q")
	videos = Video.objects.filter(Q(tags__contains=search_text))
	context = {
		'videos': videos,
		'search_text': search_text.capitalize()
	}
	return render(request, 'search.html', context)


def comment_ajax(request):
	if request.is_ajax():
		comment = request.POST.get("comment", None)
		video_title = request.POST.get("video", None)

		video = Video.objects.get(title=video_title)
		user = request.user
		instance = Comment.objects.create(user=user, video=video, text=comment)
		if instance:
			response = {"success": "Comment Added Successfully."}
		else:
			response = {"error": "Error adding comment. Try again"}
		return JsonResponse(response)


def profile_ajax(request):
	if request.is_ajax():
		user = request.user
		instance = User.objects.filter(id=user.id).update(
			first_name=request.POST['first_name'],
			last_name=request.POST['last_name'],
			mobile=request.POST['mobile'],
			address=request.POST['address']
		)
		if instance:
			response = {"success": "Profile Updated Successfully."}
		else:
			response = {"error": "Error updating profile. Try again"}
		return JsonResponse(response)
