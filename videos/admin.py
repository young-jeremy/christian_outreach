from django.contrib import admin
from .models import (
    Video, ContentGuidelines, Moderation, Privacy, Playlist, ModerationRequest, ShortVideo, WatchedVideo, LikedVideo,
    FavoriteVideo, Advertisement, Channel, VideoHistory, WatchLater

)
from django.utils.translation import ngettext
from django.contrib import messages

from django.contrib.auth import get_permission_codename


admin.site.register(Channel)


@admin.register(ContentGuidelines)
class ContentGuidelineAdmin(admin.ModelAdmin):
    list_display = ['title']


class VideoAdmin(admin.ModelAdmin):
    list_display = ['thumbnail', 'title', 'description', 'owner', 'status', 'privacy', 'channel', 'category', 'path',]

    actions = ['make_published', 'make_blocked', 'make_pending']

    @admin.action(description='Mark the SELECTED videos as APPROVED')
    def make_published(self, request, queryset):
        updated = queryset.update(status='APPROVED')
        self.message_user(request, ngettext(
            '%d video was successfully marked as published',
            '%d videos were successfully marked as published',
            updated,



        )
                  % updated, messages.SUCCESS
                          )

    @admin.action(description='Mark selected videos as BLOCKED')
    def make_blocked(self, request, queryset):
        updated = queryset.update(status='REJECTED')
        self.message_user(request, ngettext(
            '%d video was successfully marked as blocked',
            '%d videos were successfully marked as blocked',
            updated,



        )
                  % updated, messages.SUCCESS
                          )

    @admin.action(description='Mark selected videos as PENDING')
    def make_pending(self, request, queryset):
        updated = queryset.update(status='PENDING')
        self.message_user(request, ngettext(
            '%d video was successfully marked as pending',
            '%d video were successfully marked as pending',
            updated,



        )
                  % updated, messages.SUCCESS
                          )


admin.site.register(Video, VideoAdmin)
admin.site.register(Moderation)
admin.site.register(Playlist)
admin.site.register(ModerationRequest)
admin.site.register(ShortVideo)
admin.site.register(WatchedVideo)
admin.site.register(LikedVideo)
admin.site.register(FavoriteVideo)
admin.site.register(Advertisement)
admin.site.register(VideoHistory)
admin.site.register(WatchLater)


