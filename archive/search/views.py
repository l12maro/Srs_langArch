from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView, ListView
from browse.models import File, Session, Collection, Person, Genre
from django.db.models import Q


class HomePageView(TemplateView):
    template_name = 'search\\base_search.html'
    
class SearchResultsView(ListView):
    model = Session
    template_name = 'search\\base_results.html'
    context_object_name = 'search_results'
    
    def get_context_data(self, **kwargs):
        models = [Collection, Session, File, Person, Genre]
        names = ['Collection', 'Session', 'File', 'Person', 'Genre']
        context = super(SearchResultsView, self).get_context_data(**kwargs)

        for i in range(0, len(models)):
            context[names[i]] = self.get_queryset(model=models[i])
        
        return context
    
    def apply_filters(self, model, queryresult, queried=True):
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
        
        #language
        lang = self.request.GET.get("language")                
        if lang:
            if model == Collection:
                queryresult = queryresult.filter(Q(language__name=lang))
            elif model == Session:
                queryresult = queryresult.filter(Q(languages__name=lang))
                    

                    
        return queryresult

    def get_queryset(self, model, **kwargs):      
        #retrieve query
        query = self.request.GET.get("query")
        
        result_list = model.objects.none()
        
        if query:
            if query == '*':
                result_list = model.objects.all()
                result_list = self.apply_filters(model, result_list)    
            
            else:
                if model == Collection or model == Session:
                    result_list = model.objects.filter(Q(title__icontains=query))
                        
                if model == File:
                    #also match with type
                    result_list = model.objects.filter(Q(type=query))
                    
                else:
                    result_list = model.objects.filter(Q(name__icontains=query))
                
                result_list = self.apply_filters(model, result_list)
                
        else:
            result_list = model.objects.none()
            result_list = self.apply_filters(model, result_list, False)

        return result_list
        
    def get(self, request, *args, **kwargs):
        # TODO: Add an if statement so that all collection is searched only if no advanced settings are selected,
        # Also that the filters are passed here for the query
        # Retrieve the queryset
        # Set the object_list attribute
        self.object_list = []  
        queryset = self.get_context_data()

        # Check if the queryset is empty (no results)
        if not queryset:
            return render(request, self.template_name, context={'search_results': None})
        
        # Pass the results to the template
        #return super().get(request, *args, **kwargs)
        return render(request, self.template_name, context=queryset)

