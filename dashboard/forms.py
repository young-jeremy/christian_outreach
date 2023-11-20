from django import forms
from .models import *


class NoticeForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea)
