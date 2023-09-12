from django.urls import path

from . import views
from .views import HomePageView, SearchResultsView


urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("results/", SearchResultsView.as_view(), name="results"),
]