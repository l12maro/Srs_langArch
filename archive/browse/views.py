from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import MetaText

def index(request):
    #return HttpResponse("You're looking at index")
    return render(request, "browse/base_index.html")

def coll(request, collection):
    elements = MetaText.objects.filter(collection__name=collection)
    session_list = elements.order_by("session")[:5]
    context = {
        "session_list": session_list,
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



def detail(request, collection, session, filetype):
    elements = MetaText.objects.filter(collection__name=collection)
    elements = MetaText.objects.filter(session__name=session)
    
    #TODO: Which details should be 
    element = elements.text_id
    return HttpResponse("You're looking at text %s." % element)

def about(request):
    return render(request, "browse/base_home.html")