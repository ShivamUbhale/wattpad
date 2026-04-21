from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    selected_genres = models.ManyToManyField('stories.Genre', blank=True, related_name='interested_users')

    def __str__(self):
        return self.username
