# signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import DataSource
from populate import trigger_populate
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=DataSource)
def populate(sender, instance, **kwargs):
    trigger_populate(instance)
     
@receiver(post_save, sender=DataSource)
def removeds(sender, instance, created, **kwargs):
    # If specified, delete the instance
    if created:
        if not instance.store:
            instance.delete()