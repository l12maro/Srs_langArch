from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import MetaText, Person, Classify
from django.db.models import Count

class IndexArchiveView(ListView):
    model = Classify
    template_name = "browse/base_index.html"
    
    def get_context_data(self, **kwargs):
        context = super(IndexArchiveView, self).get_context_data(**kwargs)
        context['speaker'] = Person.objects.filter(role='speaker')
        return context
    
    def get_queryset(self):
        return Classify.objects.filter(parent__isnull=True)

class CollectionView(ListView):
    model = Classify
    template_name = 'browse/base_collection.html'  
    context_object_name = 'collection'

    def get_queryset(self):
        coll = self.kwargs['collection']
        return Classify.objects.filter(parent__name=coll).order_by('name')
    
class SessionView(ListView):
    model = MetaText
    template_name = 'browse/base_session.html'  
    context_object_name = 'session'

    def get_queryset(self):
        coll = self.kwargs['collection']
        ses = self.kwargs['session']
        queryset = MetaText.objects.filter(collection__name=coll).filter(session__name=ses)
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

class TextView(DetailView):
    model = MetaText
    template_name = "browse/base_textpage.html"
    
    def get_object(self, queryset=None):
            coll = self.kwargs['collection']
            ses = self.kwargs['session']
            file = self.kwargs['filename']  
            queryset = MetaText.objects.filter(collection__name=coll).filter(session__name=ses).filter(filename=file)

            # Use get_object_or_404 to retrieve the object or raise a 404 if not found
            obj = get_object_or_404(queryset)
            return obj        

'''
def detail(request, collection, session, filetype):
    elements = MetaText.objects.filter(collection__name=collection).filter(session__name=session)
    elements = elements.filter(collection__fileType=filetype)
    
    
    return render(request, "browse/base_textpage.html", elements)

def coll(request, collection):
    elements = MetaText.objects.filter(collection__name=collection).order_by("date")
    context = {
        "element": elements,
    }

    return render(request, "browse/base_collection.html", context)



def ses(request, collection, session):
    elements = MetaText.objects.filter(collection__name=collection)
    elements = MetaText.objects.filter(session__name=session)
    file_list = elements.order_by("date")[:5]
    context = {
        "file_list": file_list,
    }
    return render(request, "browse/base_collection.html", context)

'''



def about(request):
    return render(request, "browse/base_home.html")