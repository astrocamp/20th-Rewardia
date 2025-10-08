from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from knox.models import AuthToken


@receiver(post_save, sender=User)
def create_auth_token(sender, instance, created, **kwargs):
    if created:
        AuthToken.objects.create(user=instance)
