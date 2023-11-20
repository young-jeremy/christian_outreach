from django import forms
from .models import Video, UploadedVideo, ModerationRequest, ShortVideo, Channel, Comment
from moviepy.editor import VideoFileClip
from .models import LiveStreamEvent


class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedVideo
        fields = ['title', 'video_file']


class VideoForm(forms.ModelForm):
    video_id = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Video
        fields = ["title", "path", 'thumbnail', 'audience',
                  'language_and_captions_certification', 'license', 'category', 'description', ]


class VideoSearchForm(forms.Form):
    query = forms.CharField(
        # label='Search for videos',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Search'})
    )


class ContentSubmissionForm(forms.Form):
    class Meta:
        model = Video
        fields = ["title", "path", 'thumbnail', 'playlist', 'audience',
                  'language_and_captions_certification', 'license', 'category', 'comments_and_ratings']


class ModerationRequestForm(forms.ModelForm):
    class Meta:
        model = ModerationRequest
        fields = ['user', 'video', 'is_approved', ]


class ShortVideoForm(forms.Form):
    video = forms.FileField()

    class Meta:
        model = ShortVideo
        fields = ['title', 'description', 'video_file']

    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video:
            # Get the user-specified video duration (default to 1 minute)
            desired_duration = self.cleaned_data.get('desired_duration', 60)

            # Use moviepy to trim the video to the desired duration
            clip = VideoFileClip(video.temporary_file_path())
            if clip.duration <= desired_duration:
                return video

            trimmed_clip = clip.subclip(0, desired_duration)
            trimmed_clip.write_videofile(video.temporary_file_path())
            return video


class ContentModerationForm(forms.Form):
    class Meta:
        model = Video
        fields = ['moderation']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
          'comment': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
        }


class CommentEditForm(forms.Form):
    class Meta:
        model = Comment
        fields = ['text']


class LiveStreamEventForm(forms.ModelForm):
    class Meta:
        model = LiveStreamEvent
        fields = ['title', 'stream_key', 'start_time', 'description']
