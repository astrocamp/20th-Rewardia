from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=User)
def comment_created(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)
