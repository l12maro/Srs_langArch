from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("<str:collection>/", views.coll, name="collection"),
    path("<str:collection>/<str:session>/", views.ses, name="session"),
    path("<str:collection>/<str:session>/<str:filetype>", views.detail, name="detail"),
]