from django.urls import path

from . import views
from .views import IndexView

app_name = 'browse'
urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("about/", views.about, name="about"),
    path("<str:collection>/", views.coll, name="collection"),
    path("<str:collection>/<str:session>/", views.ses, name="session"),
    path("<str:collection>/<str:session>/<str:filetype>", views.detail, name="detail"),
]