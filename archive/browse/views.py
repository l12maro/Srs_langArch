import os
from django.conf import settings
from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse, Http404
from django.template import loader
from .models import Session, Person, Collection, File, TierReference, TranscriptELAN
from django.db.models import Count
from docx2pdf import convert


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
    
    def convert_docx_to_pdf(self, docx_path, pdf_path):
        try:
            convert(docx_path, pdf_path)
            return True
        except Exception as e:
            print(f"Error converting DOCX to PDF: {e}")
            return False
        
    def get_tier_type(self, obj, tier_type):
        '''
        Searches the model TierReference for custom tier types
        @returns true if custom tier was found, and the desired 
        custom tierType
        '''
        tier = TierReference.objects.filter(transcriptELANfile__name=obj.name, destTierType=tier_type).first()
        if not tier:
            tier = TierReference.objects.filter(transcriptELANfile=None, collection__name=obj.session.collection.name, destTierType=tier_type).first()
            if not tier:
                return False, tier_type
            else:
                #tier = tier.get()
                tier = tier.sourceTierType
        else:
            #tier = tier.get()
            tier = tier.sourceTierType
            
        return True, tier
    
    def get_object(self, queryset=None):
        # Retrieve file
        id = self.kwargs['fileid']  
        obj = File.objects.get(id=id)

        # If file is a word or excel document, we want to convert it in pdf first for viewing
        # TODO: Get this working for word and add excel
        if obj.type == 'docx':
            # Assuming object.content.url is the path to the DOCX file
            docx_path = obj.content.url
            
            # Create a temporary PDF file path
            temp_pdf_path = os.path.join(settings.MEDIA_ROOT, 'temp', f'{obj.name}_temp.pdf')

            # Convert DOCX to PDF
            success = self.convert_docx_to_pdf(docx_path, temp_pdf_path)

            if success:
                # Now, you can use the temporary PDF file
                object.content.url = str(temp_pdf_path)
                
        # If file is of type eaf, we want to pass all of its (filtered) text
        if obj.type == 'eaf':
            # First we look for the associated media file
            transcript = TranscriptELAN.objects.filter(transcriptELANfile__name=obj.name).first()
            obj.video = transcript.video
            
            # First we find whether there is a match for the file or its collection
            # in our TierReference class. If not, we use default tiers.
            found, srs = self.get_tier_type(obj, 'text')
            found, gloss = self.get_tier_type(obj, 'gloss')
            found, translation = self.get_tier_type(obj, 'translation')
            
            # Then we get all tsuut'ina text, gloss and translation
            obj.srs_text = TranscriptELAN.objects.filter(transcriptELANfile__name=obj.name, textType=srs)
            obj.gloss_text = TranscriptELAN.objects.filter(transcriptELANfile__name=obj.name, textType=gloss)
            obj.eng_text = TranscriptELAN.objects.filter(transcriptELANfile__name=obj.name, textType=translation)

        
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