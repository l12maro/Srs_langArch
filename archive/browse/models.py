import os
import xml.etree.ElementTree as ET
from django.db import models
from django.forms import CharField, FileInput
from django.core.validators import MinLengthValidator
from pathlib import Path

from django.urls import reverse

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
    possibleRoles = [
        ("speaker", "speaker"),
        ("participant", "participant"),
        ("depositor", "depositor"),
        ("contact", "contact"),
    ]
    role = models.CharField(max_length=15, choices=possibleRoles, default="participant")
    
    def __str__(self):
        return self.name

    
# The Classify class stores all collections and sessions given
class Classify(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    synopsis = models.TextField(null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    working_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    continent = models.CharField(max_length=255)
    access = models.CharField(max_length=255)
    depositor = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    contact_person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    def parse_xml_coll(self, xml_path):
        try:
            with open(xml_path, 'r', encoding='utf-8') as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                self.title = root.find('Title').text
                
                #if no languages are specified, we add Tsuut'ina as the default
                languages = root.find('VernacularISO3CodeAndName').text
                if languages is not None:
                    code, _ = languages.split(':')
                    l, created = Language.objects.get_or_create(name=l.strip())
                    self.language = l

                else:
                    tsuu, created = Language.objects.get_or_create(name="srs")
                    self.language = tsuu
                    
                #if no working languages are specified, we add English as the default
                working_languages = root.find('AnalysisISO3CodeAndName').text
                if working_languages is not None:
                    code, _ = languages.split(':')
                    l, created = Language.objects.get_or_create(name=l.strip())
                    self.working_language = l
            
                else:
                    eng, created = Language.objects.get_or_create(name="eng")
                    self.working_language = eng

                loc = root.find('Location').text
                if loc is not None:
                    self.location = loc
                    
                region = root.find('Region').text
                if region is not None:
                    self.region = region
                    
                country = root.find('Country').text
                if country is not None:
                    self.country = country
                    
                continent = root.find('Continent').text
                if continent is not None:
                    self.continent = continent
                
                access = root.find('AccessProtocol').text
                if access is not None:
                    self.access = access
                    
                synopsis = root.find('ProjectDescription').text
                if synopsis is not None:
                    self.synopsis = synopsis
                
                depositor = root.find('Depositor').text
                if depositor is not None:
                    depositor, created = Person.objects.get_or_create(name=depositor, role="depositor")
                    self.depositor = depositor
                    
                contact = root.find('ContactPerson').text
                if contact is not None:
                    contact, created = Person.objects.get_or_create(name=contact, role="contact")
                    self.contact_person = contact

        except Exception as e:
            print(f"Error parsing XML: {e}")
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        if self.parent == None:
            return reverse('collection', args=[str(self.name)])
        else:
            return reverse('session', args=[str(self.parent), str(self.name)])

class MetaText(models.Model):
    # Define the path where the FilePathField should store files
    textEAF = models.TextField()
    filename = models.CharField(max_length=255, null=True, blank=True)
    fileType = models.CharField(max_length=5, null=True, blank=True)
    
    #Extract Metadata from the FilePathField
    #Several values will be separated using commas
    collection = models.ForeignKey(Classify, on_delete=models.SET_NULL, null=True, related_name='collections', blank=True)
    session = models.ForeignKey(Classify, on_delete=models.SET_NULL, null=True, related_name='sessions', blank=True)
    
    # Extracted values from XML
    title = models.CharField(max_length=255, null=True, blank=True)
    languages = models.ManyToManyField(Language, related_name="language", blank=True)
    working_languages = models.ManyToManyField(Language, related_name="working_language", blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name='genres', blank=True)
    subgenre = models.ForeignKey(Genre, on_delete=models.SET_NULL, related_name='subgenres', null=True, blank=True)
    synopsis = models.TextField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    speakers = models.ManyToManyField(Person, related_name='speaker', blank=True)
    participants = models.ManyToManyField(Person, related_name='participant', blank=True)    

    def parse_xml_session(self, xml_path):
        
        try:
            with open(xml_path, 'r', encoding='utf-8') as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                self.title = root.find('Title').text
                
                #if no languages are specified, we add English and Tsuut'ina as the default
                languages = root.find('languages').text
                if languages is not None:
                    if len(languages) > 3:
                        lang = []
                        lang = languages.split(';')
                        for l in lang:
                            l, created = Language.objects.get_or_create(name=l)
                            self.languages.add(l)
                    else:
                        lang, created = Language.objects.get_or_create(name=languages)
                        self.languages.add(lang)
                else:
                    eng, created = Language.objects.get_or_create(name="eng")
                    tsuu, created = Language.objects.get_or_create(name="srs")
                    self.languages.add(eng)
                    self.languages.add(tsuu)
                    

                working_languages = root.find('workingLanguages').text
                if working_languages is not None:
                    if len(working_languages) > 3:
                        lang = []
                        lang = working_languages.split(';')
                        for l in lang:
                            l, created = Language.objects.get_or_create(name=l)
                            self.working_languages.add(l)
                    else:
                        lang, created = Language.objects.get_or_create(name=working_languages)
                        self.working_languages.add(lang)
                else:
                    eng, created = Language.objects.get_or_create(name="eng")
                    tsuu, created = Language.objects.get_or_create(name="srs")
                    self.working_languages.add(eng)
                    self.working_languages.add(tsuu)

                genre = root.find('genre').text
                if genre is not None:
                    self.genre, created = Genre.objects.get_or_create(name=genre)
                else:
                    self.genre, created = Genre.objects.get_or_create(name="Unclassified")
                    
                subgenre = root.find('Sub-Genre').text
                if subgenre is not None:
                    self.subgenre, created = Genre.objects.get_or_create(name=subgenre, parent_genre=self.genre)
                else:
                    self.subgenre = None
                    
                synopsis = root.find('synopsis').text
                if synopsis is not None:
                    self.synopsis = synopsis
                
                date = root.find('date').text
                if date is not None:
                    self.date = date
                
                contributors = root.find('contributions')
                for contributor in contributors.findall('contributor'):
                    name = contributor.find('name').text
                    role = contributor.find('role').text
                    contributor_obj, created = Person.objects.get_or_create(name=name, role=role)
                    if role == 'speaker':
                        self.speakers.add(contributor_obj)
                    elif role == 'participant':
                        self.participants.add(contributor_obj)
        except Exception as e:
            print(f"Error parsing XML: {e}")
                        
    def get_values_from_path(self):
        name, type = self.textEAF.__str__().split(".")
        self.fileType = type
        xml_file = name + ".session"
        xml_file = Path(xml_file)
        
        self.parse_xml_session(xml_file)
        
        path = Path(self.textEAF.__str__())
        
        _, filename = os.path.split(path)
        self.filename = filename

        # Extract classifying values from the path
        fdir, session = get_metadata(path)
        fdir, collection = get_metadata(fdir)
        self.collection, created = Classify.objects.get_or_create(name=collection)            
        self.session, created = Classify.objects.get_or_create(name=session, parent=self.collection)

    def __repr__(self):
        return f"{self.title} spoken by {self.speakers}, with participants {self.participants}. Classified within session {self.session} of the collection {self.collection}."
    
    # Override the save method to automatically populate fields
    def save(self, *args, **kwargs):
        self.get_values_from_path()
        super().save(*args, **kwargs)