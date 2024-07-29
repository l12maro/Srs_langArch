from django.urls import path

from . import views
from .views import HomePageView, SearchResultsView, ResultView

app_name = 'search'

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("results/", SearchResultsView.as_view(), name="search_results"),
    path("result/<int:resultid>", ResultView.as_view(), name="result")
]