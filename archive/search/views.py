from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView, ListView
from browse.models import File, Session, Collection, Person, Genre, Postprocess, TierReference, TranscriptELAN, Language
from django.db.models import Q


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
        coll = self.request.GET.get("collection")
        if coll:
            filtered = True
            filters.append(("collection", coll))
            
        speakers = self.request.GET.get("speakers")
        if speakers:
            filtered = True
            filters.append(("speakers", speakers))
            
        genre = self.request.GET.get("genre")
        if genre:
            filtered = True
            filters.append(("genre", genre))
        
        lang = self.request.GET.get("language")
        if lang:
            filtered = True
            filters.append(("language", lang))                

        w = self.request.GET.get("where")
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
            f = filters[0]

            if model == Collection:
                if f[0] == "language":
                    queryresult = Collection.objects.filter(Q(language__name=f[1]) | Q(working_language__name=f[1])).distinct
                    
            if model == Session:           
                if f[0] == "collection":
                    queryresult = Session.objects.filter(collection__name=f[1])
                        
                if f[0] == "speakers":
                    people = Person.objects.filter(role='speaker')
                    speaker = people.get(tier=f[1])
                    queryresult = speaker.ses_speaker.all()
                    
                if f[0] == "genre":
                    g = Genre.objects.get(name=f[1])
                    queryresult = g.ses_genres.all()

                if f[0] == "language":
                    queryresult = Session.objects.filter(Q(languages__name=f[1]) | Q(working_languages__name=f[1])).distinct
                    
            return queryresult
        
        # When the user is making a textual search, we want to return as many
        # coincidences across models as possible
        '''
        if queried == True:
            
            for f in filters[0]:
            
            # TODO: in text search, we need to make sure that we are taking
            # the right tier
            # For different collections and texts, we want different tiers
            # Based on that, we can apply language filters


                        
        '''
            


                                   

                    
            
    '''
    def apply_filters(self, model, queryresult, queried=False):
        coll = self.request.GET.get("collection")
        if coll:
            if model == Session:
                if queried==False:
                    queryresult = Session.objects.filter(collection__name=coll)

                else:
                    queryresult = queryresult.filter(collection__name=coll)
                    
            else: 
                queryresult = model.objects.none()
                    
        #speaker
        speakers = self.request.GET.get("speakers")
        if speakers:            
            if model == Session:
                if queried==False:
                    people = Person.objects.filter(role='speaker')
                    speaker = people.get(tier=speakers)
                    queryresult = speaker.ses_speaker.all()
                    queried = True
                        
                else:
                    queryresult = queryresult.filter(speakers__tier=speakers)
            else:
                queryresult = None
                
        #genre
        genre = self.request.GET.get("genre")
        if genre:
            if model == Session:
                if queried==False:
                    g = Genre.objects.get(name=genre)
                    queryresult = g.ses_genres.all()
                    queried = True
                    
                else:
                    queryresult = queryresult.filter(genre=genre)
        
        #language
        lang = self.request.GET.get("language")                
        if lang:
            if model == Collection:
                queryresult = queryresult.filter(Q(language__name=lang))
            elif model == Session:
                queryresult = queryresult.filter(Q(languages__name=lang))
                    

                    
        return queryresult
    '''
    def get_queryset(self, model, **kwargs):      
        '''
        Queries the object of the database model for search matches
        @returns a list of queried objects
        '''
        query = self.request.GET.get("query")
        
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
                        if query == '*':
                            result_list = model.objects.all()
                                
                        else:
                            result_list = model.objects.filter(Q(annotation__icontains=query))
                        
                if w == "title":
                    if model in titleM:
                        if query == '*':
                            result_list = model.objects.all()
                        else:
                            result_list = model.objects.filter(Q(title__icontains=query))
                
                if w == "metadata":
                    if query == '*':
                        if model in titleM:
                            result_list = model.objects.all()
                            
                        # For the model Genre, we only want main genres
                        if model == Genre:
                            result_list = model.objects.filter(parent_genre=None)
                            
                        # For the model Person, we only want speakers
                        if model == Person:
                            result_list = model.objects.filter(role="speaker")
                            
                    else:
                        #TODO: work on apply_filters()
                        if model in titleM:
                            result_list = model.objects.filter(title__icontains=query)
                        
                        if model == Genre:
                            result_list = model.objects.filter(Q(name__icontains=query)).filter(Q(parent_genre=None))
                            
                        if model == Person:
                            result_list = model.objects.filter(Q(name__icontains=query)).filter(Q(role="speaker"))
                        
            
            return result_list
            

                
            
        '''
        if query:
            if query == '*':
                if model == Person:
                    result_list = model.objects.filter(Q(role="speaker"))
                    
                else:
                    result_list = model.objects.all()
                
                if filtered:
                    result_list = self.apply_filters(model, result_list, filters, queried=True)    
            
            else:
                if model == Collection or model == Session:
                    result_list = model.objects.filter(Q(title__icontains=query))
                    
                elif model == TranscriptELAN:
                    result_list = model.objects.filter(Q(annotation__icontains=query))
                        
                elif model == File:
                    #also match with type
                    result_list = model.objects.filter(Q(type=query))
                    
                else:
                    result_list = model.objects.filter(Q(name__icontains=query))
                    
                if filtered:
                    result_list = self.apply_filters(model, result_list, filters, queried=True)
                
        '''
            

        
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

