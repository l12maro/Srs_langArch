import os
import subprocess
import tempfile
from django import template
from django.urls import resolve
from archive import settings
from browse.models import Collection, Session, Person, Genre, Language, File
from django.utils.html import escape, mark_safe
from django.http import FileResponse
from django.urls import reverse
from django.utils.dateparse import parse_duration


register = template.Library()

@register.simple_tag
def is_active(request, view_name):
    current_url = resolve(request.path_info).url_name
    app, view_name = view_name.split(":")
    return mark_safe('.active') if current_url == view_name else ''

@register.filter
def is_audio_file(value):
    audio_extensions = ['wav', 'mp3']  
    return value.lower() in audio_extensions

@register.filter
def is_video_file(value):
    audio_extensions = ['mp4', 'm4a']  
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

@register.simple_tag
def getAudio(transcript):                    
    base_dir = settings.MEDIA_ROOT
    temp_dir = tempfile.mkdtemp(dir=os.path.join(base_dir, 'uploads'))
    
    if transcript.video and transcript.startTime and transcript.endTime:
        v_path = os.path.join('uploads', transcript.video.name + "." + transcript.video.type)
        audio_path = os.path.join(base_dir, v_path)
                                                            
        start_time = transcript.startTime
        end_time = transcript.endTime
                            
        # Convert start_time_str and end_time_str to timedelta objects
        start_time = parse_duration(start_time)
        end_time = parse_duration(end_time)
        
        temp_file = None  # Initialize temp_file outside the try block
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3', dir=temp_dir)

            # Use ffmpeg to extract the audio fragment and convert it to mp3
            ffmpeg_command = [
                'ffmpeg',
                '-i', audio_path,
                '-ss', str(start_time.total_seconds()),
                '-to', str(end_time.total_seconds()),
                '-q:a', '0',  # Set the audio quality (0 is the highest)
                '-map', 'a',  # Select the audio stream
                '-v', '0',
                '-y',
                temp_file.name
            ]
            subprocess.run(ffmpeg_command, check=True)
            
            print("FILE_NAME: " + temp_file.name)

            audio_fragment_path = temp_file.name  # Return the temporary file path containing the audio fragment in mp3 format

        except subprocess.CalledProcessError as e:
            # Handle errors if ffmpeg command fails
            print(f"Error extracting audio fragment: {e}")
            return None

        finally:
            # Close and delete the temporary file
            temp_file.close()
            if audio_fragment_path:
                relative_path = os.path.relpath(audio_fragment_path, settings.MEDIA_ROOT)
                relative_path = os.path.join("/uploads", relative_path)
                return relative_path
        
