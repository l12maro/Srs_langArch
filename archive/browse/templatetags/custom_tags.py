from django import template
from django.urls import resolve
from browse.models import Collection, Session, Person, Genre, Language
from django.utils.html import escape, mark_safe

register = template.Library()

@register.simple_tag
def is_active(request, view_name):
    current_url = resolve(request.path_info).url_name
    return 'active' if current_url == view_name else ''

@register.filter
def is_audio_file(value):
    audio_extensions = ['wav', 'mp3']  # Add more audio extensions as needed
    return value.lower() in audio_extensions

@register.filter
def is_video_file(value):
    audio_extensions = ['mp4', 'm4a']  # Add more audio extensions as needed
    return value.lower() in audio_extensions


@register.simple_tag
def filterCollection():
    list = Collection.objects.all()  # Retrieve objects with parent=None
    content = htmlReturn(list)
    return mark_safe(content)

@register.simple_tag
def filterGenre():
    list = Genre.objects.all() 
    content = htmlReturn(list)
    return mark_safe(content)
   
@register.simple_tag 
def filterSpeaker():
    list = Person.objects.filter(role="speaker") # For now we consider all people speakers
    content = htmlReturn(list)
    return mark_safe(content)

@register.simple_tag 
def filterLanguage():
    list = Language.objects.all() # For now we consider all people speakers
    content = htmlReturn(list)
    return mark_safe(content)
    
#helper function to print all filters   
def htmlReturn(list):
    html = []
    for obj in list:
        html.append(f'<li><a href=""><span class="fa fa-chevron-right mr-2"></span>{escape(obj.name)}</a></li>')
    html = "".join(html)
    return html
    
        