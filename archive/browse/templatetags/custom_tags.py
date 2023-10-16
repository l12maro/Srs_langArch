from django import template
from django.urls import resolve
from browse.models import Collection, Session, Person, Genre, Language, File
from django.utils.html import escape, mark_safe
from django.http import FileResponse

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
def returnPDF(id):
    file = File.objects.get(pk=id)
    return FileResponse(file.content, content_type='application/pdf')

@register.simple_tag
def filterCollection(as_button=False):
    list = Collection.objects.all()  # Retrieve objects with parent=None
    html = []
    for obj in list:
        if as_button:
            html.append(f'<option value={escape(obj.name)}>{escape(obj.title)}</option>')
        else:
            html.append(f'<li><a href=""><span class="fa fa-chevron-right mr-2"></span>{escape(obj.title)}</a></li>')
    html = "".join(html)
    return mark_safe(html)

@register.simple_tag
def filterGenre(as_button=False):
    list = Genre.objects.filter(parent_genre__isnull=True)
    html = []
    for obj in list:
        if as_button:
            html.append(f'<option value={escape(obj.name)}>{escape(obj.name)}</option>')
        else:
            html.append(f'<li><a href=""><span class="fa fa-chevron-right mr-2"></span>{escape(obj.name)}</a></li>')
    html = "".join(html)
    return mark_safe(html)
   
@register.simple_tag
def filterSpeaker(as_button=False):
    list = Person.objects.filter(role="speaker") # For now we consider all people speakers
    html = []
    for obj in list:
        if as_button:
            html.append(f'<option value={escape(obj.name)}>{escape(obj.name)}</option>')
        else:
            html.append(f'<li><a href=""><span class="fa fa-chevron-right mr-2"></span>{escape(obj.name)}</a></li>')
    html = "".join(html)
    return mark_safe(html)


@register.simple_tag 
def filterLanguage():
    list = Language.objects.all() # For now we consider all people speakers
    #content = htmlReturn(list)
    #return mark_safe(content)

'''
#helper function to print all filters   
def htmlReturn(list):
    html = []
    for obj in list:
        html.append(f'<li><a href=""><span class="fa fa-chevron-right mr-2"></span>{escape(obj.name)}</a></li>')
    html = "".join(html)
    return html
    
#helper function to print all filters   
def htmlReturn(list):
    html = []
    i = 0
    for obj in list:
        html.append(f'<option value={escape(obj.name)}>{escape(names)}</option>')
    html = "".join(html)
    return html
'''
    