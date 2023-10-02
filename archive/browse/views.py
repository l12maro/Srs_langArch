from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import MetaText, Person, Classify

class IndexView(ListView):
    model = Classify
    template_name = "browse/base_index.html"
    context_object_name = 'meta_list'
    
    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context.update({
            'meta_list': Person.objects.order_by('name'),
        })
        return context
    
    def get_queryset(self):
        return Classify.objects.filter(parent__isnull=True)

class CollectionDetailView(DetailView):
    model = MetaText
    template_name = 'browse/base_collection.html'  
    context_object_name = 'collection'
    slug_field = 'name' 

    #def get_queryset(self):
        #return MetaText.objects.filter(collection__name=slug_field)

'''
def coll(request, collection):
    elements = MetaText.objects.filter(collection__name=collection)
    session_list = elements.order_by("session")[:5]
    context = {
        "session_list": session_list,
    }
    return render(request, "browse/base_collection.html", context)
    
'''

def ses(request, collection, session):
    elements = MetaText.objects.filter(collection__name=collection)
    elements = MetaText.objects.filter(session__name=session)
    file_list = elements.order_by("date")[:5]
    context = {
        "file_list": file_list,
    }
    return render(request, "browse/base_collection.html", context)



def detail(request, collection, session, filetype):
    elements = MetaText.objects.filter(collection__name=collection).filter(session__name=session)
    elements = elements.filter(collection__fileType=filetype)
    
    
    return render(request, "browse/base_textpage.html", elements)

def about(request):
    return render(request, "browse/base_home.html")