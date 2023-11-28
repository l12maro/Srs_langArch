from django import template
from django.urls import resolve
from browse.models import Collection, Session, Person, Genre, Language, File
from django.utils.html import escape, mark_safe
from django.http import FileResponse
from django.urls import reverse


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
        url = reverse('search:results') + f'?coll={obj.name}'
        if as_button:
            html.append(f'<option value={escape(obj.name)}>{escape(obj.title)}</option>')
        else:
            html.append(f'<li><a href="{url}">{escape(obj.title)}</a></li>')
    html = "".join(html)
    return mark_safe(html)

@register.simple_tag
def filterGenre(as_button=False):
    list = Genre.objects.filter(parent_genre=None)
    html = []
    for obj in list:
        url = reverse('search:results') + f'?genre={obj.name}'
        if as_button:
            html.append(f'<option value={escape(obj.name)}>{escape(obj.title)}</option>')        
        else:
            html.append(f'<li><a href="{url}">{escape(obj.name)}</a></li>')
    html = "".join(html)
    return mark_safe(html)
   
@register.simple_tag
def filterSpeaker(as_button=False, **kwargs):
    list = Person.objects.filter(role="speaker")
    html = []
    for obj in list:
        url = reverse('search:results') + f'?s={obj.tier}'
        if as_button:
            html.append(f'<label for={escape(obj.tier)}>\
                        <option id=={escape(obj.tier)} value={escape(obj.tier)}>{escape(obj.name)}</option>\
                        </label>')
        else:
            html.append(f'<li><a href="{url}">{escape(obj.name)}</a></li>')
    html = "".join(html)
    return mark_safe(html)


@register.simple_tag 
def filterLanguage():
    list = Language.objects.all()
    html = []
    for obj in list:
        url = reverse('search:results') + f'?lang={obj.name}'
        html.append(f'<li><a href="{url}">{escape(obj.name)}</a></li>')
    html = "".join(html)
    return mark_safe(html)

