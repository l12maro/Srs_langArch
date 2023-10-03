from django.urls import path

from . import views

app_name = 'browse'
urlpatterns = [
    path("", views.IndexArchiveView.as_view(), name="index"),
    path("about/", views.about, name="about"),
    path("<str:collection>/", views.CollectionView.as_view(), name="collection"),
    #path("<str:collection>/", views.coll, name="collection"),
    path("<str:collection>/<str:session>/", views.SessionView.as_view(), name="session"),
    path("<str:collection>/<str:session>/<str:filename>", views.TextView.as_view(), name="detail"),
]