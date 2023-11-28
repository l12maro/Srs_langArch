from datetime import timedelta
import datetime
import os
from pathlib import Path
import subprocess
from tempfile import NamedTemporaryFile
from archive import settings
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
    
    def extract_audio_fragment(self, audio_path, start_time, end_time):
        try:
            temp_file = NamedTemporaryFile(delete=False, suffix='.mp3')

            # Use ffmpeg to extract the audio fragment and convert it to mp3
            ffmpeg_command = [
                'ffmpeg',
                '-i', audio_path,
                '-ss', str(start_time.total_seconds()),
                '-to', str(end_time.total_seconds()),
                '-q:a', '0',  # Set the audio quality (0 is the highest)
                '-map', 'a',  # Select the audio stream
                temp_file.name
            ]
            subprocess.run(ffmpeg_command, check=True)

            return temp_file.name  # Return the temporary file path containing the audio fragment in mp3 format

        except subprocess.CalledProcessError as e:
            # Handle errors if ffmpeg command fails
            print(f"Error extracting audio fragment: {e}")
            return None

        finally:
            # Close and delete the temporary file
            temp_file.close()
            os.unlink(temp_file.name)
    
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
            '''
                if model == TranscriptELAN:
                    if f[0] == "coll":
                        queryresult = TranscriptELAN.objects.filter(transcriptELANfile__session__collection__name=f[1])
                        filters = filters[1:]
                        queried = True
                            
                    if f[0] == "s":
                        people = Person.objects.filter(role='speaker')
                        speaker = people.get(tier=f[1])
                        queryresult = speaker.ses_speaker.all()
                        filters = filters[1:]
                        queried = True
                        
                    if f[0] == "genre":
                        g = Genre.objects.get(transcriptELANfile__session__genre__name=f[1])
                        queryresult = g.ses_genres.all()
                        filters = filters[1:]
                        queried = True
            '''
                                
        # When the user is making a textual search, we want to return as many
        # coincidences across models as possible
        if queried == True:
            # TODO: in text search, we need to make sure that we are taking
            # the right tier
            # For different collections and texts, we want different tiers
            # Based on that, we can apply language filters
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
                        
                        #first we retrieve the text_types to search
                        texttype = "text"
                        glosstype = "gloss"
                        translationtype = "translation"
                        
                        # TODO: get text_types
                        
                        if filtered:
                        # First we check if we only want results
                        # in English or in Tsuut'ina or both
                            for f in filters:
                                if f[0] == "lang":
                                    if f[1] == "srs":
                                        result_list = model.objects.annotate(headline=search_headline
                                                                                  ).filter(textType=texttype
                                                                                           ).filter(search_vector=query)
                                        if len(filters) > 1:
                                            result_list = self.apply_filters(model, queryresult=result_list.text, filters=filters, queried=True)
                                        
                                    if f[1] == "eng":
                                        translation = model.objects.annotate(headline=search_headline
                                                                                         ).filter(textType=translationtype
                                                                                                  ).filter(search_vector=query)
                                        if len(filters) > 1:
                                            translation = self.apply_filters(model, queryresult=result_list, filters=filters, queried=True)
                                            
                                        #TODO: get text and gloss 
                                    break
                        
                        else: 
                            result_list = model.objects.annotate(headline=search_headline).filter(search_vector=query)

                                
                        # process result_list
                        

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
        queryset = self.get_context_data()

        # Check if the queryset is empty (no results)
        if not queryset:
            return render(request, self.template_name, context={'search_results': None})
        
        # Pass the results to the template
        #return super().get(request, *args, **kwargs)
        return render(request, self.template_name, context=queryset)

