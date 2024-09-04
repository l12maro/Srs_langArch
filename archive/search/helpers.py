from functools import reduce
import os
import shutil
import subprocess
from tempfile import NamedTemporaryFile
import tempfile
from django.utils.dateparse import parse_duration
from django.db.models import Q

from archive.settings import MEDIA_ROOT
from browse.models import File, TierReference, TranscriptELAN, Postprocess
from logging import getLogger, basicConfig, INFO

basicConfig(level=INFO)
logger = getLogger(__name__)

def get_querysets():
    # We get all the distinct transcripts to search
    distinct_files = TranscriptELAN.objects.values_list('transcriptELANfile__name', flat=True).distinct()
    distinct_files = list(distinct_files)
                                        
    queriesText = []
    queriesGlosses = []
    queriesTranslation = []
                        
    # we search for each file
    for file_name in distinct_files:
        #get the tier_types
        tier = get_tiers(file_name)
        text = tier["text"]
        gloss = tier["gloss"]
        translation = tier["translation"]

        #get the results in the tsuut'ina text
        q = Q(transcriptELANfile__name=file_name) & Q(textType=text)
        queriesText.append(q)
                            
        q = Q(transcriptELANfile__name=file_name) & Q(textType=gloss)
        queriesGlosses.append(q)

        q = Q(transcriptELANfile__name=file_name) & Q(textType=translation)
        queriesTranslation.append(q)                            
                        
        # Combine the querysets
        combined_text_filter = reduce(lambda x, y: x | y, queriesText)
        combined_gloss_filter = reduce(lambda x, y: x | y, queriesGlosses)
        combined_trans_filter = reduce(lambda x, y: x | y, queriesTranslation)
        
        return combined_text_filter, combined_gloss_filter, combined_trans_filter

def get_result_srs(transcript):
    _, combined_gloss_filter, combined_trans_filter = get_querysets()

    # Get glossing if there is any
    transcript.textgloss = get_aligned_glossing(transcript, combined_gloss_filter)
                                        
    # Get translation
    translation = TranscriptELAN.objects.filter(combined_trans_filter).filter(
                startTime=transcript.startTime, endTime=transcript.endTime
                ).exclude(id=transcript.id).first()
                                
    transcript.translation = translation.annotation if translation else None
    transcript.audio = get_audio(transcript)
    return transcript
            
def get_result_eng(transcript):
    combined_text_filter, combined_gloss_filter, _ = get_querysets()
    
    transcript.translation = transcript.annotation
    transcript.audio = get_audio(transcript)
                                    
    text = TranscriptELAN.objects.filter(combined_text_filter).filter(
            startTime=transcript.startTime, endTime=transcript.endTime
            ).exclude(id=transcript.id).first()
                                    
    if text:
        transcript.annotation = text.annotation
        transcript.textglossing = get_aligned_glossing(transcript, combined_gloss_filter)

    return transcript

def get_tiers(file_name, **kwargs):
        
    def get_from_collection(collection, tierType):
        # Check if the collection is listed in TierReference
        tier_reference_entry = TierReference.objects.filter(collection__name=collection).filter(destTierType=tierType).first()
        return tier_reference_entry

    if kwargs.get('tiers'):
        tiers = kwargs.get('tiers')
        
    else:
        # set default tier values
        tiers = {
            "text": "text",
            "gloss": "gloss",
            "translation": "translation"
            }
        
    # Check if the file name is listed in TierReference
    for key in tiers:
        tier_reference_entry = TierReference.objects.filter(transcriptELANfile__name=file_name).filter(destTierType=key).first()

        if tier_reference_entry:
            tiers[key] = tier_reference_entry.sourceTierType
        else:
            file = File.objects.filter(name=file_name).first()
            search = get_from_collection(file.session.collection, key)
            if search:
                tiers[key] = search.sourceTierType
            
    return tiers
    

def get_aligned_glossing(transcript, combined_gloss_filter):
        gloss = TranscriptELAN.objects.filter(combined_gloss_filter).filter(
            startTime=transcript.startTime, endTime=transcript.endTime
            ).exclude(id=transcript.id).first()
        
        transcript.text = transcript.annotation.split()
        transcript.textgloss = {}
        
        if gloss:
            transcript.gloss = gloss.annotation.split()
        
            # store word/gloss pairs as a dictionary
            for i in range(0, len(transcript.text)):
                transcript.textgloss[transcript.text[i]] = transcript.gloss[i]
        
        else:
            # store word/gloss pairs as a dictionary
            for i in range(0, len(transcript.text)):
                transcript.textgloss[transcript.text[i]] = None
            
        return transcript.textgloss

def cleanup(temp_dir):
        # Clean up temporary files in the specified directory
        for item_name in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item_name)
            try:
                if os.path.isdir(item_path) and item_name.startswith("tmp"):
                    # Recursively remove the folder
                    shutil.rmtree(item_path)
                    logger.info(f"Deleted temporary folder: {item_path}")
            except Exception as e:
                logger.critical(f"Error deleting temporary folder {item_path}: {e}")
        
def extract_audio_fragment(audio_path, temp_dir, start_time, end_time):
    temp_file = None  # Initialize temp_file outside the try block
    try:
        temp_file = NamedTemporaryFile(delete=False, suffix='.mp3', dir=temp_dir)

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
            
        logger.info("FILE_NAME: " + temp_file.name)

        return temp_file.name  # Return the temporary file path containing the audio fragment in mp3 format

    except subprocess.CalledProcessError as e:
        # Handle errors if ffmpeg command fails
        logger.error(f"Error extracting audio fragment: {e}")
        return None

    finally:
        # Close and delete the temporary file
        temp_file.close()
            
def get_audio(transcript):
    if transcript.video and transcript.startTime and transcript.endTime:
        uploads = os.path.join(MEDIA_ROOT, 'uploads')
        temp_dir = tempfile.mkdtemp(dir=uploads)
        v_path = os.path.join('uploads', transcript.video.name + "." + transcript.video.type)
        audio_path = os.path.join(MEDIA_ROOT, v_path)
                                                                
        start_time = transcript.startTime
        end_time = transcript.endTime
                                
        # Convert start_time_str and end_time_str to timedelta objects
        start_time = parse_duration(start_time)
        end_time = parse_duration(end_time)

        audio_fragment_path = extract_audio_fragment(audio_path, temp_dir, start_time, end_time)
        
        if audio_fragment_path:
            relative_path = os.path.relpath(audio_fragment_path, MEDIA_ROOT)
            relative_path = os.path.join("/uploads", relative_path)
            return relative_path
        
            
        return None
    
def remove_apostrophes(input_string):
    # Split the input string by comma followed by space and handle each tuple
    tuples = input_string.split(', ')
    
    # Process each tuple to remove apostrophes
    cleaned_tuples = []
    for tuple_str in tuples:
        # Remove the apostrophes by replacing them with an empty string
        cleaned_tuple = tuple_str.replace("'", "")
        cleaned_tuples.append(cleaned_tuple)
    
    # Join the cleaned tuples with ', ' and return the result
    return ', '.join(cleaned_tuples)
    
def extract_postprocessed(audio_path, intervals, filetype):
    uploads = os.path.join(MEDIA_ROOT, 'uploads')
    temp_file = None  # Initialize temp_file outside the try block
    
    select = 'between' + str(intervals[0])
    
    for i in range(1, len(intervals) - 1):
        between = '+between' + str(intervals[i])
        select += between
        
    select = remove_apostrophes(select)
            
    try:
        temp_file = NamedTemporaryFile(delete=False, suffix=filetype, dir=uploads)
        # Use ffmpeg to extract the audio fragment and convert it to mp3
        ffmpeg_command = [
            'ffmpeg',
            '-i', audio_path,
            '-vf', f"select='not({select})', setpts=N/FRAME_RATE/TB",
            '-af', f"aselect='not({select})', asetpts=N/SR/TB",
            '-q:a', '0',  # Set the audio quality (0 is the highest)
            '-map', 'a',  # Select the audio stream
            '-v', '3',
            '-y',
            temp_file.name
            ]
        subprocess.run(ffmpeg_command, check=True)
            
        return temp_file  # Return the temporary file path containing the audio fragment in mp3 format

    except subprocess.CalledProcessError as e:
        # Handle errors if ffmpeg command fails
        logger.error(f"Error extracting audio fragment: {e}")
        return None

        
def get_postprocessed_timelines(file):
    postp = Postprocess.objects.filter(transcriptELANfile=file).order_by('startTime')
        
    timestamps = []
    for o in postp:
        #process start and end times
        start_time = str(parse_duration(o.startTime).total_seconds())
        end_time = str(parse_duration(o.endTime).total_seconds())
            
        #create tuples
        timest = (start_time, end_time)
        timestamps.append(timest)
        
    return timestamps
    
    
def get_postprocessed_media(file):
    # Get associated ELAN file 
    elan_file = File.objects.filter(name=file.name, type='eaf').first()
        
    if elan_file:
        # Extract all postprocessed fragments
        logger.info("Name: " + str(elan_file.name))
        timestamps = get_postprocessed_timelines(elan_file)
        t = ("t",)
        timestamps = [t + timestamp for timestamp in timestamps]
            
        # Process media content, we use a different function depending on if it's video or audio
        v_path = os.path.join('uploads', file.name + "." + file.type)
        audio_path = os.path.join(MEDIA_ROOT, v_path)
        
        audio = ['wav', '.mp3']
        video = ['mp4', 'm4a']
        
        if file.type in audio:
            return extract_postprocessed(audio_path, timestamps, '.mp3')
        
        if file.type in video:
            return extract_postprocessed(audio_path, timestamps, '.mp4')
            
    return None
        