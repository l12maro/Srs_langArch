from datetime import timedelta
import datetime
from functools import reduce
import os
from itertools import chain
from pathlib import Path
import shutil
import subprocess
from tempfile import NamedTemporaryFile, TemporaryDirectory
import tempfile
from archive import settings
from archive.settings import MEDIA_ROOT, MEDIA_URL
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView, ListView
from django.utils.dateparse import parse_duration
from browse.models import File, Session, Collection, Person, Genre, Postprocess, TierReference, TranscriptELAN, Language
from django.db.models import Q
from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchVector, SearchRank


class HomePageView(TemplateView):
    template_name = 'search\\base_search.html'
    
class SearchResultsView(ListView):
    model = Session
    template_name = 'search\\base_results.html'
    context_object_name = 'search_results'
    paginate_by=5
    
    def get_context_data(self, **kwargs):
        '''
        creates a context entry for each of the models to be searched
        @returns context as a dictionary
        '''
        
        models = [Collection, Session, File, Person, Genre, TranscriptELAN]
        names = ['Collection', 'Session', 'File', 'Person', 'Genre', 'TranscriptELAN']
        context = super(SearchResultsView, self).get_context_data(**kwargs)

        for i in range(0, len(models)):
            context[names[i]] = self.get_queryset(model=models[i])
        
        return context
    
    def cleanup(self, temp_dir):
        # Clean up temporary files in the specified directory
        for item_name in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item_name)
            try:
                if os.path.isdir(item_path) and item_name.startswith("tmp"):
                    # Recursively remove the folder
                    shutil.rmtree(item_path)
                    print(f"Deleted temporary folder: {item_path}")
            except Exception as e:
                print(f"Error deleting temporary folder {item_path}: {e}")
        
    def extract_audio_fragment(self, audio_path, temp_dir, start_time, end_time):
        temp_file = None  # Initialize temp_file outside the try block
        try:
            print(temp_dir)
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
            
            print("FILE_NAME: " + temp_file.name)

            return temp_file.name  # Return the temporary file path containing the audio fragment in mp3 format

        except subprocess.CalledProcessError as e:
            # Handle errors if ffmpeg command fails
            print(f"Error extracting audio fragment: {e}")
            return None

        finally:
            # Close and delete the temporary file
            temp_file.close()
            #os.unlink(temp_file.name)
            
    def get_audio(self, transcript, base_dir, temp_dir):
        if transcript.video and transcript.startTime and transcript.endTime:
            v_path = os.path.join('uploads', transcript.video.name + "." + transcript.video.type)
            audio_path = os.path.join(base_dir, v_path)
                                                                
            start_time = transcript.startTime
            end_time = transcript.endTime
                                
            # Convert start_time_str and end_time_str to timedelta objects
            start_time = parse_duration(start_time)
            end_time = parse_duration(end_time)

            audio_fragment_path = self.extract_audio_fragment(audio_path, temp_dir, start_time, end_time)

            if audio_fragment_path:
                relative_path = os.path.relpath(audio_fragment_path, MEDIA_ROOT)
                relative_path = os.path.join("/uploads", relative_path)
                return relative_path
            
            return None
    
    def get_filters(self):
        '''
        A function that checks the content of the potential search filters that the user can call
        @returns true if there is a filter to be applied
        @returns a list of the filters to apply
        @returns a list of the fields to search
        '''
        filtered = False
        filters = []
        where = []
        
        #collection filter
        coll = self.request.GET.get("coll")
        if coll:
            filtered = True
            filters.append(("coll", coll))
            
        speakers = self.request.GET.get("s")
        if speakers:
            filtered = True
            filters.append(("s", speakers))
            
        genre = self.request.GET.get("genre")
        if genre:
            filtered = True
            filters.append(("genre", genre))
        
        lang = self.request.GET.get("lang")
        if lang:
            filtered = True
            filters.append(("lang", lang))                

        w = self.request.GET.get("w")
        if w:
            where.append(w)
        else:
            where = ['text', 'title', 'metadata']
    
        return filtered, filters, where
    
    def apply_filters(self, model, queryresult, filters, queried=False):
        '''
        Filters a queryset according to metadata criteria
        @returns a list of queried objects
        '''        
        # If no textual search, then the request was made from the sidebar
        # For now, we only return collections and sessions in those searches
        if queried == False:
            for f in filters:
                if model == Collection:
                    if f[0] == "lang":
                        queryresult = Collection.objects.filter(Q(language__name=f[1]) | Q(working_language__name=f[1])).distinct
                        filters = filters[1:]
                        queried = True
                        
                if model == Session:           
                    if f[0] == "coll":
                        queryresult = Session.objects.filter(collection__name=f[1])
                        return queryresult   
                            
                    if f[0] == "s":
                        people = Person.objects.filter(role='speaker')
                        speaker = people.get(tier=f[1])
                        queryresult = speaker.ses_speaker.all()
                        filters = filters[1:]
                        queried = True
                        
                    if f[0] == "genre":
                        g = Genre.objects.get(name=f[1])
                        queryresult = g.ses_genres.all()
                        filters = filters[1:]
                        queried = True

                    if f[0] == "lang":
                        queryresult = Session.objects.filter(Q(languages__name=f[1]) | Q(working_languages__name=f[1])).distinct
                        filters = filters[1:]
                        queried = True
                                
        # When the user is making a textual search, we want to return as many
        # coincidences across models as possible
        if queried == True:
            if model == TranscriptELAN:
                for f in filters:
                    if f[0] == "coll":
                        queryresult = queryresult.filter(transcriptELANfile__session__collection__name=f[1])
                        
                    if f[0] == "s":
                        queryresult = queryresult.filter(transcriptELANfile__session__speakers__tier=f[1])
                    
            if model == Session:     
                for f in filters:      
                    if f[0] == "coll":
                        queryresult = queryresult.filter(collection__name=f[1])

                    if f[0] == "s":
                        #people = Person.objects.filter(role='speaker')
                        #speaker = people.get(tier=f[1])
                        queryresult = queryresult.filter(Q(speakers__tier=f[1]))
                        
                    if f[0] == "genre":
                        queryresult = queryresult.filter(Q(genre__name=f[1]))

                    if f[0] == "lang":
                        queryresult = queryresult.filter(Q(languages__name=f[1]) | Q(working_languages__name=f[1])).distinct
                    
            
        return queryresult   

    def get_tiers(self, file_name):
        
        def get_from_collection(collection, tierType):
            # Check if the collection is listed in TierReference
            tier_reference_entry = TierReference.objects.filter(collection__name=collection).filter(destTierType=tierType).first()
            return tier_reference_entry
            
        # set default values
        tiers = {
            "text": "text",
            "gloss": "gloss",
            "translation": "translation"
         }
        
        # Check if the file name is listed in TierReference
        tier_reference_entry = TierReference.objects.filter(transcriptELANfile__name=file_name)

        if tier_reference_entry.first():
            print("yes")
            for key in tiers:
                print("destiny tier: " + key)
                tier_reference_entry.filter(destTierType=key)
                if tier_reference_entry.first():
                    tiers[key] = tier_reference_entry.sourceTierType
                    print("source tier (from file): " + tiers[key])
                else:
                    search = get_from_collection(tier_reference_entry.first().collection, key)
                    if search:
                        tiers[key] = search.sourceTierType
                        print("source tier (from collection): " + tiers[key])


        # If there is no listing in TierReference, we check the collection
        else:
            file = File.objects.filter(name=file_name).first()
            for key in tiers:
                search = get_from_collection(file.session.collection, key)
                if search:
                    tiers[key] = search.sourceTierType
                    print("source tier (from collection): " + tiers[key])
            
            
        return tiers["text"], tiers["gloss"], tiers["translation"]
    
    def get_aligned_glossing(self, transcript, combined_gloss_filter):
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
                    
    def get_queryset(self, model, **kwargs):      
        '''
        Queries the object of the database model for search matches
        @returns a list of queried objects
        '''
        query = self.request.GET.get("q")

        result_list = model.objects.none()
        filtered, filters, where = self.get_filters()

        # when no query is performed, it means the user is using the sidebar and not
        # performing a textual search
        if not query:
            result_list = model.objects.none()
            if filtered:
                result_list = self.apply_filters(model, result_list, filters, False)
            
            return result_list

        else:
            # For textual search, we first want to check any constraints on 
            # where to perform the search.
            # There are three possible values: text, title and metadata
            # However, the user can select one or more of these values
            
            titleM = [Collection, Session]
            
            for w in where:
                
                # When the user only wants textual matches, we look only
                # in the indexed texts
                if w == "text":
                    if model == TranscriptELAN:
                        searchq = SearchQuery(query)
                        search_headline = SearchHeadline("annotation", searchq)
                        
                        # We get all the distinct transcripts to search
                        # TODO: Figure out how to apply additional filters
                        # if filtered:
                        #     result_list = self.apply_filters(model, queryresult=eng_result, filters=filters, queried=True)
                        distinct_files = TranscriptELAN.objects.values_list('transcriptELANfile__name', flat=True).distinct()
                        distinct_files = list(distinct_files)
                        
                                        
                        queriesText = []
                        queriesGlosses = []
                        queriesTranslation = []
                        
                        # we search for each file
                        for file_name in distinct_files:
                            #get the tier_types
                            text, gloss, translation = self.get_tiers(file_name)

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
                        
                        srs = True
                        eng = True
                        if filtered:
                        # First we check if we only want results
                        # in English or in Tsuut'ina or both
                            for f in filters:
                                if f[0] == "lang":
                                    if f[1] == "srs":
                                        eng = False
                                    else:
                                        srs = False
                                                        
                        base_dir = settings.MEDIA_ROOT
                        temp_dir = tempfile.mkdtemp(dir=os.path.join(base_dir, 'uploads'))
                        

                        if srs:
                            result_list = model.objects.annotate(headline=search_headline
                                                                ).filter(combined_text_filter).filter(search_vector=query)
                                
                            for transcript in result_list:
                                # Get glossing if there is any
                                transcript.textgloss = self.get_aligned_glossing(transcript, combined_gloss_filter)
                                        
                                # Get translation
                                translation = TranscriptELAN.objects.filter(combined_trans_filter).filter(
                                    startTime=transcript.startTime, endTime=transcript.endTime
                                    ).exclude(id=transcript.id).first()
                                
                                transcript.translation = translation.annotation if translation else None
                                transcript.audio = self.get_audio(transcript, base_dir, temp_dir)
                            
                            if eng:
                                eng_result = model.objects.annotate(headline=search_headline
                                                                ).filter(combined_trans_filter).filter(search_vector=query)
                                                                
                                # Get text
                                for transcript in eng_result:
                                    transcript.translation = transcript.annotation
                                    transcript.audio = self.get_audio(transcript, base_dir, temp_dir)
                                    
                                    text = TranscriptELAN.objects.filter(combined_text_filter).filter(
                                    startTime=transcript.startTime, endTime=transcript.endTime
                                    ).exclude(id=transcript.id).first()
                                    
                                    if text:
                                        transcript.annotation = text.annotation
                                        transcript.textglossing = self.get_aligned_glossing(transcript, combined_gloss_filter)
                                        
                                if len(result_list) > 0:
                                    result_list = result_list.union(eng_result)
                                else:
                                    result_list = eng_result
                                
                        else:
                            result_list = model.objects.annotate(headline=search_headline
                                                            ).filter(combined_trans_filter).filter(search_vector=query)                
                            
                            for transcript in result_list:
                                transcript.audio = self.get_audio(transcript, base_dir, temp_dir)
                                transcript.translation = transcript.annotation
                                    
                                text = TranscriptELAN.objects.filter(combined_text_filter).filter(
                                startTime=transcript.startTime, endTime=transcript.endTime
                                ).exclude(id=transcript.id).first()
                                
                                if text:
                                    transcript.annotation = text.annotation
                                    transcript.textglossing = self.get_aligned_glossing(transcript, combined_gloss_filter)
                                    
                            
                                        
                        '''
                        base_dir = settings.MEDIA_ROOT
                        temp_dir = tempfile.mkdtemp(dir=os.path.join(base_dir, 'uploads'))
                                
                        for transcript in result_list:
                            transcript.audio = self.get_audio(transcript, base_dir, temp_dir)
                            
                        '''
                                                      

                if w == "title":
                    if model in titleM:
                        result_list = model.objects.filter(Q(title__icontains=query))
                        if filtered:
                            result_list = self.apply_filters(model, queryresult=result_list, filters=filters, queried=True)
                
                if w == "metadata":
                    if model in titleM:
                        result_list = model.objects.filter(title__icontains=query)
                        
                    if model == Genre:
                        result_list = model.objects.filter(Q(name__icontains=query)).filter(Q(parent_genre=None))
                            
                    if model == Person:
                        result_list = model.objects.filter(Q(name__icontains=query)).filter(Q(role="speaker"))
                    
                    if filtered:
                        result_list = self.apply_filters(model, queryresult=result_list, filters=filters, queried=True)
                        
            
            return result_list
            

        
    def get(self, request, *args, **kwargs):
        '''
        checks if there are any objects to retrieve
        @returns queryset as context
        '''
        self.object_list = []
        #remove the previous temp folders
        uploads = os.path.join(MEDIA_ROOT, 'uploads')
        
        self.cleanup(uploads)
        queryset = self.get_context_data()

        # Check if the queryset is empty (no results)
        if not queryset:
            return render(request, self.template_name, context={'search_results': None})
        
        # Pass the results to the template
        #return super().get(request, *args, **kwargs)
        return render(request, self.template_name, context=queryset)

