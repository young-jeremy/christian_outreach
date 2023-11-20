from django.db import models
from django.conf import settings


class Notice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Assuming you have a User model
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
