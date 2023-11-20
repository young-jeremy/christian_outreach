from users.models import *
from django.shortcuts import redirect, render, get_object_or_404
from .forms import *
from videos.models import *


def dashboard(request):
    template_name = 'dashboard/dark_theme.html'
    return render(request, template_name)


def content(request):
    template_name = 'dashboard/content.html'
    videos = Video.objects.all()
    return render(request, template_name, {'videos': videos})


def send_copyright_notice(request, user_id):
    template_name = 'dashboard/send_copyright_notice.html'
    user = CustomUser.objects.get(pk=user_id)  # Fetch the user
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            Notice.objects.create(user=user, content=content)
            # You can send an email notification to the user here
            return redirect('dashboard:notice_sent_successfully')  # Redirect to a success page
    else:
        form = NoticeForm()
    return render(request, template_name, {'form': form, 'user': user})


def copyright_notice_sent_successfully(request):
    template_name = 'dashboard/notice_sent_successfully.html'
    return render(request, template_name)


def all_comments(request):
    template_name = 'dashboard/all_comments.html'
    comments = Comment.objects.all()
    return render(request, template_name, {'comments': comments})


def video_traffic(request):
    template_name = 'dashboard/video_traffic.html'
    # Assuming you have fields like 'views', 'likes', 'shares', 'comments' in your Video model
    videos = Video.objects.all()
    # views = video.views
    # likes = video.likes
    # shares = video.shares
    # comments = video.comments

    return render(request, template_name, {

        'videos': videos
        # 'video': video,
        # 'views': views,
        # 'likes': likes,
        # 'shares': shares,
        # 'comments': comments,
    })


def analytics(request):
    template_name = 'dashboard/video_traffic.html'
    return render(request, template_name)


def customizations(request):
    template_name = 'dashboard/customizations.html'
    return render(request, template_name)


def earn(request):
    template_name = 'dashboard/earn.html'
    return render(request, template_name)


def subtitles(request):
    template_name = 'dashboard/subtitles.html'
    return render(request, template_name)


def audio_library(request):
    template_name = 'dashboard/audio_library.html'
    return render(request, template_name)


def report_something(request):
    template_name = 'dashboard/report_something.html'
    return render(request, template_name)


def video_settings(request):
    template_name = 'dashboard/video_settings.html'
    return render(request, template_name)


def channel_details(request, channel_id):
    template_name = 'videos/channel_details.html'
    channel = Channel.objects.get(pk=channel_id)
    user = request.user
    user_profile = Profile.objects.get_or_create(user=user)[0]
    account_subscriptions = Subscription.objects.filter(user=user)
    videos_uploaded = Video.objects.filter(owner=user)
    channels_subscribed = [subscription.channel for subscription in account_subscriptions]
    playlists = Playlist.objects.all()
    context = {
        'user_profile': user_profile,
        'account_subscriptions': account_subscriptions,
        'videos_uploaded': videos_uploaded,
        'channels_subscribed': channels_subscribed,
        'playlists': playlists

    }
    if request.method == 'POST':
        channel = Channel.objects.get(pk=channel_id)
        user = request.user
    else:
        channel = Channel.objects.create(owner=request.user,)
    return render(request, template_name, context)

