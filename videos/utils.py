# utils.py
from moviepy.editor import VideoFileClip
from django.core.files.uploadedfile import InMemoryUploadedFile


def get_video_duration(video_file):
    try:
        if isinstance(video_file, InMemoryUploadedFile):
            # Ensure the file is an uploaded file
            video = VideoFileClip(video_file)
            duration = int(video.duration)
            return duration
        else:
            return 0  # Return 0 if the file is not valid
    except Exception as e:
        # Handle any exceptions that may occur when reading the video
        return 0  # Return 0 if unable to get the duration
