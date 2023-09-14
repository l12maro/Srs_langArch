from django import template
from django.urls import resolve
from browse.models import Classify, Person

register = template.Library()

@register.simple_tag
def is_active(request, view_name):
    current_url = resolve(request.path_info).url_name
    return 'active' if current_url == view_name else ''

@register.simple_tag
def filterCollection():
    list = Classify.objects.filter(parent=None)  # Retrieve objects with parent=None
    htmlReturn(list)

@register.simple_tag
def filterSession():
    list = Classify.objects.exclude(parent=None)  # Retrieve objects with parent
    htmlReturn(list)
   
@register.simple_tag 
def filterSpeaker():
    list = Person.objects.all() # For now we consider all people speakers
    htmlReturn(list)
    
#helper function to print all filters   
def htmlReturn(list):
    html = ""
    for obj in list:
        html += f'\n<li><a href=""><span class="fa fa-chevron-right mr-2"></span>{obj.name}</a></li>'
    return html
    
        