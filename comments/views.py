from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django import views
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import stripe
from videos.forms import ContentModerationForm, ContentSubmissionForm
from videos.models import Playlist
from google.cloud import vision
from rest_framework import status, generics
from users.admin import CustomUserCreationForm
from .admin import *
from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import views as auth_views
from django.contrib.auth import login, logout
from .forms import *
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import requests
from videos.views import moderate_content
from django.template.loader import render_to_string
# from django.contrib.auth.decorators import check_captcha
import django.utils.encoding
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models.query_utils import Q
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from .forms import *
from django.core.mail import send_mail, BadHeaderError
from .models import *
from django.apps import apps
from django_cleanup import cleanup
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import serializers
from django.shortcuts import render


def create_comment(request):
    if request.method == 'POST':
        text_content = request.POST.get('text_content')
        toxicity_score = moderate_content(text_content)

        if toxicity_score is not None and toxicity_score >= 0.5:
            # The content is deemed toxic, take appropriate action (e.g., reject the comment)
            return render(request, 'toxic_content.html')
        else:
            # Save the comment to the database and display it
            Comment.objects.create(text_content=text_content)
            return render(request, 'comment_created.html')


# Create your views here.
@login_required
def edit_comment(request, comment_id):
    template_name = 'videos/video_details.html'
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return HttpResponse('Comment not found ', status=404)
    if request.method == 'POST':
        form = CommentEditForm(request.POST)
        if comment.user == request.user:
            comment_text = request.POST.get('comment_text')
            comment.text = comment_text
            comment.save()
            return HttpResponse('Comment updated successfully')
        else:
            return redirect('videos:video_details', video_id=comment.video.pk)
    else:
        form = CommentEditForm()
        return render(request, template_name, {'form': form})


def like_comment(request, comment_id):
    template_name = 'videos/video_details.html'
    if request.method == 'POST':
        comment = Comment.objects.get(pk=comment_id)
        user = request.user
        if user in comment.likes.all():
            comment.likes.remove(user)
        else:
            comment.likes.add(user)
        return JsonResponse({'likes_count': comment.likes.count()})
    else:
        comment = Comment.objects.get(pk=comment_id)
        return render(request, template_name, {'comment': comment})


def delete_comment(request, comment_id):
    template_name = 'videos/video_details.html'
    if request.method == 'POST':
        comment = get_object_or_404(Comment, pk=comment_id)
        # comment = Comment.objects.get(pk=comment_id)
        if comment.user == request.user:
            comment.delete()

        return redirect('videos:video_details', video_id=comment.video.pk)
    else:
        comment = get_object_or_404(Comment, pk=comment_id)
        return render(request, template_name, {'comment': comment})


