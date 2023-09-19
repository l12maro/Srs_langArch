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

    def get_queryset(self):
        result_list = []
        
        #retrieve query
        query = self.request.GET.get("query")
        
        #retrieve any other filters
        lang = self.request.GET.get("language")
        
        if lang:
            result_list = MetaText.objects.filter(Q(languages__name=lang))
                    
        result_list = result_list.filter(
            Q(title__icontains=query)
        )
        return result_list