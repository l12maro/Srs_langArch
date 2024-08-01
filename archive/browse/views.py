import os
import tempfile
from wsgiref.util import FileWrapper
from django.conf import settings
from django.views.generic import ListView, DetailView
from django.shortcuts import render
from django.http import FileResponse
from .models import Session, Person, Collection, File, TranscriptELAN
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from search.helpers import *


class IndexArchiveView(LoginRequiredMixin, ListView):
    model = Collection
    template_name = "browse/base_index.html"
    
    def get_context_data(self, **kwargs):
        context = super(IndexArchiveView, self).get_context_data(**kwargs)
        context['speaker'] = Person.objects.filter(role='speaker')
        return context
    
    def get_queryset(self):
        return Collection.objects.all()

class CollectionView(LoginRequiredMixin, ListView):
    model = Session
    template_name = 'browse/base_collection.html'  
    context_object_name = 'collection'

    def get_queryset(self):
        coll = self.kwargs['collection']
        return Session.objects.filter(collection__name=coll).order_by('name')
    
class SessionView(LoginRequiredMixin, ListView):
    model = File
    template_name = 'browse/base_session.html'  
    context_object_name = 'session'

    def get_queryset(self):
        coll = self.kwargs['collection']
        ses = self.kwargs['session']
        #TODO: How to filter from collection when collection is not refered in File
        queryset = File.objects.filter(session__name=ses)            

        return queryset

class TextView(LoginRequiredMixin, DetailView):
    model = File
    template_name = "browse/base_textpage.html"
    
    def get_object(self, queryset=None):
        # Retrieve file
        fileid = self.kwargs['fileid']  
        obj = File.objects.get(id=fileid)
        base_dir = settings.MEDIA_ROOT
        temp_dir = tempfile.mkdtemp(dir=os.path.join(base_dir, 'uploads'))

                
        # If file is of type eaf, we want to pass all of its (filtered) text
        if obj.type == 'eaf':
            # First we look for the associated media file
            transcript = TranscriptELAN.objects.filter(transcriptELANfile__name=obj.name).first()
            obj.video = transcript.video
            
            # First we find whether there is a match for the file or its collection
            # in our TierReference class. If not, we use default tiers.
            tiers = {
                "text": "text",
                "translation": "translation"
            }
            tiers = get_tiers(obj.name, tiers=tiers)
            text = tiers["text"]
            translation = tiers["translation"]
            
            # Then we get all tsuut'ina text, gloss and translation
            srs = TranscriptELAN.objects.filter(transcriptELANfile__name=obj.name, textType=text)
            
            text = {}
            
            for result in srs:
                eng = TranscriptELAN.objects.filter(
                    transcriptELANfile__name=obj.name, textType=translation).filter(
                    startTime=result.startTime, endTime=result.endTime).first()
                
                content = {}
                content["id"] = result.id
                content["start"] = result.startTime
                content["end"] = result.endTime
                content["srs"] = result.annotation
                
                if eng:
                    content["eng"] = eng.annotation
                    
                text[result.id] = content
                
            obj.text = text
            
        return obj    
        
    def get_context_data(self, **kwargs):
        ses = self.kwargs['session']
        context = super(TextView, self).get_context_data(**kwargs)
        context['files'] = File.objects.filter(session__name=ses)
        return context
    
@login_required
def mediaView(request, fileid):    
    # Retrieve the File object 
    obj = File.objects.get(id=fileid)

    # Serve the file
    response = FileResponse(obj.content)
        
    return response

@login_required
def ppMediaView(request, fileid):
    uploads = os.path.join(MEDIA_ROOT, 'uploads')
    cleanup(uploads)
    
    # Retrieve the File object 
    obj = File.objects.get(id=fileid)
    
    pp = get_postprocessed_media(obj)
    print("got it")

    # Serve the file
    return FileResponse(FileWrapper(pp))
        
@login_required
def segmentView(request, resultid):    
    uploads = os.path.join(MEDIA_ROOT, 'uploads')
    cleanup(uploads)
    
    transcript = TranscriptELAN.objects.get(id=resultid)
    
    # Get segment
    response = FileResponse(FileWrapper(get_audio(transcript)))
    
    
    return response


def about(request):
    return render(request, "browse/base_home.html")

def how(request):
    return render(request, "browse/base_instructions.html")