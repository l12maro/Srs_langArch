import os
import subprocess
import tempfile
from xml.dom.minidom import Document
from django.conf import settings
from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse, Http404
from django.template import loader
from .models import Session, Person, Collection, File, TierReference, TranscriptELAN
from django.db.models import Count
from docx2pdf import convert
import comtypes.client
from django.utils.dateparse import parse_duration
from archive.settings import MEDIA_ROOT, MEDIA_URL



class IndexArchiveView(ListView):
    model = Collection
    template_name = "browse/base_index.html"
    
    def get_context_data(self, **kwargs):
        context = super(IndexArchiveView, self).get_context_data(**kwargs)
        context['speaker'] = Person.objects.filter(role='speaker')
        return context
    
    def get_queryset(self):
        return Collection.objects.all()

class CollectionView(ListView):
    model = Session
    template_name = 'browse/base_collection.html'  
    context_object_name = 'collection'

    def get_queryset(self):
        coll = self.kwargs['collection']
        return Session.objects.filter(collection__name=coll).order_by('name')
    
class SessionView(ListView):
    model = File
    template_name = 'browse/base_session.html'  
    context_object_name = 'session'

    def get_queryset(self):
        coll = self.kwargs['collection']
        ses = self.kwargs['session']
        #TODO: How to filter from collection when collection is not refered in File
        queryset = File.objects.filter(session__name=ses)            

        return queryset

class TextView(DetailView):
    model = File
    template_name = "browse/base_textpage.html"
    
        
    def get_tiers(self, file_name):
        
        def get_from_collection(collection, tierType):
            # Check if the collection is listed in TierReference
            tier_reference_entry = TierReference.objects.filter(collection__name=collection).filter(destTierType=tierType).first()
            return tier_reference_entry
            
        # set default values
        tiers = {
            "text": "text",
            "gloss": "gloss",
            "translation": "translation"
         }
        
        # Check if the file name is listed in TierReference
        tier_reference_entry = TierReference.objects.filter(transcriptELANfile__name=file_name)

        if tier_reference_entry.first():
            print("yes")
            for key in tiers:
                print("destiny tier: " + key)
                tier_reference_entry.filter(destTierType=key)
                if tier_reference_entry.first():
                    tiers[key] = tier_reference_entry.sourceTierType
                    print("source tier (from file): " + tiers[key])
                else:
                    search = get_from_collection(tier_reference_entry.first().collection, key)
                    if search:
                        tiers[key] = search.sourceTierType
                        print("source tier (from collection): " + tiers[key])


        # If there is no listing in TierReference, we check the collection
        else:
            file = File.objects.filter(name=file_name).first()
            for key in tiers:
                search = get_from_collection(file.session.collection, key)
                if search:
                    tiers[key] = search.sourceTierType
                    print("source tier (from collection): " + tiers[key])
            
            
        return tiers["text"], tiers["gloss"], tiers["translation"]
    
    def get_object(self, queryset=None):
        # Retrieve file
        id = self.kwargs['fileid']  
        obj = File.objects.get(id=id)
        base_dir = settings.MEDIA_ROOT
        temp_dir = tempfile.mkdtemp(dir=os.path.join(base_dir, 'uploads'))

                
        # If file is of type eaf, we want to pass all of its (filtered) text
        if obj.type == 'eaf':
            # First we look for the associated media file
            transcript = TranscriptELAN.objects.filter(transcriptELANfile__name=obj.name).first()
            obj.video = transcript.video
            
            # First we find whether there is a match for the file or its collection
            # in our TierReference class. If not, we use default tiers.
            text, gloss, translation = self.get_tiers(obj.name)
            
            # Then we get all tsuut'ina text, gloss and translation
            srs = TranscriptELAN.objects.filter(transcriptELANfile__name=obj.name, textType=text)
            eng = TranscriptELAN.objects.filter(transcriptELANfile__name=obj.name, textType=translation)
            
            text = {}
            
            i = 0
            for e in eng:
                ts = srs.filter(startTime=e.startTime, endTime=e.endTime).first()
                
                if ts:
                    i += 1
                    content = {}
                    content["start"] = e.startTime
                    content["end"] = e.endTime
                    content["srs"] = ts.annotation
                    content["eng"] = e.annotation
                    content["transcript"] = e
                    
                    text[i] = content
                
            obj.text = text
            
        return obj    
        
    def get_context_data(self, **kwargs):
        ses = self.kwargs['session']
        context = super(TextView, self).get_context_data(**kwargs)
        context['files'] = File.objects.filter(session__name=ses)
        return context
    
            
def mediaView(request, collection, session, fileid):    
    # Retrieve the File object 
    obj = File.objects.get(id=fileid)

    # Serve the file
    response = FileResponse(obj.content)
    return response


def about(request):
    return render(request, "browse/base_home.html")

def how(request):
    return render(request, "browse/base_instructions.html")