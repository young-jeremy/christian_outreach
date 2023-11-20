# Import necessary modules
from django.shortcuts import get_object_or_404
from .models import Video


def get_related_videos(video_id, max_results=5):
    # Fetch the currently viewed video
    current_video = get_object_or_404(Video, pk=video_id)

    # Get all videos with common tags (excluding the current video)
    related_videos = Video.objects.filter(tags__in=current_video.tags.all()) \
        .exclude(pk=video_id) \
        .distinct()  # Ensure distinct videos

    # Limit the number of related videos to the specified maximum
    related_videos = related_videos[:max_results]

    return related_videos

