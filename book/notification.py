from notifications.signals import notify
from django.contrib.auth.models import User,Group




def send_notification(sender,target,verb):
    if not sender.is_superuser:
        notify.send(
            sender,
            recipient=User.objects.filter(is_superuser=1),
            verb=verb,
            target=target,
            )