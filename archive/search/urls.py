from django.urls import path

from . import views
from .views import HomePageView, SearchResultsView

app_name = 'search'

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("results/", SearchResultsView.as_view(), name="results"),
]