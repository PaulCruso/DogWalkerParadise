from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment, Notification, UserProfile
from datetime import datetime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User


@receiver(post_save, sender=Appointment)
def create_notification(sender, instance, created, **kwargs):
    appointment_time = instance.appointment_date.strftime('%b %d, %Y at %I:%M %p')

    if created:
        # Notify owner about the new appointment
        message = (
            f"A new appointment has been created for {instance.dog_type} at "
            f"{instance.location} on {appointment_time}."
        )
        Notification.objects.create(user=instance.dog_owner, message=message, appointment=instance)
        send_notification_to_ws(instance.dog_owner.id, message, instance.id)
    else:
        # Notify both owner and walker about status changes
        message = (
            f"Appointment status updated to {instance.status} for {instance.dog_type} "
            f"at {instance.location} on {appointment_time}."
        )
        if instance.dog_walker:
            Notification.objects.create(user=instance.dog_walker, message=message, appointment=instance)
            send_notification_to_ws(instance.dog_walker.id, message, instance.id)
        Notification.objects.create(user=instance.dog_owner, message=message, appointment=instance)
        send_notification_to_ws(instance.dog_owner.id, message, instance.id)


def send_notification_to_ws(user_id, message, appointment_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "send_notification",
            "message": message,
            "appointment_id": appointment_id,
            "timestamp": datetime.now().isoformat(),
        }
    )
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()