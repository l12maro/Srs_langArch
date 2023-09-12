from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView, ListView
from browse.models import MetaText

class HomePageView(TemplateView):
    template_name = 'search\search.html'
    
class SearchResultsView(ListView):
    model = MetaText
    template_name = 'search\\results.html'
