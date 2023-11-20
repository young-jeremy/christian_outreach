from django import forms
from .models import Community
from videos.models import Channel
from django.contrib.auth import authenticate
from django.conf import settings
from .admin import UserChangeForm, CustomUserCreationForm
from .models import Profile, Report, Subscription, AccountSettings
from django.contrib.auth.forms import (
    PasswordResetForm,
    SetPasswordForm, AuthenticationForm
)
from .models import CustomUser
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import ReadOnlyPasswordHashField


class EditProfile(UserChangeForm):
    bio = forms.CharField(max_length=500)
    # date_of_birth = forms.DateField()
    place_of_birth = forms.CharField(max_length=100)
    current_city_of_residency = forms.CharField(max_length=100)
    citizenship = forms.CharField(max_length=100)
    social_security_number = forms.CharField(max_length=100)
    profile = forms.ImageField()
    products = forms.CharField(max_length=100)
    services = forms.CharField(max_length=100)

    class Meta:
        model = Profile
        exclude = ['username', 'first_name', 'last_name']

        def __init__(self):
            self.cleaned_data = None

        def save(self, commit=True):
            super(UserChangeForm).save(commit=False)
            get_user_model().first_name = self.cleaned_data['first_name']
            get_user_model().last_name = self.cleaned_data['last_name']
            get_user_model().email = self.cleaned_data['email']
            if commit:
                get_user_model().save()
                return get_user_model()


class UserLoginForm(AuthenticationForm):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(args, **kwargs)
        self.fields['username'].widget.attrs().update({'class': 'form-control', 'name': 'username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control',
                                                     'name': 'password'})

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if username and password:
            authenticate(username=username, password=password)
            if not username:
                raise forms.ValidationError("This user does not exist!")
            if not password:
                raise forms.ValidationError("Incorrect Password")
            if not username.is_active:
                raise forms.ValidationError('User is no longer active')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'


class ReportForm(forms.Form):
    class Meta:
        model = Report
        fields = ['user', 'content_type', 'content_id', 'content_object', 'reason', 'timestamp']


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'description', 'members']

    def __int__(self, *args, **kwargs):
        super(CommunityForm, self).__init__(*args, **kwargs)
        self.fields['members'].widget_attrs['class'] = 'select2'


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['user', ]


class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'description', 'owner']


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = AccountSettings
        fields = ['receive_email_notifications', 'profile_visibility']


class JoinCommunityForm(forms.Form):
    community_id = forms.IntegerField(widget=forms.HiddenInput())
