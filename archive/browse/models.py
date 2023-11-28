import os
import xml.etree.ElementTree as ET
from django.db import models
from django.forms import CharField, FileInput
from django.core.validators import MinLengthValidator
from pathlib import Path
from django.core.files.base import ContentFile
from django.contrib.postgres.search import SearchVectorField 
from django.contrib.postgres.indexes import GinIndex


from django.urls import reverse


# TODO: Edit so that instead of giving an object and then session and collection is added, 
# we give a collection path and it recursively creates all sessions and files

def currentDir():
    s = r'g:\Unidades compartidas\Tsuutina-Resources\COLLECTIONS'
    return Path(s)

def get_metadata(file_path):
    file_directory = os.path.dirname(file_path)
    return os.path.split(file_directory)


# The language class stores the possible language values in ISO-639-2 format
class Language(models.Model):
    name = models.CharField(max_length=3, validators=[MinLengthValidator(3)])
    
    def __str__(self):
        return self.name

# The Genre class stores all genres and subgenres given
class Genre(models.Model):
    name = models.CharField(max_length=100)
    parent_genre = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

# The Person class stores all people speaking or participating on files
class Person(models.Model):
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

    
# The collection class stores all collections and their metadata
class Collection(models.Model):
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
            
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('collection', args=[str(self.name)])


class Session(models.Model):    
    name = models.CharField(max_length=100, blank=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='session', blank=True)
    
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

    def __str__(self):
        return self.name
    

class File(models.Model):
    # Define the path where the FileField should store files
    name = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=5, null=True, blank=True)
    content = models.FileField(upload_to='uploads/', blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, blank=True)
    
    def __str__(self):
        return self.name
    

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
    
    def __str__(self):
        return self.annotation
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
                                    
    
'''
class TextEAF(models.Model):
    fileEAF = models.ForeignKey(File, on_delete=models.CASCADE, blank=True)
    srsTier = models.TextField(blank=True)
    previousSrsTier = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    engTier = models.TextField(blank=True)
    previousEngTier = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    startTime = models.CharField(max_length=50, blank=True)
    endTime = models.CharField(max_length=50, blank=True)
    video = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True)
'''
