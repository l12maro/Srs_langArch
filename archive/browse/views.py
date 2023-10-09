from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.template import loader
from .models import Session, Person, Collection, File
from django.db.models import Count

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
        '''
        results = []
        #get distinct titles
        titles = queryset.values('title').annotate(count=Count('title'))
        
        value_hierarchy = ['wav', 'mp3', 'pdf', 'docx']
        
        for t in titles:
            queryset_title = queryset.filter(title=t['title'])
            #If there are several elements with the same title, check if audio exists
            if t['count'] > 1:
                for v in value_hierarchy:
                    queryset_type = queryset_title.filter(fileType=v)
                    if queryset_type:
                        results.append(get_object_or_404(queryset_type))
                        break

            else:
                results.append(get_object_or_404(queryset_title))
        
        return results
        '''
        return queryset

class TextView(DetailView):
    model = File
    template_name = "browse/base_textpage.html"
    
    def get_object(self, queryset=None):
            coll = self.kwargs['collection']
            ses = self.kwargs['session']
            type = self.kwargs['filetype']  
            #TODO: How to filter from collection when collection is not refered in File
            queryset = File.objects.filter(session__name=ses).filter(type=type)

            # Use get_object_or_404 to retrieve the object or raise a 404 if not found
            obj = get_object_or_404(queryset)
            return obj    
        
    def get_context_data(self, **kwargs):
        ses = self.kwargs['session']
        context = super(TextView, self).get_context_data(**kwargs)
        context['files'] = File.objects.filter(session__name=ses)
        return context
    
            
def videoView(request, collection, session, filetype):
    # Retrieve the File object based on session and file type
    file = File.objects.filter(session__name=session).filter(type=filetype)
    file = get_object_or_404(file)

    # Serve the video file
    response = FileResponse(file.content)
    return response

def download_file(request, file_id):
    file = File.objects.filter(id=file_id)
    file = get_object_or_404(file)

    response = FileResponse(file.content)
    response['Content-Disposition'] = f'attachment; filename="{file.name}"'
    return response

def about(request):
    return render(request, "browse/base_home.html")