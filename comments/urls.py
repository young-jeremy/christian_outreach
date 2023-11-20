from django.urls import path
from . import views
app_name = 'comments'
urlpatterns = [
    path('add_comment/', views.create_comment, name='add_comment'),
    path('<int:comment_id>/edit_comment/', views.edit_comment, name='edit_comment'),
    path('<int:comment_id>/delete_comment/', views.delete_comment, name='delete_comment'),
    path('like_comment/<int:comment_id>/', views.like_comment, name='like_comment'),




]
