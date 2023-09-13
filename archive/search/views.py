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

    def get_queryset(self): # new
        return MetaText.objects.filter(
            Q(title__contains='5')
        )