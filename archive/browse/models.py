from functools import partial
import os
from django.db import models
from django.core.validators import MinLengthValidator
from pathlib import Path
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.search import SearchVectorField 
from django.contrib.postgres.indexes import GinIndex
from django.urls import reverse
from django.contrib.auth.models import User

global PERMISSIONS, CASCADE_A_ONLY

PERMISSIONS = [
    ("p", "public"),
    ("l", "login"),
    ("r", "restricted"),
    ("a", "author only"),
    ]


def CONDITIONAL_CASCADE(collector, field, sub_objs, using, **kwargs):
    
    condition = kwargs.get("condition", {})
    default_value = kwargs.get("default_value", None)

    sub_objs_to_cascade = sub_objs.filter(**condition)
    sub_objs_to_set = sub_objs.exclude(**condition)

    models.CASCADE(collector, field, sub_objs_to_cascade, using)
    collector.add_field_update(field, default_value, sub_objs_to_set)
    
# If users are removed we want to remove as well their author-only files
CASCADE_A_ONLY = partial(
    CONDITIONAL_CASCADE,
    condition={"permissions": "a"},
    default_value=None
)


def currentDir():
    s = r'g:\Unidades compartidas\Tsuutina-Resources\COLLECTIONS'
    return Path(s)

def get_metadata(file_path):
    file_directory = os.path.dirname(file_path)
    return os.path.split(file_directory)

class User(AbstractUser):
    pass


class DataSource(models.Model):
    """
    This class allows the superuser and staff to specify a local folder
    from which to upload the data.
    Properties:
    path: path to the local folder
    store: indicates whether the path should remain stored for future reference or deleted after upload. Default "True"
    overwrite: indicates whether all data stored should be removed and overwritten with the new data. Default "False"
    data owner: indicates the user which is associated with the uploaded data. This serves to manage author-only permissions. Default owner is superuser.

    """
    path = models.TextField()
    store = models.BooleanField(default=True)
    overwrite = models.BooleanField(default=False)
    data_owner = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=User.objects.filter(is_superuser=True).first().id)
    access_rights = models.CharField(max_length=15, choices=PERMISSIONS, default="login")
    

class Language(models.Model):
    """
    The language class stores language values in ISO-639-2 format

    """
    name = models.CharField(max_length=3, validators=[MinLengthValidator(3)])
    
    def __str__(self):
        return self.name

class Genre(models.Model):
    """
    The Genre class stores all genres and subgenres given in the database

    """
    name = models.CharField(max_length=100)
    parent_genre = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

class Person(models.Model):
    """
    The Person class stores all people speaking or participating on files

    """
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=5, null=True)
    possibleRoles = [
        ("speaker", "speaker"),
        ("participant", "participant"),
        ("depositor", "depositor"),
        ("contact", "contact"),
    ]
    role = models.CharField(max_length=15, choices=possibleRoles, default="participant", null=True)
    
    def __str__(self):
        return self.name


class Collection(models.Model):
    """    
    The collection class stores all collections and their metadata

    """
    name = models.CharField(max_length=100)
    
    title = models.CharField(max_length=100, null=True, blank=True)
    synopsis = models.TextField(null=True, blank=True)
    language = models.ForeignKey(Language, related_name="coll_lang", on_delete=models.SET_NULL, null=True, blank=True)
    working_language = models.ForeignKey(Language, related_name="coll_wl", on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    continent = models.CharField(max_length=255, null=True, blank=True)
    access = models.CharField(max_length=255, null=True, blank=True)
    depositor = models.ForeignKey(Person, related_name="coll_depositor", on_delete=models.SET_NULL, null=True, blank=True)
    contact_person = models.ForeignKey(Person, related_name="coll_contact", on_delete=models.SET_NULL, null=True, blank=True)
    
    # Add information about access procedures
    permissions = models.CharField(max_length=15, choices=PERMISSIONS, default="login")
    owner = models.ForeignKey(User, on_delete=models.SET(CASCADE_A_ONLY), null=True, related_name="coll_user")
            
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('browse:collection', args=[str(self.name)])


class Session(models.Model):    
    name = models.CharField(max_length=100, blank=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, blank=True)
    
    # Extracted values from XML
    title = models.CharField(max_length=255, null=True, blank=True)
    languages = models.ManyToManyField(Language, related_name="ses_language", blank=True)
    working_languages = models.ManyToManyField(Language, related_name="ses_wl", blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name='ses_genres', blank=True)
    subgenre = models.ForeignKey(Genre, on_delete=models.SET_NULL, related_name='ses_subgenres', null=True, blank=True)
    synopsis = models.TextField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    speakers = models.ManyToManyField(Person, related_name='ses_speaker', blank=True)
    participants = models.ManyToManyField(Person, related_name='ses_participant', blank=True)
    
    # Add information about access procedures
    permissions = models.CharField(max_length=15, choices=PERMISSIONS, default="login")
    owner = models.ForeignKey(User, on_delete=models.SET(CASCADE_A_ONLY), null=True, related_name="ses_user")

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('browse:session', args=[str(self.collection.name), str(self.name)])
    

class File(models.Model):
    # Define the path where the FileField should store files
    name = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=5, null=True, blank=True)
    content = models.FileField(upload_to='uploads/', blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, blank=True)
    
    # Add information about access procedures
    permissions = models.CharField(max_length=15, choices=PERMISSIONS, default="login")
    owner = models.ForeignKey(User, on_delete=models.SET(CASCADE_A_ONLY), null=True, related_name="file_user")
    
    def __str__(self):
        fullname = self.name + '.' + self.type
        return fullname
    
    def get_absolute_url(self):
        return reverse('browse:detail', args=[str(self.session.collection.name), str(self.session.name), str(self.id)])


class Postprocess(models.Model):
    annotationID = models.CharField(max_length=255, blank=True)
    transcriptELANfile = models.ForeignKey(File, related_name="file_pp", on_delete=models.CASCADE, blank=True)
    annotation = models.TextField(null=True, blank=True)
    startTime = models.CharField(max_length=50, blank=True)
    endTime = models.CharField(max_length=50, blank=True)

 
class TranscriptELAN(models.Model):
    transcriptELANfile = models.ForeignKey(File, related_name="file", on_delete=models.CASCADE, blank=True)
    video = models.ForeignKey(File, related_name="vid", on_delete=models.SET_NULL, null=True, blank=True)
    annotationID = models.CharField(max_length=255, blank=True)
    annotation = models.TextField(blank=True, db_index=True)
    search_vector = SearchVectorField(null=True)
    textType = models.CharField(max_length=255, blank=True)
    startTime = models.CharField(max_length=50, blank=True)
    endTime = models.CharField(max_length=50, blank=True)
    postprocess = models.ManyToManyField(Postprocess, blank=True)
    speaker = models.ForeignKey(Person, related_name="spk", on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.annotation
    
    def get_absolute_url(self):
        return reverse('search:result', args=[str(self.id)])
    
    class Meta:
        indexes = [
            GinIndex(fields=["search_vector"]),
        ]

   
class TierReference(models.Model):
    
    #Limit choices from destTierType to text, gloss, translation
    DEST_TIER_TYPE_CHOICES = [
        ('text', 'text'),
        ('gloss', 'gloss'),
        ('translation', 'translation'),
    ]    
    
    #Limit choices from sourceTierType to the tierTypes in TranscriptELAN
    TRANSCRIPT_ELAN_CHOICES = [
        (tier_type, tier_type) for tier_type in TranscriptELAN.objects.values_list('textType', flat=True).distinct()
    ]
    
    transcriptELANfile = models.ForeignKey(File, related_name="file_ref", on_delete=models.DO_NOTHING, null=True, blank=True, limit_choices_to={"type": "eaf"})
    collection = models.ForeignKey(Collection, on_delete=models.DO_NOTHING, null=True, blank=True)
    sourceTierType = models.CharField(max_length=255, null=True, blank=True, choices=TRANSCRIPT_ELAN_CHOICES)
    destTierType = models.CharField(max_length=255, null=True, blank=True, choices=DEST_TIER_TYPE_CHOICES)


