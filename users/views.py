from django.shortcuts import render, redirect, HttpResponseRedirect, reverse
from django.contrib.auth.decorators import user_passes_test
from django import views
from django.views.generic import ListView

from django.http import JsonResponse
from .models import Subscription
import stripe
# from .models import Channel
from videos.models import Playlist, Video
from google.cloud import vision
from rest_framework import status, generics
from .admin import CustomUserCreationForm
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

apps.get_models()


def splash_register(request):
    if request.session.get('beta'):

        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.username = hash(user.email)
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                user.save()
                username = user.username
                password = str(form.cleaned_data['password'])
                auth.login(request, user)
                request.session['first_visit'] = True
                return HttpResponseRedirect("videos:home")
            else:
                user = MyUserCreationForm(request.POST)
                return render_to_response("users/splash_register.html", {'form': form}, context_instance=RequestContext(request))
        return render_to_response("users/splash_register.html", context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('users:splash_register'))


def subscribe(request, channel_id):
    template_name = 'users/subscribe.html'
    channel = Channel.objects.get(pk=channel_id)
    user = request.user
    if not Subscription.objects.filter(subscriber=user, channel=channel).exists():
        Subscription.objects.create(user=user, channel=channel)
        return redirect('users:channel_details', channel_id=channel_id)
    return render(request, template_name, {'channel': channel, 'user': user})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            password2 = request.POST['password2']
            if password == password2:
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'That username is taken')
                    return redirect('register')
                else:
                    if User.objects.filter(email=email).exists():
                        messages.error(request, 'That email is being used')
                        return redirect('register')
                    else:
                        user = User.objects.create_user(username=username, password=password, email=email,
                                                        first_name=first_name, last_name=last_name)

                        user.save()
                        messages.success(request, 'You are now registered and can log in')
                        return redirect('login')
            else:
                messages.error(request, 'Passwords do not match')
                return redirect('register')
        else:
            form = CustomUserCreationForm()
    return render(request, 'users/register.html')


def account_settings(request):
    template_name = 'users/account_settings.html'
    user = request.user
    user_profile = Profile.objects.get_or_create(user=user)[0]
    account_subscriptions = Subscription.objects.filter(user=user)
    videos_uploaded = Video.objects.filter(owner=user)
    channel_description = user_profile.channel_description
    channel_cover_image = user_profile.channel_cover_image
    channels_subscribed = [subscription.channel for subscription in account_subscriptions]
    about = user_profile.bio

    # playlists = Playlists.objects.filter(pk=playlist_id)
    context = {
        'user_profile': user_profile,
        'account_subscriptions': account_subscriptions,
        'videos_uploaded': videos_uploaded,
        'channels_subscribed': channels_subscribed,
        'channel_description': channel_description,
        'channel_cover_image': channel_cover_image,
        'about': about,

        # 'playlists': playlists


    }
    return render(request, template_name, context)


def view_notifications(request):
    template_name = 'users/notifications.html'
    notifications = Notifications.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, template_name, {'notifications': notifications
                                           })


def mark_all_as_read(request):
    template_name = 'users/notifications.html'
    Notifications.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('users:view_notifications')


def apps(request):
    template_name = 'users/apps.html'
    return render(request, template_name)


def subscriptions(request):
    template_name = 'users/subscriptions.html'
    user = request.user
    user_profile = Profile.objects.get_or_create(user=user)[0]
    account_subscriptions = Subscription.objects.filter(subscriber=user)
    videos_uploaded = Video.objects.filter(owner=user)
    channels_subscribed = [subscription.channel for subscription in account_subscriptions]
    # playlists = Playlists.objects.filter(pk=playlist_id)
    context = {
        'user_profile': user_profile,
        'account_subscriptions': account_subscriptions,
        'videos_uploaded': videos_uploaded,
        'channels_subscribed': channels_subscribed,
        # 'playlists': playlists

    }
    return render(request, template_name, context)


def profile(request):
    template_name = 'users/profile.html'
    liked_videos = LikedVideo.objects.filter(user=request.user)

    # Retrieve favorite videos for a user
    favorite_videos = FavoriteVideo.objects.filter(user=request.user)

    # Retrieve watched videos for a user
    watched_videos = WatchedVideo.objects.filter(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been created!')
            return redirect('users:profile')
        else:
            u_form = UserUpdateForm()
            p_form = ProfileUpdateForm()
    else:
        u_form = UserUpdateForm()
        p_form = ProfileUpdateForm()
    return render(request, template_name, {'u_form': u_form, 'p_form': p_form, 'liked_videos': liked_videos, 'favorite_videos': favorite_videos, 'watched_videos': watched_videos})


@login_required()
def create_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile_form = form.save(commit=False)
            profile_form.user = request.user
            profile_form.save()
            return redirect('users:profile')
    else:
        form = ProfileForm
    return render(request, 'users/create_users.html', {'form': form})


def update_profile(request):
    template_name = 'users/update_profile.html'
    user_profile = Profile.objects.filter(user=request.user)
    if request.method == 'POST':
        form = ProfileForm()
        if form.is_valid():
            form.save()
            return redirect('users:profile')
        else:
            form = ProfileForm(instance=user_profile)
        return render(request, template_name, {'form': form})


def post_comment(request):
    if request.session.get('has_commented', False):
        return HttpResponse('you have already commented!')
    # c = comments.Comment(comment=new_comment)
    # c.save()
    request.session['has_commented'] = True
    return HttpResponse('Thanks for commenting')


def password_reset_request(request):
    template_name = 'users/password_reset.html'
    if request.method == 'POST':
        domain = request.headers['Host']
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = CustomUser.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = 'Password Request Reset'
                    email_template_name = 'users/password_reset_email.txt'
                    c = {
                        'email': user.email,
                        'domain': 'domain',
                        'site_name': 'Interface',
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'protocol': 'http',
                        'user': user,
                        'token': default_token_generator.make_token(user),
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse("Invalid Header found")
                    return redirect('users/password_reset/done/')
    password_reset_form = PasswordResetForm()
    context = {
            'password_reset_form': password_reset_form,
        }
    return render(request, template_name, context)


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('accounts:login')
        else:
            messages.info(request, 'Please correct the errors before proceeding')
    else:
        form = UserCreationForm(request.POST)
    return render(request, 'users/register.html', {'form': form})


def email_check(user):
    return user.email.endswith('@example.com')


def login_view(request):
    if request.method == 'POST':
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user_form = authenticate(username=username, password=password)
            if user_form is not None:
                login(request, user_form)
                messages.info(request, f"You are now logged in as {username}")
                return redirect('videos:home')
            else:
                if not request.user.email.endswith('@example.com'):
                    return redirect('/login/?next=%s' % request.path)
                else:
                    messages.error(request, "Invalid username or password.")
                    request.session.set_test_cookie()
        else:
            messages.error(request, "Invalid username or password.")

    else:
        messages.info(request, 'There is something wrong, check if there is a problem before logging in again')
        form = AuthenticationForm()
    return render(request=request, template_name="users/login.html",
                  context={"form": form, })


def sign_up(request):
    template_name = 'users/sign_up.html'
    if request.method == 'GET':
        form = CustomUserCreationForm()
        return render(request, 'users/register.html', {'form': form})

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            messages.success(request, 'You have singed up successfully.')
            login(request, user)
            return redirect('posts')
        else:
            return render(request, template_name, {'form': form})


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user_form = authenticate(username=username, password=raw_password)
            login(request, user_form, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home:home')
    else:
        form = CustomUserCreationForm(request.POST)
    return render(request, 'users/register.html', {'form': form})


@login_required(login_url='users/login')
def logout_view(request):
    try:
        del request.session['member_id']
    except KeyError:
        pass
    logout(request)
    return redirect('videos:home')


@login_required(login_url='users/login')
def update_profile(request):
    if request.method == 'POST':
        user_form = EditProfile(request.POST)
        profile_form = Profile(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.info(request, f"Your Profile Has Been Updated Successfully")
            return redirect('users:profile')
        else:
            messages.error(request, f"Please Correct The Errors Before Trying Again")
            return render(request, 'users/profile2.html', {'user_form': user_form, 'profile_form': profile_form})

    else:
        user_form = CustomUserCreationForm()
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        return render(request, 'users/profile2.html', {'user_form': user_form, 'profile_form': profile_form})


@login_required(login_url='users/login')
def profile(request):
    my_user_profile = CustomUser.objects.filter(email=request.user.profile).first()
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your Profile Was Updated Successfully!')
            return redirect('users:update_profile')
        messages.info(request, 'Click On  Edit Profile To Make Important Changes To Your Profile To Help Us track You')
        return render(request, 'users/profile.html', {'form': form})
    else:
        form = CustomUserCreationForm(request.POST)
        return render(request, 'users/profile.html', {'form': form, 'my_user_profile': my_user_profile})


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:update_profile')
        else:
            form = PasswordChangeForm(user=request.POST)
            return render(request, 'users/password_change.html', {'form': form})
    else:
        form = PasswordChangeForm(user=request.POST)
        return render(request, 'users/password_change.html', {'form': form})


def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:login')
        else:
            form = PasswordChangeForm(user=request.user)
            return render(request, 'accounts/password_reset.html', {'form': form})
    else:
        form = PasswordChangeForm(user=request.user)
        return render(request, 'users/password_reset.html', {'form': form})


def process_payment(user, amount):
    try:
        charge = stripe.Charge.create(
            amount=int(amount*100),
            currency='usd',
            source=user.payment_source,
        )
    except stripe.error.StripeError as e:
        print('There are error, kindly check before trying out')


def distribute_revenue(video, revenue):
    creators = video.creators.all()
    for creator in creators:
        share = (creator.revenue_sharing_rule.percentage_share / 100) * revenue
        # Transfer share to the content creator's account
        # Example: creator.account_balance += share
        creator.save()


def check_for_nudity(image_url):
    client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = image_url

    response = client.safe_search_detection(image=image)
    safe_search = response.safe_search_annotation

    return safe_search.adult == vision.Likelihood.LIKELY or safe_search.violence == vision.Likelihood.LIKELY


def create_user_profile(request):
    if not hasattr(request.user, 'userprofile'):
        user_profile = Profile(user=request.user)
        user_profile.save()
        return redirect('users:profile_edit')


def create_community(request):
    template_name = 'users/create_community.html'
    form = CommunityForm()
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            form.save(commit=False)
            return redirect('users:community_list')
        else:
            form = CommunityForm()
    return render(request, template_name, {'form': form})


def community_list(request):

    template_name = 'users/community_list.html'
    view_communities = Community.objects.all()

    return render(request, template_name, {'view_communities': view_communities})


def community_details(request, community_id):
    template_name = 'users/community_details.html'
    community = Community.objects.get(id=community_id)
    return render(request, template_name, {'community': community})


def join_community(request):
    template_name = 'users/join_community.html'
    if request.method == 'POST':
        form = JoinCommunityForm(request.POST)
        if form.is_valid():
            community_id = form.cleaned_data['community_id']
            community = Community.objects.get(id=community_id)
            user = request.user
            user.communities.add(community)
            return redirect('users:community_list')
    else:
        form = JoinCommunityForm()
    return render(request, template_name, {'form': form})


def channels(request):
    template_name = 'users/channel_list.html'
    channel_list = Channel.objects.all()
    return render(request, template_name)


def toggle_subscription(request):
    if request.method == 'POST':
        user = request.user  # Assuming you're using Django's built-in User model
        channel_id = request.POST.get('channel_id')
        channel = Channel.objects.get(id=channel_id)  # Replace 'Channel' with your channel model

        try:
            subscription = Subscription.objects.get(user=user, channel=channel)
            subscription.delete()  # Remove the subscription if it exists
            subscribed = False
        except Subscription.DoesNotExist:
            subscription = Subscription(user=user, channel=channel)
            subscription.save()  # Create a new subscription
            subscribed = True

        subscription_count = Subscription.objects.filter(channel=channel).count()

        return JsonResponse({'success': True, 'subscribed': subscribed, 'subscription_count': subscription_count})
    return JsonResponse({'success': False})


def subscribed_channels(request):
    # Assuming you are using Django's built-in User model
    template_name = 'users/subscriptions.html'
    user = request.user
    user_profile = Profile.objects.get_or_create(user=user)[0]
    account_subscriptions = Subscription.objects.filter(user=user)
    videos_uploaded = Video.objects.filter(owner=user)
    channel_description = user_profile.channel_description
    channel_cover_image = user_profile.channel_cover_image
    channels_subscribed = [subscription.channel for subscription in account_subscriptions]
    about = user_profile.bio

    # playlists = Playlists.objects.filter(pk=playlist_id)
    context = {
        'user_profile': user_profile,
        'account_subscriptions': account_subscriptions,
        'videos_uploaded': videos_uploaded,
        'channels_subscribed': channels_subscribed,
        'channel_description': channel_description,
        'channel_cover_image': channel_cover_image,
        'about': about,

        # 'playlists': playlists


    }

    return render(request, template_name, context)


def register_new_user(request):
    template_name = 'users/new_user_template.html'
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('users:profile')  # Redirect to user profile or another page
    else:
        form = CustomUserCreationForm()
    return render(request, template_name, {'form': form})

