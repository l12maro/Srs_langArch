from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView, ListView
from browse.models import MetaText
from django.db.models import Q

class HomePageView(TemplateView):
    template_name = 'search\\base_search.html'
    
class SearchResultsView(ListView):
    model = MetaText
    template_name = 'search\\base_results.html'
    context_object_name = 'search_results'

    def get_queryset(self):
        result_list = []
        
        #retrieve query
        query = self.request.GET.get("query")
        
        if query:
        
            #retrieve any other filters
            lang = self.request.GET.get("language")
            
            if lang:
                result_list = MetaText.objects.filter(Q(languages__name=lang)).filter(Q(title__icontains=query))
            
            else:
                result_list = MetaText.objects.filter(
                Q(title__icontains=query)
                )
        else:
            result_list = MetaText.objects.none()
        
        return result_list
    
    def get(self, request, *args, **kwargs):
        # Retrieve the queryset
        queryset = self.get_queryset()

        # Check if the queryset is empty (no results)
        if not queryset:
            return render(request, self.template_name, context={'search_results': None})
        
        # Pass the results to the template
        return super().get(request, *args, **kwargs)