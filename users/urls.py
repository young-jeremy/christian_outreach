from django.urls import path
from . import views
app_name = 'users'

urlpatterns = [
    path('register', views.register_view, name='register'),
    path('change_password/', views.change_password, name='change_password'),
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('account_settings/', views.account_settings, name='account_settings'),
    path('account_settings/community/', views.community_list, name='community'),
    path('view_notifications/', views.view_notifications, name='view_notification'),
    path('view_notifications/mark_all_as_read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('account_settings/create_community/', views.create_community, name='create_community'),
    path('community_list/', views.community_list, name='community_list'),
    path('community_details/<int:community_id>/', views.community_details, name='community_details'),
    path('join_community/', views.join_community, name='join_community'),
    path('splash_register/', views.splash_register, name='splash_register'),
    path('account_settings/<int:channel_id>/subscribe/', views.subscribe, name='subscribe'),
    path('apps/', views.apps, name='apps'),
    path('notifications/', views.view_notifications, name='view_notifications'),
    path('add_subscriptions/', views.toggle_subscription, name='add_subscriptions'),
    path('profile/', views.profile, name='profile'),
    path('create_profile/', views.create_profile, name='create_profile'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check_nudity/', views.check_for_nudity, name='check_nudity'),
    path('subscribe/<int:channel_id>/', views.subscribe, name='subscribe'),
    path('channels_list/', views.channels, name='channel_list'),
    path('channels_subscribed/', views.subscribed_channels, name='channels_subscribed'),
    path('sign_up/', views.sign_up, name='sign_up'),
    path('register_new_user/', views.register_new_user, name='register_new_user'),


    # P
    path('password/', views.password_reset_request, name='password_reset'),

    # U
    path('update_profile/', views.update_profile, name='update_profile'),
    path('password_reset/', views.password_reset_request, name='password_reset'),

    # S
    path('signup/', views.signup_view, name='signup'),

    # R
    path('register/', views.register, name='register'),



]

