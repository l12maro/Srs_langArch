import os
from archive.settings import MEDIA_ROOT
from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from browse.models import File, Session, Collection, Person, Genre, TranscriptELAN
from django.db.models import Q
from django.contrib.postgres.search import SearchHeadline, SearchQuery
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from search.helpers import *


class HomePageView(TemplateView):
    template_name = 'search\\base_search.html'
    
class ResultView(LoginRequiredMixin, ListView):
    model = TranscriptELAN
    template_name = 'search\\base_result.html'
    context_object_name = 'result'
    
    def get_queryset(self):
        transcript_id = self.kwargs['resultid']
        
        result = []
        
        combined_text_filter, combined_gloss_filter, combined_trans_filter = get_querysets()
        
        srs = TranscriptELAN.objects.filter(combined_text_filter).filter(id=transcript_id).first()
        
        if srs:
            transcript = get_result_srs(srs)
                  
        else:
            eng = TranscriptELAN.objects.filter(combined_trans_filter).filter(id=transcript_id).first()
            transcript = get_result_eng(eng)
            
            
        return transcript
    
class SearchResultsView(LoginRequiredMixin, ListView):
    model = TranscriptELAN
    template_name = 'search\\base_search_results.html'
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
                        
                        combined_text_filter, combined_gloss_filter, combined_trans_filter = get_querysets()
                        
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
                            
                        
                        if srs:
                            result_list = model.objects.annotate(headline=search_headline
                                                                ).filter(combined_text_filter).filter(search_vector=query)
                                
                            for transcript in result_list:
                                transcript = get_result_srs(transcript)
                            
                            if eng:
                                eng_result = model.objects.annotate(headline=search_headline
                                                                ).filter(combined_trans_filter).filter(search_vector=query)
                                                                
                                # Get text
                                for transcript in eng_result:
                                    transcript = get_result_eng(transcript)                  
                                        
                                if len(result_list) > 0:
                                    result_list = result_list.union(eng_result)
                                else:
                                    result_list = eng_result
                                
                                
                        else:
                            result_list = model.objects.annotate(headline=search_headline
                                                            ).filter(combined_trans_filter).filter(search_vector=query)                
                            
                            for transcript in result_list:
                                transcript = get_result_eng(transcript)
                                
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
        
        cleanup(uploads)
        queryset = self.get_context_data()

        # Check if the queryset is empty (no results)
        if not queryset:
            return render(request, self.template_name, context={'search_results': None})
        
        # Pass the results to the template
        #return super().get(request, *args, **kwargs)
        return render(request, self.template_name, context=queryset)

