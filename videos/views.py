from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect, reverse
from django. views import View
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from .models import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators import gzip
from .forms import ContentModerationForm
from django.core.paginator import Paginator
from users.models import *
from comments.forms import CommentForm
from comments.models import Comment
from datetime import timedelta, datetime
from users.signals import send_notification
import logging
from users.custom_decorators import channel_verified_required
import json
import cv2
import threading
from moviepy.editor import VideoFileClip
from haystack.query import SearchQuerySet
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse
from users.models import Subscription, Notifications
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forbidden_content import has_forbidden_content
from django.contrib.contenttypes.models import ContentType
from .recommendations import get_video_recommendations
# from utils import check_for_nudity
from users.models import Report
from users.forms import ReportForm, ChannelForm
from django.views.generic import ListView, DetailView
from .forms import VideoForm, VideoSearchForm, VideoUploadForm, ModerationRequestForm, ShortVideoForm, ContentSubmissionForm, CommentEditForm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from google.cloud import vision
from django.db.models import Q
import nltk
from elasticsearch_dsl import Index
from .documents import VideoDocument
from .models import Video, WatchLater
import speech_recognition as sr
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
# from moviepy.editor import TextClip, FileClip, CompositeVideoClip
import pysrt
import sys
from google.cloud import speech

logger = logging.getLogger(__name__)
recognizer = sr.Recognizer()


def time_to_seconds(time_obj):
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds/1000


def create_subtitle_clips(subtitles, videosize, fontsize=24, font='Arial', color='yellow', debug=False):
    subtitle_clips = []
    for subtitle in subtitles:
        start_time = time_to_seconds(subtitle.start)
        end_time = time_to_seconds(subtitle.end)
        duration = end_time-start_time

        video_width, video_height = videosize
        text_clip = TextClip(subtitle.text, bg_color='black', font=font, fontsize=fontsize, size=(video_width*3/4, None), methods='caption').set_start(start_time).set_duration(duration)
        subtitle_x_position = 'center'
        subtitle_y_position = video_height*4/5
        text_position = (subtitle_y_position, subtitle_x_position)
        subtitle_clips.append(text_clip.set_position(text_position))
        return subtitle_clips
    video = VideoFileClip()


"""text = "Your transcribed text"
subtitle_duration = 5  # Adjust as needed
text_chunks = [text[i:i + subtitle_duration] for i in range(0, len(text), subtitle_duration)]

start_time = 0
for i, chunk in enumerate(text_chunks):
    end_time = start_time + subtitle_duration
    subtitle = TextClip(chunk, fontsize=24, color='white')
    subtitle = subtitle.set_position(('center', 'bottom')).set_duration(subtitle_duration)
    subtitle = subtitle.set_start(start_time)
    subtitle.write_videofile(f'subtitle_{i}.mp4', codec='libx264')
    start_time = end_time

with sr.AudioFile('video_audio.wav') as source:
    audio = recognizer.record(source)

try:
    text = recognizer.recognize_google(audio)  # You can use other engines
    print("Transcription: " + text)
except sr.UnknownValueError:
    print("Google Speech Recognition could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Google Speech Recognition service; {0}".format(e))


video = VideoFileClip(video_path)
subtitles = [VideoFileClip(f'subtitle_{i}.mp4') for i in range(len(text_chunks))]

final_video = video.set_duration(sum([subtitle.duration for subtitle in subtitles]))
final_video = final_video.set_audio(audio_clip)

for subtitle in subtitles:
    final_video = final_video.set_duration(subtitle.duration)
    final_video = final_video.set_duration(subtitle.duration)
    final_video = final_video.set_duration(subtitle.duration)

final_video.write_videofile('video_with_subtitles.mp4')

"""


def home(request):
    template_name = 'home/home.html'
    all_gospel_videos = Video.objects.all()
    all_videos = Video.objects.all()
    approved_videos = Video.objects.filter(status='APPROVED')
    rejected_videos = Video.objects.filter(status='REJECTED')
    ads = Advertisement.objects.all()
    videos_per_page = 9
    paginator = Paginator(approved_videos, videos_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # path = video.path

    # form = VideoForm(request.POST or None, request.FILES or None)
    # if form.is_valid():
    #     form.save()

    context = {
        'approved_videos': approved_videos,
        'rejected_videos': rejected_videos,
        'ads': ads,
        'all_gospel_videos': all_gospel_videos,
    }
    return render(request, template_name, context)


def sermons(request):
    template_name = 'home/sermons.html'
    sermons_videos = Video.objects.filter(category='SERMON')
    return render(request, template_name, {'sermons_videos': sermons_videos})


def gospel_made_for_kids(request):
    template_name = 'home/gospel_made_for_kids.html'
    gospel_for_kids = Video.objects.filter(category='GOSPEL_MADE_FOR_KIDS')
    return render(request, template_name, {'gospel_for_kids': gospel_for_kids})


def praise_and_worship(request):
    template_name = 'home/praise_and_worship.html'
    praise_and_worship_videos = Video.objects.filter(category='PRAISE_AND_WORSHIP')
    return render(request, template_name, {'praise_and_worship_videos': praise_and_worship_videos})


def music(request):
    template_name = 'home/music_videos.html'
    music_videos = Video.objects.filter(category='MUSIC')
    return render(request, template_name, {'music_videos': music_videos})


def index_video(video):
    video_doc = VideoDocument(
        meta={'id': video.id},
        title=video.title,
        description=video.description,
    )
    video_doc.save()


def search_video(request):
    template_name = 'videos/search_videos.html'
    search_form = VideoSearchForm(request.GET)
    query = search_form['query'].value() if search_form.is_valid() else None
    videos = Video.objects.filter(title__icontains=query) if query else []

    return render(request, template_name, {'search_form': search_form, 'query': query, 'videos': videos})


def video_search(request):
    template_name = 'videos/video_search_results.html'
    query = request.GET.get('query')
    search_form = VideoSearchForm(request.GET, request.FILES)
    search_results = []
    # Search for the videos matching the query
    if query:
        try:
            # perform search using haystack
            search_results = SearchQuerySet().filter(content=query)

            query_str = json.dumps(search_results.query.to_dict(), indent=2)
            logger.debug(f'Elasticsearch Query: \n{query_str}')
            logger.debug(f'Search Results: \n{search_results}')
        except Exception as e:
            logger.error(f'Search Error: {e}')

    return render(request, template_name, {'query': query, 'search_form': search_form, 'search_results': search_results})


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


def create_channel(request):
    template_name = 'videos/create_channel.html'
    form = ChannelForm()
    if request.user.is_authenticated:
        try:
            channel = request.user
        except Channel.DoesNotExist:
            channel = None
            if channel:
                messages.warning(request, "You already have a channel, Enjoy your Christian Content")
                return redirect('home:home')
            if request.method == 'POST':
                channel_name = request.POST('channel_name')
                new_channel = Channel(user=request.user, channel=channel_name)
                new_channel.save()
                messages.success(request, 'New channel created successfully! You are now verified to upload on our site')
                return redirect('home:home')
            return render(request, template_name,)
    else:
        messages.error(request, "You need to be logged in in order to create a channel")
        return redirect('users:login')
    return render(request, template_name)


def channel_list(request):
    template_name = 'videos/channel_list.html'
    channels = Channel.objects.filter(owner=request.user)
    return render(request, template_name, {'channels': channels})


def admin_dashboard(request):
    videos = Video.objects.all()

    # path = video.path

    # form = VideoForm(request.POST or None, request.FILES or None)
    # if form.is_valid():
    #     form.save()

    context = {
        'videos': videos,
        # 'form': form,
    }
    return render(request, 'videos/dashboard.html', context)


def admin_panel(request):
    form = VideoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()

    context = {

        'form': form,
    }
    return render(request, 'videos/admin_panel.html', context)


@login_required()
@channel_verified_required
def upload_form(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            content_file = request.FILES['content']
            content = content_file.read().decode('utf-8')
            video = form.save(commit=False)
            is_nudity = check_for_nudity(video.video_content.read())
            if is_nudity:
                messages.error(request, 'The content contains nudity, Please upload another video')
            else:
                video.save()
                messages.success(request, 'Video uploaded successfully')
                return redirect('videos:upload_video')

            if has_forbidden_content(content):
                # Content contains forbidden words or patterns
                return render(request, 'videos/upload.html', {'form': form, 'error_message': 'Content contains inappropriate words. Please review your content.'})

            # Save or process the content (e.g., save to the database)
            # ...

            return redirect('videos:upload_success')  # Redirect to a success page
    else:
        form = VideoForm()

    return render(request, 'videos/admin_panel.html', {'form': form})


def upload_success(request):
    template_name = 'videos/upload_success'
    return render(request, template_name)


def recommended(request):
    template_name = 'videos.recommended.html'
    # Retrieve video data from the database
    recommended_videos = Video.objects.all()

    # Create a TF-IDF vectorizer
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')

    # Combine video descriptions and categories to create a text field for each video
    video_texts = [f'{video.description} {video.category}' for video in recommended_videos]

    # Compute TF-IDF vectors for video descriptions and categories
    tfidf_matrix = tfidf_vectorizer.fit_transform(video_texts)

    # Calculate cosine similarity between user preferences and video TF-IDF vectors
    user_preferences = 'made_for_gospel praise_and_worship preachings'  # Replace with user's preferences
    user_preferences_vector = tfidf_vectorizer.transform([user_preferences])
    cosine_sim = linear_kernel(user_preferences_vector, tfidf_matrix)

    # Get the indices of videos sorted by similarity
    video_indices = cosine_sim[0].argsort()[::-1]

    # Recommend videos based on similarity
    recommended_videos = [recommended_videos[i] for i in video_indices]

    # Pass the recommended videos to the template
    context = {'recommended_videos': recommended_videos}
    return render(request, template_name, context)


def history(request):
    template_name = 'videos/watched_videos.html'
    return render(request, template_name)


def library(request):
    template_name = 'base_channel.html'
    user = request.user
    videos_uploaded = Video.objects.filter(owner=user)

    return render(request, template_name, {'videos_uploaded': videos_uploaded})


def liked_videos(request):
    template_name = 'videos/liked_videos.html'
    liked_videos = LikedVideo.objects.get(liked=True)
    return render(request, template_name, {'liked_videos': liked_videos })


def trending(request):
    template_name = 'videos/trending.html'
    return render(request, template_name)


@login_required()
def watch_later(request):
    template_name = 'videos/watch_later.html'
    watch_later_videos = Video.objects.filter(owner=request.user)
    return render(request, template_name, {'watch_later_videos': watch_later_videos})


@login_required()
def add_watch_later(request, video_id):
    template_name = 'videos/add_to_watch_later.html'
    try:

        video = Video.objects.get(pk=video_id)

        # Create a WatchLater instance for the authenticated user and the selected video
        WatchLater.objects.create(user=request.user, video=video)

        return redirect('videos:watch_later')
    except Video.DoesNotExist:
        video = Video.objects.filter(pk=video_id)
        return render(request, template_name, {'video': video})


def remove_watch_later(request, watch_later_id):
    watch_later_video = Video.objects.filter(id=watch_later_id)
    watch_later_video.delete()
    return redirect('videos:watch_later')


def your_videos(request):
    template_name = 'videos/your_videos.html'
    return render(request, template_name)


def status(request, video_id):
    template_name = 'videos/status.html'
    video = Video.objects.filter(id=video_id)
    video_status = Video.objects.filter(video=video, status=video_id.status)
    return render(request, template_name, {'video_status': video_status})


def coming_events(request):
    template_name = 'videos/coming_events.html'
    return render(request, template_name)


def overview(request):
    template_name = 'videos/overview.html'
    return render(request, template_name)


def update_video_views(request, video_id):
    template_name = 'videos/video_details.html'
    video = Video.objects.get(pk=video_id)
    if request.method == 'POST':
        start_time = datetime.strptime(request.POST.get('start_time'), '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(request.POST.get('end_time'), '%Y-%m-%d %H:%M:%S')
        duration_watched = (end_time-start_time).total_seconds()
        if duration_watched >= 30:
            video = Video.objects.get(pk=video_id)
            video.view_count += 1
            video.save()
            VideoView.objects.create(video=video, user=request.user)
            return JsonResponse({'message': 'View counted successfully'})
        return JsonResponse({'message': 'View not counted'})
    context = {
        'video': video

        }
    return render(request, template_name, context)


@login_required()
def dislike_video(request, video_id):
    template_name = 'videos/disliked_videos.html'
    video = get_object_or_404(Video, pk=video_id)
    dislike, created = Dislike.objects.get_or_create(user=request.user, video=video)

    if not created:
        dislike.delete()
        return redirect('videos:video_details', video_id=video_id)
    return render(request, template_name, {'video': video, 'dislike': dislike})


@login_required
def share_video(request, video_id):
    video = get_object_or_404(Video, pk=video_id)
    # Check if the user has already shared the video
    shared = Share.objects.filter(user=request.user, video=video).exists()

    if not shared:
        # Create a new share entry
        Share.objects.create(user=request.user, video=video)

    return redirect('videos:video_details', video_id=video_id)


def upload_image(request):
    if request.method == 'POST':
        uploaded_image = request.FILES.get('image')
        if check_for_nudity(uploaded_image.url):
            return HttpResponse('Nudity detected. This content is not allowed.')
        else:
            # Process and save the image as acceptable content
            # ...
            return HttpResponse('Image uploaded successfully.')


def report_content(request, object_id):
    template_name = 'users/report_content.html'
    # content_type = ContentType.objects.get_for_id(content_type_id)
    # content_object = content_type.get_objects_for_this_type(id=object_id)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            Report.objects.create(
                user=request.user,
                # content_type=content_type,
                reason=reason,
                object_id=object_id,
            )
            return redirect('report_success')
        else:
            form = ReportForm()

        return render(request, template_name, {'form': form, })


def post_comment(request):
    template_name = 'videos/video_details.html'
    if request.method == 'POST':
        # video = Video.objects.get(pk=video_id)
        text = request.POST['text']
        video_id = request.POST.get('video_id')
        Comment.objects.create(video_id=video_id, user=request.user, text=text)
        send_notification(sender=request.user, recipient=video_id.user, video=video_id, interaction_type='comment')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


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


def send_notifications(sender, recipient, interaction_type, video):
    content = f'{sender.username} {interaction_type} your video: {video.title}'
    notification = Notifications(user=recipient, video=video, content=content)
    notification.save()


def subscription_success(request):
    template_name = 'videos/subscriptions_success.html'
    return render(request, template_name)


def create_video(request):
    template_name = 'videos/create_video.html'
    if request.method == 'POST':
        form = VideoForm(request.POST)
        if form.is_valid():
            video = form.save(commit=False)
            video.save()
            return redirect('videos:videos')
    else:
        form = VideoForm()
        return render(request, template_name, {'form': form})

    return render(request, template_name)


def edit_video(request):
    template_name = 'videos/edit_video.html'
    video = Video.objects.filter()
    if request.method == 'POST':
        form = VideoForm(request.POST, instance=video)


def submit_content(request):
    template_name = 'videos/content_submission.html'
    if request.method == 'POST':
        form = ContentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.save()
            content.user = request.user
            content.save()
            ModerationRequest.objects.create(user=request.user, content=content)
            return redirect('videos:content_submission_success')
        else:
            form = ContentSubmissionForm()
            return render(request, template_name, {'form': form})


def blocked_videos(request,):
    template_name = 'videos/blocked_videos.html'
    moderated_videos = Video.objects.filter(status__in=['REJECTED', 'BLOCKED'])
    return render(request, template_name, {'moderated_videos': moderated_videos})


def moderation_dashboard(request):
    template_name = 'videos/moderation_dashboard.html'
    if request.method == 'POST':
        form = ModerationRequestForm(request.POST)
        if request.user.is_staff:
            moderation_requests = ModerationRequest.objects.filter(is_approved=False)
            return HttpResponse({'moderation_requests': 'moderation_requests'})
        else:
            return redirect('videos:access_denied')
    else:
        form = ModerationRequestForm()
        moderation_requests = ModerationRequest.objects.filter(is_approved=False)
    return render(request, template_name, {'form': form, 'moderation_requests': moderation_requests})


def approve_content(request, video_id):
    if request.user.is_staff:
        content = get_object_or_404(Video, id=video_id)
        content.is_approved = True
        content.save()
        return redirect('videos:moderation_dashboard')
    else:
        return redirect('videos:access_denied')


def view_content_guidelines(request):
    template_name = 'videos/content_guidelines.html'
    guidelines = ContentGuidelines.objects.all()
    return render(request, template_name, {'guidelines': guidelines})


def video_details(request, video_id):
    video = Video.objects.get(pk=video_id)
    msg = False
    channel = video.channel
    user = request.user
    report = ReportForm
    is_subscribed = Subscription.objects.filter(user=user, channel=channel).exists()
    related_videos = Video.objects.filter(category=video.category).exclude(pk=video_id).order_by('-id')[:5]
    comments = Comment.objects.filter(video=video)
    if request.method == 'POST':
        if request.user.is_authenticated:
            user = request.user
            if video.likes:
                likes.remove()
                msg = False
            else:
                video.likes
                msg = True
        form = CommentForm(request.POST)
        if form.is_valid():
            # video_id = form.cleaned_data('video_id')
            video = get_object_or_404(Video, pk=video_id)
            comment = form.save(commit=False)
            comment.user = request.user
            comment.video = video
            comment.save()
            return redirect('videos:video_details', video_id=video_id)
    else:
        form = CommentForm()
        # liked = Like.objects.filter(user=request.user, video=video).exists()
        # disliked = Dislike.objects.filter(user=request.user, video=video).exists()
    return render(request, 'videos/video_details.html', {'video': video, 'related_videos': related_videos, 'form': form, 'comments': comments, 'channel': channel, 'is_subscribed': is_subscribed, 'msg': msg})


def record_upload_video(request):
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('videos:dashboard')  # Redirect to a list of uploaded videos
    else:
        form = VideoUploadForm()

    return render(request, 'videos/record_video.html', {'form': form})


def favorite_videos(request):
    # Retrieve favorite videos for the current user
    user_profile = CustomUser.objects.filter(username=request.user)
    user_favorite_videos = Profile.objects.get(favorite_videos=request.user.username.favorite_videos)
    return render(request, 'videos/user_favorite_videos.html', {'user_favorite_videos': user_favorite_videos})


def liked_videos(request):
    # Retrieve liked videos for the current user
    user_liked_videos = LikedVideo.objects.filter(user=request.user)
    return render(request, 'videos/liked_videos.html', {'user_liked_videos': user_liked_videos})


def watched_videos(request):
    # Retrieve watched videos for the current user
    watched_videos = WatchedVideo.objects.filter(user=request.user)
    return render(request, 'videos/watched_videos.html', {'watched_videos': watched_videos})


def settings(request):
    template_name = 'videos/video_settings.html'
    form = VideoForm()
    if request.method == 'POSt':
        form = VideoForm(request.POST, request.FILE)
        if form.is_valid():
            video_settings = form.save(commit=False)
            video_settings.save()
            return render('videos:settings_success')
        else:
            form = VideoForm()
    return render(request, template_name, {'form': form, })


def video_settings(request, video_id):
    template_name = 'videos/video_settings.html'
    video = get_object_or_404(Video, pk=video_id)
    return render(request, template_name, {'video': video})


def delete_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        video.delete()
        return redirect('videos:home')  # Redirect to the user's dashboard


def promote_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        video.promoted = True
        video.save()
        return redirect('videos:video_settings', video_id=video.id)


def upload_short_videos(request):
    template_name = 'videos/upload_short_videos.html'

    if request.method == 'POST':
        # Get the uploaded video file
        uploaded_video = request.FILES.get('video')

        # Check the video's duration and size
        max_duration = 60  # Maximum duration in seconds (1 minute)
        max_file_size = 20 * 1024 * 1024  # Maximum file size in bytes (20MB)

        if uploaded_video.size > max_file_size:
            return JsonResponse({'error': 'File size exceeds the limit.'})

        # Use a custom file upload handler to check video duration
        def handle_uploaded_file(f):
            media_type = f.content_type.split('/')[0]  # 'video' part of content type
            if media_type == 'video':
                duration = get_video_duration(f.temporary_file_path())
                if duration > max_duration:
                    return JsonResponse({'error': 'Video duration exceeds the limit.'})

        # Set the custom upload handler for the duration check
        request.upload_handlers = [TemporaryFileUploadHandler(request)]
        # Process the uploaded file with the custom handler
        uploaded_video = request.FILES.get('video')
        response = handle_uploaded_file(uploaded_video)

        if response:
            return response

        # Save the video to your media directory and store its path in the database
        # (You need to configure your media settings accordingly)
        # Example code to save the video:
        # video = VideoModel(video_file=uploaded_video)
        # video.save()

        return JsonResponse({'success': 'Video uploaded successfully.'})

    return render(request, template_name)


# Function to get video duration (you need to install the required library)
def get_video_duration(file_path):
    clip = VideoFileClip(file_path)
    return clip.duration


def short_video_list(request):
    short_videos = ShortVideo.objects.filter(uploader=request.user)
    return render(request, 'videos/short_videos.html', {'short_videos': short_videos})


def notify_video_owner(video, user, liked):
    owner = video.user  # Assuming the video model has a ForeignKey to the user who uploaded it
    if liked:
        message = f"{user.username} liked your video: {video.title}"
    else:
        message = f"{user.username} unliked your video: {video.title}"
    messages.info(owner, message)


@login_required
def like_video(request, video_id):
    if request.method == 'POST':

        video = Video.objects.get(pk=video_id)
        user = request.user
        current_likes = video.likes
        liked = VideoLikes.objects.filter(user=user, video=video).count()
        if not liked:
            liked = VideoLikes.objects.create(video=video, user=user)
            current_likes += 1
        else:
            liked = VideoLikes.objects.create(video=video, user=request.user).delete()
            video = Video.objects.get(id=video_id)
            video.likes = current_likes
            video.save()
    video = Video.objects.get(id=video_id)
    return HttpResponseRedirect(reverse('videos:video_details', args=[video.id]), )


@login_required
def dislike_video(request, video_id):
    if request.method == 'POST':
        user = request.user
        video_id = request.POST.get('video_id')
        video = Video.objects.filter(video=video_id, user=user)
        try:
            video_like = VideoLikes.objects.get(user=user, video=video)
            video_like.delete()
            liked = False
        except VideoLikes.DoesNotExist:
            video_like = VideoLikes(user=user, video=video)
            video_like.save()
            liked = True

            notify_video_owner(Video, user, liked, )
            return JsonResponse({'success': True, 'liked': liked})
        return JsonResponse({'success': False})


def record_short_videos(request):
    template_name = 'videos/record_short_videos.html'
    if request.method == 'POST':
        form = ShortVideoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(request, 'videos:short_video_list')
    # Redirect to a page where the user can view the videos.
    else:
        form = ShortVideoForm()

    return render(request, template_name, {'form': form})


def video_traffic(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    # Assuming you have fields like 'views', 'likes', 'shares', 'comments' in your Video model
    views = video.views
    likes = LikedVideo.objects.filter(video=video)
    # shares = video.shares
    comments = video.comments

    return render(request, 'videos/video_traffic.html', {
        'video': video,
        'views': views,
        'likes': likes,
        # 'shares': shares,
        'comments': comments,
    })



def privacy_policy(request):
    template_name = 'home/privacy_policy.html'
    return render(request, template_name)


def public_terms_of_service(request):
    template_name = 'home/public_terms_of_service.html'
    return render(request, template_name)


def moderate_content(request, video_id):
    video = Video.objects.get(pk=video_id)
    status = Privacy.objects.filter(status=Privacy.status)

    if request.method == 'POST':
        form = ContentModerationForm(request.POST, instance=video)
        if form.is_valid():
            form.save()
            return redirect('videos:videos')  # Redirect to the list of content
    else:
        form = ContentModerationForm(instance=video)

    return render(request, 'privacy/moderate_content.html', {'form': form, 'video': video, 'status': status})


def short_video_details(request, short_id):
    template_name = 'videos/short_video_details.html'
    video = get_object_or_404(ShortVideo, pk=short_id)
    video.views += 1
    video.save()
    return render(request, template_name, {'video': video})


def blocked_video_details(request, video_id):
    template_name = 'videos/blocked_video_details.html'
    video = Video.objects.filter(pk=video_id)
    rejected_videos = Video.objects.filter(status='rejected')
    return render(request, template_name, {'rejected_videos': rejected_videos})


def approved_videos(request):
    template_name = 'videos/approved_videos.html'
    approved_content = Video.objects.filter(is_approved=True)
    return render(request, template_name, {'approved_content': approved_content})


def pending_videos(request):
    template_name = 'videos/pending_videos.html'
    total_pending_videos = Video.objects.filter(status='PENDING')
    return render(request, template_name, {'total_pending_videos': total_pending_videos})


def playlist_videos(request):
    template_name = 'videos/playlist_videos.html'
    total_playlist_videos = Playlist.objects.filter(user=request.user)
    return render(request, template_name, {'total_playlist_videos': total_playlist_videos})


def moderation_request(request):
    template_name = 'videos/moderation_requests.html'
    moderation_requests = ModerationRequest.objects.filter(is_approved=False)
    if request.method == 'POST':
        form = ModerationRequestForm(request.POST)
        if request.user.is_staff:
            moderation_requests = ModerationRequest.objects.filter(is_approved=False)
            return HttpResponse({'moderation_requests': 'moderation_requests'})
        else:
            return redirect('videos:access_denied')
    else:
        form = ModerationRequestForm()
        moderation_requests = ModerationRequest.objects.filter(is_approved=False)
    return render(request, template_name, {'moderation_requests': moderation_requests, 'form': form})


@login_required
def add_to_favorites(request, video_id):
    video = get_object_or_404(Video, pk=video_id)

    # Get or create user profile
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    # Check if the video is not already in favorites to avoid duplicates
    if video not in user_profile.favorite_videos.all():
        user_profile.favorite_videos.add(video)
        user_profile.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'already_added'})


class VideoHistoryListView(ListView):
    model = VideoHistory
    template_name = 'videos/video_history.html'
    context_object_name = 'video_history'
    paginate_by = 10  # Number of history entries per page

    def get_queryset(self):
        return VideoHistory.objects.filter(user=self.request.user)


def live_stream(request):
    # In a real-world scenario, you would fetch the live stream URL or embed code here.
    template_name = 'videos/live_stream.html'
    live_stream_url = "YOUR_LIVE_STREAM_URL"  # Replace with your live stream URL

    return render(request, template_name, {'live_stream_url': live_stream_url})


class VideoCamera(object):
    def __int__(self):
        self.video = cv2.VideoCapture(0)
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        image = self.frame
        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobtes()

    def update(self):
        while True:
            (self.grabbed, self.frame) = self.video.read()


def camera_home(request):
    template_name = 'videos/video_camera.html'
    try:
        cam = VideoCamera()
        return StreamingHttpResponse(gen(cam), content_type='multipart/x-mixed-replace;boundary=frame')
    except:
        pass
    return render(request, template_name)


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'r\n\r\n'
        )


def all_videos(request):
    template_name = 'home/all_videos.html'
    all_gospel_videos = Video.objects.all()
    return render(request, template_name, {'all_gospel_videos': all_gospel_videos})


def live_videos(request):
    template_name = 'videos/live_videos.html'
    return render(request, template_name)


def generate_captions(request):
    template_name = 'videos/generate_captions.html'
    if request.method == 'POST':
        video = request.FILES['video']
        client = speech.SpeechClient()

        with video.open('rb') as video_file:
            content = video_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        response = client.recognize(config=config, audio=audio)

        captions = [result.alternatives[0].transcript for result in response.results]

        return render(request, 'captions.html', {'captions': captions})

    return render(request, template_name)


class Requirement(View):
    form_class = CommentForm
    template_name = 'ktu/comment.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        comment = Comment.objects.all()
        context = {'page_obj': comment, 'form': form}

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            comment_form = form.save(commit=False)
            comment_form.user = request.user
            comment_form.save()
            messages.success(request, 'Your comment successfully addedd')

            return HttpResponseRedirect(reverse('comment'))

        context = {'form': form}

        return render(request, self.template_name, context)


class UpdateCommentVote(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):

        comment_id = self.kwargs.get('comment_id', None)
        opinion = self.kwargs.get('opinion', None)

        comment = get_object_or_404(Comment, id=comment_id)

        try:
            comment.dis_likes
        except Comment.dis_likes.RelatedObjectDoesNotExist as identifier:
            DisLike.objects.create(comment=comment)

        try:
            comment.likes
        except Comment.likes.RelatedObjectDoesNotExist as identifier:
            Like.objects.create(comment = comment)

        if opinion.lower() == 'like':

            if request.user in comment.likes.users.all():
                comment.likes.users.remove(request.user)
            else:
                comment.likes.users.add(request.user)
                comment.dis_likes.users.remove(request.user)

        elif opinion.lower() == 'dis_like':

            if request.user in comment.dis_likes.users.all():
                comment.dis_likes.users.remove(request.user)
            else:
                comment.dis_likes.users.add(request.user)
                comment.likes.users.remove(request.user)
        else:
            return HttpResponseRedirect(reverse('comment'))
        return HttpResponseRedirect(reverse('comment'))


def reply_comment(request):
    template_name = 'videos/video_details.html'
    return render(request, template_name, )


def add_subscriptions(request, id):
    sub = Subscribe.objects.get(id=id)
    sub_list = list(sub.subscriber.values())
    return JsonResponse(sub_list, safe=False, status=200)


def subscription_load(request, id):
    subscribers = Subscribe.objects.get(id=id)
    user = request.user
    if user in subscribers.subscriber.all():
        subscribers.subscriber.remove(user)
        response = 'Subscribe'
        return JsonResponse(response, safe=False, status=200)
    else:
        subscribers.subscriber.add(user)
        response = 'Unsubscribe'
        return JsonResponse(response, safe=False, status=200)


class SubChannelSubscriptionView(ListView):
    template_name = 'subscription.html'
    model = Channel

    def get_queryset(self):
        return Channel.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(SubChannelSubscriptionView, self).get_context_data(**kwargs)
        context['sub_channel'] = Channel.objects.all()
        context['top'] = Channel.objects.filter(category__subchannel_subs__user=self.request.user)
        return context

    def subd(self, request):
        subchannel = get_object_or_404(Channel, pk=self.kwargs['pk'])
        is_subd = False
        if subchannel.subd.filter(pk=request.user).exists():
            subchannel.subd.remove(request.user)
            is_subd = False
        else:
            subchannel.is_subd.add(request.user)
            is_subd = True
        return reverse('videos:home')


def testimonies(request):
    template_name = 'home/testimonies.html'
    all_testimonies = Video.objects.filter(category='ALL_TESTIMONIES')
    return render(request, template_name, {'all_testimonies': all_testimonies})


def evangelism(request):
    template_name = 'home/evangelism.html'
    evangelism_videos = Video.objects.filter(category='EVANGELISM')
    return render(request, template_name, {'evangelism_videos': evangelism_videos})


def bible_discussions(request):
    template_name = 'home/bible_discussions.html'
    bible_discussion_videos = Video.objects.filter(category='BIBLE_DISCUSSIONS')
    return render(request, template_name, {'bible_discussion_videos': bible_discussion_videos})

