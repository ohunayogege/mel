from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from rest_framework import response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category, Comment, Payment, User, UserVerify, UserPassToken, UserVideo, Video
from django.contrib.auth.hashers import make_password
from django.contrib import auth
from django.db.models import Count
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


def home(request):
    users = User.objects.count()
    user_per = (users/100)
    total_sales = Payment.objects.all()
    categories = Category.objects.all()
    videos = Video.objects.all()
    views_videos = Video.objects.all().order_by('views').reverse()[:15]
    sales = 0
    for sale in total_sales:
        sales += sale.amount
    sales_per = (sales/100)/100
    context = {
        'users': users,
        'user_per': user_per,
        'sales': int(sales),
        'sales_per': sales_per,
        'videos': len(videos),
        'categories': len(categories),
        'views_videos': views_videos
    }
    return render(request, 'admins/index.html', context)

def category(request):
    categories = Category.objects.all().order_by('name')
    context = {
        'categories': categories,
    }
    return render(request, 'admins/categories.html', context)

def addCategory(request):
    return render(request, 'admins/add-category.html')

def cat_ajax(request):
    if request.is_ajax():
        name = request.POST.get("name", None)
        slug = request.POST.get("slug", None)
        description = request.POST.get("description", None)
        instance = Category.objects.create(name=name,slug=slug,description=description)
        if instance:
            response = {"success": "Successfully Created"}
        else:
            response = {"error": "There wsas an error. Please try again."}
    return JsonResponse(response)

def cat_delete(request, slug):
    clink = Category.objects.get(slug=slug)
    clink.delete()
    return redirect("cats")

def cat_edit(request, slug):
    cat = Category.objects.get(slug=slug)
    context = {
        "cat": cat
    }
    return render(request, 'admins/edit_cat.html', context)

def updateCat(request):
    if request.is_ajax():
        cat_obj = request.POST.get("cat_obj", None)
        clink = Category.objects.get(slug=cat_obj)
        name = request.POST.get("name", None)
        slug = request.POST.get("slug", None)
        description = request.POST.get("description", None)
        instance = Category.objects.filter(id=clink.id).update(
            name=name, slug=slug, description=description
        )
        if instance > 0:
            response = {"success": "Updated Successfully"}
        else:
            response = {"error": "Error updating category. Please try again."}
    return JsonResponse(response)

def video(request):
    videos = Video.objects.all().order_by('title')
    context = {
        'videos': videos
    }
    return render(request, 'admins/videos.html', context)


def add_video(request):
    categories = Category.objects.all().order_by('name')
    context = {
        'categories': categories
    }
    return render(request, 'admins/add-video.html', context)


def add_video_ajax(request):
    if request.is_ajax():
        title = request.POST.get("title", None)
        slug = request.POST.get("slug", None)
        thumbnail = request.POST.get("thumbnail", None)
        category = request.POST.get("category", None)
        tags = request.POST.get("tags", None)
        price = request.POST.get("amount", None)
        duration = request.POST.get("video_length", None)
        description = request.POST.get("description", None)
        main_video = request.POST.get("main_video", None)
        
        cat = Category.objects.get(slug=category)
        print(thumbnail)
        print(main_video)
        print(title)
        instance = True
        # instance = Video.objects.create(
        #     title = title,
        #     slug = slug,
        #     thumbnail = 'media/videos/images/'+thumbnail,
        #     length = duration,
        #     description = description,
        #     cat = cat,
        #     price = float(price),
        #     tags = tags,
        #     main_video = main_video,
        #     snippet_video = 'snippet_video'
        # )
        if instance:
            response = {"success": "Thanks"}
        else:
            response = {"error": "There was an error uploading. Try again later."}
        return JsonResponse(response)


def video_delete(request, slug):
    vlink = Video.objects.get(slug=slug)
    vlink.delete()
    return redirect("videos")

def user(request):
    users = User.objects.all().order_by('first_name')
    context = {
        'users': users
    }
    return render(request, 'admins/users.html', context)

def comment(request):
    comments = Comment.objects.all().order_by('date').reverse()
    context = {
        'comments': comments
    }
    return render(request, 'admins/comments.html', context)

def com_delete(request, id):
    clink = Comment.objects.get(id=id)
    clink.delete()
    return redirect("comments")
