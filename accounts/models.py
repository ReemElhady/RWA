from django.contrib.auth.models import User
from django.db import models
from core.models import City

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.user.username
