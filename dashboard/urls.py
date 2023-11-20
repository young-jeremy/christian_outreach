from django.urls import path
from . import views
app_name = 'dashboard'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('send_copyright_notice/<int:user_id>/', views.send_copyright_notice, name='send_copyright_notice'),
    path('notice_sent_successfully/', views.copyright_notice_sent_successfully, name='notice_sent_successfully'),
    path('all_comments/', views.all_comments, name='all_comments'),
    path('', views.content, name='content'),
    path('analytics/', views.video_traffic, name='analytics'),
    path('subtitles/', views.subtitles, name='subtitles'),
    path('customizations/', views.customizations, name='customizations'),
    path('earn/', views.earn, name='earn'),
    path('audio_library/', views.audio_library, name='audio_library'),
    path('report_something/', views.report_something, name='report_something'),
    path('video_settings/', views.video_settings, name='video_settings'),
    path('channel_details/<int:channel_id>/', views.channel_details, name='channel_details'),



]
